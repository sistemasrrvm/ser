"""
Corrige DEFINER das views de lookup após import de dump (Railway/produção).

Erro típico:
  (1449, "The user specified as a definer ('root'@'%') does not exist")

Uso:
  cd backend
  python scripts/fix_mysql_view_definers.py
  python scripts/fix_mysql_view_definers.py --yes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from sqlmodel import Session

from src.core.config import settings
from src.core.database import engine

LOOKUP_VIEWS_SQL = [
    """
    DROP VIEW IF EXISTS vw_tab_clientes_lookup
    """,
    """
    CREATE DEFINER=`root`@`localhost` SQL SECURITY INVOKER VIEW vw_tab_clientes_lookup AS
    SELECT
      CLI_ID AS id,
      CLI_NOME AS label,
      NULL AS filter
    FROM tab_clientes
    WHERE CLI_NOME IS NOT NULL
    ORDER BY CLI_NOME
    """,
    """
    DROP VIEW IF EXISTS vw_tab_equipamentos_lookup
    """,
    """
    CREATE DEFINER=`root`@`localhost` SQL SECURITY INVOKER VIEW vw_tab_equipamentos_lookup AS
    SELECT
      EQP_ID AS id,
      CONCAT(EQP_TAG, ' - ', COALESCE(EQP_NOME, '')) AS label,
      EQP_CLI_ID AS filter
    FROM tab_equipamentos
    WHERE EQP_TAG IS NOT NULL
    ORDER BY EQP_TAG
    """,
    """
    DROP VIEW IF EXISTS vw_tab_tipos_equipamento_lookup
    """,
    """
    CREATE DEFINER=`root`@`localhost` SQL SECURITY INVOKER VIEW vw_tab_tipos_equipamento_lookup AS
    SELECT
      TEQP_ID AS id,
      TEQP_NOME AS label,
      NULL AS filter
    FROM tab_tipos_equipamento
    WHERE TEQP_NOME IS NOT NULL
    ORDER BY TEQP_NOME
    """,
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Recria views lookup com DEFINER root@localhost")
    parser.add_argument("--yes", action="store_true", help="Executar sem confirmação")
    args = parser.parse_args()

    db_name = settings.DATABASE_URL.rsplit("/", 1)[-1]
    print(f"Banco: {db_name}")

    if not args.yes:
        print("Use --yes para aplicar.")
        return 1

    with Session(engine) as session:
        before = session.exec(
            text(
                "SELECT TABLE_NAME, DEFINER FROM information_schema.VIEWS "
                "WHERE TABLE_SCHEMA = DATABASE()"
            )
        ).all()
        print("Antes:", before)

        for stmt in LOOKUP_VIEWS_SQL:
            session.exec(text(stmt))
        session.commit()

        after = session.exec(
            text(
                "SELECT TABLE_NAME, DEFINER FROM information_schema.VIEWS "
                "WHERE TABLE_SCHEMA = DATABASE()"
            )
        ).all()
        print("Depois:", after)

        count = session.exec(
            text("SELECT COUNT(*) FROM vw_tab_clientes_lookup")
        ).one()
        print(f"Teste vw_tab_clientes_lookup: {count[0]} registro(s)")

    print("OK — views corrigidas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
