-- Sistema de Gestao de Oficina Mecanica
-- SGBD: PostgreSQL

DROP TABLE IF EXISTS ordens_servico;
DROP TABLE IF EXISTS servicos;
DROP TABLE IF EXISTS veiculos;
DROP TABLE IF EXISTS clientes;
DROP TABLE IF EXISTS usuarios;

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(160) NOT NULL UNIQUE,
    senha_hash CHAR(64) NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(140) NOT NULL,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    telefone VARCHAR(20) NOT NULL,
    email VARCHAR(160),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE veiculos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    placa VARCHAR(8) NOT NULL UNIQUE,
    marca VARCHAR(80) NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    ano INTEGER NOT NULL CHECK (ano BETWEEN 1980 AND 2100),
    CONSTRAINT fk_veiculos_clientes
        FOREIGN KEY (cliente_id)
        REFERENCES clientes(id)
        ON DELETE CASCADE
);

CREATE TABLE servicos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL UNIQUE,
    descricao TEXT,
    valor_base NUMERIC(10, 2) NOT NULL CHECK (valor_base >= 0)
);

CREATE TABLE ordens_servico (
    id SERIAL PRIMARY KEY,
    veiculo_id INTEGER NOT NULL,
    servico_id INTEGER NOT NULL,
    data_abertura DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Aberta',
    valor_total NUMERIC(10, 2) NOT NULL CHECK (valor_total >= 0),
    observacoes TEXT,
    CONSTRAINT ck_ordens_status
        CHECK (status IN ('Aberta', 'Em andamento', 'Concluida', 'Cancelada')),
    CONSTRAINT fk_ordens_veiculos
        FOREIGN KEY (veiculo_id)
        REFERENCES veiculos(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ordens_servicos
        FOREIGN KEY (servico_id)
        REFERENCES servicos(id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_clientes_nome ON clientes(nome);
CREATE INDEX idx_veiculos_cliente_id ON veiculos(cliente_id);
CREATE INDEX idx_ordens_status ON ordens_servico(status);
CREATE INDEX idx_ordens_data_abertura ON ordens_servico(data_abertura);
