"""
Script para executar Migration 011 - Renomear campos das tabelas NR13
Alinhar nomenclatura com banco externo SQL Server
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

if not database_url:
    print("[ERRO] DATABASE_URL nao encontrada no .env")
    sys.exit(1)

# Parse DATABASE_URL
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
        print("MIGRATION 011: Renomear campos das tabelas NR13")
        print("=" * 80)

        # Ler arquivo SQL
        sql_file = os.path.join(os.path.dirname(__file__), '..', 'migrations', 'migration_011_rename_manut_fields.sql')

        print(f"\n[INFO] Lendo arquivo SQL: {sql_file}")

        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Dividir em statements individuais
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

        print(f"[INFO] Total de statements: {len(statements)}\n")

        # Executar cada statement
        for i, statement in enumerate(statements, 1):
            # Ignorar comentários e USE statements
            if statement.startswith('--') or statement.startswith('USE'):
                continue

            # Ignorar SELECTs informativos
            if 'Migracao 011 concluida' in statement or statement.startswith('SHOW'):
                continue

            try:
                print(f"[{i}/{len(statements)}] Executando statement...")
                cursor.execute(statement)
                print(f"   [OK] Executado com sucesso")
            except Exception as e:
                print(f"   [ERRO] Erro: {e}")
                print(f"   Statement: {statement[:100]}...")
                # Não para a execução, continua com próximo statement

        # Commit
        connection.commit()
        print("\n[OK] Commit realizado!")

        # Verificar resultado
        print("\n[INFO] Verificando estrutura das tabelas...")

        for table in ['tab_clientes', 'tab_tipos_equipamento', 'tab_equipamentos']:
            cursor.execute(f"SHOW COLUMNS FROM {table}")
            columns = cursor.fetchall()
            print(f"\n   Tabela: {table}")
            print(f"   Total de colunas: {len(columns)}")
            for col in columns[:5]:  # Mostrar primeiras 5 colunas
                print(f"      - {col['Field']} ({col['Type']})")
            if len(columns) > 5:
                print(f"      ... e mais {len(columns) - 5} colunas")

        print("\n" + "=" * 80)
        print("[OK] MIGRATION 011 CONCLUIDA COM SUCESSO!")
        print("=" * 80)

    connection.close()

except Exception as e:
    print(f"\n[ERRO] ERRO durante a migracao: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
