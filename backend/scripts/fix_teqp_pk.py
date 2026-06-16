"""
Script para corrigir PK de tab_tipos_equipamento
"""

import pymysql
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv("DATABASE_URL")

try:
    parts = database_url.replace("mysql+pymysql://", "").split("@")
    user_pass = parts[0].split(":")
    host_db = parts[1].split("/")

    connection = pymysql.connect(
        host=host_db[0],
        user=user_pass[0],
        password=user_pass[1],
        database=host_db[1],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    with connection.cursor() as cursor:
        # Limpar tabela
        cursor.execute("DELETE FROM tab_tipos_equipamento")
        print("[OK] Tabela limpa")

        # Adicionar PK
        cursor.execute("ALTER TABLE tab_tipos_equipamento ADD PRIMARY KEY (TEQP_ID)")
        print("[OK] Primary key adicionada")

        # Commit
        connection.commit()

        # Verificar
        cursor.execute("SHOW COLUMNS FROM tab_tipos_equipamento")
        columns = cursor.fetchall()
        print("\nColunas:")
        for col in columns:
            key = f" [{col['Key']}]" if col['Key'] else ""
            print(f"  - {col['Field']} ({col['Type']}){key}")

    connection.close()
    print("\n[OK] TEQP_ID configurado como PK!")

except Exception as e:
    print(f"[ERRO] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
