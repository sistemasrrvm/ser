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
    result = conn.execute(text("""
        SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
        AND TABLE_NAME = 'reports'
        AND COLUMN_NAME = 'tipo_inspecao'
    """))

    print("tipo_inspecao column:")
    for row in result:
        print(f"  Name: {row[0]}")
        print(f"  Type: {row[1]}")
        print(f"  Nullable: {row[2]}")
        print(f"  Default: {row[3]}")
