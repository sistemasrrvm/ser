-- Migration 013: Tornar campos opcionais na tabela reports
-- Permite criar relatórios apenas com template_id, preenchendo outros dados no formulário

-- PASSO 1: Remover foreign keys que precisam ser modificadas
ALTER TABLE reports DROP FOREIGN KEY fk_reports_cliente;
ALTER TABLE reports DROP FOREIGN KEY fk_reports_filial;
ALTER TABLE reports DROP FOREIGN KEY fk_reports_equipamento;

-- PASSO 2: Modificar colunas para permitir NULL (corrigir tipos para BIGINT)
ALTER TABLE reports MODIFY COLUMN cliente_id BIGINT NULL;
ALTER TABLE reports MODIFY COLUMN filial_id BIGINT NULL;
ALTER TABLE reports MODIFY COLUMN equipamento_id BIGINT NULL;
ALTER TABLE reports MODIFY COLUMN tipo_inspecao VARCHAR(100) NULL;

-- PASSO 3: Recriar foreign keys (agora permitindo NULL)
ALTER TABLE reports
    ADD CONSTRAINT fk_reports_cliente
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    ON DELETE RESTRICT;

ALTER TABLE reports
    ADD CONSTRAINT fk_reports_filial
    FOREIGN KEY (filial_id) REFERENCES filiais(id)
    ON DELETE RESTRICT;

ALTER TABLE reports
    ADD CONSTRAINT fk_reports_equipamento
    FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
    ON DELETE RESTRICT;
