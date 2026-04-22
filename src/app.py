import os
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from psycopg2 import Error as DatabaseError

from db import execute, fetch_all, fetch_one
from security import hash_password


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

STATUSES = ["Aberta", "Em andamento", "Concluida", "Cancelada"]


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def money_to_decimal(value, fallback="0"):
    normalized = (value or fallback).replace("R$", "").strip()
    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return Decimal(fallback)


@app.template_filter("money")
def money_filter(value):
    value = Decimal(value or 0)
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


@app.context_processor
def inject_navigation_state():
    return {"current_path": request.path, "statuses": STATUSES}


@app.errorhandler(DatabaseError)
def handle_database_error(error):
    return render_template("database_error.html", error=error), 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("usuario_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        usuario = fetch_one("SELECT * FROM usuarios WHERE email = %s", [email])

        if usuario and usuario["senha_hash"] == hash_password(senha):
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            flash("Login realizado com sucesso.", "success")
            return redirect(url_for("dashboard"))

        flash("E-mail ou senha invalidos.", "error")

    return render_template("login.html")


@app.get("/logout")
def logout():
    session.clear()
    flash("Sessao encerrada.", "success")
    return redirect(url_for("login"))


@app.get("/")
@login_required
def dashboard():
    stats = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM clientes) AS clientes,
            (SELECT COUNT(*) FROM veiculos) AS veiculos,
            (SELECT COUNT(*) FROM servicos) AS servicos,
            (SELECT COUNT(*) FROM ordens_servico) AS ordens
        """
    )
    recentes = fetch_all(
        """
        SELECT os.id, os.data_abertura, os.status, c.nome AS cliente,
               v.placa, s.nome AS servico, os.valor_total
        FROM ordens_servico os
        INNER JOIN veiculos v ON v.id = os.veiculo_id
        INNER JOIN clientes c ON c.id = v.cliente_id
        INNER JOIN servicos s ON s.id = os.servico_id
        ORDER BY os.data_abertura DESC, os.id DESC
        LIMIT 6
        """
    )
    return render_template("dashboard.html", stats=stats, recentes=recentes)


@app.get("/clientes")
@login_required
def clientes():
    q = request.args.get("q", "").strip()
    order_key = request.args.get("order", "nome")
    orders = {
        "nome": "nome ASC",
        "cpf": "cpf ASC",
        "recentes": "criado_em DESC",
    }
    params = []
    where = ""
    if q:
        where = "WHERE nome ILIKE %s OR cpf ILIKE %s OR telefone ILIKE %s"
        params = [f"%{q}%", f"%{q}%", f"%{q}%"]

    rows = fetch_all(
        f"""
        SELECT id, nome, cpf, telefone, email, criado_em
        FROM clientes
        {where}
        ORDER BY {orders.get(order_key, orders["nome"])}
        """,
        params,
    )
    return render_template("clientes.html", clientes=rows, q=q, order=order_key)


@app.route("/clientes/novo", methods=["GET", "POST"])
@login_required
def cliente_novo():
    if request.method == "POST":
        try:
            execute(
                """
                INSERT INTO clientes (nome, cpf, telefone, email)
                VALUES (%s, %s, %s, %s)
                """,
                [
                    request.form["nome"].strip(),
                    request.form["cpf"].strip(),
                    request.form["telefone"].strip(),
                    request.form.get("email", "").strip() or None,
                ],
            )
            flash("Cliente cadastrado.", "success")
            return redirect(url_for("clientes"))
        except DatabaseError as error:
            flash(f"Nao foi possivel cadastrar: {error.diag.message_primary}", "error")

    return render_template("cliente_form.html", cliente=None)


@app.route("/clientes/<int:cliente_id>/editar", methods=["GET", "POST"])
@login_required
def cliente_editar(cliente_id):
    cliente = fetch_one("SELECT * FROM clientes WHERE id = %s", [cliente_id])
    if not cliente:
        flash("Cliente nao encontrado.", "error")
        return redirect(url_for("clientes"))

    if request.method == "POST":
        try:
            execute(
                """
                UPDATE clientes
                SET nome = %s, cpf = %s, telefone = %s, email = %s
                WHERE id = %s
                """,
                [
                    request.form["nome"].strip(),
                    request.form["cpf"].strip(),
                    request.form["telefone"].strip(),
                    request.form.get("email", "").strip() or None,
                    cliente_id,
                ],
            )
            flash("Cliente atualizado.", "success")
            return redirect(url_for("clientes"))
        except DatabaseError as error:
            flash(f"Nao foi possivel atualizar: {error.diag.message_primary}", "error")

    return render_template("cliente_form.html", cliente=cliente)


@app.post("/clientes/<int:cliente_id>/excluir")
@login_required
def cliente_excluir(cliente_id):
    execute("DELETE FROM clientes WHERE id = %s", [cliente_id])
    flash("Cliente excluido.", "success")
    return redirect(url_for("clientes"))


@app.get("/veiculos")
@login_required
def veiculos():
    q = request.args.get("q", "").strip()
    order_key = request.args.get("order", "placa")
    orders = {
        "placa": "v.placa ASC",
        "marca": "v.marca ASC, v.modelo ASC",
        "cliente": "c.nome ASC",
        "ano": "v.ano DESC",
    }
    params = []
    where = ""
    if q:
        where = """
        WHERE v.placa ILIKE %s
           OR v.marca ILIKE %s
           OR v.modelo ILIKE %s
           OR c.nome ILIKE %s
        """
        params = [f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"]

    rows = fetch_all(
        f"""
        SELECT v.id, v.placa, v.marca, v.modelo, v.ano, c.nome AS cliente
        FROM veiculos v
        INNER JOIN clientes c ON c.id = v.cliente_id
        {where}
        ORDER BY {orders.get(order_key, orders["placa"])}
        """,
        params,
    )
    return render_template("veiculos.html", veiculos=rows, q=q, order=order_key)


@app.route("/veiculos/novo", methods=["GET", "POST"])
@login_required
def veiculo_novo():
    clientes_opcoes = fetch_all("SELECT id, nome FROM clientes ORDER BY nome")
    if request.method == "POST":
        try:
            execute(
                """
                INSERT INTO veiculos (cliente_id, placa, marca, modelo, ano)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [
                    request.form["cliente_id"],
                    request.form["placa"].strip().upper(),
                    request.form["marca"].strip(),
                    request.form["modelo"].strip(),
                    request.form["ano"],
                ],
            )
            flash("Veiculo cadastrado.", "success")
            return redirect(url_for("veiculos"))
        except DatabaseError as error:
            flash(f"Nao foi possivel cadastrar: {error.diag.message_primary}", "error")

    return render_template("veiculo_form.html", veiculo=None, clientes=clientes_opcoes)


@app.route("/veiculos/<int:veiculo_id>/editar", methods=["GET", "POST"])
@login_required
def veiculo_editar(veiculo_id):
    veiculo = fetch_one("SELECT * FROM veiculos WHERE id = %s", [veiculo_id])
    clientes_opcoes = fetch_all("SELECT id, nome FROM clientes ORDER BY nome")
    if not veiculo:
        flash("Veiculo nao encontrado.", "error")
        return redirect(url_for("veiculos"))

    if request.method == "POST":
        try:
            execute(
                """
                UPDATE veiculos
                SET cliente_id = %s, placa = %s, marca = %s, modelo = %s, ano = %s
                WHERE id = %s
                """,
                [
                    request.form["cliente_id"],
                    request.form["placa"].strip().upper(),
                    request.form["marca"].strip(),
                    request.form["modelo"].strip(),
                    request.form["ano"],
                    veiculo_id,
                ],
            )
            flash("Veiculo atualizado.", "success")
            return redirect(url_for("veiculos"))
        except DatabaseError as error:
            flash(f"Nao foi possivel atualizar: {error.diag.message_primary}", "error")

    return render_template("veiculo_form.html", veiculo=veiculo, clientes=clientes_opcoes)


@app.post("/veiculos/<int:veiculo_id>/excluir")
@login_required
def veiculo_excluir(veiculo_id):
    execute("DELETE FROM veiculos WHERE id = %s", [veiculo_id])
    flash("Veiculo excluido.", "success")
    return redirect(url_for("veiculos"))


@app.get("/servicos")
@login_required
def servicos():
    q = request.args.get("q", "").strip()
    order_key = request.args.get("order", "nome")
    orders = {
        "nome": "nome ASC",
        "valor": "valor_base DESC",
    }
    params = []
    where = ""
    if q:
        where = "WHERE nome ILIKE %s OR descricao ILIKE %s"
        params = [f"%{q}%", f"%{q}%"]

    rows = fetch_all(
        f"""
        SELECT id, nome, descricao, valor_base
        FROM servicos
        {where}
        ORDER BY {orders.get(order_key, orders["nome"])}
        """,
        params,
    )
    return render_template("servicos.html", servicos=rows, q=q, order=order_key)


@app.route("/servicos/novo", methods=["GET", "POST"])
@login_required
def servico_novo():
    if request.method == "POST":
        try:
            execute(
                """
                INSERT INTO servicos (nome, descricao, valor_base)
                VALUES (%s, %s, %s)
                """,
                [
                    request.form["nome"].strip(),
                    request.form.get("descricao", "").strip() or None,
                    money_to_decimal(request.form["valor_base"]),
                ],
            )
            flash("Servico cadastrado.", "success")
            return redirect(url_for("servicos"))
        except DatabaseError as error:
            flash(f"Nao foi possivel cadastrar: {error.diag.message_primary}", "error")

    return render_template("servico_form.html", servico=None)


@app.route("/servicos/<int:servico_id>/editar", methods=["GET", "POST"])
@login_required
def servico_editar(servico_id):
    servico = fetch_one("SELECT * FROM servicos WHERE id = %s", [servico_id])
    if not servico:
        flash("Servico nao encontrado.", "error")
        return redirect(url_for("servicos"))

    if request.method == "POST":
        try:
            execute(
                """
                UPDATE servicos
                SET nome = %s, descricao = %s, valor_base = %s
                WHERE id = %s
                """,
                [
                    request.form["nome"].strip(),
                    request.form.get("descricao", "").strip() or None,
                    money_to_decimal(request.form["valor_base"]),
                    servico_id,
                ],
            )
            flash("Servico atualizado.", "success")
            return redirect(url_for("servicos"))
        except DatabaseError as error:
            flash(f"Nao foi possivel atualizar: {error.diag.message_primary}", "error")

    return render_template("servico_form.html", servico=servico)


@app.post("/servicos/<int:servico_id>/excluir")
@login_required
def servico_excluir(servico_id):
    try:
        execute("DELETE FROM servicos WHERE id = %s", [servico_id])
        flash("Servico excluido.", "success")
    except DatabaseError as error:
        flash(f"Nao foi possivel excluir: {error.diag.message_primary}", "error")
    return redirect(url_for("servicos"))


def ordem_form_options():
    veiculos_opcoes = fetch_all(
        """
        SELECT v.id, v.placa, v.marca, v.modelo, c.nome AS cliente
        FROM veiculos v
        INNER JOIN clientes c ON c.id = v.cliente_id
        ORDER BY c.nome, v.placa
        """
    )
    servicos_opcoes = fetch_all("SELECT id, nome, valor_base FROM servicos ORDER BY nome")
    return veiculos_opcoes, servicos_opcoes


@app.get("/ordens")
@login_required
def ordens():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    order_key = request.args.get("order", "recentes")
    orders = {
        "recentes": "os.data_abertura DESC, os.id DESC",
        "cliente": "c.nome ASC",
        "status": "os.status ASC",
        "valor": "os.valor_total DESC",
    }
    params = []
    where_parts = []
    if q:
        where_parts.append("(c.nome ILIKE %s OR v.placa ILIKE %s OR s.nome ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    if status:
        where_parts.append("os.status = %s")
        params.append(status)

    where = "WHERE " + " AND ".join(where_parts) if where_parts else ""
    rows = fetch_all(
        f"""
        SELECT os.id, os.data_abertura, os.status, os.valor_total, os.observacoes,
               c.nome AS cliente, v.placa, v.marca, v.modelo, s.nome AS servico
        FROM ordens_servico os
        INNER JOIN veiculos v ON v.id = os.veiculo_id
        INNER JOIN clientes c ON c.id = v.cliente_id
        INNER JOIN servicos s ON s.id = os.servico_id
        {where}
        ORDER BY {orders.get(order_key, orders["recentes"])}
        """,
        params,
    )
    return render_template("ordens.html", ordens=rows, q=q, status=status, order=order_key)


@app.route("/ordens/nova", methods=["GET", "POST"])
@login_required
def ordem_nova():
    veiculos_opcoes, servicos_opcoes = ordem_form_options()
    if request.method == "POST":
        try:
            execute(
                """
                INSERT INTO ordens_servico
                    (veiculo_id, servico_id, data_abertura, status, valor_total, observacoes)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    request.form["veiculo_id"],
                    request.form["servico_id"],
                    request.form["data_abertura"],
                    request.form["status"],
                    money_to_decimal(request.form["valor_total"]),
                    request.form.get("observacoes", "").strip() or None,
                ],
            )
            flash("Ordem de servico cadastrada.", "success")
            return redirect(url_for("ordens"))
        except DatabaseError as error:
            flash(f"Nao foi possivel cadastrar: {error.diag.message_primary}", "error")

    return render_template(
        "ordem_form.html",
        ordem=None,
        veiculos=veiculos_opcoes,
        servicos=servicos_opcoes,
    )


@app.route("/ordens/<int:ordem_id>/editar", methods=["GET", "POST"])
@login_required
def ordem_editar(ordem_id):
    ordem = fetch_one("SELECT * FROM ordens_servico WHERE id = %s", [ordem_id])
    veiculos_opcoes, servicos_opcoes = ordem_form_options()
    if not ordem:
        flash("Ordem de servico nao encontrada.", "error")
        return redirect(url_for("ordens"))

    if request.method == "POST":
        try:
            execute(
                """
                UPDATE ordens_servico
                SET veiculo_id = %s,
                    servico_id = %s,
                    data_abertura = %s,
                    status = %s,
                    valor_total = %s,
                    observacoes = %s
                WHERE id = %s
                """,
                [
                    request.form["veiculo_id"],
                    request.form["servico_id"],
                    request.form["data_abertura"],
                    request.form["status"],
                    money_to_decimal(request.form["valor_total"]),
                    request.form.get("observacoes", "").strip() or None,
                    ordem_id,
                ],
            )
            flash("Ordem de servico atualizada.", "success")
            return redirect(url_for("ordens"))
        except DatabaseError as error:
            flash(f"Nao foi possivel atualizar: {error.diag.message_primary}", "error")

    return render_template(
        "ordem_form.html",
        ordem=ordem,
        veiculos=veiculos_opcoes,
        servicos=servicos_opcoes,
    )


@app.post("/ordens/<int:ordem_id>/excluir")
@login_required
def ordem_excluir(ordem_id):
    execute("DELETE FROM ordens_servico WHERE id = %s", [ordem_id])
    flash("Ordem de servico excluida.", "success")
    return redirect(url_for("ordens"))


@app.get("/relatorios")
@login_required
def relatorios():
    status = request.args.get("status", "").strip()
    params = []
    where = ""
    if status:
        where = "WHERE os.status = %s"
        params.append(status)

    inner_join = fetch_all(
        f"""
        SELECT os.id, os.data_abertura, os.status, c.nome AS cliente,
               v.placa, v.marca, v.modelo, s.nome AS servico, os.valor_total
        FROM ordens_servico os
        INNER JOIN veiculos v ON v.id = os.veiculo_id
        INNER JOIN clientes c ON c.id = v.cliente_id
        INNER JOIN servicos s ON s.id = os.servico_id
        {where}
        ORDER BY os.data_abertura DESC, os.id DESC
        """,
        params,
    )
    left_join = fetch_all(
        """
        SELECT c.id, c.nome, COUNT(os.id) AS total_ordens,
               COALESCE(SUM(os.valor_total), 0) AS valor_total_gasto
        FROM clientes c
        LEFT JOIN veiculos v ON v.cliente_id = c.id
        LEFT JOIN ordens_servico os ON os.veiculo_id = v.id
        GROUP BY c.id, c.nome
        ORDER BY valor_total_gasto DESC, c.nome ASC
        """
    )
    return render_template(
        "relatorios.html",
        inner_join=inner_join,
        left_join=left_join,
        status=status,
    )


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    use_reloader = os.getenv("FLASK_USE_RELOADER", "1") == "1"
    app.run(debug=debug, port=int(os.getenv("PORT", "5000")), use_reloader=use_reloader)
