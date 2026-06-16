"""
Script para executar Migration 004
Adiciona campo excel_template na tabela formularios
"""

import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def run_migration():
    print("="*70)
    print("Migration 004: Adicionar excel_template em formularios")
    print("="*70)

    # Carregar variáveis de ambiente
    backend_dir = Path(__file__).parent.parent
    env_file = backend_dir / ".env"
    load_dotenv(env_file)

    # Obter DATABASE_URL do ambiente
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERRO: DATABASE_URL nao encontrada no .env")
        sys.exit(1)

    print("Conectando ao banco...")

    # Conectar ao banco
    engine = create_engine(database_url)

    # Ler arquivo de migration
    migration_file = backend_dir / "migrations" / "004_add_excel_template_to_formularios.sql"

    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Executar migration
    try:
        with engine.begin() as conn:
            # Remover comentários COMMENT (PostgreSQL específico)
            sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('COMMENT')]

            for statement in sql_statements:
                print(f"\nExecutando: {statement[:100]}...")
                conn.execute(text(statement))

        print("\n" + "="*70)
        print("Migration 004 executada com sucesso!")
        print("="*70)

    except Exception as e:
        print(f"\nERRO ao executar migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
