# Instruções para Executar Migration 006

## ⚠️ ATENÇÃO - Leia Antes de Executar

Esta migração renomeia tabelas e campos do banco de dados para português. É uma operação **irreversível** que afeta a estrutura do banco.

---

## 📋 Pré-requisitos

1. Backup do banco de dados
2. MySQL Workbench instalado
3. Acesso ao banco `db_a2cb65_laudonr`
4. Backend e Frontend **PARADOS** durante a migração

---

## 🔧 Passo a Passo

### 1. Fazer Backup

```sql
-- Execute no MySQL Workbench
mysqldump -u root -p db_a2cb65_laudonr > backup_antes_migration_006.sql
```

### 2. Verificar Estado Atual

```sql
-- Deve listar as tabelas: form_pages, form_fields
SHOW TABLES LIKE 'form_%';

-- Verificar foreign keys
SELECT
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
  AND TABLE_NAME IN ('form_pages', 'form_fields')
  AND REFERENCED_TABLE_NAME IS NOT NULL;
```

### 3. Executar Migration

**Copie e cole TODO o conteúdo do arquivo:**
`backend/migrations/migration_006_rename_tables_pt_mysql.sql`

**NO MySQL Workbench**, selecione todo o SQL e execute (⚡ Execute).

### 4. Verificar Sucesso

```sql
-- Deve listar: formularios_paginas, formularios_campos
SHOW TABLES LIKE 'formularios_%';

-- Verificar dados
SELECT COUNT(*) FROM formularios_paginas;
SELECT COUNT(*) FROM formularios_campos;

-- Verificar foreign keys novas
SELECT
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
  AND TABLE_NAME IN ('formularios_paginas', 'formularios_campos')
  AND REFERENCED_TABLE_NAME IS NOT NULL;
```

### 5. Iniciar Aplicação

Após verificar que a migração foi bem-sucedida:

1. Iniciar backend: `cd backend && uvicorn src.main:app --reload`
2. Iniciar frontend: `cd frontend && npm run dev`
3. Testar funcionalidades de formulários

---

## 🔄 Rollback (se necessário)

**⚠️ APENAS se algo der errado!**

```sql
-- 1. Remover FKs
ALTER TABLE `formularios_campos` DROP FOREIGN KEY `fk_formularios_campos_pagina`;
ALTER TABLE `formularios_paginas` DROP FOREIGN KEY `fk_formularios_paginas_formulario`;

-- 2. Renomear tabelas de volta
RENAME TABLE `formularios_campos` TO `form_fields`;
RENAME TABLE `formularios_paginas` TO `form_pages`;

-- 3. Renomear colunas de volta
ALTER TABLE `form_fields`
  CHANGE COLUMN `pagina_id` `form_page_id` INT NOT NULL,
  CHANGE COLUMN `rotulo` `label` VARCHAR(100) NOT NULL,
  CHANGE COLUMN `tipo` `type` VARCHAR(20) NOT NULL,
  CHANGE COLUMN `configuracao` `config` JSON NOT NULL,
  CHANGE COLUMN `regra_exibicao_id` `show_when_rule_id` INT NULL;

ALTER TABLE `form_pages`
  CHANGE COLUMN `formulario_id` `form_template_id` INT NOT NULL,
  CHANGE COLUMN `nome` `label` VARCHAR(100) NOT NULL,
  CHANGE COLUMN `regra_exibicao_id` `show_when_rule_id` INT NULL;

-- 4. Recriar FKs antigas
ALTER TABLE `form_fields`
  ADD CONSTRAINT `fk_form_fields_page`
  FOREIGN KEY (`form_page_id`) REFERENCES `form_pages`(`id`)
  ON DELETE CASCADE;

ALTER TABLE `form_pages`
  ADD CONSTRAINT `fk_form_pages_formulario`
  FOREIGN KEY (`form_template_id`) REFERENCES `formularios`(`id`)
  ON DELETE CASCADE;
```

---

## ✅ Checklist Final

- [ ] Backup do banco criado
- [ ] Migration executada sem erros
- [ ] Tabelas renomeadas (`formularios_paginas`, `formularios_campos`)
- [ ] Colunas renomeadas (verificar com `DESCRIBE`)
- [ ] Foreign keys recriadas corretamente
- [ ] Contagem de registros mantida
- [ ] Backend inicia sem erros
- [ ] Frontend inicia sem erros
- [ ] Teste criar/editar página de formulário
- [ ] Teste criar/editar campo de formulário
- [ ] Teste importação Excel

---

## 📞 Em Caso de Problemas

1. **Backend não inicia**: Verifique se todas as tabelas foram renomeadas
2. **Frontend com erro 404**: Limpe cache do navegador (Ctrl+Shift+Del)
3. **Erro de FK**: Execute o rollback completo
4. **Dados perdidos**: Restaure o backup

---

**Data da migração:** 2025-11-14
**Arquivo SQL:** `backend/migrations/migration_006_rename_tables_pt_mysql.sql`
