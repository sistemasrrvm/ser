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

def complete_migration():
    print("Completing migration 013...")

    try:
        with engine.begin() as conn:
            # Modificar colunas para BIGINT NULL (as FKs já foram removidas)
            print("Step 1: Modifying columns to BIGINT NULL...")
            conn.execute(text("ALTER TABLE reports MODIFY COLUMN cliente_id BIGINT NULL"))
            conn.execute(text("ALTER TABLE reports MODIFY COLUMN filial_id BIGINT NULL"))
            conn.execute(text("ALTER TABLE reports MODIFY COLUMN equipamento_id BIGINT NULL"))
            conn.execute(text("ALTER TABLE reports MODIFY COLUMN tipo_inspecao VARCHAR(100) NULL"))

            # Recriar foreign keys
            print("Step 2: Recreating foreign keys...")
            conn.execute(text("""
                ALTER TABLE reports
                ADD CONSTRAINT fk_reports_cliente
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                ON DELETE RESTRICT
            """))

            conn.execute(text("""
                ALTER TABLE reports
                ADD CONSTRAINT fk_reports_filial
                FOREIGN KEY (filial_id) REFERENCES filiais(id)
                ON DELETE RESTRICT
            """))

            conn.execute(text("""
                ALTER TABLE reports
                ADD CONSTRAINT fk_reports_equipamento
                FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
                ON DELETE RESTRICT
            """))

        print("SUCCESS: Migration 013 completed!")
        print("All fields are now BIGINT NULL and foreign keys recreated")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = complete_migration()
    sys.exit(0 if success else 1)
