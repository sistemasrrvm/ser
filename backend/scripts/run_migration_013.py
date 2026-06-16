# -*- coding: utf-8 -*-
"""
Migration 013: Tornar campos opcionais na tabela reports
Executar: python scripts/run_migration_013.py
"""

import sys
import os
from pathlib import Path
from sqlalchemy import text, create_engine
from dotenv import load_dotenv

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Carregar .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Pegar DATABASE_URL do ambiente
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("❌ DATABASE_URL não encontrada no .env")
    sys.exit(1)

# Criar engine direto
engine = create_engine(database_url)

def run_migration():
    print("= [MIGRATION 013] Iniciando migration...")
    print("= [MIGRATION 013] Tornar campos opcionais na tabela reports")

    migration_sql = Path(__file__).parent.parent / "migrations" / "migration_013_reports_optional_fields.sql"

    if not migration_sql.exists():
        print(f"L [MIGRATION 013] Arquivo SQL n�o encontrado: {migration_sql}")
        return False

    with open(migration_sql, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Dividir por statement (ponto e v�rgula)
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]

    try:
        with engine.begin() as conn:
            for i, statement in enumerate(statements, 1):
                if statement:
                    print(f"= [MIGRATION 013] Executando statement {i}/{len(statements)}...")
                    print(f"   SQL: {statement[:100]}...")
                    conn.execute(text(statement))

        print(" [MIGRATION 013] Migration executada com sucesso!")
        print(" [MIGRATION 013] Campos cliente_id, filial_id, equipamento_id e tipo_inspecao agora s�o opcionais")
        return True

    except Exception as e:
        print(f"L [MIGRATION 013] Erro ao executar migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
