"""
Script para executar Migration 012 - Criar tabela configuracoes
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
        print("MIGRATION 012: Criar Tabela configuracoes")
        print("=" * 80)

        # Ler arquivo SQL
        sql_file = os.path.join(os.path.dirname(__file__), '..', 'migrations', 'migration_012_create_configuracoes.sql')

        print(f"\n[INFO] Lendo arquivo SQL: {sql_file}")

        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Dividir em statements individuais
        raw_statements = sql_content.split(';')
        statements = []

        for stmt in raw_statements:
            # Remover linhas de comentário
            lines = [line for line in stmt.split('\n') if line.strip() and not line.strip().startswith('--')]
            clean_stmt = '\n'.join(lines).strip()
            if clean_stmt:
                statements.append(clean_stmt)

        print(f"[INFO] Total de statements: {len(statements)}\n")

        # Executar cada statement
        for i, statement in enumerate(statements, 1):

            try:
                print(f"[{i}/{len(statements)}] Executando statement...")
                cursor.execute(statement)

                # Se for SELECT, mostrar resultado
                if statement.strip().upper().startswith('SELECT'):
                    result = cursor.fetchone()
                    if result:
                        print(f"   [OK] {result}")
                else:
                    print(f"   [OK] Executado com sucesso")
            except Exception as e:
                if '1050' in str(e):  # Table already exists
                    print(f"   [SKIP] Tabela ja existe")
                elif '1062' in str(e):  # Duplicate entry
                    print(f"   [SKIP] Registro ja existe")
                else:
                    print(f"   [ERRO] {e}")

        # Commit
        connection.commit()
        print("\n[OK] Commit realizado!")

        # Verificar resultado
        print("\n[INFO] Verificando tabela criada...")
        cursor.execute("SHOW TABLES LIKE 'configuracoes'")
        if cursor.fetchone():
            print("   [OK] Tabela 'configuracoes' existe")

            # Verificar estrutura
            cursor.execute("SHOW COLUMNS FROM configuracoes")
            columns = cursor.fetchall()
            print(f"\n   Estrutura da tabela ({len(columns)} colunas):")
            for col in columns:
                key = f" [{col['Key']}]" if col['Key'] else ""
                print(f"      - {col['Field']} ({col['Type']}){key}")

            # Verificar registro inicial
            cursor.execute("SELECT * FROM configuracoes WHERE chave = 'lookup_views'")
            config = cursor.fetchone()
            if config:
                print(f"\n   [OK] Configuracao 'lookup_views' criada:")
                print(f"      - Valor: {config['valor']}")
            else:
                print("\n   [AVISO] Configuracao 'lookup_views' nao encontrada")
        else:
            print("   [ERRO] Tabela 'configuracoes' nao foi criada")

        print("\n" + "=" * 80)
        print("[OK] MIGRATION 012 CONCLUIDA!")
        print("=" * 80)

    connection.close()

except Exception as e:
    print(f"\n[ERRO] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
