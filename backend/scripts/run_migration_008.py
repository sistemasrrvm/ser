"""
Migration 008: Renomear tabela listas_lookup para listas
Data: 2025-11-16 13:29:22
Executar via: python scripts/run_migration_008.py (no container do Railway)
"""

import os
import pymysql
from urllib.parse import urlparse
from pathlib import Path

# Carregar .env se existir (desenvolvimento local)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

# Obter DATABASE_URL do ambiente
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("[ERRO] DATABASE_URL nao definida")
    exit(1)

# Parsear URL: mysql+pymysql://user:pass@host:port/database
parsed = urlparse(database_url.replace("mysql+pymysql://", "mysql://"))
db_config = {
    "host": parsed.hostname,
    "port": parsed.port or 3306,
    "user": parsed.username,
    "password": parsed.password,
    "database": parsed.path.lstrip("/").split("?")[0],
}

def run_migration():
    """Executa migration 008"""

    print("=" * 80)
    print("MIGRATION 008: Renomear tabela listas_lookup para listas")
    print("=" * 80)
    print(f"\nConectando em: {db_config['host']}:{db_config['port']}/{db_config['database']}")

    try:
        # Conectar ao MySQL
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        print("\n1. Verificando se tabela 'listas_lookup' existe...")
        cursor.execute("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = 'listas_lookup'
        """, (db_config['database'],))

        exists_old = cursor.fetchone()[0] > 0

        if not exists_old:
            print("   [AVISO] Tabela 'listas_lookup' nao encontrada!")
            print("   Verificando se tabela 'listas' ja existe...")

            cursor.execute("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = 'listas'
            """, (db_config['database'],))

            exists_new = cursor.fetchone()[0] > 0

            if exists_new:
                print("   [OK] Tabela 'listas' ja existe - Migration ja foi executada anteriormente!")
                return
            else:
                print("   [ERRO] Nenhuma das tabelas encontrada - Migration nao pode ser executada!")
                return

        print("   [OK] Tabela 'listas_lookup' encontrada")

        print("\n2. Verificando se tabela 'listas' já existe...")
        cursor.execute("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = 'listas'
        """, (db_config['database'],))

        exists_new = cursor.fetchone()[0] > 0

        if exists_new:
            print("   [ERRO] Tabela 'listas' ja existe - Nao e possivel renomear!")
            print("   ATENCAO: Conflito de nomes. Verifique manualmente.")
            return

        print("   [OK] Tabela 'listas' nao existe - pode prosseguir")

        print("\n3. Renomeando tabela de 'listas_lookup' para 'listas'...")
        cursor.execute("RENAME TABLE listas_lookup TO listas")

        conn.commit()
        print("   [OK] Tabela renomeada com sucesso!")

        print("\n4. Verificando apos renomeacao...")
        cursor.execute("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = 'listas'
        """, (db_config['database'],))

        if cursor.fetchone()[0] > 0:
            print("   [OK] Tabela 'listas' confirmada")

        cursor.execute("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = 'listas_lookup'
        """, (db_config['database'],))

        if cursor.fetchone()[0] == 0:
            print("   [OK] Tabela 'listas_lookup' nao existe mais")

        print("\n" + "=" * 80)
        print("[SUCESSO] MIGRATION 008 CONCLUIDA COM SUCESSO!")
        print("=" * 80)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n[ERRO] ERRO AO EXECUTAR MIGRATION: {e}")
        raise

if __name__ == "__main__":
    run_migration()
