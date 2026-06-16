"""
Script para completar Migration 011 - Adicionar campos faltantes e limpar campos antigos
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
        print("FIX MIGRATION 011: Completando alteracoes")
        print("=" * 80)

        # Adicionar campos faltantes em tab_clientes
        print("\n[INFO] Adicionando campos faltantes em tab_clientes...")
        campos_clientes = [
            "ALTER TABLE tab_clientes ADD COLUMN CLI_SITE VARCHAR(100) NULL",
            "ALTER TABLE tab_clientes ADD COLUMN CLI_CONTATO VARCHAR(100) NULL",
            "ALTER TABLE tab_clientes ADD COLUMN CLI_EMAIL VARCHAR(100) NULL",
            "ALTER TABLE tab_clientes ADD COLUMN CLI_TELEFONE VARCHAR(50) NULL"
        ]

        for sql in campos_clientes:
            try:
                cursor.execute(sql)
                print(f"   [OK] {sql[:60]}...")
            except Exception as e:
                if '1060' in str(e):  # Duplicate column
                    print(f"   [SKIP] Campo ja existe")
                else:
                    print(f"   [ERRO] {e}")

        # Adicionar campos faltantes em tab_tipos_equipamento
        print("\n[INFO] Adicionando campos faltantes em tab_tipos_equipamento...")
        campos_tipos = [
            "ALTER TABLE tab_tipos_equipamento ADD COLUMN TEQP_VENC_CALIBRACAO INT NULL",
            "ALTER TABLE tab_tipos_equipamento ADD COLUMN TEQP_REQUER_INSPECAO_EXTERNA INT NOT NULL DEFAULT 0",
            "ALTER TABLE tab_tipos_equipamento ADD COLUMN TEQP_REQUER_INSPECAO_INTERNA INT NOT NULL DEFAULT 0"
        ]

        for sql in campos_tipos:
            try:
                cursor.execute(sql)
                print(f"   [OK] {sql[:60]}...")
            except Exception as e:
                if '1060' in str(e):
                    print(f"   [SKIP] Campo ja existe")
                else:
                    print(f"   [ERRO] {e}")

        # Remover campos antigos se ainda existirem
        print("\n[INFO] Removendo campos antigos...")

        # tab_clientes
        try:
            cursor.execute("ALTER TABLE tab_clientes DROP COLUMN id")
            print("   [OK] Removido id de tab_clientes")
        except:
            print("   [SKIP] Campo id ja removido de tab_clientes")

        try:
            cursor.execute("ALTER TABLE tab_clientes DROP COLUMN codigo")
            print("   [OK] Removido codigo de tab_clientes")
        except:
            print("   [SKIP] Campo codigo ja removido de tab_clientes")

        # tab_tipos_equipamento
        try:
            cursor.execute("ALTER TABLE tab_tipos_equipamento DROP COLUMN id")
            print("   [OK] Removido id de tab_tipos_equipamento")
        except:
            print("   [SKIP] Campo id ja removido de tab_tipos_equipamento")

        try:
            cursor.execute("ALTER TABLE tab_tipos_equipamento DROP COLUMN codigo")
            print("   [OK] Removido codigo de tab_tipos_equipamento")
        except:
            print("   [SKIP] Campo codigo ja removido de tab_tipos_equipamento")

        # tab_equipamentos
        try:
            cursor.execute("ALTER TABLE tab_equipamentos DROP COLUMN id")
            print("   [OK] Removido id de tab_equipamentos")
        except:
            print("   [SKIP] Campo id ja removido de tab_equipamentos")

        try:
            cursor.execute("ALTER TABLE tab_equipamentos DROP COLUMN codigo")
            print("   [OK] Removido codigo de tab_equipamentos")
        except:
            print("   [SKIP] Campo codigo ja removido de tab_equipamentos")

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
                print(f"      - {col['Field']} ({col['Type']})")

        print("\n" + "=" * 80)
        print("[OK] FIX CONCLUIDO!")
        print("=" * 80)

    connection.close()

except Exception as e:
    print(f"\n[ERRO] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
