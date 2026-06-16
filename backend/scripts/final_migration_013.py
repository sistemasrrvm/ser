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

def final_migration():
    print("Finalizing migration 013...")
    print("Adding missing foreign keys for filial_id and equipamento_id")

    try:
        with engine.begin() as conn:
            # Recriar fk_reports_filial
            print("Creating fk_reports_filial...")
            conn.execute(text("""
                ALTER TABLE reports
                ADD CONSTRAINT fk_reports_filial
                FOREIGN KEY (filial_id) REFERENCES filiais(id)
                ON DELETE RESTRICT
            """))

            # Recriar fk_reports_equipamento
            print("Creating fk_reports_equipamento...")
            conn.execute(text("""
                ALTER TABLE reports
                ADD CONSTRAINT fk_reports_equipamento
                FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
                ON DELETE RESTRICT
            """))

        print("SUCCESS: Migration 013 completed!")
        print("All fields are now BIGINT NULL with proper foreign keys")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = final_migration()
    sys.exit(0 if success else 1)
