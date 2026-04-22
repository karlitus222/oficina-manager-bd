-- Consultas utilizadas pela aplicacao.

-- Listagem simples com filtro por nome ou CPF.
SELECT id, nome, cpf, telefone, email
FROM clientes
WHERE nome ILIKE '%mar%'
   OR cpf ILIKE '%mar%'
ORDER BY nome ASC;

-- Ordenacao de veiculos por marca e modelo.
SELECT v.id, v.placa, v.marca, v.modelo, v.ano, c.nome AS cliente
FROM veiculos v
INNER JOIN clientes c ON c.id = v.cliente_id
ORDER BY v.marca ASC, v.modelo ASC;

-- INNER JOIN: ordens de servico com cliente, veiculo e servico.
SELECT
    os.id,
    os.data_abertura,
    os.status,
    c.nome AS cliente,
    v.placa,
    v.marca,
    v.modelo,
    s.nome AS servico,
    os.valor_total
FROM ordens_servico os
INNER JOIN veiculos v ON v.id = os.veiculo_id
INNER JOIN clientes c ON c.id = v.cliente_id
INNER JOIN servicos s ON s.id = os.servico_id
WHERE os.status = 'Aberta'
ORDER BY os.data_abertura DESC;

-- LEFT JOIN: todos os clientes, inclusive os que ainda nao possuem ordem.
SELECT
    c.id,
    c.nome,
    COUNT(os.id) AS total_ordens,
    COALESCE(SUM(os.valor_total), 0) AS valor_total_gasto
FROM clientes c
LEFT JOIN veiculos v ON v.cliente_id = c.id
LEFT JOIN ordens_servico os ON os.veiculo_id = v.id
GROUP BY c.id, c.nome
ORDER BY valor_total_gasto DESC, c.nome ASC;
