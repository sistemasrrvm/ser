-- Migration 019: Status em_correcao + histórico de solicitações de correção (#246)
-- Executar no Railway após backup

CREATE TABLE IF NOT EXISTS `relatorios_correcoes` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `report_id` BIGINT NOT NULL,
  `solicitado_por_id` BIGINT NOT NULL,
  `descricao` TEXT NOT NULL,
  `status_anterior` VARCHAR(20) NOT NULL,
  `status_novo` VARCHAR(20) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_correcoes_report` (`report_id`, `created_at`),
  CONSTRAINT `fk_correcoes_report`
    FOREIGN KEY (`report_id`) REFERENCES `reports` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_correcoes_user`
    FOREIGN KEY (`solicitado_por_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2) Liberar status em_correcao (CHECK legado da migration 003)
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

SELECT 'Migration 019 concluída: relatorios_correcoes + em_correcao' AS status;
