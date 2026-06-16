-- Migration 007: Alterar campo excel_template para LONGTEXT
-- Data: 2025-11-15 23:21:36
-- Motivo: Campo VARCHAR muito pequeno para armazenar templates Excel em base64
-- Relacionado: Sprint 007 - Exportar/Importar Template

-- Verificar tamanho atual do campo
SELECT
    COLUMN_NAME,
    COLUMN_TYPE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'formularios'
  AND COLUMN_NAME = 'excel_template';

-- Alterar campo para LONGTEXT (suporta até 4GB)
ALTER TABLE formularios
MODIFY COLUMN excel_template LONGTEXT NULL
COMMENT 'Template Excel em base64 para mesclagem';

-- Verificar após alteração
SELECT
    COLUMN_NAME,
    COLUMN_TYPE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'formularios'
  AND COLUMN_NAME = 'excel_template';
