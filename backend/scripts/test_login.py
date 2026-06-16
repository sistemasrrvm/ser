"""
Script para testar login na API
Testa tanto local quanto Railway
"""

import requests
import sys
import json

def test_login(base_url: str, username: str, password: str):
    """
    Testa login na API

    Args:
        base_url: URL base da API (ex: http://localhost:8000 ou https://laudonr13-production.up.railway.app)
        username: Nome de usuario
        password: Senha

    Returns:
        True se login bem sucedido, False caso contrario
    """

    print("=" * 80)
    print("TESTE DE LOGIN")
    print("=" * 80)
    print(f"\nURL: {base_url}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")

    # Endpoint de login
    login_url = f"{base_url}/api/v1/auth/login"

    # Dados do login
    payload = {
        "username": username,
        "password": password
    }

    print(f"\n1. Testando conexao com servidor...")
    try:
        # Fazer requisicao POST
        print(f"   POST {login_url}")
        response = requests.post(
            login_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"\n2. Resposta do servidor:")
        print(f"   Status Code: {response.status_code}")

        # Verificar resultado
        if response.status_code == 200:
            print(f"   [OK] LOGIN BEM SUCEDIDO!")

            # Parsear resposta
            data = response.json()

            print(f"\n3. Dados retornados:")
            if "user" in data:
                user = data["user"]
                print(f"   ID: {user.get('id')}")
                print(f"   Username: {user.get('username')}")
                print(f"   Nome: {user.get('full_name')}")
                print(f"   Email: {user.get('email')}")
                print(f"   Role: {user.get('role')}")

            if "access_token" in data:
                token = data["access_token"]
                print(f"\n   Access Token: {token[:20]}...{token[-20:] if len(token) > 40 else ''}")

            if "refresh_token" in data:
                refresh = data["refresh_token"]
                print(f"   Refresh Token: {refresh[:20]}...{refresh[-20:] if len(refresh) > 40 else ''}")

            print("\n" + "=" * 80)
            print("[OK] TESTE CONCLUIDO COM SUCESSO!")
            print("=" * 80)
            return True

        elif response.status_code == 401:
            print(f"   [X] LOGIN FALHOU - Credenciais invalidas")
            try:
                error_data = response.json()
                print(f"   Mensagem: {error_data.get('detail', 'Sem detalhes')}")
            except:
                print(f"   Resposta: {response.text}")

        elif response.status_code == 500:
            print(f"   [X] ERRO 500 - Erro interno do servidor")
            try:
                error_data = response.json()
                print(f"   Mensagem: {error_data.get('detail', 'Sem detalhes')}")
            except:
                print(f"   Resposta: {response.text}")

        else:
            print(f"   [X] ERRO INESPERADO")
            print(f"   Resposta: {response.text}")

        print("\n" + "=" * 80)
        print("[X] TESTE FALHOU!")
        print("=" * 80)
        return False

    except requests.exceptions.ConnectionError:
        print(f"   [X] ERRO: Nao foi possivel conectar ao servidor")
        print(f"   Verifique se o servidor esta rodando em: {base_url}")
        return False

    except requests.exceptions.Timeout:
        print(f"   [X] ERRO: Timeout ao conectar ao servidor")
        return False

    except Exception as e:
        print(f"   [X] ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Funcao principal"""

    # URLs para testar
    urls = {
        "railway": "https://laudonr13-production.up.railway.app",
        "local": "http://localhost:8000"
    }

    # Solicitar ambiente
    print("\nESCOLHA O AMBIENTE:")
    print("1. Railway (producao)")
    print("2. Local (desenvolvimento)")
    print("3. Customizado")

    choice = input("\nOpcao (1/2/3): ").strip()

    if choice == "1":
        base_url = urls["railway"]
    elif choice == "2":
        base_url = urls["local"]
    elif choice == "3":
        base_url = input("Digite a URL base: ").strip()
    else:
        print("[X] Opcao invalida!")
        sys.exit(1)

    # Solicitar credenciais
    username = input("\nUsername: ").strip()
    password = input("Password: ").strip()

    # Executar teste
    success = test_login(base_url, username, password)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    # Verificar se foi passado argumentos
    if len(sys.argv) == 4:
        # Modo nao-interativo: python script.py url username password
        base_url = sys.argv[1]
        username = sys.argv[2]
        password = sys.argv[3]
        success = test_login(base_url, username, password)
        sys.exit(0 if success else 1)
    else:
        # Modo interativo
        main()
