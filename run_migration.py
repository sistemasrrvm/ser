"""
Script para executar migration SQL no banco de dados
"""

import pymysql
from pathlib import Path

# Conexão com banco
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='1234',
    database='db_a2cb65_laudonr',
    charset='utf8mb4'
)

try:
    # Ler arquivo SQL
    sql_file = Path('backend/migrations/002_create_form_pages_tables.sql')
    sql_content = sql_file.read_text(encoding='utf-8')

    # Executar SQL
    with connection.cursor() as cursor:
        # Separar statements por ';'
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

        for statement in statements:
            print(f"Executando: {statement[:100]}...")
            cursor.execute(statement)

    connection.commit()
    print("\n[OK] Migration executada com sucesso!")
    print("Tabelas criadas:")
    print("  - form_pages")
    print("  - form_fields")

except Exception as e:
    print(f"\n[ERRO] Erro ao executar migration: {e}")
    connection.rollback()

finally:
    connection.close()
