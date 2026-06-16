"""
Script para Verificar e Corrigir Hashes de Senha
Verifica se todos os hashes estão no formato Argon2 correto e corrige os que estão truncados/incompletos

Uso:
  Local: python backend/scripts/verify_and_fix_password_hashes.py
  Railway: railway run python backend/scripts/verify_and_fix_password_hashes.py
"""

import os
import sys
from pathlib import Path
from typing import Tuple

# Adicionar src ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, text
from src.models.user import User
from src.core.security import get_password_hash, verify_password
from src.core.database import engine


def verify_hash_format(password_hash: str) -> Tuple[bool, str]:
    """
    Verifica se o hash está no formato correto
    
    Returns:
        (is_valid, reason)
    """
    if not password_hash:
        return False, "Hash vazio"
    
    # Verificar se começa com $argon2id$
    if not password_hash.startswith("$argon2id$"):
        return False, f"Hash não começa com $argon2id$ (início: {password_hash[:20]})"
    
    # Verificar comprimento (Argon2 normalmente tem ~97 caracteres)
    if len(password_hash) < 90:
        return False, f"Hash muito curto ({len(password_hash)} chars, esperado ~97)"
    
    # Verificar se contém todas as partes do formato Argon2
    if password_hash.count("$") < 5:
        return False, f"Hash não tem formato Argon2 completo (apenas {password_hash.count('$')} separadores $)"
    
    return True, "Hash válido"


def check_all_hashes() -> dict:
    """
    Verifica todos os hashes de senha no banco
    
    Returns:
        dict com usuários problemáticos
    """
    print("=" * 80)
    print("VERIFICAÇÃO DE HASHES DE SENHA")
    print("=" * 80)
    
    problematic_users = []
    
    try:
        with Session(engine) as session:
            # Buscar todos os usuários
            print("\n1. Buscando todos os usuários...")
            statement = select(User)
            users = session.exec(statement).all()
            
            print(f"   [OK] {len(users)} usuário(s) encontrado(s)\n")
            
            # Verificar cada usuário
            print("2. Verificando hashes...\n")
            for user in users:
                hash_valid, reason = verify_hash_format(user.password_hash)
                
                hash_length = len(user.password_hash) if user.password_hash else 0
                hash_start = user.password_hash[:30] if user.password_hash and len(user.password_hash) >= 30 else user.password_hash
                
                status = "✅ VÁLIDO" if hash_valid else "❌ INVÁLIDO"
                print(f"   {status} | ID: {user.id:2d} | {user.username:20s} | Hash: {hash_length:3d} chars | {hash_start}...")
                
                if not hash_valid:
                    problematic_users.append({
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "hash_length": hash_length,
                        "hash_start": hash_start,
                        "reason": reason,
                        "full_hash": user.password_hash
                    })
        
        print(f"\n3. Resultado:")
        print(f"   Total de usuários: {len(users)}")
        print(f"   Usuários com hash válido: {len(users) - len(problematic_users)}")
        print(f"   Usuários com hash inválido: {len(problematic_users)}")
        
        return {
            "total": len(users),
            "valid": len(users) - len(problematic_users),
            "invalid": len(problematic_users),
            "problematic": problematic_users
        }
    
    except Exception as e:
        print(f"\n[X] ERRO ao verificar hashes: {e}")
        import traceback
        traceback.print_exc()
        return None


def fix_user_hash(user_id: int, new_password: str = None) -> bool:
    """
    Corrige o hash de um usuário específico
    
    Args:
        user_id: ID do usuário
        new_password: Nova senha (se None, usa "TempPassword123!")
    """
    if new_password is None:
        new_password = "TempPassword123!"
    
    try:
        with Session(engine) as session:
            user = session.get(User, user_id)
            if not user:
                print(f"   [X] Usuário ID {user_id} não encontrado!")
                return False
            
            print(f"\n   Corrigindo hash do usuário: {user.username} (ID: {user.id})")
            print(f"   Senha temporária: {new_password}")
            
            # Gerar novo hash
            new_hash = get_password_hash(new_password)
            print(f"   Novo hash gerado: {len(new_hash)} caracteres")
            print(f"   Novo hash começa com: {new_hash[:30]}...")
            
            # Atualizar hash
            user.password_hash = new_hash
            session.add(user)
            session.commit()
            session.refresh(user)
            
            # Verificar se foi salvo corretamente
            hash_valid, reason = verify_hash_format(user.password_hash)
            if hash_valid:
                print(f"   [OK] Hash corrigido com sucesso!")
                return True
            else:
                print(f"   [X] Hash ainda inválido após atualização: {reason}")
                return False
    
    except Exception as e:
        print(f"   [X] ERRO ao corrigir hash: {e}")
        import traceback
        traceback.print_exc()
        return False


def fix_all_problematic_hashes(problematic_users: list, new_password: str = None) -> dict:
    """
    Corrige todos os hashes problemáticos
    
    Args:
        problematic_users: Lista de usuários com hash inválido
        new_password: Senha temporária padrão (se None, usa "TempPassword123!")
    """
    if not problematic_users:
        print("\n[OK] Nenhum hash precisa ser corrigido!")
        return {"fixed": 0, "failed": 0}
    
    print("\n" + "=" * 80)
    print("CORREÇÃO DE HASHES INVÁLIDOS")
    print("=" * 80)
    print(f"\n{len(problematic_users)} usuário(s) com hash inválido serão corrigidos.\n")
    
    if new_password is None:
        new_password = "TempPassword123!"
    
    print(f"Senha temporária que será definida para todos: {new_password}")
    print("[!] IMPORTANTE: Os usuários precisarão trocar a senha no primeiro login!\n")
    
    fixed = 0
    failed = 0
    
    for user_info in problematic_users:
        user_id = user_info["id"]
        username = user_info["username"]
        
        print(f"\nCorrigindo usuário: {username} (ID: {user_id})")
        if fix_user_hash(user_id, new_password):
            fixed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 80)
    print("RESUMO DA CORREÇÃO")
    print("=" * 80)
    print(f"   Hashes corrigidos: {fixed}")
    print(f"   Falhas: {failed}")
    print(f"   Senha temporária para todos: {new_password}")
    print("\n[!] IMPORTANTE: Avise os usuários para trocarem a senha no primeiro login!")
    print("=" * 80)
    
    return {"fixed": fixed, "failed": failed}


def main():
    """Função principal"""
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO E CORREÇÃO DE HASHES DE SENHA")
    print("=" * 80)
    
    # 1. Verificar todos os hashes
    result = check_all_hashes()
    
    if result is None:
        print("\n[X] Falha na verificação!")
        sys.exit(1)
    
    if result["invalid"] == 0:
        print("\n[OK] Todos os hashes estão válidos! Nenhuma correção necessária.")
        sys.exit(0)
    
    # 2. Perguntar se deseja corrigir
    print("\n" + "=" * 80)
    print(f"Encontrados {result['invalid']} usuário(s) com hash inválido!")
    print("=" * 80)
    
    if "--auto-fix" in sys.argv:
        # Modo automático
        fix_all_problematic_hashes(result["problematic"])
    else:
        # Modo interativo
        print("\nUsuários com hash inválido:")
        for user_info in result["problematic"]:
            print(f"   - ID {user_info['id']:2d}: {user_info['username']:20s} ({user_info['reason']})")
        
        response = input("\nDeseja corrigir todos os hashes inválidos? (sim/nao): ").strip().lower()
        
        if response in ['sim', 's', 'yes', 'y']:
            # Perguntar senha temporária
            temp_password = input("Digite a senha temporária padrão (ou Enter para 'TempPassword123!'): ").strip()
            if not temp_password:
                temp_password = "TempPassword123!"
            
            fix_all_problematic_hashes(result["problematic"], temp_password)
        else:
            print("\n[X] Operação cancelada pelo usuário")
            sys.exit(0)


if __name__ == "__main__":
    main()

