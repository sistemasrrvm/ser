"""
Script para Resetar Senha de Usuario
Uso:
  Local: python scripts/reset_user_password.py
  Railway: railway run python scripts/reset_user_password.py
"""

import os
import sys
from pathlib import Path

# Adicionar src ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select
from src.models.user import User
from src.core.security import get_password_hash, validate_password_strength
from src.core.database import engine


def reset_password(username: str, new_password: str) -> bool:
    """
    Reseta a senha de um usuario

    Args:
        username: Nome de usuario
        new_password: Nova senha

    Returns:
        True se sucesso, False caso contrario
    """

    print("=" * 80)
    print("RESET DE SENHA DE USUARIO")
    print("=" * 80)

    # Validar forca da senha
    print(f"\n1. Validando forca da senha...")
    is_valid, message = validate_password_strength(new_password)
    if not is_valid:
        print(f"   [X] Senha invalida: {message}")
        print("\n   Requisitos:")
        print("   - Minimo 8 caracteres")
        print("   - Pelo menos 1 letra maiuscula")
        print("   - Pelo menos 1 numero")
        print("   - Pelo menos 1 caractere especial (!@#$%^&*()_+-=[]{}|;:,.<>?)")
        return False

    print(f"   [OK] Senha valida: {message}")

    # Conectar ao banco
    print(f"\n2. Conectando ao banco de dados...")
    try:
        with Session(engine) as session:
            # Buscar usuario
            print(f"\n3. Buscando usuario '{username}'...")
            statement = select(User).where(User.username == username)
            user = session.exec(statement).first()

            if not user:
                print(f"   [X] Usuario '{username}' nao encontrado!")
                return False

            print(f"   [OK] Usuario encontrado!")
            print(f"      ID: {user.id}")
            print(f"      Nome completo: {user.full_name}")
            print(f"      Email: {user.email or 'N/A'}")
            print(f"      Ativo: {'Sim' if user.is_active else 'Nao'}")

            # Gerar hash da nova senha
            print(f"\n4. Gerando hash da nova senha...")
            new_hash = get_password_hash(new_password)
            print(f"   [OK] Hash gerado com sucesso")

            # Atualizar senha
            print(f"\n5. Atualizando senha no banco de dados...")
            user.password_hash = new_hash
            session.add(user)
            session.commit()
            session.refresh(user)

            print(f"   [OK] Senha atualizada com sucesso!")

            print("\n" + "=" * 80)
            print("[OK] SENHA RESETADA COM SUCESSO!")
            print("=" * 80)
            print(f"\nCredenciais de acesso:")
            print(f"   Username: {username}")
            print(f"   Senha: {new_password}")
            print("\n[!] IMPORTANTE: Guarde estas credenciais em local seguro!")
            print("=" * 80)

            return True

    except Exception as e:
        print(f"\n[X] ERRO ao resetar senha: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Funcao principal - modo interativo"""

    print("\nRESET DE SENHA - MODO INTERATIVO")
    print("=" * 80)

    # Solicitar username
    username = input("\nDigite o username do usuario: ").strip()
    if not username:
        print("[X] Username nao pode ser vazio!")
        sys.exit(1)

    # Solicitar nova senha
    new_password = input("Digite a nova senha: ").strip()
    if not new_password:
        print("[X] Senha nao pode ser vazia!")
        sys.exit(1)

    # Confirmar senha
    confirm_password = input("Confirme a nova senha: ").strip()
    if new_password != confirm_password:
        print("[X] As senhas nao coincidem!")
        sys.exit(1)

    # Confirmar operacao
    print(f"\n[!] ATENCAO: Voce esta prestes a resetar a senha do usuario '{username}'")
    confirm = input("Deseja continuar? (sim/nao): ").strip().lower()

    if confirm not in ['sim', 's', 'yes', 'y']:
        print("[X] Operacao cancelada pelo usuario")
        sys.exit(0)

    # Executar reset
    success = reset_password(username, new_password)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    # Verificar se foi passado argumentos
    if len(sys.argv) == 3:
        # Modo nao-interativo: python script.py username senha
        username = sys.argv[1]
        new_password = sys.argv[2]
        success = reset_password(username, new_password)
        sys.exit(0 if success else 1)
    else:
        # Modo interativo
        main()
