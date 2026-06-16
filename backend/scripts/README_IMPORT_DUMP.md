# 📦 Como Importar Dump SQL no Railway

Este guia explica como importar um dump SQL do banco local para o Railway.

## 📋 Pré-requisitos

1. **Railway CLI instalado**
   ```bash
   npm install -g @railway/cli
   ```

2. **Autenticado no Railway**
   ```bash
   railway login
   ```

3. **Projeto conectado**
   ```bash
   railway link
   ```
   (ou navegue até a pasta do projeto que já está linkado)

## 🚀 Método 1: Via Railway Shell (Recomendado)

### Passo 1: Conectar no Railway Shell
```bash
railway shell
```

### Passo 2: Executar o script
```bash
python scripts/import_dump_to_railway.py /caminho/para/Dump20251120-laudonr13.sql
```

**No Windows, o caminho pode ser:**
```bash
python scripts/import_dump_to_railway.py C:\\Users\\rafael.silva\\Documents\\dumps\\Dump20251120-laudonr13.sql
```

**Ou copie o arquivo para dentro do projeto:**
```bash
# Copiar arquivo para o projeto
cp C:\Users\rafael.silva\Documents\dumps\Dump20251120-laudonr13.sql ./dump.sql

# Executar
python scripts/import_dump_to_railway.py ./dump.sql
```

---

## 🖥️ Método 2: Via Railway Run (Local)

Execute direto do seu computador (o Railway CLI vai executar no ambiente Railway):

```bash
railway run python scripts/import_dump_to_railway.py C:\Users\rafael.silva\Documents\dumps\Dump20251120-laudonr13.sql
```

**Nota:** O arquivo precisa estar acessível. Se estiver local, copie para o projeto primeiro.

---

## 📝 Método 3: Via MySQL direto (Alternativa)

Se preferir usar o MySQL diretamente:

### 1. Obter DATABASE_URL do Railway
```bash
railway variables
# Copie o valor de DATABASE_URL
```

### 2. Parsear a URL
Formato: `mysql+pymysql://user:password@host:port/database`

### 3. Executar via mysql CLI
```bash
mysql -h <host> -P <port> -u <user> -p<password> <database> < Dump20251120-laudonr13.sql
```

---

## ⚠️ Importante

1. **Backup primeiro!** O script vai sobrescrever dados existentes
2. **Tamanho do arquivo:** Dumps grandes podem demorar
3. **Erros comuns:** 
   - "Table already exists" - pode ignorar (tabela já existe)
   - "Duplicate key" - pode ignorar (dados já existem)

## 🔍 Verificar Importação

Após importar, verifique:

```bash
railway shell
python scripts/check_tables.py
```

---

## 🆘 Troubleshooting

### Erro: "DATABASE_URL não configurada"
- Certifique-se de estar no ambiente Railway (`railway shell`)
- Ou configure DATABASE_URL no `.env` local

### Erro: "Arquivo não encontrado"
- Verifique o caminho do arquivo
- Use caminho absoluto ou copie o arquivo para o projeto

### Erro de conexão
- Verifique se o banco do Railway está ativo
- Verifique as credenciais na DATABASE_URL

