# 📦 Importar Dump SQL no Railway - Método Simplificado

## 🚀 Forma Mais Simples (Recomendada)

### Passo 1: Fazer commit do dump SQL (opcional)

Se você já exportou o dump do MySQL Workbench/local:

```bash
# Copiar dump para o projeto
cp C:\Users\rafael.silva\Documents\dumps\Dump20251120-laudonr13.sql backend/migrations/dump_completo.sql

# Commit
git add backend/migrations/dump_completo.sql
git commit -m "feat: dump completo do banco local"
git push
```

### Passo 2: Executar via Railway CLI

**Opção A: Via Railway Run (Mais Simples)**

```powershell
railway run python scripts/import_dump_railway_simple.py migrations/dump_completo.sql
```

**Opção B: Via Railway Shell**

```powershell
railway shell
python scripts/import_dump_railway_simple.py migrations/dump_completo.sql
```

**Opção C: Com arquivo local**

```powershell
railway run python scripts/import_dump_railway_simple.py C:\Users\rafael.silva\Documents\dumps\Dump20251120-laudonr13.sql
```

---

## 📋 Conectando Manualmente (Alternativa)

Se preferir conectar manualmente com as credenciais do Railway:

### 1. Obter credenciais do Railway

No dashboard do Railway, vá em **Variables** e copie:
- `MYSQLHOST`
- `MYSQLPORT` 
- `MYSQLUSER`
- `MYSQLPASSWORD`
- `MYSQLDATABASE`

### 2. Executar com credenciais

```powershell
python scripts/import_dump_railway_simple.py dump.sql `
  --host shinkansen.proxy.rlwy.net `
  --port 19259 `
  --user <MYSQLUSER> `
  --password <MYSQLPASSWORD> `
  --database <MYSQLDATABASE>
```

---

## ⚡ Método Mais Rápido: MySQL CLI

Se tiver `mysql` instalado localmente:

### 1. Obter DATABASE_URL do Railway

```bash
railway variables
# Copie o valor de DATABASE_URL
```

### 2. Parsear e conectar

```bash
# Formato: mysql+pymysql://user:password@host:port/database
# Extrair componentes e executar:

mysql -h shinkansen.proxy.rlwy.net -P 19259 -u <user> -p<password> <database> < Dump20251120-laudonr13.sql
```

---

## ✅ Vantagens do Método Simplificado

- ✅ Usa DATABASE_URL automaticamente (via Railway)
- ✅ Não precisa configurar .env local
- ✅ Executa direto no ambiente Railway
- ✅ Mais rápido e direto

---

## 🎯 Recomendação

**Use:** `railway run python scripts/import_dump_railway_simple.py <dump.sql>`

É a forma mais simples e segura! 🚀

