# 📦 Migration: Importar Dump Completo para Railway

Este guia explica como gerar e executar uma migration completa com dump do banco local para o Railway.

## 🎯 Fluxo de Trabalho

1. **Gerar migration SQL** do banco local → arquivo na pasta `migrations/`
2. **Fazer commit** do arquivo SQL
3. **Executar no Railway** via script ou durante build

---

## 📝 Passo 1: Gerar Migration SQL Completa

### No seu computador (banco local configurado):

```bash
cd backend
python scripts/generate_full_dump_migration.py --output migrations/migration_015_full_dump.sql
```

**Ou direcionar para stdout:**

```bash
python scripts/generate_full_dump_migration.py > migrations/migration_015_full_dump.sql
```

**O que o script faz:**
- ✅ Conecta no banco local (DATABASE_URL do .env)
- ✅ Gera CREATE TABLE para todas as tabelas
- ✅ Gera INSERT para todos os registros
- ✅ Salva em `migrations/migration_015_full_dump.sql`

---

## 📦 Passo 2: Fazer Commit

```bash
git add backend/migrations/migration_015_full_dump.sql
git commit -m "feat: migration 015 - dump completo do banco local"
git push
```

---

## 🚀 Passo 3: Executar no Railway

### Opção A: Via Railway Shell (Manual)

```bash
railway shell
python scripts/run_migration_full_dump.py
```

### Opção B: Via Railway Run (Local)

```bash
railway run python scripts/run_migration_full_dump.py
```

### Opção C: Automático no Build (Recomendado)

Configurar no `railway.json` para executar durante o deploy:

```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt && python scripts/run_migration_full_dump.py"
  }
}
```

⚠️ **CUIDADO:** Isso executará a migration em TODO deploy. Use apenas uma vez!

---

## 🔄 Fluxo Recomendado (Uso Único)

1. Gerar migration uma vez
2. Commit e push
3. Executar manualmente no Railway uma vez via `railway run`
4. Remover do `railway.json` após execução

---

## ⚠️ Avisos Importantes

- ⚠️ **Backup primeiro!** A migration pode sobrescrever dados
- ⚠️ **Use apenas uma vez** para importação inicial
- ⚠️ **Verifique o tamanho** - dumps grandes podem demorar
- ⚠️ **Teste localmente** antes de executar no Railway

---

## 📋 Checklist

- [ ] Backup do banco Railway (se necessário)
- [ ] Gerar migration: `python scripts/generate_full_dump_migration.py --output migrations/migration_015_full_dump.sql`
- [ ] Verificar arquivo gerado
- [ ] Commit e push
- [ ] Executar no Railway: `railway run python scripts/run_migration_full_dump.py`
- [ ] Verificar dados importados

