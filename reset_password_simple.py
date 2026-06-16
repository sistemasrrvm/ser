"""
Script simples para resetar senhas via API
Uso: python reset_password_simple.py <username ou user_id> <senha>
"""

import requests
import sys
import json

# URL da API
API_URL = "https://laudonr13-production.up.railway.app/api/v1/debug/reset-password"


def reset_password(username=None, user_id=None, new_password=None):
    """
    Reseta a senha de um usuário via API
    """
    print("=" * 80)
    print("RESET DE SENHA VIA API")
    print("=" * 80)
    
    # Preparar dados
    data = {"new_password": new_password}
    if username:
        data["username"] = username
        print(f"\n📝 Username: {username}")
    elif user_id:
        data["user_id"] = user_id
        print(f"\n📝 User ID: {user_id}")
    
    print(f"🔑 Nova senha: {'*' * len(new_password)}")
    print(f"\n🌐 Enviando requisição para: {API_URL}")
    
    try:
        # Fazer requisição
        response = requests.post(API_URL, json=data, timeout=30)
        
        # Verificar resposta
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCESSO! Senha resetada com sucesso!")
            print("=" * 80)
            print(f"\n👤 Usuário:")
            print(f"   ID: {result['user']['id']}")
            print(f"   Username: {result['user']['username']}")
            print(f"   Email: {result['user']['email']}")
            print(f"   Role ID: {result['user']['role_id']}")
            
            print(f"\n🔐 Hash Info:")
            print(f"   Hash antigo: {result['hash_info']['old_hash_length']} caracteres")
            print(f"   Hash novo: {result['hash_info']['new_hash_length']} caracteres")
            print(f"   Hash válido: {'✅ Sim' if result['hash_info']['new_hash_valid'] else '❌ Não'}")
            print(f"   Hash começa com: {result['hash_info']['new_hash_start']}...")
            
            print("\n" + "=" * 80)
            print(f"✅ Senha resetada: {new_password}")
            print("=" * 80)
            
            return True
        else:
            print(f"\n❌ ERRO: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Detalhes: {error_data.get('detail', response.text)}")
            except:
                print(f"   Resposta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERRO de conexão: {e}")
        print(f"   Verifique se a API está online: {API_URL}")
        return False
    except Exception as e:
        print(f"\n❌ ERRO inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal"""
    
    if len(sys.argv) < 3:
        print("\n❌ Uso incorreto!")
        print("\nUso:")
        print("  python reset_password_simple.py <username> <senha>")
        print("  python reset_password_simple.py <user_id> <senha>")
        print("\nExemplos:")
        print("  python reset_password_simple.py usuario.tecnico1 NovaSenha123!")
        print("  python reset_password_simple.py 7 NovaSenha123!")
        print("\n⚠️ Requisitos da senha:")
        print("  - Mínimo 8 caracteres")
        print("  - Pelo menos 1 letra maiúscula")
        print("  - Pelo menos 1 número")
        print("  - Pelo menos 1 caractere especial (!@#$%^&*()_+-=[]{}|;:,.<>?)")
        sys.exit(1)
    
    identifier = sys.argv[1]
    password = sys.argv[2]
    
    # Verificar se é número (user_id) ou string (username)
    if identifier.isdigit():
        success = reset_password(user_id=int(identifier), new_password=password)
    else:
        success = reset_password(username=identifier, new_password=password)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

