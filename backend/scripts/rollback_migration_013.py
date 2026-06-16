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

def rollback():
    print("Rolling back migration 013...")

    try:
        with engine.begin() as conn:
            # Restaurar as colunas para NOT NULL e INT original
            print("Restoring original column types...")
            conn.execute(text("ALTER TABLE reports MODIFY COLUMN cliente_id BIGINT NOT NULL"))
            conn.execute(text("ALTER TABLE reports MODIFY COLUMN filial_id INT NOT NULL"))
            conn.execute(text("ALTER TABLE reports MODIFY COLUMN equipamento_id INT NOT NULL"))
            conn.execute(text("ALTER TABLE reports MODIFY COLUMN tipo_inspecao VARCHAR(100) NOT NULL"))

            # Recriar as foreign keys originais
            print("Recreating original foreign keys...")
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

        print("SUCCESS: Rollback completed!")
        return True

    except Exception as e:
        print(f"ERROR during rollback: {e}")
        return False

if __name__ == "__main__":
    success = rollback()
    sys.exit(0 if success else 1)
