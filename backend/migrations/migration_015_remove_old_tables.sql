-- ============================================================================
-- Migration 015: Remover tabelas antigas e coluna filial_id
-- Data: 2025-11-21
-- Descrição: Remove tabelas clientes, filiais, equipamentos e coluna filial_id
--            que foram substituídas por tab_clientes e tab_equipamentos
-- ============================================================================

USE db_a2cb65_laudonr;

-- ============================================================================
-- 1. REMOVER FOREIGN KEYS QUE REFERENCIAM TABELAS ANTIGAS
-- ============================================================================

-- Remover FK de reports.filial_id -> filiais.id (se existir)
SET @fk_exists = (
    SELECT COUNT(*)
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'reports'
      AND REFERENCED_TABLE_NAME = 'filiais'
      AND REFERENCED_COLUMN_NAME = 'id'
);

SET @fk_name = (
    SELECT CONSTRAINT_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'reports'
      AND REFERENCED_TABLE_NAME = 'filiais'
      AND REFERENCED_COLUMN_NAME = 'id'
    LIMIT 1
);

SET @sql = IF(@fk_exists > 0 AND @fk_name IS NOT NULL,
    CONCAT('ALTER TABLE `reports` DROP FOREIGN KEY `', @fk_name, '`'),
    'SELECT "FK reports -> filiais não existe" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================================================
-- 2. REMOVER OUTRAS FOREIGN KEYS
-- ============================================================================

-- Remover FK de reports.cliente_id -> clientes.id (se existir)
SET @fk_exists = (
    SELECT COUNT(*)
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'reports'
      AND REFERENCED_TABLE_NAME = 'clientes'
      AND REFERENCED_COLUMN_NAME = 'id'
);

SET @fk_name = (
    SELECT CONSTRAINT_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'reports'
      AND REFERENCED_TABLE_NAME = 'clientes'
      AND REFERENCED_COLUMN_NAME = 'id'
    LIMIT 1
);

SET @sql = IF(@fk_exists > 0 AND @fk_name IS NOT NULL,
    CONCAT('ALTER TABLE `reports` DROP FOREIGN KEY `', @fk_name, '`'),
    'SELECT "FK reports -> clientes não existe" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Remover FK de equipamentos.filial_id -> filiais.id (se existir)
SET @fk_exists = (
    SELECT COUNT(*)
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'equipamentos'
      AND REFERENCED_TABLE_NAME = 'filiais'
      AND REFERENCED_COLUMN_NAME = 'id'
);

SET @fk_name = (
    SELECT CONSTRAINT_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'equipamentos'
      AND REFERENCED_TABLE_NAME = 'filiais'
      AND REFERENCED_COLUMN_NAME = 'id'
    LIMIT 1
);

SET @sql = IF(@fk_exists > 0 AND @fk_name IS NOT NULL,
    CONCAT('ALTER TABLE `equipamentos` DROP FOREIGN KEY `', @fk_name, '`'),
    'SELECT "FK equipamentos -> filiais não existe" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Remover FK de filiais.cliente_id -> clientes.id (se existir)
SET @fk_exists = (
    SELECT COUNT(*)
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'filiais'
      AND REFERENCED_TABLE_NAME = 'clientes'
      AND REFERENCED_COLUMN_NAME = 'id'
);

SET @fk_name = (
    SELECT CONSTRAINT_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'filiais'
      AND REFERENCED_TABLE_NAME = 'clientes'
      AND REFERENCED_COLUMN_NAME = 'id'
    LIMIT 1
);

SET @sql = IF(@fk_exists > 0 AND @fk_name IS NOT NULL,
    CONCAT('ALTER TABLE `filiais` DROP FOREIGN KEY `', @fk_name, '`'),
    'SELECT "FK filiais -> clientes não existe" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Remover FK de reports.equipamento_id -> equipamentos.id (se existir)
SET @fk_exists = (
    SELECT COUNT(*)
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'reports'
      AND REFERENCED_TABLE_NAME = 'equipamentos'
      AND REFERENCED_COLUMN_NAME = 'id'
);

SET @fk_name = (
    SELECT CONSTRAINT_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'reports'
      AND REFERENCED_TABLE_NAME = 'equipamentos'
      AND REFERENCED_COLUMN_NAME = 'id'
    LIMIT 1
);

SET @sql = IF(@fk_exists > 0 AND @fk_name IS NOT NULL,
    CONCAT('ALTER TABLE `reports` DROP FOREIGN KEY `', @fk_name, '`'),
    'SELECT "FK reports -> equipamentos não existe" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================================================
-- 3. REMOVER COLUNA filial_id DA TABELA reports
-- ============================================================================

-- Verificar se a coluna existe antes de remover
SET @column_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
      AND TABLE_NAME = 'reports'
      AND COLUMN_NAME = 'filial_id'
);

-- Remover coluna se existir (FK já foi removida acima)
SET @sql = IF(@column_exists > 0,
    'ALTER TABLE `reports` DROP COLUMN `filial_id`',
    'SELECT "Coluna filial_id não existe na tabela reports" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================================================
-- 4. REMOVER TABELAS ANTIGAS
-- ============================================================================

-- Remover tabela equipamentos (se existir)
DROP TABLE IF EXISTS `equipamentos`;

-- Remover tabela filiais (se existir)
DROP TABLE IF EXISTS `filiais`;

-- Remover tabela clientes (se existir)
DROP TABLE IF EXISTS `clientes`;

-- Remover tabela campos (se existir - não usada)
DROP TABLE IF EXISTS `campos`;

-- ============================================================================
-- VERIFICAÇÃO
-- ============================================================================

-- Verificar se tabelas foram removidas
SELECT 
    'Tabelas antigas removidas:' AS status,
    CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'ERRO: Tabelas ainda existem' END AS resultado
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
  AND TABLE_NAME IN ('clientes', 'filiais', 'equipamentos', 'campos');

-- Verificar estrutura da tabela reports
DESCRIBE `reports`;

-- Verificar se coluna filial_id foi removida
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN 'OK: Coluna filial_id removida'
        ELSE 'ERRO: Coluna filial_id ainda existe'
    END AS status
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
  AND TABLE_NAME = 'reports'
  AND COLUMN_NAME = 'filial_id';

