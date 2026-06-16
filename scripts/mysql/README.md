# Scripts SQL - SER (Sistema de Emissão de Relatórios)

## Ordem de Execução

Execute os scripts na seguinte ordem:

### 1. `001_create_tables.sql`
Cria todas as tabelas necessárias para o funcionamento do sistema:
- `roles` - Perfis de acesso
- `users` - Usuários do sistema
- `password_reset_tokens` - Tokens para recuperação de senha
- `refresh_tokens` - Tokens de refresh (manter conectado)
- `formularios` - Cadastro de formulários
- `show_when_rules` - Regras de visibilidade (Sprint 002)
- `show_when_conditions` - Condições das regras (Sprint 002)

**Nota:** As tabelas `paginas` e `campos` foram removidas. O sistema agora usa `formularios_paginas` e `formularios_campos`.

### 2. `002_seed_admin.sql`
Insere dados iniciais:
- 3 roles: `admin` (100), `revisor` (40), `usuario` (20)
- Usuário admin padrão

## Configuração de Acesso Inicial

### Primeiro Login
- **Username:** `admin`
- **Senha:** `Admin@123`

⚠️ **IMPORTANTE:** Altere a senha após o primeiro acesso!

## Como Executar

### Via MySQL CLI
```bash
mysql -u root -p < scripts/mysql/001_create_tables.sql
mysql -u root -p < scripts/mysql/002_seed_admin.sql
```

### Via MySQL Workbench
1. Abra o MySQL Workbench
2. Conecte ao servidor MySQL
3. Abra cada arquivo SQL
4. Execute na ordem especificada

### Via Script Python (Futuro)
```bash
cd backend
python scripts/init_db.py
```

## Observações

- As tabelas `campos`, `show_when_rules` e `show_when_conditions` estão prontas mas serão utilizadas apenas a partir da **Sprint 002**
- O hash da senha do admin foi gerado com **Argon2id** (memory=65536, iterations=3, parallelism=4)
- A senha padrão atende aos requisitos: 8+ caracteres, maiúsculas, números e caracteres especiais

## Conexão do Backend

```env
DATABASE_URL=mysql://root:1234@localhost/db_a2cb65_laudonr
```
