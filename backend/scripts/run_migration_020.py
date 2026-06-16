"""Aplica migration 020 — remove CHECK chk_reports_status (#246)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text
from src.core.config import settings


def main() -> None:
    engine = create_engine(settings.DATABASE_URL)
    with engine.begin() as conn:
        count = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM information_schema.TABLE_CONSTRAINTS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'reports'
                  AND CONSTRAINT_NAME = 'chk_reports_status'
                  AND CONSTRAINT_TYPE = 'CHECK'
                """
            )
        ).scalar()
        print(f"constraint exists: {count}")
        if count and count > 0:
            conn.execute(text("ALTER TABLE `reports` DROP CHECK `chk_reports_status`"))
            print("dropped chk_reports_status")
        else:
            print("already removed")


if __name__ == "__main__":
    main()
