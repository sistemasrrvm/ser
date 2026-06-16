-- ========================================
-- Migration 006: Renomear tabelas e campos para português (MySQL)
-- Data: 2025-11-14
-- ========================================

-- IMPORTANTE: Execute este script MANUALMENTE no MySQL Workbench ou via CLI

-- ========================================
-- 0. REMOVER FOREIGN KEYS
-- ========================================

ALTER TABLE `form_fields` DROP FOREIGN KEY `fk_form_fields_page`;
ALTER TABLE `form_pages` DROP FOREIGN KEY `fk_form_pages_formulario`;

-- ========================================
-- 1. RENOMEAR TABELA form_fields → formularios_campos
-- ========================================

RENAME TABLE `form_fields` TO `formularios_campos`;

ALTER TABLE `formularios_campos`
  CHANGE COLUMN `form_page_id` `pagina_id` INT NOT NULL,
  CHANGE COLUMN `label` `rotulo` VARCHAR(100) NOT NULL,
  CHANGE COLUMN `type` `tipo` VARCHAR(20) NOT NULL,
  CHANGE COLUMN `config` `configuracao` JSON NOT NULL,
  CHANGE COLUMN `show_when_rule_id` `regra_exibicao_id` INT NULL;

-- ========================================
-- 2. RENOMEAR TABELA form_pages → formularios_paginas
-- ========================================

RENAME TABLE `form_pages` TO `formularios_paginas`;

ALTER TABLE `formularios_paginas`
  CHANGE COLUMN `form_template_id` `formulario_id` INT NOT NULL,
  CHANGE COLUMN `label` `nome` VARCHAR(100) NOT NULL,
  CHANGE COLUMN `show_when_rule_id` `regra_exibicao_id` INT NULL;

-- ========================================
-- 3. RECRIAR FOREIGN KEYS
-- ========================================

ALTER TABLE `formularios_campos`
  ADD CONSTRAINT `fk_formularios_campos_pagina`
  FOREIGN KEY (`pagina_id`) REFERENCES `formularios_paginas`(`id`)
  ON DELETE CASCADE;

ALTER TABLE `formularios_paginas`
  ADD CONSTRAINT `fk_formularios_paginas_formulario`
  FOREIGN KEY (`formulario_id`) REFERENCES `formularios`(`id`)
  ON DELETE CASCADE;

-- ========================================
-- VERIFICAÇÃO
-- ========================================

SELECT '✅ Migration 006 concluída com sucesso!' as status;
SELECT 'Tabelas renomeadas:' as info;
SELECT '  - form_pages → formularios_paginas' as tabela1;
SELECT '  - form_fields → formularios_campos' as tabela2;

SELECT COUNT(*) as total_paginas FROM formularios_paginas;
SELECT COUNT(*) as total_campos FROM formularios_campos;
