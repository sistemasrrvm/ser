"""
Script para executar migration 006: Renomear tabelas para português (MySQL)
"""

import pymysql
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Carregar variáveis de ambiente
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Obter DATABASE_URL
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("❌ DATABASE_URL não encontrada no .env")
    sys.exit(1)

# Parse DATABASE_URL: mysql+pymysql://root:1234@localhost/db_a2cb65_laudonr
# Formato: mysql+pymysql://user:password@host/database
try:
    _, connection_string = database_url.split("://")
    user_pass, host_db = connection_string.split("@")
    user, password = user_pass.split(":")
    host, database = host_db.split("/")
except Exception as e:
    print(f"❌ Erro ao parsear DATABASE_URL: {e}")
    print(f"DATABASE_URL: {database_url}")
    sys.exit(1)

MIGRATION_PATH = Path(__file__).parent.parent / "migrations" / "migration_006_rename_tables_pt_mysql.sql"

def run_migration():
    """Executa a migration 006 no MySQL"""

    print("=" * 70)
    print("🔄 MIGRATION 006: Renomear tabelas e campos para português (MySQL)")
    print("=" * 70)

    if not MIGRATION_PATH.exists():
        print(f"❌ Arquivo de migration não encontrado: {MIGRATION_PATH}")
        return False

    try:
        # Conectar ao MySQL
        print(f"\n📡 Conectando ao MySQL: {user}@{host}/{database}")
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        print("✅ Conexão estabelecida")

        # Ler SQL da migration
        with open(MIGRATION_PATH, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Habilitar autocommit para DDL
        connection.autocommit(True)

        # Executar migration
        print("\n📝 Executando migration...")

        with connection.cursor() as cursor:
            # Executar cada statement separadamente
            raw_statements = migration_sql.split(';')
            statements = []

            for s in raw_statements:
                s = s.strip()
                # Remover comentários de linha
                lines = [line for line in s.split('\n') if line.strip() and not line.strip().startswith('--')]
                cleaned = '\n'.join(lines).strip()

                if cleaned:
                    statements.append(cleaned)

            print(f"\nTotal de statements a executar: {len(statements)}\n")

            for i, statement in enumerate(statements, 1):
                # Pular SELECTs de verificação
                if statement.upper().startswith('SELECT'):
                    continue

                try:
                    # Mostrar qual tabela/comando está sendo executado
                    if 'RENAME' in statement.upper():
                        print(f"  [{i}] 🔄 Renomeando tabela...")
                    elif 'ALTER' in statement.upper():
                        print(f"  [{i}] ⚙️  Renomeando colunas...")
                    else:
                        print(f"  [{i}] Executando...")

                    print(f"      SQL: {statement[:80]}...")
                    cursor.execute(statement)
                    print(f"      ✅ Sucesso\n")
                except Exception as e:
                    print(f"      ❌ Erro: {e}\n")
                    raise

        print("\n✅ Migration executada com sucesso!")

        # Verificar resultados
        print("\n📊 Verificando tabelas...")

        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'formularios_%'")
            tables = cursor.fetchall()
            print("\nTabelas encontradas:")
            for table in tables:
                table_name = list(table.values())[0]
                print(f"  ✓ {table_name}")

            cursor.execute("SELECT COUNT(*) as total FROM formularios_paginas")
            paginas_count = cursor.fetchone()['total']
            print(f"\n📄 Total de páginas: {paginas_count}")

            cursor.execute("SELECT COUNT(*) as total FROM formularios_campos")
            campos_count = cursor.fetchone()['total']
            print(f"📋 Total de campos: {campos_count}")

        print("\n" + "=" * 70)
        print("✅ MIGRATION 006 CONCLUÍDA COM SUCESSO!")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ Erro ao executar migration: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if 'connection' in locals():
            connection.close()
            print("\n🔌 Conexão fechada")

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
