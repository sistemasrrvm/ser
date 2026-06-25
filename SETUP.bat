@echo off
REM ============================================================
REM  SER - INSTALACAO AUTOMATICA (rodar UMA UNICA VEZ no PC novo)
REM  Instala Python, Node e MySQL, cria o banco, importa o dump,
REM  instala dependencias e prepara tudo para o INICIAR.bat.
REM ============================================================
setlocal enabledelayedexpansion
set "PROJ=%~dp0"

echo.
echo ============================================================
echo  SER - Setup do ambiente (uma vez so)
echo ============================================================
echo  ATENCAO: podem aparecer janelas do Windows pedindo permissao
echo  (UAC) ao instalar Node e MySQL. Clique em SIM.
echo ============================================================
echo.
pause

REM ----------------------------------------------------------------
REM 1) Instalar Python 3.12, Node LTS e MySQL 8.4 via winget
REM ----------------------------------------------------------------
echo [1/8] Instalando Python 3.12...
winget install --id Python.Python.3.12 -e --scope user --accept-package-agreements --accept-source-agreements

echo [2/8] Instalando Node.js LTS...
winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements

echo [3/8] Instalando MySQL 8.4 Community Server...
winget install --id Oracle.MySQL -e --accept-package-agreements --accept-source-agreements

REM ----------------------------------------------------------------
REM Caminhos (o PATH desta janela ainda nao enxerga os novos
REM programas, por isso usamos caminhos completos)
REM ----------------------------------------------------------------
set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
set "NPMCMD=C:\Program Files\nodejs\npm.cmd"

REM Auto-detecta a pasta do MySQL (qualquer versao "MySQL Server X.Y")
set "MYSQLBIN="
for /d %%d in ("C:\Program Files\MySQL\MySQL Server *") do set "MYSQLBIN=%%d\bin"
set "MYSQLDATA=C:\ProgramData\MySQL\SER_Data"

echo.
echo --- Verificando instalacoes ---
if not exist "%PYEXE%" (
  echo [ERRO] Python nao encontrado em "%PYEXE%".
  echo Feche esta janela, abra de novo e rode SETUP.bat novamente.
  pause & exit /b 1
)
echo   Python OK
if not exist "%NPMCMD%" (
  echo [ERRO] Node.js nao encontrado em "%NPMCMD%".
  echo A instalacao do Node falhou ^(UAC negado?^). Rode o SETUP.bat de novo.
  pause & exit /b 1
)
echo   Node OK
if not defined MYSQLBIN goto :mysql_missing
if not exist "%MYSQLBIN%\mysqld.exe" goto :mysql_missing
echo   MySQL OK em "%MYSQLBIN%"
goto :mysql_ok
:mysql_missing
echo [ERRO] MySQL nao encontrado em "C:\Program Files\MySQL\".
echo A instalacao do MySQL falhou ^(UAC negado?^). Rode o SETUP.bat de novo.
pause & exit /b 1
:mysql_ok

REM ----------------------------------------------------------------
REM 4) Inicializar e subir o MySQL, e esperar ele aceitar conexao
REM ----------------------------------------------------------------
echo.
echo [4/8] Preparando o MySQL...
if not exist "%MYSQLDATA%" (
  echo     Inicializando banco de dados ^(primeira vez^)...
  "%MYSQLBIN%\mysqld.exe" --initialize-insecure --datadir="%MYSQLDATA%"
)
netstat -ano -p TCP | find ":3306 " | find "LISTENING" >nul
if errorlevel 1 (
  start "MySQL" /min "%MYSQLBIN%\mysqld.exe" --datadir="%MYSQLDATA%" --port=3306
)
echo     Aguardando o MySQL aceitar conexao...
set "TRIES=0"
:waitmysql
"%MYSQLBIN%\mysqladmin.exe" ping --host=127.0.0.1 --port=3306 --silent >nul 2>&1
if not errorlevel 1 goto mysqlup
set /a TRIES+=1
if !TRIES! geq 40 (
  echo [ERRO] MySQL nao respondeu a tempo. Verifique a janela "MySQL".
  pause & exit /b 1
)
timeout /t 1 /nobreak >nul
goto waitmysql
:mysqlup
echo     MySQL pronto.

REM ----------------------------------------------------------------
REM 5) Criar senha root, usuario root@%% (p/ as views do dump) e o banco
REM ----------------------------------------------------------------
echo [5/8] Configurando usuario root e banco rrvm_laudonr13...
REM Tenta sem senha (1a vez). Se ja tiver senha (re-execucao), tenta com 1234.
"%MYSQLBIN%\mysql.exe" -u root --host=127.0.0.1 -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '1234'; CREATE USER IF NOT EXISTS 'root'@'%%' IDENTIFIED BY '1234'; GRANT ALL PRIVILEGES ON *.* TO 'root'@'%%' WITH GRANT OPTION; CREATE DATABASE IF NOT EXISTS rrvm_laudonr13 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; FLUSH PRIVILEGES;" 2>nul
if errorlevel 1 (
  "%MYSQLBIN%\mysql.exe" -u root -p1234 --host=127.0.0.1 -e "CREATE USER IF NOT EXISTS 'root'@'%%' IDENTIFIED BY '1234'; GRANT ALL PRIVILEGES ON *.* TO 'root'@'%%' WITH GRANT OPTION; CREATE DATABASE IF NOT EXISTS rrvm_laudonr13 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; FLUSH PRIVILEGES;"
)

REM ----------------------------------------------------------------
REM 6) Importar o dump de producao (se estiver presente)
REM ----------------------------------------------------------------
echo [6/8] Importando dados (banco_atual.sql)...
if exist "%PROJ%backend\migrations\banco_atual.sql" (
  "%MYSQLBIN%\mysql.exe" -u root -p1234 --host=127.0.0.1 rrvm_laudonr13 < "%PROJ%backend\migrations\banco_atual.sql"
  echo     Dados importados.
) else (
  echo     [AVISO] backend\migrations\banco_atual.sql NAO encontrado.
  echo     Copie o dump para essa pasta e rode o SETUP de novo, ou crie um
  echo     banco vazio depois via POST http://localhost:8000/api/v1/init-db
)

REM ----------------------------------------------------------------
REM 7) Criar .env, venv e instalar dependencias do backend
REM ----------------------------------------------------------------
echo [7/8] Criando .env e instalando dependencias do backend...
"%PYEXE%" -c "import secrets;print(secrets.token_urlsafe(48))" > "%TEMP%\ser_secret.txt"
set "SECRET="
set /p SECRET=<"%TEMP%\ser_secret.txt"
del "%TEMP%\ser_secret.txt" >nul 2>&1
if "!SECRET!"=="" set "SECRET=troque-esta-chave-insegura-gerada-como-fallback"
(
  echo # Gerado pelo SETUP.bat - ambiente LOCAL
  echo DATABASE_URL=mysql+pymysql://root:1234@localhost/rrvm_laudonr13
  echo SECRET_KEY=!SECRET!
  echo ALGORITHM=HS256
  echo ACCESS_TOKEN_EXPIRE_MINUTES=480
  echo REFRESH_TOKEN_EXPIRE_DAYS=7
  echo PASSWORD_RESET_TOKEN_EXPIRE_HOURS=1
  echo CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
  echo APP_NAME=SER - Sistema de Emissao de Relatorios
  echo APP_VERSION=1.0.0
  echo ENVIRONMENT=development
  echo DEBUG=True
  echo PORT=8000
  echo EXPORT_ENGINE=
  echo FRONTEND_URL=http://localhost:5173
) > "%PROJ%backend\.env"

"%PYEXE%" -m venv "%PROJ%backend\venv"
"%PROJ%backend\venv\Scripts\python.exe" -m pip install --upgrade pip
"%PROJ%backend\venv\Scripts\python.exe" -m pip install -r "%PROJ%backend\requirements.txt"
"%PROJ%backend\venv\Scripts\python.exe" -m pip install -r "%PROJ%backend\requirements-windows.txt"

REM Resetar senha do admin para Admin@123 (a senha de producao e desconhecida)
set "PYTHONUTF8=1"
pushd "%PROJ%backend"
venv\Scripts\python.exe scripts\reset_user_password.py admin "Admin@123"
popd

REM ----------------------------------------------------------------
REM 8) Instalar dependencias do frontend
REM ----------------------------------------------------------------
echo [8/8] Instalando dependencias do frontend (pode demorar)...
pushd "%PROJ%frontend"
call "%NPMCMD%" install
popd

echo.
echo ============================================================
echo  SETUP CONCLUIDO!
echo  Agora use o INICIAR.bat para abrir o sistema.
echo  Login: admin   Senha: Admin@123
echo ============================================================
pause
endlocal
