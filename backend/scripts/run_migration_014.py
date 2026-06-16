"""
Script para executar Migration 014: Adicionar campos de endereço em tab_clientes
"""

import sys
import os

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text, create_engine
from src.core.config import settings

def run_migration():
    """Executa a migration 014"""

    print("=" * 80)
    print("MIGRATION 014: Adicionar campos de endereço em tab_clientes")
    print("=" * 80)

    # Criar engine
    engine = create_engine(settings.DATABASE_URL, echo=True)

    try:
        with engine.connect() as conn:
            print("\n[1/3] Adicionando campos de endereço...")

            # SQL da migration
            migration_sql = """
            ALTER TABLE `tab_clientes`
            ADD COLUMN `CLI_ENDERECO` VARCHAR(200) NULL COMMENT 'Endereço (logradouro)',
            ADD COLUMN `CLI_NUMERO` VARCHAR(20) NULL COMMENT 'Número do endereço',
            ADD COLUMN `CLI_BAIRRO` VARCHAR(100) NULL COMMENT 'Bairro',
            ADD COLUMN `CLI_CEP` VARCHAR(10) NULL COMMENT 'CEP',
            ADD COLUMN `CLI_CIDADE` VARCHAR(100) NULL COMMENT 'Cidade',
            ADD COLUMN `CLI_ESTADO` VARCHAR(2) NULL COMMENT 'Estado (UF)';
            """

            conn.execute(text(migration_sql))
            conn.commit()

            print("\n[2/3] Verificando campos criados...")

            # Verificar campos
            verify_sql = """
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
              AND TABLE_NAME = 'tab_clientes'
              AND COLUMN_NAME IN ('CLI_ENDERECO', 'CLI_NUMERO', 'CLI_BAIRRO', 'CLI_CEP', 'CLI_CIDADE', 'CLI_ESTADO')
            ORDER BY ORDINAL_POSITION;
            """

            result = conn.execute(text(verify_sql))
            rows = result.fetchall()

            print("\nCampos criados:")
            for row in rows:
                print(f"  - {row[0]}: {row[1]}({row[2]}) NULL={row[3]} COMMENT='{row[4]}'")

            print("\n[3/3] Migration 014 concluída com sucesso! ✅")

    except Exception as e:
        print(f"\n❌ ERRO ao executar migration: {e}")
        return False

    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
