@echo off
REM ============================================================
REM  SER - Sistema de Emissao de Relatorios  -  Iniciar tudo
REM ============================================================
setlocal
set "PROJ=%~dp0"

REM Auto-detecta a pasta do MySQL (qualquer versao instalada)
set "MYSQLD="
for /d %%d in ("C:\Program Files\MySQL\MySQL Server *") do set "MYSQLD=%%d\bin\mysqld.exe"
set "MYSQLDATA=C:\ProgramData\MySQL\SER_Data"

REM Variaveis de ambiente do Python (aspas evitam espaco no fim; janelas filhas herdam)
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
REM Garante o Node no PATH (npm pode nao estar antes de reiniciar o PC)
set "PATH=C:\Program Files\nodejs;%PATH%"

echo ============================================================
echo  Iniciando o SER...
echo ============================================================

if not defined MYSQLD (
    echo [ERRO] MySQL nao encontrado. Rode o SETUP.bat primeiro.
    pause & exit /b 1
)

REM --- 1) MySQL (so sobe se a porta 3306 estiver parada) ---
netstat -ano -p TCP | find ":3306 " | find "LISTENING" >nul
if errorlevel 1 (
    echo [1/3] Subindo MySQL...
    start "MySQL" /min "%MYSQLD%" --datadir="%MYSQLDATA%" --port=3306
    timeout /t 5 /nobreak >nul
) else (
    echo [1/3] MySQL ja esta rodando.
)

REM --- 2) Backend (FastAPI / uvicorn) ---
echo [2/3] Subindo Backend (porta 8000)...
start "SER Backend" /d "%PROJ%backend" cmd /k "venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8000"

REM --- 3) Frontend (Vite) ---
echo [3/3] Subindo Frontend (porta 5173)...
start "SER Frontend" /d "%PROJ%frontend" cmd /k "npm run dev"

REM --- Abrir navegador apos alguns segundos ---
timeout /t 8 /nobreak >nul
start "" http://localhost:5173

echo.
echo ============================================================
echo  Pronto! Acesse:  http://localhost:5173
echo  Login: admin   Senha: Admin@123
echo  (Feche as janelas "SER Backend" e "SER Frontend" para parar)
echo ============================================================
endlocal
