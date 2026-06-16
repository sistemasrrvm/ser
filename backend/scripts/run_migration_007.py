"""
Migration 007: Alterar campo excel_template para LONGTEXT
Data: 2025-11-15 23:21:36
Executar via: python scripts/run_migration_007.py (no container do Railway)
"""

import os
import pymysql
from urllib.parse import urlparse

# Obter DATABASE_URL do ambiente
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("❌ ERRO: DATABASE_URL não definida")
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
    """Executa migration 007"""

    print("=" * 80)
    print("MIGRATION 007: Alterar excel_template para LONGTEXT")
    print("=" * 80)
    print(f"\nConectando em: {db_config['host']}:{db_config['port']}/{db_config['database']}")

    try:
        # Conectar ao MySQL
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        print("\n1. Verificando tamanho atual do campo excel_template...")
        cursor.execute("""
            SELECT
                COLUMN_NAME,
                COLUMN_TYPE,
                CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = 'formularios'
              AND COLUMN_NAME = 'excel_template'
        """, (db_config['database'],))

        row = cursor.fetchone()
        if row:
            print(f"   Campo atual: {row[0]}")
            print(f"   Tipo: {row[1]}")
            print(f"   Tamanho máximo: {row[2]}")
        else:
            print("   ⚠️ Campo excel_template não encontrado!")
            return

        print("\n2. Alterando campo para LONGTEXT...")
        cursor.execute("""
            ALTER TABLE formularios
            MODIFY COLUMN excel_template LONGTEXT NULL
            COMMENT 'Template Excel em base64 para mesclagem'
        """)

        conn.commit()
        print("   OK - Campo alterado com sucesso!")

        print("\n3. Verificando após alteração...")
        cursor.execute("""
            SELECT
                COLUMN_NAME,
                COLUMN_TYPE,
                CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = 'formularios'
              AND COLUMN_NAME = 'excel_template'
        """, (db_config['database'],))

        row = cursor.fetchone()
        if row:
            print(f"   Campo: {row[0]}")
            print(f"   Tipo: {row[1]}")
            print(f"   Tamanho maximo: {row[2]} (NULL = ilimitado)")

        print("\n" + "=" * 80)
        print("OK - MIGRATION 007 CONCLUIDA COM SUCESSO!")
        print("=" * 80)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\nERRO AO EXECUTAR MIGRATION: {e}")
        raise

if __name__ == "__main__":
    run_migration()
