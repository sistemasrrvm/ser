"""
Script para adicionar primary keys nas tabelas NR13
"""

import pymysql
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("[ERRO] DATABASE_URL nao encontrada")
    sys.exit(1)

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

    print("[INFO] Conectado ao MySQL\n")

    with connection.cursor() as cursor:
        print("=" * 80)
        print("ADICIONANDO PRIMARY KEYS")
        print("=" * 80)

        # tab_clientes - Adicionar CLI_ID como primeira coluna
        print("\n[INFO] Adicionando CLI_ID em tab_clientes...")
        try:
            cursor.execute("ALTER TABLE tab_clientes ADD COLUMN CLI_ID INT NOT NULL FIRST")
            cursor.execute("ALTER TABLE tab_clientes ADD PRIMARY KEY (CLI_ID)")
            print("   [OK] CLI_ID adicionado como PK")
        except Exception as e:
            print(f"   [ERRO] {e}")

        # tab_tipos_equipamento - Adicionar TEQP_ID
        print("\n[INFO] Adicionando TEQP_ID em tab_tipos_equipamento...")
        try:
            cursor.execute("ALTER TABLE tab_tipos_equipamento ADD COLUMN TEQP_ID INT NOT NULL FIRST")
            cursor.execute("ALTER TABLE tab_tipos_equipamento ADD PRIMARY KEY (TEQP_ID)")
            print("   [OK] TEQP_ID adicionado como PK")
        except Exception as e:
            print(f"   [ERRO] {e}")

        # tab_equipamentos - Adicionar EQP_ID e EQP_TAG
        print("\n[INFO] Adicionando EQP_ID e EQP_TAG em tab_equipamentos...")
        try:
            cursor.execute("ALTER TABLE tab_equipamentos ADD COLUMN EQP_ID INT NOT NULL FIRST")
            cursor.execute("ALTER TABLE tab_equipamentos ADD PRIMARY KEY (EQP_ID)")
            print("   [OK] EQP_ID adicionado como PK")
        except Exception as e:
            print(f"   [ERRO] {e}")

        try:
            cursor.execute("ALTER TABLE tab_equipamentos ADD COLUMN EQP_TAG VARCHAR(200) NOT NULL AFTER EQP_ID")
            print("   [OK] EQP_TAG adicionado")
        except Exception as e:
            if '1060' in str(e):
                print("   [SKIP] EQP_TAG ja existe")
            else:
                print(f"   [ERRO] {e}")

        # Commit
        connection.commit()
        print("\n[OK] Commit realizado!")

        # Verificar estrutura final
        print("\n[INFO] Estrutura final das tabelas:")
        for table in ['tab_clientes', 'tab_tipos_equipamento', 'tab_equipamentos']:
            cursor.execute(f"SHOW COLUMNS FROM {table}")
            columns = cursor.fetchall()
            print(f"\n   {table}: {len(columns)} colunas")
            for col in columns:
                key = f" [{col['Key']}]" if col['Key'] else ""
                print(f"      - {col['Field']} ({col['Type']}){key}")

        print("\n" + "=" * 80)
        print("[OK] PRIMARY KEYS ADICIONADAS!")
        print("=" * 80)

    connection.close()

except Exception as e:
    print(f"\n[ERRO] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
