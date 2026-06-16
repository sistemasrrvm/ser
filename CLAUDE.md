## Pasta de Sprints
`D:\REPOSITORIO_GIT\laudonr13-doc\.claude-sprints`

## Deploy no Railway - Processo Completo

### ⚠️ IMPORTANTE: Inicialização de Banco de Dados

**PROBLEMA:** Railway **NÃO** possui shell interativo para executar scripts de migração/seeds.

**SOLUÇÃO QUE FUNCIONOU:** Criar endpoint HTTP para inicializar banco de dados.

#### Passos para Inicialização do Banco:

1. **Criar endpoint `/api/v1/init-db`** (POST) no backend que:
   - Executa `SQLModel.metadata.create_all(engine)` para criar todas as tabelas
   - Cria Role admin (name="admin", level=100)
   - Cria User admin (username="admin", password="admin123")
   - Retorna status de sucesso/erro

2. **Exemplo de código funcional:**
```python
@api_router.post("/init-db", tags=["Admin"])
async def init_database():
    from ...core.database import create_db_and_tables, engine
    from ...models import User, Role
    from ...core.security import get_password_hash
    from sqlmodel import Session, select

    try:
        create_db_and_tables()  # Cria todas as tabelas

        with Session(engine) as session:
            # Criar Role admin
            admin_role = session.exec(select(Role).where(Role.name == "admin")).first()
            if not admin_role:
                admin_role = Role(name="admin", level=100, description="Administrador do Sistema")
                session.add(admin_role)
                session.commit()
                session.refresh(admin_role)

            # Criar User admin
            admin = session.exec(select(User).where(User.username == "admin")).first()
            if not admin:
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    full_name="Administrador",
                    password_hash=get_password_hash("admin123"),
                    role_id=admin_role.id,
                    is_active=True
                )
                session.add(admin_user)
                session.commit()

                return {
                    "status": "completed",
                    "admin_created": True,
                    "admin_username": "admin",
                    "admin_password": "admin123"
                }

            return {"status": "completed", "admin_created": False}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
```

3. **Executar via HTTP POST:**
```bash
# PowerShell
Invoke-RestMethod -Method POST -Uri "https://seu-backend.railway.app/api/v1/init-db"

# Postman
POST https://seu-backend.railway.app/api/v1/init-db
```

**Dicas importantes:**
- ✅ Verificar sempre se campos obrigatórios têm valores (ex: `level`, `password_hash`, `role_id`)
- ✅ Criar dependências primeiro (Role antes de User)
- ✅ Usar `session.commit()` e `session.refresh()` após cada insert
- ❌ NÃO tentar executar scripts locais com `railway run` (roda no seu PC, não no container)
- ❌ NÃO tentar usar `railway shell` interativo (não existe shell web no Railway básico)

---

## Railway CLI - Comandos Corretos

### Variáveis de Ambiente

**Listar variáveis:**
```bash
railway variables
railway variables --service <nome-servico>
railway variables --kv  # Formato KEY=VALUE
railway variables --json  # Formato JSON
```

**Adicionar/Alterar variável:**
```bash
# Sintaxe correta: --set (com dois traços)
railway variables --set "KEY=VALUE"
railway variables --set "DATABASE_URL=${{MySQL.DATABASE_URL}}"

# Múltiplas variáveis de uma vez
railway variables --set "KEY1=VALUE1" --set "KEY2=VALUE2"

# ❌ ERRADO: railway variables set KEY=VALUE (sem --)
```

**Referências do Railway (variáveis compartilhadas):**
```bash
# Para referenciar variáveis de outros serviços (como MySQL)
railway variables --set "DATABASE_URL=${{MySQL.DATABASE_URL}}"
railway variables --set "REDIS_URL=${{Redis.REDIS_URL}}"
```

**PowerShell - Problemas com aspas:**
```bash
# ✅ Use aspas duplas para variáveis com $ ou {}
railway variables --set "DATABASE_URL=${{MySQL.DATABASE_URL}}"

# ❌ Aspas simples no PowerShell não funcionam com ${{}}
# railway variables --set 'DATABASE_URL=${{MySQL.DATABASE_URL}}'
```

### Outros Comandos Úteis

**Linkar projeto:**
```bash
railway link
railway link --project <nome-projeto> --service <nome-servico>
```

**Deploy:**
```bash
railway up  # Deploy da pasta atual
railway up --detach  # Deploy em background
```

**Domínio:**
```bash
railway domain  # Gerar/listar domínio público
```

**Adicionar serviços:**
```bash
railway add  # Interativo
# Opções: Database (MySQL, PostgreSQL, Redis, MongoDB)
```

**Shell remoto:**
```bash
railway shell  # Acessa shell do container em produção
```

**Logs:**
```bash
railway logs  # Ver logs em tempo real
railway logs --service <nome-servico>
```

---

## Pasta de Documentação
**IMPORTANTE:** Documentos que não correspondem a código fonte devem ser gravados em:
`D:\REPOSITORIO_GIT\laudonr13-doc`

**Exemplos de documentos:**
- Guias de deploy e configuração
- Documentação de arquitetura
- Manuais de usuário
- Especificações técnicas
- Diagramas e fluxogramas
- Notas de release

**O que NÃO gravar nesta pasta:**
- Código fonte (backend/frontend)
- Arquivos de configuração do projeto (.json, .ts, .py)
- README.md técnico do projeto
- Migrations de banco de dados

---

## Estrutura do Banco de Dados (MySQL)

### Tabelas de Formulários

#### `formularios_paginas` (Páginas de Formulários)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INT (PK) | ID único da página |
| `formulario_id` | INT (FK → formularios.id) | ID do formulário |
| `nome` | VARCHAR(100) | Nome da página |
| `ordem` | INT | Ordem de exibição |
| `regra_exibicao_id` | INT (NULL) | ID da regra de exibição condicional |
| `created_at` | TIMESTAMP | Data de criação |
| `updated_at` | TIMESTAMP | Data de atualização |

**Foreign Keys:**
- `fk_formularios_paginas_formulario`: `formulario_id` → `formularios(id)` ON DELETE CASCADE

---

#### `formularios_campos` (Campos de Formulários)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INT (PK) | ID único do campo |
| `pagina_id` | INT (FK → formularios_paginas.id) | ID da página |
| `rotulo` | VARCHAR(100) | Rótulo/Label do campo |
| `ordem` | INT | Ordem do campo na página |
| `tipo` | VARCHAR(20) | Tipo do campo (textbox, date, number, yes_no, choice, lookup, separator) |
| `configuracao` | JSON | Configurações específicas do campo |
| `regra_exibicao_id` | INT (NULL) | ID da regra de exibição condicional |
| `created_at` | TIMESTAMP | Data de criação |
| `updated_at` | TIMESTAMP | Data de atualização |

**Foreign Keys:**
- `fk_formularios_campos_pagina`: `pagina_id` → `formularios_paginas(id)` ON DELETE CASCADE

**Tipos de campo válidos:**
- `textbox` - Campo de texto
- `date` - Campo de data
- `number` - Campo numérico
- `yes_no` - Campo booleano (Sim/Não)
- `choice` - Campo de escolha única (dropdown)
- `lookup` - Campo de busca em outra tabela
- `separator` - Separador visual (não é campo de dados)

---

### Histórico de Migrações

#### Migration 006 - Renomear Tabelas para Português (2025-11-14)
**Objetivo:** Padronizar nomenclatura do banco de dados em português

**Alterações:**
1. `form_pages` → `formularios_paginas`
   - `form_template_id` → `formulario_id`
   - `label` → `nome`
   - `show_when_rule_id` → `regra_exibicao_id`

2. `form_fields` → `formularios_campos`
   - `form_page_id` → `pagina_id`
   - `label` → `rotulo`
   - `type` → `tipo`
   - `config` → `configuracao`
   - `show_when_rule_id` → `regra_exibicao_id`

**Arquivos de migração:**
- `backend/migrations/migration_006_rename_tables_pt_mysql.sql` - SQL para MySQL
- `backend/scripts/run_migration_006_mysql.py` - Script Python para execução

**⚠️ IMPORTANTE:** Esta migração deve ser executada MANUALMENTE via MySQL Workbench devido à complexidade das foreign keys.