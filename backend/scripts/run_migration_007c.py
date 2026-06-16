"""
Migration 007c: Alterar campo excel_template para MEDIUMTEXT ou VARCHAR(16777215)
Data: 2025-11-15 23:35:00
Motivo: Template atual tem 1.2MB, precisa de mais que TEXT (65KB)
Executar via: python scripts/run_migration_007c.py (no container do Railway)
"""

import os
import pymysql
from urllib.parse import urlparse

# Obter DATABASE_URL do ambiente
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERRO: DATABASE_URL nao definida")
    exit(1)

# Parsear URL
parsed = urlparse(database_url.replace("mysql+pymysql://", "mysql://"))
db_config = {
    "host": parsed.hostname,
    "port": parsed.port or 3306,
    "user": parsed.username,
    "password": parsed.password,
    "database": parsed.path.lstrip("/").split("?")[0],
}

def run_migration():
    """Executa migration 007c"""

    print("=" * 80)
    print("MIGRATION 007c: Alterar excel_template para suportar 16MB")
    print("=" * 80)
    print(f"\nConectando em: {db_config['host']}:{db_config['port']}/{db_config['database']}")

    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        print("\n1. Verificando tamanho atual...")
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
            print(f"   Tipo atual: {row[1]}")
            print(f"   Tamanho atual: {row[2]} bytes")

        print("\n2. Verificando tamanho do maior template existente...")
        cursor.execute("SELECT MAX(LENGTH(excel_template)) as max_size FROM formularios")
        max_size = cursor.fetchone()[0] or 0
        if max_size > 0:
            print(f"   Maior template: {max_size} bytes (~{max_size//1024}KB ~{max_size//1024//1024}MB)")
        else:
            print("   Nenhum template armazenado ainda")

        print("\n3. Tentando usar MEDIUMTEXT (16MB)...")
        try:
            cursor.execute("""
                ALTER TABLE formularios
                MODIFY COLUMN excel_template MEDIUMTEXT NULL
                COMMENT 'Template Excel em base64 (MEDIUMTEXT 16MB)'
            """)
            conn.commit()
            print("   OK - Alterado para MEDIUMTEXT com sucesso!")
        except Exception as e:
            print(f"   MEDIUMTEXT nao suportado: {e}")
            print("\n4. Usando VARCHAR(16777215) como alternativa...")
            cursor.execute("""
                ALTER TABLE formularios
                MODIFY COLUMN excel_template VARCHAR(16777215) NULL
                COMMENT 'Template Excel em base64 (VARCHAR max 16MB)'
            """)
            conn.commit()
            print("   OK - Alterado para VARCHAR(16777215) com sucesso!")

        print("\n5. Verificando resultado final...")
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = 'formularios'
              AND COLUMN_NAME = 'excel_template'
        """, (db_config['database'],))

        row = cursor.fetchone()
        if row:
            print(f"   Tipo final: {row[1]}")
            print(f"   Tamanho maximo: {row[2]} bytes (~{row[2]//1024//1024}MB)")

        print("\n" + "=" * 80)
        print("OK - MIGRATION 007c CONCLUIDA!")
        print("=" * 80)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\nERRO: {e}")
        raise

if __name__ == "__main__":
    run_migration()
