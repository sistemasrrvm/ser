"""
Transferência SQL Server -> MySQL (tab_clientes + tab_equipamentos)

Uso mais fácil (Windows):

  1. copy scripts\run_transfer.bat.example scripts\run_transfer.bat
  2. Edite run_transfer.bat (senhas no topo do arquivo)
  3. Duplo-clique em run_transfer.bat

Uso manual (PowerShell, na pasta backend):

  pip install pymssql pymysql python-dotenv

  $env:MSSQL_SERVER = "sql7001.site4now.net"
  $env:MSSQL_DATABASE = "DB_A2CB65_rrvm"
  $env:MSSQL_USER = "DB_A2CB65_rrvm_admin"
  $env:MSSQL_PASSWORD = "sua_senha"

  # URL do Railway TCP Proxy (Connect > Public Network):
  $env:MYSQL_DATABASE_URL = "mysql://root:senha@xxxx.proxy.rlwy.net:PORTA/railway"

  python scripts/transfer_sqlserver_to_mysql.py
  python scripts/transfer_sqlserver_to_mysql.py --dry-run
  python scripts/transfer_sqlserver_to_mysql.py --only equipamentos

Ou use DATABASE_URL do Railway no .env (host público, não o .internal):

  DATABASE_URL=mysql://root:senha@mysql-production-9fd6.up.railway.app:3306/railway
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import pymssql
    import pymysql
except ImportError:
    print("Instale dependências: pip install pymssql pymysql python-dotenv")
    sys.exit(1)

try:
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Queries de origem (SQL Server)
# ---------------------------------------------------------------------------

SQL_CLIENTES = """
SELECT
    CLI_ID,
    CLI_NOME,
    CLI_CNPJ
FROM dbo.MANUT_CLIENTE
ORDER BY CLI_ID
"""

SQL_EQUIPAMENTOS = """
SELECT
    EQP_ID,
    EQP_TAG,
    EQP_NOME,
    EQP_CLI_ID,
    EQP_TEQP_ID
FROM dbo.MANUT_EQUIPAMENTO
WHERE EQP_TEQP_ID = 12
ORDER BY EQP_ID
"""


def normalize_mysql_url(url: str) -> str:
    """Aceita mysql:// ou mysql+pymysql:// (formato SQLAlchemy / Railway)."""
    url = url.strip()
    for prefix in ("mysql+pymysql://", "mysql+ pymysql://"):
        if url.startswith(prefix):
            return "mysql://" + url[len(prefix) :]
    return url


def parse_database_url(url: str) -> dict[str, Any]:
    parsed = urlparse(normalize_mysql_url(url))
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": (parsed.path or "/").lstrip("/") or "railway",
    }


def get_mssql_conn(args: argparse.Namespace):
    server = args.mssql_server or os.getenv("MSSQL_SERVER")
    database = args.mssql_database or os.getenv("MSSQL_DATABASE")
    user = args.mssql_user or os.getenv("MSSQL_USER")
    password = args.mssql_password or os.getenv("MSSQL_PASSWORD")

    missing = [k for k, v in {
        "MSSQL_SERVER": server,
        "MSSQL_DATABASE": database,
        "MSSQL_USER": user,
        "MSSQL_PASSWORD": password,
    }.items() if not v]
    if missing:
        raise SystemExit(f"SQL Server: defina {', '.join(missing)}")

    return pymssql.connect(
        server=server,
        user=user,
        password=password,
        database=database,
        login_timeout=30,
        timeout=120,
    )


def get_mysql_conn(args: argparse.Namespace) -> tuple[Any, dict[str, Any]]:
    """
    Prioridade de conexão:
      1) --database-url (CLI)
      2) MYSQL_DATABASE_URL (run_transfer.bat — URL completa do Railway TCP Proxy)
      3) MYSQL_HOST + MYSQL_PORT (host *.proxy.rlwy.net — NÃO use *.railway.app:3306)
      4) DATABASE_URL (backend/.env)
    """
    source = ""
    host = port = user = password = database = None

    if args.database_url:
        cfg = parse_database_url(args.database_url)
        host, port = cfg["host"], cfg["port"]
        user, password, database = cfg["user"], cfg["password"], cfg["database"]
        source = "argumento --database-url"
    elif os.getenv("MYSQL_DATABASE_URL"):
        cfg = parse_database_url(os.getenv("MYSQL_DATABASE_URL", ""))
        host, port = cfg["host"], cfg["port"]
        user, password, database = cfg["user"], cfg["password"], cfg["database"]
        source = "MYSQL_DATABASE_URL (run_transfer.bat)"
    elif args.mysql_host or os.getenv("MYSQL_HOST"):
        host = args.mysql_host or os.getenv("MYSQL_HOST")
        port = int(args.mysql_port or os.getenv("MYSQL_PORT", "3306"))
        user = args.mysql_user or os.getenv("MYSQL_USER")
        password = args.mysql_password or os.getenv("MYSQL_PASSWORD")
        database = args.mysql_database or os.getenv("MYSQL_DATABASE", "railway")
        source = "variáveis MYSQL_HOST/PORT (run_transfer.bat)"
        if host and host.endswith(".railway.app"):
            log(
                "  AVISO: host *.railway.app geralmente NÃO aceita MySQL na porta 3306.\n"
                "  No Railway: MySQL → Connect → Public Network → copie host *.proxy.rlwy.net e a porta."
            )
    elif os.getenv("DATABASE_URL"):
        cfg = parse_database_url(os.getenv("DATABASE_URL", ""))
        host, port = cfg["host"], cfg["port"]
        user, password, database = cfg["user"], cfg["password"], cfg["database"]
        source = "DATABASE_URL (backend/.env)"

    missing = [k for k, v in {
        "MYSQL_HOST": host,
        "MYSQL_USER": user,
        "MYSQL_PASSWORD": password,
    }.items() if not v]
    if missing:
        raise SystemExit(f"MySQL: defina {', '.join(missing)} (ou DATABASE_URL)")

    info = {
        "host": host,
        "port": port,
        "user": user,
        "database": database,
        "source": source,
    }

    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        autocommit=False,
        connect_timeout=30,
        read_timeout=120,
        write_timeout=120,
    )
    return conn, info


BATCH_SIZE = 100


def log(msg: str) -> None:
    """Log imediato no console (flush para ver progresso em tempo real)."""
    print(msg, flush=True)


def mysql_count(mysql, table: str) -> int:
    cur = mysql.cursor()
    cur.execute(f"SELECT COUNT(*) FROM `{table}`")
    row = cur.fetchone()
    return int(row[0]) if row else 0


def log_mysql_destino(mysql, mysql_info: dict[str, Any], *, momento: str) -> None:
    """Exibe banco conectado e COUNT nas tabelas de destino."""
    cur = mysql.cursor()
    cur.execute("SELECT DATABASE()")
    db_atual = cur.fetchone()[0]

    log(f"\n  [verificação — {momento}]")
    log(f"  Conexão : {mysql_info['user']}@{mysql_info['host']}:{mysql_info['port']}")
    log(f"  Fonte   : {mysql_info['source']}")
    log(f"  DATABASE(): {db_atual}")

    for tabela in ("tab_clientes", "tab_equipamentos"):
        try:
            n = mysql_count(mysql, tabela)
            log(f"  COUNT({tabela}) = {n}")
        except Exception as e:
            log(f"  COUNT({tabela}) = ERRO ({e})")

    try:
        cur.execute(
            "SELECT CLI_ID, CLI_NOME FROM tab_clientes ORDER BY CLI_ID LIMIT 3"
        )
        amostra = cur.fetchall()
        if amostra:
            log("  Amostra tab_clientes (até 3):")
            for row in amostra:
                log(f"    CLI_ID={row[0]} | {row[1]}")
    except Exception:
        pass


def insert_in_batches(
    mysql,
    sql: str,
    batch: list,
    *,
    label: str,
    dry_run: bool,
    batch_size: int = BATCH_SIZE,
) -> int:
    """Insere registros em lotes de `batch_size` com log no console."""
    total = len(batch)
    if total == 0:
        log(f"  [{label}] Nenhum registro para inserir.")
        return 0

    total_lotes = (total + batch_size - 1) // batch_size

    if dry_run:
        log(f"  [{label}] [dry-run] Simularia {total} registros em {total_lotes} lote(s) de {batch_size}")
        for i in range(0, total, batch_size):
            lote_num = i // batch_size + 1
            fim = min(i + batch_size, total)
            log(f"  [{label}] [dry-run] Lote {lote_num}/{total_lotes}: registros {i + 1}-{fim}")
        return total

    cur = mysql.cursor()
    inseridos = 0

    for i in range(0, total, batch_size):
        lote_num = i // batch_size + 1
        chunk = batch[i : i + batch_size]
        inicio = i + 1
        fim = i + len(chunk)

        log(f"  [{label}] Lote {lote_num}/{total_lotes}: inserindo registros {inicio}-{fim} de {total}...")

        cur.executemany(sql, chunk)
        mysql.commit()
        inseridos += len(chunk)

        log(f"  [{label}] Lote {lote_num}/{total_lotes}: OK — {len(chunk)} registros gravados (total acumulado: {inseridos}/{total})")

    log(f"  [{label}] Concluído: {inseridos} registros enviados ao MySQL.")
    return inseridos


def clean_str(value: Any, max_len: int | None = None) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if max_len:
        return s[:max_len]
    return s


def transfer_clientes(mssql, mysql, dry_run: bool, batch_size: int) -> int:
    log("\n--- Clientes (MANUT_CLIENTE -> tab_clientes) ---")
    count_antes = mysql_count(mysql, "tab_clientes")
    log(f"  Destino ANTES: {count_antes} registros em tab_clientes")

    log("  Lendo origem (SQL Server)...")
    cur_src = mssql.cursor()
    cur_src.execute(SQL_CLIENTES)
    rows = cur_src.fetchall()
    log(f"  Origem: {len(rows)} registros lidos")

    sql = """
        INSERT INTO tab_clientes (CLI_ID, CLI_NOME, CLI_CNPJ)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            CLI_NOME = VALUES(CLI_NOME),
            CLI_CNPJ = VALUES(CLI_CNPJ)
    """
    batch = [
        (
            int(r[0]),
            clean_str(r[1], 200),
            clean_str(r[2], 14),
        )
        for r in rows
    ]

    n = insert_in_batches(
        mysql, sql, batch, label="clientes", dry_run=dry_run, batch_size=batch_size
    )

    if not dry_run:
        count_depois = mysql_count(mysql, "tab_clientes")
        delta = count_depois - count_antes
        log(f"  Destino DEPOIS: {count_depois} registros em tab_clientes (Δ +{delta})")
        if n > 0 and count_depois == 0:
            log("  *** ALERTA: processou registros mas a tabela continua vazia!")
            log("  *** Verifique se o host/banco do .bat é o mesmo que você consulta no Workbench.")
        elif n > 0 and delta == 0 and count_antes == count_depois:
            log("  *** ALERTA: COUNT não aumentou. Pode ser UPDATE em PKs existentes ou banco errado.")

    return n


def transfer_equipamentos(mssql, mysql, dry_run: bool, batch_size: int) -> int:
    log("\n--- Equipamentos (MANUT_EQUIPAMENTO -> tab_equipamentos, TEQP=12) ---")
    count_antes = mysql_count(mysql, "tab_equipamentos")
    log(f"  Destino ANTES: {count_antes} registros em tab_equipamentos")

    log("  Lendo origem (SQL Server)...")
    cur_src = mssql.cursor()
    cur_src.execute(SQL_EQUIPAMENTOS)
    rows = cur_src.fetchall()
    log(f"  Origem: {len(rows)} registros lidos")

    # EQP_TAG é NOT NULL no MySQL
    sql = """
        INSERT INTO tab_equipamentos (EQP_ID, EQP_TAG, EQP_NOME, EQP_CLI_ID, EQP_TEQP_ID)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            EQP_TAG = VALUES(EQP_TAG),
            EQP_NOME = VALUES(EQP_NOME),
            EQP_CLI_ID = VALUES(EQP_CLI_ID),
            EQP_TEQP_ID = VALUES(EQP_TEQP_ID)
    """
    batch = []
    skipped = 0
    for r in rows:
        tag = clean_str(r[1], 200)
        if not tag:
            skipped += 1
            continue
        batch.append(
            (
                int(r[0]),
                tag,
                clean_str(r[2], 200),
                int(r[3]),
                int(r[4]) if r[4] is not None else 12,
            )
        )

    if skipped:
        log(f"  Aviso: {skipped} equipamentos sem EQP_TAG ignorados")

    n = insert_in_batches(
        mysql, sql, batch, label="equipamentos", dry_run=dry_run, batch_size=batch_size
    )

    if not dry_run:
        count_depois = mysql_count(mysql, "tab_equipamentos")
        delta = count_depois - count_antes
        log(f"  Destino DEPOIS: {count_depois} registros em tab_equipamentos (Δ +{delta})")
        if n > 0 and count_depois == 0:
            log("  *** ALERTA: processou registros mas a tabela continua vazia!")

    return n


def main():
    parser = argparse.ArgumentParser(description="Transferir clientes/equipamentos SQL Server -> MySQL")
    parser.add_argument("--dry-run", action="store_true", help="Só mostra contagens, não grava")
    parser.add_argument(
        "--only",
        choices=["clientes", "equipamentos", "all"],
        default="all",
        help="O que transferir (padrão: all)",
    )
    parser.add_argument("--mssql-server", help="SQL Server host")
    parser.add_argument("--mssql-database", help="SQL Server database")
    parser.add_argument("--mssql-user", help="SQL Server user")
    parser.add_argument("--mssql-password", help="SQL Server password")
    parser.add_argument("--mysql-host", help="MySQL host (use host público do Railway)")
    parser.add_argument("--mysql-port", type=int, default=None)
    parser.add_argument("--mysql-user", help="MySQL user")
    parser.add_argument("--mysql-password", help="MySQL password")
    parser.add_argument("--mysql-database", default=None)
    parser.add_argument("--database-url", help="mysql://user:pass@host:port/db")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Registros por lote (padrão: {BATCH_SIZE})",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Só conecta e exibe COUNT no destino (não transfere)",
    )
    args = parser.parse_args()

    batch_size = max(1, args.batch_size)

    log("=" * 70)
    log("Transferência SQL Server -> MySQL")
    log("=" * 70)
    log(f"Lotes de {batch_size} registros com commit após cada lote")
    if args.dry_run:
        log("Modo: DRY-RUN (nenhuma alteração no MySQL)")

    log("\nConectando ao SQL Server...")
    mssql = get_mssql_conn(args)
    log("Conectado ao SQL Server.")

    log("Conectando ao MySQL...")
    try:
        mysql, mysql_info = get_mysql_conn(args)
    except Exception as e:
        log(f"\n[ERRO] Falha ao conectar no MySQL: {e}")
        log(
            "\nDica Railway (conexão do seu PC):\n"
            "  1. Painel Railway → serviço MySQL → aba Connect\n"
            "  2. Ative 'Public Network' / TCP Proxy\n"
            "  3. Copie a URL (host tipo xxxxx.proxy.rlwy.net e porta tipo 12345)\n"
            "  4. Cole em run_transfer.bat em MYSQL_DATABASE_URL=\n"
            "     Exemplo: mysql://root:SENHA@roundhouse.proxy.rlwy.net:19259/railway\n"
            "\nAlternativa: na pasta backend, com Railway CLI linkado:\n"
            "  railway run python scripts/transfer_sqlserver_to_mysql.py --verify-only\n"
        )
        raise
    log(f"Conectado ao MySQL ({mysql_info['host']}:{mysql_info['port']} / {mysql_info['database']}).")
    log(f"  Fonte da conexão: {mysql_info['source']}")

    try:
        if args.verify_only:
            log_mysql_destino(mysql, mysql_info, momento="verificação")
            log("\nModo --verify-only: nenhuma transferência executada.")
            return

        log_mysql_destino(mysql, mysql_info, momento="ANTES da transferência")

        total = 0
        if args.only in ("clientes", "all"):
            total += transfer_clientes(mssql, mysql, args.dry_run, batch_size)
        if args.only in ("equipamentos", "all"):
            total += transfer_equipamentos(mssql, mysql, args.dry_run, batch_size)

        if not args.dry_run:
            log_mysql_destino(mysql, mysql_info, momento="DEPOIS da transferência")

        log("\n" + "=" * 70)
        log(f"Concluído. Registros processados: {total}")
        log("=" * 70)
    finally:
        mssql.close()
        mysql.close()


if __name__ == "__main__":
    main()
