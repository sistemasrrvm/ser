import pymysql
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

database_url = os.getenv("DATABASE_URL")
_, connection_string = database_url.split("://")
user_pass, host_db = connection_string.split("@")
user, password = user_pass.split(":")
host, database = host_db.split("/")

connection = pymysql.connect(
    host=host,
    user=user,
    password=password,
    database=database,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

print("🔍 FOREIGN KEYS em form_fields:")
print("=" * 70)

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT
            CONSTRAINT_NAME,
            TABLE_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s
          AND TABLE_NAME IN ('form_fields', 'formularios_campos', 'form_pages', 'formularios_paginas')
          AND REFERENCED_TABLE_NAME IS NOT NULL
    """, (database,))

    fks = cursor.fetchall()
    for fk in fks:
        print(f"  Tabela: {fk['TABLE_NAME']}")
        print(f"  Constraint: {fk['CONSTRAINT_NAME']}")
        print(f"  Coluna: {fk['COLUMN_NAME']} → {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}")
        print("-" * 70)

connection.close()
