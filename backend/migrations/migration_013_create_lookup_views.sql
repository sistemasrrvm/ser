-- Migration 013: Criar Views de Lookup para NR13
-- Data: 2025-11-17
-- Objetivo: Criar views com estrutura padronizada (id, label, filter) para uso em campos Lookup

-- View: Clientes NR13
-- Estrutura: id = CLI_ID, label = CLI_NOME, filter = NULL
DROP VIEW IF EXISTS vw_tab_clientes_lookup;
CREATE VIEW vw_tab_clientes_lookup AS
SELECT
  CLI_ID AS id,
  CLI_NOME AS label,
  NULL AS filter
FROM tab_clientes
WHERE CLI_NOME IS NOT NULL
ORDER BY CLI_NOME;

-- View: Equipamentos NR13 (filtrado por cliente)
-- Estrutura: id = EQP_ID, label = TAG + NOME, filter = CLI_ID (para filtro dependente)
DROP VIEW IF EXISTS vw_tab_equipamentos_lookup;
CREATE VIEW vw_tab_equipamentos_lookup AS
SELECT
  EQP_ID AS id,
  CONCAT(EQP_TAG, ' - ', COALESCE(EQP_NOME, '')) AS label,
  EQP_CLI_ID AS filter
FROM tab_equipamentos
WHERE EQP_TAG IS NOT NULL
ORDER BY EQP_TAG;

-- View: Tipos de Equipamento NR13
-- Estrutura: id = TEQP_ID, label = TEQP_NOME, filter = NULL
DROP VIEW IF EXISTS vw_tab_tipos_equipamento_lookup;
CREATE VIEW vw_tab_tipos_equipamento_lookup AS
SELECT
  TEQP_ID AS id,
  TEQP_NOME AS label,
  NULL AS filter
FROM tab_tipos_equipamento
WHERE TEQP_NOME IS NOT NULL
ORDER BY TEQP_NOME;

-- Verificar views criadas
SELECT 'Migration 013 concluida: Views de Lookup criadas' AS status;
