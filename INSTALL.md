# 🪟 Instalação do SER no Windows (passo a passo)

Como colocar o **SER (Sistema de Emissão de Relatórios)** rodando em uma máquina Windows
do zero. Este projeto tem **backend** (FastAPI/MySQL) e **frontend** (React/Vite).

> **Resumo:** clonar (branch `quality`) → obter o banco à parte → `SETUP.bat` (uma vez) → `INICIAR.bat` (uso diário).

---

## 1. Pré-requisitos

- **Windows 10/11** com `winget` (o `SETUP.bat` instala Python, Node e MySQL automaticamente).
- **Microsoft Excel instalado** — necessário **apenas** para a exportação de relatórios em Excel.
  Sem Excel, o sistema funciona normalmente, exceto exportar (ou use `EXPORT_ENGINE=openpyxl` no `.env`).

## 2. Obter o código

```bash
git clone https://github.com/sistemasrrvm/ser.git
cd ser
git checkout quality
```

## 3. Obter o banco de dados (à parte — NÃO está no Git)

O arquivo `backend/migrations/banco_atual.sql` contém **dados reais** (clientes, equipamentos,
usuários com hashes de senha) e por isso **não é versionado** (privacidade / LGPD).

Peça o arquivo `banco_atual.sql` a quem administra o sistema e coloque-o em:

```
backend/migrations/banco_atual.sql
```

> Sem esse arquivo, o `SETUP.bat` cria o banco **vazio**. Você pode popular depois iniciando o
> backend e chamando `POST http://localhost:8000/api/v1/init-db` (cria as tabelas + admin).

## 4. Instalar (uma vez)

Dê **duplo-clique em `SETUP.bat`**. Ele:

1. Instala **Python 3.12**, **Node.js LTS** e **MySQL 8.4** (via `winget` — aceite os prompts de UAC).
2. Inicializa o MySQL, cria o usuário `root` (senha `1234`) e o banco `rrvm_laudonr13`.
3. Importa o `banco_atual.sql` (se presente).
4. Gera o `backend/.env` (com `SECRET_KEY` nova), cria o `venv` e instala as dependências
   (`requirements.txt` + `requirements-windows.txt`).
5. Reseta a senha do `admin` para `Admin@123`.
6. Roda `npm install` no frontend.

## 5. Usar (dia a dia)

Dê **duplo-clique em `INICIAR.bat`** → sobem MySQL, backend e frontend, e o navegador abre em
**http://localhost:5173**.

- **Login:** `admin` / `Admin@123`
- **API/Swagger:** http://localhost:8000/api/docs

Para parar: feche as janelas “SER Backend” e “SER Frontend”.

---

## Notas técnicas

- **MySQL** roda como processo (não serviço) — o `INICIAR.bat` o sobe a cada uso.
- **`PYTHONUTF8=1`** é obrigatório ao rodar o backend no Windows (o `INICIAR.bat` já define);
  sem isso o startup quebra com `UnicodeEncodeError`. Em `.bat` use `set "PYTHONUTF8=1"` (com aspas).
- **Banco:** MySQL `rrvm_laudonr13`, `DATABASE_URL=mysql+pymysql://root:1234@localhost/rrvm_laudonr13`.
- Instalação manual detalhada e solução de problemas: ver o backend `README.md` e `KNOWN_ISSUES.md`.
