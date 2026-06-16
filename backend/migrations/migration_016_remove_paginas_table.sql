-- ============================================================================
-- Migration 016: Remover tabela paginas (redundante)
-- Data: 2025-11-21
-- Descrição: Remove tabela paginas que foi substituída por formularios_paginas
--            Tabela paginas não está mais em uso no código
-- ============================================================================

USE db_a2cb65_laudonr;

-- ============================================================================
-- VERIFICAÇÃO: Verificar se tabela existe
-- ============================================================================

SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN CONCAT('Tabela paginas encontrada. Registros: ', COUNT(*))
        ELSE 'Tabela paginas não existe'
    END AS status
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
  AND TABLE_NAME = 'paginas';

-- Verificar se há foreign keys referenciando paginas
SELECT 
    CONCAT('FK encontrada: ', CONSTRAINT_NAME, ' na tabela ', TABLE_NAME) AS foreign_keys
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
  AND REFERENCED_TABLE_NAME = 'paginas'
GROUP BY CONSTRAINT_NAME, TABLE_NAME;

-- ============================================================================
-- REMOVER FOREIGN KEYS QUE REFERENCIAM paginas (se existir)
-- ============================================================================

-- Remover FK de campos.pagina_id -> paginas.id (se existir)
SET @fk_exists = (
    SELECT COUNT(*)
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'campos'
      AND REFERENCED_TABLE_NAME = 'paginas'
      AND REFERENCED_COLUMN_NAME = 'id'
);

SET @fk_name = (
    SELECT CONSTRAINT_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'campos'
      AND REFERENCED_TABLE_NAME = 'paginas'
      AND REFERENCED_COLUMN_NAME = 'id'
    LIMIT 1
);

SET @sql = IF(@fk_exists > 0 AND @fk_name IS NOT NULL,
    CONCAT('ALTER TABLE `campos` DROP FOREIGN KEY `', @fk_name, '`'),
    'SELECT "FK campos -> paginas não existe" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Remover FK de paginas.formulario_id -> formularios.id (se existir)
SET @fk_exists = (
    SELECT COUNT(*)
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'paginas'
      AND REFERENCED_TABLE_NAME = 'formularios'
      AND REFERENCED_COLUMN_NAME = 'id'
);

SET @fk_name = (
    SELECT CONSTRAINT_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'paginas'
      AND REFERENCED_TABLE_NAME = 'formularios'
      AND REFERENCED_COLUMN_NAME = 'id'
    LIMIT 1
);

SET @sql = IF(@fk_exists > 0 AND @fk_name IS NOT NULL,
    CONCAT('ALTER TABLE `paginas` DROP FOREIGN KEY `', @fk_name, '`'),
    'SELECT "FK paginas -> formularios não existe" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================================================
-- REMOVER TABELA paginas
-- ============================================================================

DROP TABLE IF EXISTS `paginas`;

-- ============================================================================
-- VERIFICAÇÃO FINAL
-- ============================================================================

-- Verificar se tabela foi removida
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN 'OK: Tabela paginas removida com sucesso'
        ELSE 'ERRO: Tabela paginas ainda existe'
    END AS status
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
  AND TABLE_NAME = 'paginas';

