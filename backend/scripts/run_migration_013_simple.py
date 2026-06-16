import sys
import os
from pathlib import Path
from sqlalchemy import text, create_engine
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Get DATABASE_URL
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL not found")
    sys.exit(1)

# Create engine
engine = create_engine(database_url)

def run_migration():
    print("Starting migration 013...")
    print("Making cliente_id, filial_id, equipamento_id, tipo_inspecao nullable")

    # Read SQL file
    migration_sql = Path(__file__).parent.parent / "migrations" / "migration_013_reports_optional_fields.sql"

    if not migration_sql.exists():
        print(f"ERROR: SQL file not found: {migration_sql}")
        return False

    with open(migration_sql, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Split by semicolon and filter comments
    statements = [
        stmt.strip()
        for stmt in sql_content.split(';')
        if stmt.strip() and not stmt.strip().startswith('--')
    ]

    try:
        with engine.begin() as conn:
            for i, statement in enumerate(statements, 1):
                print(f"Executing statement {i}/{len(statements)}...")
                conn.execute(text(statement))

        print("SUCCESS: Migration 013 completed!")
        print("Fields are now nullable and foreign keys recreated")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
