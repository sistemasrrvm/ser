-- ============================================================================
-- Migration 011: Renomear campos das tabelas NR13 para nomenclatura SQL Server
-- Data: 2025-11-16
-- Descrição: Alinhar nomenclatura com banco externo SQL Server
-- ============================================================================

USE db_a2cb65_laudonr;

-- ============================================================================
-- TABELA: tab_clientes
-- ============================================================================

-- Renomear campos existentes
ALTER TABLE tab_clientes CHANGE COLUMN id CLI_ID INT NOT NULL;
ALTER TABLE tab_clientes CHANGE COLUMN nome CLI_NOME VARCHAR(200) NULL;
ALTER TABLE tab_clientes CHANGE COLUMN cnpj CLI_CNPJ VARCHAR(14) NULL;
ALTER TABLE tab_clientes CHANGE COLUMN criado_em CLI_DT_INS DATETIME NULL;
ALTER TABLE tab_clientes CHANGE COLUMN atualizado_em CLI_DT_UPD DATETIME NULL;

-- Adicionar novos campos
ALTER TABLE tab_clientes ADD COLUMN CLI_SITE VARCHAR(100) NULL AFTER CLI_NOME;
ALTER TABLE tab_clientes ADD COLUMN CLI_CONTATO VARCHAR(100) NULL AFTER CLI_SITE;
ALTER TABLE tab_clientes ADD COLUMN CLI_EMAIL VARCHAR(100) NULL AFTER CLI_CONTATO;
ALTER TABLE tab_clientes ADD COLUMN CLI_TELEFONE VARCHAR(50) NULL AFTER CLI_EMAIL;

-- Remover campos antigos
ALTER TABLE tab_clientes DROP COLUMN codigo;
ALTER TABLE tab_clientes DROP COLUMN ativo;
ALTER TABLE tab_clientes DROP COLUMN ultima_sinc;

-- Adicionar índice UNIQUE em CLI_ID
ALTER TABLE tab_clientes ADD UNIQUE INDEX idx_cli_id (CLI_ID);


-- ============================================================================
-- TABELA: tab_tipos_equipamento
-- ============================================================================

-- Renomear campos existentes
ALTER TABLE tab_tipos_equipamento CHANGE COLUMN id TEQP_ID INT NOT NULL;
ALTER TABLE tab_tipos_equipamento CHANGE COLUMN nome TEQP_NOME VARCHAR(100) NULL;
ALTER TABLE tab_tipos_equipamento CHANGE COLUMN criado_em TEQP_DT_INS DATETIME NULL;
ALTER TABLE tab_tipos_equipamento CHANGE COLUMN atualizado_em TEQP_DT_UPD DATETIME NULL;

-- Adicionar novos campos
ALTER TABLE tab_tipos_equipamento ADD COLUMN TEQP_VENC_CALIBRACAO INT NULL AFTER TEQP_NOME;
ALTER TABLE tab_tipos_equipamento ADD COLUMN TEQP_REQUER_INSPECAO_EXTERNA INT NOT NULL DEFAULT 0 AFTER TEQP_VENC_CALIBRACAO;
ALTER TABLE tab_tipos_equipamento ADD COLUMN TEQP_REQUER_INSPECAO_INTERNA INT NOT NULL DEFAULT 0 AFTER TEQP_REQUER_INSPECAO_EXTERNA;

-- Remover campos antigos
ALTER TABLE tab_tipos_equipamento DROP COLUMN codigo;
ALTER TABLE tab_tipos_equipamento DROP COLUMN descricao;
ALTER TABLE tab_tipos_equipamento DROP COLUMN ativo;
ALTER TABLE tab_tipos_equipamento DROP COLUMN ultima_sinc;

-- Adicionar índice UNIQUE em TEQP_ID
ALTER TABLE tab_tipos_equipamento ADD UNIQUE INDEX idx_teqp_id (TEQP_ID);


-- ============================================================================
-- TABELA: tab_equipamentos
-- ============================================================================

-- Renomear campos existentes
ALTER TABLE tab_equipamentos CHANGE COLUMN id EQP_ID INT NOT NULL;
ALTER TABLE tab_equipamentos CHANGE COLUMN cliente_id EQP_CLI_ID INT NOT NULL;
ALTER TABLE tab_equipamentos CHANGE COLUMN tipo_equipamento_id EQP_TEQP_ID INT NULL;
ALTER TABLE tab_equipamentos CHANGE COLUMN nome EQP_NOME VARCHAR(200) NULL;
ALTER TABLE tab_equipamentos CHANGE COLUMN numero_serie EQP_NUMERO_SERIE VARCHAR(50) NULL;
ALTER TABLE tab_equipamentos CHANGE COLUMN criado_em EQP_DT_INS DATETIME NULL;
ALTER TABLE tab_equipamentos CHANGE COLUMN atualizado_em EQP_DT_UPD DATETIME NULL;

-- Adicionar novos campos
ALTER TABLE tab_equipamentos ADD COLUMN EQP_TAG VARCHAR(200) NOT NULL AFTER EQP_TEQP_ID;
ALTER TABLE tab_equipamentos ADD COLUMN EQP_AREA VARCHAR(200) NULL AFTER EQP_NOME;
ALTER TABLE tab_equipamentos ADD COLUMN EQP_QTD_EQPI INT NULL AFTER EQP_AREA;
ALTER TABLE tab_equipamentos ADD COLUMN EQP_QTD_EQPI_VENCIDO INT NULL AFTER EQP_QTD_EQPI;
ALTER TABLE tab_equipamentos ADD COLUMN EQP_QTD_INST INT NULL AFTER EQP_QTD_EQPI_VENCIDO;
ALTER TABLE tab_equipamentos ADD COLUMN EQP_QTD_INSC INT NULL AFTER EQP_QTD_INST;
ALTER TABLE tab_equipamentos ADD COLUMN EQP_QTD_INSC_CLASS_0 INT NULL AFTER EQP_QTD_INSC;
ALTER TABLE tab_equipamentos ADD COLUMN EQP_QTD_INSC_CLASS_1 INT NULL AFTER EQP_QTD_INSC_CLASS_0;
ALTER TABLE tab_equipamentos ADD COLUMN EQP_QTD_INSC_CLASS_2 INT NULL AFTER EQP_QTD_INSC_CLASS_1;
ALTER TABLE tab_equipamentos ADD COLUMN EQP_QTD_INSC_CLASS_3 INT NULL AFTER EQP_QTD_INSC_CLASS_2;
ALTER TABLE tab_equipamentos ADD COLUMN EQP_QTD_INSC_CLASS_9 INT NULL AFTER EQP_QTD_INSC_CLASS_3;

-- Remover campos antigos
ALTER TABLE tab_equipamentos DROP COLUMN codigo;
ALTER TABLE tab_equipamentos DROP COLUMN localizacao;
ALTER TABLE tab_equipamentos DROP COLUMN ativo;
ALTER TABLE tab_equipamentos DROP COLUMN ultima_sinc;

-- Adicionar índice UNIQUE em EQP_ID
ALTER TABLE tab_equipamentos ADD UNIQUE INDEX idx_eqp_id (EQP_ID);


-- Verificar resultado
SELECT 'Migração 011 concluída com sucesso!' AS status;
SHOW COLUMNS FROM tab_clientes;
SHOW COLUMNS FROM tab_tipos_equipamento;
SHOW COLUMNS FROM tab_equipamentos;
