# Verificação de Uso das Tabelas

## Resumo

Verificação realizada em: 2025-11-21

---

## 1. Tabela `clientes`

**Status: ✅ EM USO - NÃO PODE SER REMOVIDA**

### Uso no código:
- **Modelo**: `Cliente` (`backend/src/models/cliente.py`)
  - `__tablename__ = "clientes"`
- **API Endpoint**: `/api/v1/clientes` (`backend/src/api/v1/clientes.py`)
  - GET `/clientes` - Listar clientes
  - GET `/clientes/{id}` - Obter cliente
  - POST `/clientes` - Criar cliente (admin)
  - PUT `/clientes/{id}` - Atualizar cliente (admin)
  - DELETE `/clientes/{id}` - Deletar cliente (admin)
- **Relacionamentos**:
  - `Report.cliente_id` → FK para `clientes.id`
  - `Filial.cliente_id` → FK para `clientes.id`

### Tabela substituta:
- **`tab_clientes`** existe, mas é uma tabela diferente (cache do SQL Server)
  - Modelo: `ManutCliente` (`backend/src/models/manut_cliente.py`)
  - Usada para sincronização com sistema externo
  - **NÃO substitui `clientes`**

---

## 2. Tabela `filiais`

**Status: ✅ EM USO - NÃO PODE SER REMOVIDA**

### Uso no código:
- **Modelo**: `Filial` (`backend/src/models/filial.py`)
  - `__tablename__ = "filiais"`
- **API Endpoint**: `/api/v1/clientes/{cliente_id}/filiais` (`backend/src/api/v1/clientes.py`)
  - GET `/clientes/{cliente_id}/filiais` - Listar filiais de um cliente
- **Relacionamentos**:
  - `Report.filial_id` → FK para `filiais.id`
  - `Equipamento.filial_id` → FK para `filiais.id`

### Tabela substituta:
- **Nenhuma** - esta é a tabela principal

---

## 3. Tabela `equipamentos`

**Status: ✅ EM USO - NÃO PODE SER REMOVIDA**

### Uso no código:
- **Modelo**: `Equipamento` (`backend/src/models/equipamento.py`)
  - `__tablename__ = "equipamentos"`
- **API Endpoint**: `/api/v1/filiais/{filial_id}/equipamentos` (`backend/src/api/v1/equipamentos.py`)
  - GET `/filiais/{filial_id}/equipamentos` - Listar equipamentos de uma filial
  - GET `/filiais/{filial_id}/equipamentos/{id}` - Obter equipamento
- **Relacionamentos**:
  - `Report.equipamento_id` → FK para `equipamentos.id`

### Tabela substituta:
- **`tab_equipamentos`** existe, mas é uma tabela diferente (cache do SQL Server)
  - Modelo: `ManutEquipamento` (`backend/src/models/manut_equipamento.py`)
  - Usada para sincronização com sistema externo
  - **NÃO substitui `equipamentos`**

---

## 4. Tabela `campos`

**Status: ❌ NÃO ENCONTRADA NO CÓDIGO - PODE SER REMOVIDA**

### Uso no código:
- **Nenhum modelo** usa `__tablename__ = "campos"`
- **Nenhum endpoint** referencia a tabela `campos`
- **Nenhuma FK** aponta para `campos`

### Tabela substituta:
- **`formularios_campos`** é a tabela ativa para campos de formulários
  - Modelo: `FormField` (`backend/src/models/form_field.py`)
  - `__tablename__ = "formularios_campos"`
  - Usada pelo sistema de formulários dinâmicos

### Observação:
- Se a tabela `campos` existe no banco, provavelmente é uma tabela antiga/obsoleta
- Pode ser removida com segurança se não houver dados importantes

---

## Recomendações

### ❌ NÃO REMOVER:
1. `clientes` - Tabela principal de clientes, usada por Reports e Filiais
2. `filiais` - Tabela principal de filiais, usada por Reports e Equipamentos
3. `equipamentos` - Tabela principal de equipamentos, usada por Reports

### ✅ PODE REMOVER (após verificação no banco):
1. `campos` - Não encontrada no código, provavelmente obsoleta
   - **Ação**: Verificar se existe no banco e se tem dados importantes antes de remover

---

## Script de Verificação no Banco

Execute estas queries para verificar se as tabelas existem e têm dados:

```sql
-- Verificar se tabelas existem
SELECT TABLE_NAME, TABLE_ROWS 
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr' 
  AND TABLE_NAME IN ('clientes', 'filiais', 'equipamentos', 'campos');

-- Verificar registros em cada tabela
SELECT 'clientes' as tabela, COUNT(*) as total FROM clientes
UNION ALL
SELECT 'filiais', COUNT(*) FROM filiais
UNION ALL
SELECT 'equipamentos', COUNT(*) FROM equipamentos
UNION ALL
SELECT 'campos', COUNT(*) FROM campos;

-- Verificar FKs que referenciam essas tabelas
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
  AND REFERENCED_TABLE_NAME IN ('clientes', 'filiais', 'equipamentos', 'campos');
```

