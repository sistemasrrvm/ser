-- Migration 005: Alterar tipo da coluna excel_template para LONGTEXT
-- Data: 2025-11-14
-- Descrição: Aumentar capacidade de armazenamento para arquivos Excel maiores

-- Alterar tipo da coluna
ALTER TABLE formularios
MODIFY COLUMN excel_template LONGTEXT NULL COMMENT 'Template Excel em base64 para mesclagem com dados do formulario';
