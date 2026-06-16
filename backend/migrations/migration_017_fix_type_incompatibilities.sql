-- Migration 017: Corrigir incompatibilidades de tipo e remover filial_id de reports
-- Data: 2025-11-21
-- Descrição: Corrige incompatibilidades de tipo entre tabelas e remove filial_id de reports

-- 1. Remover coluna filial_id da tabela reports (se existir)
ALTER TABLE `reports` DROP COLUMN IF EXISTS `filial_id`;

-- 2. Corrigir tipo de formulario_id em formularios_paginas (INT -> BIGINT)
ALTER TABLE `formularios_paginas` 
MODIFY COLUMN `formulario_id` bigint NOT NULL;

-- 3. Corrigir tipo de pagina_id em formularios_campos (INT -> BIGINT)
ALTER TABLE `formularios_campos` 
MODIFY COLUMN `pagina_id` bigint NOT NULL;

-- 4. Verificar se foreign keys estão corretas (não precisa alterar, apenas documentar)
-- formularios_paginas.formulario_id -> formularios.id (BIGINT -> BIGINT) ✓
-- formularios_campos.pagina_id -> formularios_paginas.id (BIGINT -> BIGINT) ✓

-- Nota: Os modelos SQLModel já esperam BIGINT para essas FKs, então a correção do banco
-- deve resolver os problemas de validação de tipo.

