-- Dados iniciais para teste do sistema.
-- Login padrao da aplicacao:
-- email: admin@oficina.local
-- senha: admin123

INSERT INTO usuarios (nome, email, senha_hash) VALUES
('Administrador', 'admin@oficina.local', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9');

INSERT INTO clientes (nome, cpf, telefone, email) VALUES
('Mariana Rocha', '111.222.333-44', '(86) 99910-1000', 'mariana.rocha@email.com'),
('Carlos Lima', '222.333.444-55', '(86) 99920-2000', 'carlos.lima@email.com'),
('Beatriz Sousa', '333.444.555-66', '(86) 99930-3000', 'beatriz.sousa@email.com'),
('Rafael Martins', '444.555.666-77', '(86) 99940-4000', 'rafael.martins@email.com');

INSERT INTO veiculos (cliente_id, placa, marca, modelo, ano) VALUES
(1, 'PIA1A23', 'Toyota', 'Corolla', 2020),
(2, 'OEA2B34', 'Honda', 'Civic', 2019),
(3, 'LWW3C45', 'Hyundai', 'HB20', 2022),
(1, 'NII4D56', 'Chevrolet', 'Onix', 2021);

INSERT INTO servicos (nome, descricao, valor_base) VALUES
('Troca de oleo', 'Substituicao de oleo do motor e filtro.', 180.00),
('Alinhamento e balanceamento', 'Ajuste de alinhamento e balanceamento das rodas.', 220.00),
('Revisao preventiva', 'Checklist completo de freios, suspensao, motor e fluidos.', 650.00),
('Diagnostico eletronico', 'Leitura de scanner e analise de falhas.', 150.00);

INSERT INTO ordens_servico (veiculo_id, servico_id, data_abertura, status, valor_total, observacoes) VALUES
(1, 1, '2026-04-02', 'Concluida', 190.00, 'Cliente solicitou oleo sintetico.'),
(2, 3, '2026-04-08', 'Em andamento', 680.00, 'Aguardando chegada de peca.'),
(3, 2, '2026-04-12', 'Aberta', 220.00, 'Agendado para o turno da tarde.'),
(4, 4, '2026-04-15', 'Aberta', 150.00, 'Luz de injecao acesa no painel.');
