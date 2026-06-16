"""
Script para executar Migration 010 - Renomear tabelas NR13
Renomeia cache_sqlserver_* para tab_*
"""

import pymysql
import sys
import os

# Adicionar diretório src ao Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Extrair credenciais da DATABASE_URL
database_url = os.getenv("DATABASE_URL")
# mysql+pymysql://root:1234@localhost/db_a2cb65_laudonr

if not database_url:
    print("[ERRO] DATABASE_URL nao encontrada no .env")
    sys.exit(1)

# Parse DATABASE_URL
# Formato: mysql+pymysql://user:password@host/database
try:
    parts = database_url.replace("mysql+pymysql://", "").split("@")
    user_pass = parts[0].split(":")
    host_db = parts[1].split("/")

    db_user = user_pass[0]
    db_password = user_pass[1]
    db_host = host_db[0]
    db_name = host_db[1]

    print(f"[INFO] Conectando ao MySQL...")
    print(f"   Host: {db_host}")
    print(f"   Database: {db_name}")
    print(f"   User: {db_user}")

except Exception as e:
    print(f"[ERRO] Erro ao parsear DATABASE_URL: {e}")
    sys.exit(1)

try:
    # Conectar ao MySQL
    connection = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    print("[OK] Conexao estabelecida com sucesso!\n")

    with connection.cursor() as cursor:
        print("=" * 80)
        print("MIGRATION 010: Renomear tabelas NR13")
        print("=" * 80)

        # Verificar se tabelas antigas existem
        print("\n[INFO] Verificando tabelas existentes...")
        cursor.execute("SHOW TABLES LIKE 'cache_sqlserver_%'")
        old_tables = cursor.fetchall()

        if not old_tables:
            print("[AVISO] Tabelas antigas (cache_sqlserver_*) nao encontradas.")
            print("   Verificando se ja foram renomeadas...")

            cursor.execute("SHOW TABLES LIKE 'tab_%'")
            new_tables = cursor.fetchall()

            if new_tables:
                print("[OK] Tabelas novas (tab_*) ja existem. Migracao ja foi executada!")
                for table in new_tables:
                    print(f"   - {list(table.values())[0]}")
                connection.close()
                sys.exit(0)
            else:
                print("[ERRO] Nenhuma tabela encontrada!")
                connection.close()
                sys.exit(1)

        print(f"   Encontradas {len(old_tables)} tabelas antigas:")
        for table in old_tables:
            print(f"   - {list(table.values())[0]}")

        # Renomear tabelas
        print("\n[INFO] Renomeando tabelas...")

        renames = [
            ("cache_sqlserver_clientes", "tab_clientes"),
            ("cache_sqlserver_tipos_equipamento", "tab_tipos_equipamento"),
            ("cache_sqlserver_equipamentos", "tab_equipamentos")
        ]

        for old_name, new_name in renames:
            print(f"\n   {old_name} -> {new_name}")
            cursor.execute(f"RENAME TABLE {old_name} TO {new_name}")
            print(f"   [OK] Renomeada!")

        # Commit
        connection.commit()

        # Verificar resultado
        print("\n[INFO] Verificando resultado...")
        cursor.execute("SHOW TABLES LIKE 'tab_%'")
        new_tables = cursor.fetchall()

        print(f"\n[OK] {len(new_tables)} tabelas renomeadas com sucesso:")
        for table in new_tables:
            table_name = list(table.values())[0]
            cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
            count = cursor.fetchone()['total']
            print(f"   - {table_name}: {count} registros")

        print("\n" + "=" * 80)
        print("[OK] MIGRATION 010 CONCLUIDA COM SUCESSO!")
        print("=" * 80)

    connection.close()

except Exception as e:
    print(f"\n[ERRO] ERRO durante a migracao: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
