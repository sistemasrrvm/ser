"""
Ambiente de TESTES — define senha de cada usuário igual ao username.

Uso:
  cd backend
  python scripts/set_test_passwords_equal_username.py --yes

  # Simular sem gravar:
  python scripts/set_test_passwords_equal_username.py --dry-run

  # Apenas um usuário:
  python scripts/set_test_passwords_equal_username.py --yes --username admin

ATENÇÃO: usar SOMENTE em desenvolvimento/homologação local.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select

from src.core.config import settings
from src.core.database import engine
from src.core.security import get_password_hash, verify_password
from src.models.user import User


def set_passwords(
    *,
    dry_run: bool = False,
    only_username: str | None = None,
) -> int:
    env = (getattr(settings, "ENVIRONMENT", "") or "").lower()
    debug = bool(getattr(settings, "DEBUG", False))

    print("=" * 72)
    print("SER — senhas de teste (password = username)")
    print("=" * 72)
    print(f"Banco: {settings.DATABASE_URL.rsplit('/', 1)[-1]}")
    print(f"ENVIRONMENT={env or '(nao definido)'}  DEBUG={debug}")
    if dry_run:
        print("MODO: dry-run (nenhuma alteracao sera gravada)")
    print()

    updated = 0
    failed: list[str] = []

    with Session(engine) as session:
        stmt = select(User).order_by(User.username)
        if only_username:
            stmt = stmt.where(User.username == only_username)
        users = session.exec(stmt).all()

        if not users:
            print("Nenhum usuario encontrado.")
            return 1

        for user in users:
            new_password = user.username
            old_ok = verify_password(new_password, user.password_hash)

            if old_ok:
                print(f"  [OK] {user.username} — ja estava com senha = username")
                continue

            new_hash = get_password_hash(new_password)
            if not new_hash.startswith("$argon2id$"):
                failed.append(user.username)
                print(f"  [ERRO] {user.username} — hash gerado invalido")
                continue

            if dry_run:
                print(f"  [dry-run] {user.username} -> senha '{new_password}'")
                updated += 1
                continue

            user.password_hash = new_hash
            user.updated_at = datetime.now(timezone.utc)
            session.add(user)
            session.commit()
            session.refresh(user)

            if not verify_password(new_password, user.password_hash):
                failed.append(user.username)
                print(f"  [ERRO] {user.username} — falha ao verificar apos gravar")
                continue

            updated += 1
            active = "ativo" if user.is_active else "INATIVO"
            print(f"  [OK] {user.username} / {new_password} ({active})")

    print()
    print("-" * 72)
    if dry_run:
        print(f"Usuarios que seriam atualizados: {updated}")
    else:
        print(f"Usuarios atualizados: {updated}")
    if failed:
        print(f"Falhas: {', '.join(failed)}")
        return 1

    if not dry_run and updated:
        print()
        print("Login: username = senha (ex.: admin / admin)")
    print("=" * 72)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Define senha = username para todos os usuarios (ambiente de testes)"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirma execucao (obrigatorio para gravar)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Lista alteracoes sem gravar",
    )
    parser.add_argument(
        "--username",
        help="Aplicar apenas a este username",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.yes:
        print("Use --yes para gravar ou --dry-run para simular.")
        print("Exemplo: python scripts/set_test_passwords_equal_username.py --yes")
        return 1

    return set_passwords(dry_run=args.dry_run, only_username=args.username)


if __name__ == "__main__":
    raise SystemExit(main())
