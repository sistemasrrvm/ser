-- ============================================================================
-- Migration 018: Sincronizar banco Railway restaurado (backup antigo) com o app
-- Data: 2026-05-19
-- Objetivo: Aplicar pendências das migrations 014–017 + views lookup
--
-- CONTEXTO: Backup antigo ainda contém:
--   - clientes / filiais / equipamentos (mock, substituídos por tab_*)
--   - reports.filial_id + FKs para tabelas antigas
--   - formularios_paginas.formulario_id e formularios_campos.pagina_id como INT
--
-- EXECUÇÃO: MySQL Workbench ou Railway (query tab). Fazer BACKUP antes.
-- Usa DATABASE() — não depende do nome do schema (railway, db_a2cb65_laudonr, etc.)
-- ============================================================================

SET @db := DATABASE();
SELECT CONCAT('Migration 018 em: ', @db) AS info;

-- ============================================================================
-- 0. tab_clientes — campos de endereço (migration 014)
-- ============================================================================

SET @col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'tab_clientes' AND COLUMN_NAME = 'CLI_ENDERECO'
);
SET @sql := IF(@col = 0,
  'ALTER TABLE `tab_clientes`
     ADD COLUMN `CLI_ENDERECO` VARCHAR(200) NULL COMMENT ''Endereço (logradouro)'',
     ADD COLUMN `CLI_NUMERO` VARCHAR(20) NULL COMMENT ''Número'',
     ADD COLUMN `CLI_BAIRRO` VARCHAR(100) NULL COMMENT ''Bairro'',
     ADD COLUMN `CLI_CEP` VARCHAR(10) NULL COMMENT ''CEP'',
     ADD COLUMN `CLI_CIDADE` VARCHAR(100) NULL COMMENT ''Cidade'',
     ADD COLUMN `CLI_ESTADO` VARCHAR(2) NULL COMMENT ''UF''',
  'SELECT ''tab_clientes: endereço OK'' AS msg'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ============================================================================
-- 1. Remapear reports.cliente_id / equipamento_id (old mock → tab_*)
--    COLLATE utf8mb4_unicode_ci evita erro 1267 (mix unicode_ci / 0900_ai_ci)
-- ============================================================================

DROP PROCEDURE IF EXISTS m018_remap_reports;
DELIMITER //
CREATE PROCEDURE m018_remap_reports()
BEGIN
  DECLARE v_clientes INT DEFAULT 0;
  DECLARE v_equipamentos INT DEFAULT 0;

  SELECT COUNT(*) INTO v_clientes
  FROM information_schema.TABLES
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'clientes';

  SELECT COUNT(*) INTO v_equipamentos
  FROM information_schema.TABLES
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'equipamentos';

  IF v_clientes > 0 THEN
    UPDATE reports r
    INNER JOIN clientes c ON c.id = r.cliente_id
    LEFT JOIN tab_clientes tc
      ON tc.CLI_CNPJ COLLATE utf8mb4_unicode_ci = c.cnpj COLLATE utf8mb4_unicode_ci
      AND c.cnpj IS NOT NULL AND TRIM(c.cnpj) <> ''
    LEFT JOIN tab_clientes tn
      ON tn.CLI_NOME COLLATE utf8mb4_unicode_ci = c.nome COLLATE utf8mb4_unicode_ci
      AND tc.CLI_ID IS NULL
    SET r.cliente_id = COALESCE(tc.CLI_ID, tn.CLI_ID, r.cliente_id)
    WHERE r.cliente_id IS NOT NULL;
  END IF;

  IF v_equipamentos > 0 THEN
    UPDATE reports r
    INNER JOIN equipamentos e ON e.id = r.equipamento_id
    LEFT JOIN tab_equipamentos te
      ON te.EQP_NUMERO_SERIE COLLATE utf8mb4_unicode_ci = e.numero_serie COLLATE utf8mb4_unicode_ci
      AND e.numero_serie IS NOT NULL AND TRIM(e.numero_serie) <> ''
    LEFT JOIN tab_equipamentos tc
      ON tc.EQP_TAG COLLATE utf8mb4_unicode_ci = e.codigo COLLATE utf8mb4_unicode_ci
      AND te.EQP_ID IS NULL
    SET r.equipamento_id = COALESCE(te.EQP_ID, tc.EQP_ID, r.equipamento_id)
    WHERE r.equipamento_id IS NOT NULL;
  END IF;

  -- Órfãos: IDs que não existem em tab_*
  UPDATE reports r
  LEFT JOIN tab_clientes tc ON tc.CLI_ID = r.cliente_id
  SET r.cliente_id = NULL
  WHERE r.cliente_id IS NOT NULL AND tc.CLI_ID IS NULL;

  UPDATE reports r
  LEFT JOIN tab_equipamentos te ON te.EQP_ID = r.equipamento_id
  SET r.equipamento_id = NULL
  WHERE r.equipamento_id IS NOT NULL AND te.EQP_ID IS NULL;
END//
DELIMITER ;

CALL m018_remap_reports();
DROP PROCEDURE IF EXISTS m018_remap_reports;

-- ============================================================================
-- 2. reports — remover FKs antigas, tornar campos opcionais, remover filial_id
-- ============================================================================

-- Helper: drop FK by referenced table
DROP PROCEDURE IF EXISTS m018_drop_fk_to;
DELIMITER //
CREATE PROCEDURE m018_drop_fk_to(IN p_table VARCHAR(64), IN p_ref_table VARCHAR(64))
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE v_fk VARCHAR(255);
  DECLARE cur CURSOR FOR
    SELECT CONSTRAINT_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = p_table
      AND REFERENCED_TABLE_NAME = p_ref_table;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
  OPEN cur;
  read_loop: LOOP
    FETCH cur INTO v_fk;
    IF done THEN LEAVE read_loop; END IF;
    SET @s = CONCAT('ALTER TABLE `', p_table, '` DROP FOREIGN KEY `', v_fk, '`');
    PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
  END LOOP;
  CLOSE cur;
END//
DELIMITER ;

CALL m018_drop_fk_to('reports', 'clientes');
CALL m018_drop_fk_to('reports', 'filiais');
CALL m018_drop_fk_to('reports', 'equipamentos');

-- Garantir tipos e NULL (app atual)
ALTER TABLE `reports`
  MODIFY COLUMN `cliente_id` BIGINT NULL,
  MODIFY COLUMN `equipamento_id` BIGINT NULL,
  MODIFY COLUMN `tipo_inspecao` VARCHAR(100) NULL,
  MODIFY COLUMN `status` VARCHAR(20) NOT NULL DEFAULT 'rascunho',
  MODIFY COLUMN `respostas` JSON NOT NULL;

-- Remover filial_id (migration 015/017)
SET @col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'reports' AND COLUMN_NAME = 'filial_id'
);
SET @sql := IF(@col > 0, 'ALTER TABLE `reports` DROP COLUMN `filial_id`', 'SELECT ''filial_id já removida'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Remover índice legado de filial_id se existir
SET @idx := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'reports' AND INDEX_NAME = 'idx_reports_filial'
);
SET @sql := IF(@idx > 0, 'ALTER TABLE `reports` DROP INDEX `idx_reports_filial`', 'SELECT ''idx_reports_filial OK'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ============================================================================
-- 3. formularios — tipos BIGINT nas FKs (migration 017)
-- ============================================================================

ALTER TABLE `formularios_paginas`
  MODIFY COLUMN `formulario_id` BIGINT NOT NULL;

ALTER TABLE `formularios_campos`
  MODIFY COLUMN `pagina_id` BIGINT NOT NULL;

-- ============================================================================
-- 4. Remover tabelas legadas (migration 015/016)
-- ============================================================================

CALL m018_drop_fk_to('equipamentos', 'filiais');
CALL m018_drop_fk_to('filiais', 'clientes');

DROP TABLE IF EXISTS `equipamentos`;
DROP TABLE IF EXISTS `filiais`;
DROP TABLE IF EXISTS `clientes`;
DROP TABLE IF EXISTS `campos`;
DROP TABLE IF EXISTS `paginas`;

DROP PROCEDURE IF EXISTS m018_drop_fk_to;

-- ============================================================================
-- 5. configuracoes — seed lookup_views se ausente (migration 012)
-- ============================================================================

SET @cfg := (
  SELECT COUNT(*) FROM configuracoes WHERE chave = 'lookup_views'
);
SET @sql := IF(@cfg = 0,
  'INSERT INTO configuracoes (chave, valor, tipo, descricao, categoria) VALUES (
    ''lookup_views'',
    ''{\"views\":[{\"value\":\"vw_tab_clientes_lookup\",\"label\":\"Clientes (NR13)\",\"description\":\"View de lookup para clientes NR13\"},{\"value\":\"vw_tab_equipamentos_lookup\",\"label\":\"Equipamentos (NR13)\",\"description\":\"View de lookup para equipamentos NR13\"},{\"value\":\"vw_tab_tipos_equipamento_lookup\",\"label\":\"Tipos de Equipamento (NR13)\",\"description\":\"View de lookup para tipos de equipamento NR13\"}]}'',
    ''json'',
    ''Lista de views homologadas para uso em campos Lookup'',
    ''sistema''
  )',
  'SELECT ''configuracoes.lookup_views OK'' AS msg'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ============================================================================
-- 6. Views de lookup (migration 013) — filter como VARCHAR
-- ============================================================================

DROP VIEW IF EXISTS vw_tab_clientes_lookup;
CREATE VIEW vw_tab_clientes_lookup AS
SELECT
  CAST(CLI_ID AS CHAR CHARACTER SET utf8mb4) COLLATE utf8mb4_unicode_ci AS id,
  CLI_NOME AS label,
  CAST(NULL AS CHAR(50) CHARACTER SET utf8mb4) COLLATE utf8mb4_unicode_ci AS filter
FROM tab_clientes
WHERE CLI_NOME IS NOT NULL
ORDER BY CLI_NOME;

DROP VIEW IF EXISTS vw_tab_equipamentos_lookup;
CREATE VIEW vw_tab_equipamentos_lookup AS
SELECT
  CAST(EQP_ID AS CHAR CHARACTER SET utf8mb4) COLLATE utf8mb4_unicode_ci AS id,
  CONCAT(EQP_TAG, ' - ', COALESCE(EQP_NOME, '')) AS label,
  CAST(EQP_CLI_ID AS CHAR CHARACTER SET utf8mb4) COLLATE utf8mb4_unicode_ci AS filter
FROM tab_equipamentos
WHERE EQP_TAG IS NOT NULL
ORDER BY EQP_TAG;

DROP VIEW IF EXISTS vw_tab_tipos_equipamento_lookup;
CREATE VIEW vw_tab_tipos_equipamento_lookup AS
SELECT
  CAST(TEQP_ID AS CHAR CHARACTER SET utf8mb4) COLLATE utf8mb4_unicode_ci AS id,
  TEQP_NOME AS label,
  CAST(NULL AS CHAR(50) CHARACTER SET utf8mb4) COLLATE utf8mb4_unicode_ci AS filter
FROM tab_tipos_equipamento
WHERE TEQP_NOME IS NOT NULL
ORDER BY TEQP_NOME;

-- ============================================================================
-- 7. Verificação final
-- ============================================================================

SELECT 'Tabelas legadas (devem ser 0):' AS check_name,
       COUNT(*) AS qtd
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = @db
  AND TABLE_NAME IN ('clientes', 'filiais', 'equipamentos', 'paginas', 'campos');

SELECT 'reports.filial_id (deve ser 0):' AS check_name,
       COUNT(*) AS qtd
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'reports' AND COLUMN_NAME = 'filial_id';

SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = @db
  AND TABLE_NAME IN ('formularios_paginas', 'formularios_campos', 'reports')
  AND COLUMN_NAME IN ('formulario_id', 'pagina_id', 'cliente_id', 'equipamento_id', 'filial_id')
ORDER BY TABLE_NAME, COLUMN_NAME;

SELECT 'Relatórios com cliente_id inválido (deve ser 0):' AS check_name,
       COUNT(*) AS qtd
FROM reports r
LEFT JOIN tab_clientes tc ON tc.CLI_ID = r.cliente_id
WHERE r.cliente_id IS NOT NULL AND tc.CLI_ID IS NULL;

SELECT 'Relatórios com equipamento_id inválido (deve ser 0):' AS check_name,
       COUNT(*) AS qtd
FROM reports r
LEFT JOIN tab_equipamentos te ON te.EQP_ID = r.equipamento_id
WHERE r.equipamento_id IS NOT NULL AND te.EQP_ID IS NULL;

SELECT 'Migration 018 concluída' AS status;
