-- Exemplos de UPDATE e DELETE para demonstracao de DML.
-- Este arquivo e opcional e serve para mostrar manipulacao dos dados.

UPDATE ordens_servico
SET status = 'Em andamento',
    observacoes = 'Servico iniciado apos avaliacao inicial.'
WHERE id = 3;

INSERT INTO clientes (nome, cpf, telefone, email)
VALUES ('Cliente Temporario', '999.888.777-66', '(86) 98888-7777', 'temporario@email.com');

DELETE FROM clientes
WHERE cpf = '999.888.777-66';
