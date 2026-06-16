# Scripts de Atualização de Roles e Usuário Admin

Este diretório contém scripts para atualizar os perfis do sistema (Tecnico, Suporte, Administrador) e ajustar o usuário admin para usar o perfil "Administrador".

## Arquivos Disponíveis

1. **003_update_roles_and_admin.sql** - Script SQL para MySQL
2. **../update_roles_and_admin.py** - Script Python (alternativa)

## O que os scripts fazem

### 1. Cria/Atualiza os Roles

- **Tecnico** (nível 20): Dashboard e Relatórios
- **Suporte** (nível 50): Dashboard, Relatórios, Clientes, Equipamentos
- **Administrador** (nível 100): Acesso total ao sistema

### 2. Atualiza o Usuário Admin

Atualiza o `role_id` do usuário `admin` para o perfil "Administrador".

## Como Executar

### Opção 1: Script SQL (Recomendado)

```bash
# No MySQL
mysql -u seu_usuario -p db_a2cb65_laudonr < scripts/mysql/003_update_roles_and_admin.sql
```

Ou execute diretamente no cliente MySQL:

```sql
USE db_a2cb65_laudonr;
SOURCE scripts/mysql/003_update_roles_and_admin.sql;
```

### Opção 2: Script Python

```bash
# A partir da raiz do projeto
cd scripts
python update_roles_and_admin.py
```

**Nota:** O script Python requer que o ambiente virtual esteja ativado e as dependências instaladas.

## Verificação

Após executar o script, você pode verificar os resultados executando:

```sql
-- Verificar usuário admin
SELECT 
    u.id,
    u.username,
    u.full_name,
    u.email,
    u.role_id,
    r.name as role_name,
    r.level as role_level,
    r.description as role_description,
    u.is_active
FROM users u
INNER JOIN roles r ON u.role_id = r.id
WHERE u.username = 'admin';

-- Verificar todos os roles
SELECT 
    id,
    name,
    level,
    description,
    created_at
FROM roles
ORDER BY level DESC;
```

## Resultado Esperado

O usuário `admin` deve estar com:
- `role_id` apontando para o role "Administrador"
- `role_name` = "Administrador"
- `role_level` = 100

Os três roles devem existir no banco:
- Tecnico (nível 20)
- Suporte (nível 50)
- Administrador (nível 100)

## Importante

⚠️ **Execute este script APENAS UMA VEZ** após a migração para o novo sistema de roles.

Os roles antigos (`admin`, `revisor`, `usuario`) podem permanecer no banco, mas não serão mais usados pelo sistema.

