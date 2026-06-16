-- Migration 020: Permitir status em_correcao (#246)
-- Remove CHECK legado que só aceitava rascunho|em_revisao|aprovado|cancelado

SET @db := DATABASE();

SET @chk := (
  SELECT COUNT(*)
  FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = @db
    AND TABLE_NAME = 'reports'
    AND CONSTRAINT_NAME = 'chk_reports_status'
    AND CONSTRAINT_TYPE = 'CHECK'
);

SET @sql := IF(
  @chk > 0,
  'ALTER TABLE `reports` DROP CHECK `chk_reports_status`',
  'SELECT ''chk_reports_status já removido'' AS msg'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Migration 020 concluída: status em_correcao liberado' AS status;
