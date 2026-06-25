# 🤖 Runbook para o Claude Code — Instalar o SER do zero (Windows)

> **Para o agente:** Este arquivo é um runbook completo. Execute na ordem, **verificando
> cada etapa antes de seguir**. Pare e avise o usuário se algo divergir. Não pule a
> seção "Pulos do gato" — ela contém erros já conhecidos que quebram a instalação.

## Contexto

- Projeto **SER** (Sistema de Emissão de Relatórios): `backend` FastAPI + MySQL, `frontend` React/Vite.
- Repositório: `https://github.com/sistemasrrvm/ser` — usar a branch **`quality`**.
- Objetivo: deixar rodando em `http://localhost:5173`, login `admin` / `Admin@123`.
- Plataforma: Windows. Shell primário PowerShell; há também Bash (Git). Comandos abaixo
  funcionam no Git Bash; adapte se usar PowerShell.

## Pré-requisitos (verificar primeiro)

```bash
winget --version          # precisa existir (Windows 11 tem)
```
- Internet ativa (baixa ~300 MB).
- **Microsoft Excel** instalado é necessário SÓ para exportar relatórios (não bloqueia o resto).
- **O banco de dados (`banco_atual.sql`) NÃO está no Git** (contém dados reais/LGPD).
  **PERGUNTE ao usuário onde está esse arquivo** e copie-o para `backend/migrations/banco_atual.sql`.
  Se ele não tiver o arquivo, siga assim mesmo: no fim, em vez de importar, use o endpoint
  `POST /api/v1/init-db` para criar um banco vazio com admin.

---

## Passo 1 — Clonar e ir para a branch `quality`

```bash
cd ~/Documents/GitHub 2>/dev/null || mkdir -p ~/Documents/GitHub && cd ~/Documents/GitHub
git clone https://github.com/sistemasrrvm/ser.git
cd ser
git checkout quality
git log --oneline -1   # deve mostrar o commit de setup automatizado
```
> Se já estiver clonado, só faça `git fetch && git checkout quality && git pull`.

## Passo 2 — Colocar o dump no lugar

Peça o `banco_atual.sql` ao usuário e copie:
```bash
cp "<caminho informado pelo usuario>/banco_atual.sql" backend/migrations/banco_atual.sql
ls -la backend/migrations/banco_atual.sql   # confirmar ~3 MB
```

## Passo 3 — Rodar o instalador automático

O jeito mais simples é deixar o próprio `SETUP.bat` fazer tudo:
```bash
cmd //c "SETUP.bat"
```
Ele instala Python/Node/MySQL (via winget — **avise o usuário para aceitar os prompts de UAC**),
inicializa o MySQL em `C:\ProgramData\MySQL\SER_Data`, cria o banco `rrvm_laudonr13`,
importa o dump, gera o `.env`, cria o venv, instala dependências e reseta a senha do admin.

> **Se preferir controle total (ou o SETUP.bat falhar), faça manualmente** — Passo 3-A a 3-G abaixo.
> Em ambos os casos, ao final valide pelo Passo 4.

### 3-A. Instalar toolchain (winget)
```bash
winget install --id Python.Python.3.12 -e --scope user --accept-package-agreements --accept-source-agreements
winget install --id OpenJS.NodeJS.LTS  -e --accept-package-agreements --accept-source-agreements
winget install --id Oracle.MySQL       -e --accept-package-agreements --accept-source-agreements
```
**O PATH desta sessão NÃO enxerga os novos programas.** Use caminhos completos:
- Python: `"$LOCALAPPDATA/Programs/Python/Python312/python.exe"` (em bash: `/c/Users/<user>/AppData/Local/Programs/Python/Python312/python.exe`)
- npm:    `"/c/Program Files/nodejs/npm.cmd"`
- MySQL:  detectar a pasta: `ls -d "/c/Program Files/MySQL/MySQL Server "*/bin`

### 3-B. Inicializar e subir o MySQL
```bash
MYSQLBIN="/c/Program Files/MySQL/MySQL Server 8.4/bin"   # ajuste a versão se necessário
DATADIR="C:/ProgramData/MySQL/SER_Data"
[ -d "/c/ProgramData/MySQL/SER_Data" ] || "$MYSQLBIN/mysqld.exe" --initialize-insecure --datadir="$DATADIR"
# subir em background:
"$MYSQLBIN/mysqld.exe" --datadir="$DATADIR" --port=3306   # rode com run_in_background
# esperar aceitar conexão (loop de mysqladmin ping --silent)
```

### 3-C. Configurar root e criar o banco
```bash
"$MYSQLBIN/mysql.exe" -u root --host=127.0.0.1 -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '1234'; CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY '1234'; GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION; CREATE DATABASE IF NOT EXISTS rrvm_laudonr13 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; FLUSH PRIVILEGES;"
```
> Criar `root@'%'` é o que faz as 3 VIEWs do dump importarem sem o erro de DEFINER.

### 3-D. Importar o dump
```bash
"$MYSQLBIN/mysql.exe" -u root -p1234 --host=127.0.0.1 rrvm_laudonr13 < backend/migrations/banco_atual.sql
# conferir:
"$MYSQLBIN/mysql.exe" -u root -p1234 --host=127.0.0.1 rrvm_laudonr13 -e "SELECT COUNT(*) FROM tab_equipamentos;"
```

### 3-E. Criar .env + venv + dependências
```bash
PYEXE="/c/Users/<user>/AppData/Local/Programs/Python/Python312/python.exe"
SECRET=$("$PYEXE" -c "import secrets;print(secrets.token_urlsafe(48))")
cat > backend/.env <<EOF
DATABASE_URL=mysql+pymysql://root:1234@localhost/rrvm_laudonr13
SECRET_KEY=$SECRET
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_RESET_TOKEN_EXPIRE_HOURS=1
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
APP_NAME=SER - Sistema de Emissao de Relatorios
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=True
PORT=8000
EXPORT_ENGINE=
FRONTEND_URL=http://localhost:5173
EOF
"$PYEXE" -m venv backend/venv
backend/venv/Scripts/python.exe -m pip install --upgrade pip
backend/venv/Scripts/python.exe -m pip install -r backend/requirements.txt
backend/venv/Scripts/python.exe -m pip install -r backend/requirements-windows.txt
```

### 3-F. Resetar a senha do admin
```bash
cd backend && PYTHONUTF8=1 venv/Scripts/python.exe scripts/reset_user_password.py admin "Admin@123"; cd ..
```
> Só funciona se o dump tiver sido importado (o usuário admin precisa existir).

### 3-G. Dependências do frontend
```bash
cd frontend && "/c/Program Files/nodejs/npm.cmd" install; cd ..
```

## Passo 4 — Subir e validar

```bash
# Backend (run_in_background), na pasta backend, COM PYTHONUTF8=1:
cd backend && export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 && venv/Scripts/python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8000
# Frontend (run_in_background), na pasta frontend:
cd frontend && "/c/Program Files/nodejs/npm.cmd" run dev
```
Validar:
```bash
curl -s -m 5 http://localhost:8000/api/v1/health
curl -s -m 8 -X POST http://localhost:5173/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"Admin@123"}' -o /dev/null -w "%{http_code}\n"   # esperado: 200
```
Depois disso, o uso diário é só o **`INICIAR.bat`** (duplo-clique).

---

## 🐱 Pulos do gato (erros já conhecidos — NÃO repetir)

1. **`PYTHONUTF8` é obrigatório** no backend (Windows), senão o startup quebra com
   `UnicodeEncodeError` (print de emoji em console cp1252). Em `.bat`, use
   `set "PYTHONUTF8=1"` **com aspas** — sem aspas captura espaço (`"1 "`) → erro fatal do Python.
2. **DEFINER das VIEWs**: o dump tem `DEFINER=root@%`. Por isso criamos `root@'%'` no MySQL
   (Passo 3-C). Sem isso, as 3 views `vw_*_lookup` falham na importação.
3. **Datadir é `C:\ProgramData\MySQL\SER_Data`** (não o padrão do MySQL). SETUP.bat e
   INICIAR.bat já usam esse caminho — mantenha consistente.
4. **MySQL não é serviço** — sobe como processo (INICIAR.bat cuida). Após reboot, rodar INICIAR.bat.
5. **PATH pós-winget**: a sessão atual não vê Python/Node/MySQL recém-instalados — use caminhos
   completos. O INICIAR.bat adiciona o Node ao PATH para o `npm` funcionar.
6. **Schema vs models**: `user.py` já tem `User.id` como BIGINT (corrigido). Se for usar
   `/init-db` (banco vazio) em vez do dump, isso é necessário; com o dump, já vem certo.

## 📤 Commit / push (política)

- **NUNCA** commitar: `backend/migrations/banco_atual.sql`, `backend/.env`,
  `backend/migrations/_backup_local_*.sql`, `venv/`, `node_modules/` — já estão no `.gitignore`.
  Sempre rode `git status` e confira antes de `git add`.
- Trabalhar na branch **`quality`** (ou criar branch a partir dela).
- Mensagem de commit clara; terminar com:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **Push**: pode usar as credenciais já salvas (Git Credential Manager do GitHub Desktop) —
  `git push origin quality`. Se pedir login e não houver credencial, **avise o usuário**
  (não peça token no chat).
