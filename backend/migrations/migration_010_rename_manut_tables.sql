-- ============================================================================
-- Migration 010: Renomear tabelas NR13 para nomenclatura simplificada
-- Data: 2025-11-16
-- Descrição: Renomear tabelas cache_sqlserver_* para tab_*
-- ============================================================================

USE db_a2cb65_laudonr;

-- Renomear tabelas
-- IMPORTANTE: RENAME TABLE mantém automaticamente as foreign keys

RENAME TABLE cache_sqlserver_clientes TO tab_clientes;
RENAME TABLE cache_sqlserver_tipos_equipamento TO tab_tipos_equipamento;
RENAME TABLE cache_sqlserver_equipamentos TO tab_equipamentos;

-- Verificar resultado
SELECT 'Migração 010 concluída com sucesso!' AS status;
SHOW TABLES LIKE 'tab_%';
