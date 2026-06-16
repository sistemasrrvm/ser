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
        SELECT
            CONSTRAINT_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
        AND TABLE_NAME = 'reports'
        AND REFERENCED_TABLE_NAME IS NOT NULL
    """))

    print("Foreign keys in reports table:")
    for row in result:
        print(f"- {row[0]}: {row[1]} -> {row[2]}.{row[3]}")
