import sys
import os
from pathlib import Path
from sqlalchemy import text, create_engine
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)

with engine.begin() as conn:
    # Check reports table columns
    result = conn.execute(text("""
        SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
        AND TABLE_NAME = 'reports'
        AND COLUMN_NAME IN ('cliente_id', 'filial_id', 'equipamento_id')
    """))

    print("Reports table foreign key columns:")
    for row in result:
        print(f"  {row[0]}: {row[1]} | Nullable: {row[2]} | Key: {row[3]}")

    # Check referenced tables id columns
    for table in ['clientes', 'filiais', 'equipamentos']:
        result = conn.execute(text(f"""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
            AND TABLE_NAME = '{table}'
            AND COLUMN_NAME = 'id'
        """))

        print(f"\n{table} table id column:")
        for row in result:
            print(f"  {row[0]}: {row[1]} | Nullable: {row[2]} | Key: {row[3]}")
