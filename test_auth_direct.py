"""
Script de teste para verificar autenticação diretamente no backend
Testa se os cookies estão sendo setados corretamente pelo FastAPI
"""

import requests

# URL do backend (direta, sem proxy)
BASE_URL = "http://localhost:8000/api/v1"

def test_login():
    """Testa login e verifica se cookies são setados"""
    print("\n" + "="*60)
    print("TESTE 1: LOGIN DIRETO NO BACKEND")
    print("="*60)

    # Criar sessão para manter cookies
    session = requests.Session()

    # Fazer login
    login_data = {
        "username": "admin",
        "password": "Admin@123",
        "remember_me": False
    }

    print(f"\n[POST] {BASE_URL}/auth/login")
    print(f"   Payload: {login_data}")

    response = session.post(f"{BASE_URL}/auth/login", json=login_data)

    print(f"\n[RESPONSE]")
    print(f"   Status: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    print(f"\n[COOKIES RECEBIDOS]")

    if response.cookies:
        for cookie in response.cookies:
            print(f"   - {cookie.name} = {cookie.value[:20]}...")
            print(f"     HttpOnly: {cookie.has_nonstandard_attr('HttpOnly')}")
            print(f"     Secure: {cookie.secure}")
            print(f"     Path: {cookie.path}")
            print(f"     SameSite: {cookie.get_nonstandard_attr('SameSite', 'nao definido')}")
    else:
        print("   [X] NENHUM COOKIE RECEBIDO!")

    print(f"\n[BODY]")
    print(f"   {response.json()}")

    return session

def test_get_me(session):
    """Testa endpoint /auth/me com cookies da sessão"""
    print("\n" + "="*60)
    print("TESTE 2: GET /auth/me COM COOKIES")
    print("="*60)

    print(f"\n[GET] {BASE_URL}/auth/me")
    print(f"   Cookies enviados: {session.cookies.get_dict()}")

    response = session.get(f"{BASE_URL}/auth/me")

    print(f"\n[RESPONSE]")
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        print(f"   [OK] AUTENTICADO!")
        print(f"   User: {response.json()}")
    else:
        print(f"   [X] FALHOU!")
        print(f"   Error: {response.json()}")

def test_without_cookies():
    """Testa endpoint /auth/me SEM cookies"""
    print("\n" + "="*60)
    print("TESTE 3: GET /auth/me SEM COOKIES")
    print("="*60)

    print(f"\n[GET] {BASE_URL}/auth/me")
    print(f"   Cookies enviados: Nenhum")

    response = requests.get(f"{BASE_URL}/auth/me")

    print(f"\n[RESPONSE]")
    print(f"   Status: {response.status_code}")
    print(f"   Error: {response.json()}")

if __name__ == "__main__":
    try:
        # Teste 1: Login e verificar cookies
        session = test_login()

        # Teste 2: Usar cookies para acessar /auth/me
        if session.cookies:
            test_get_me(session)

        # Teste 3: Tentar sem cookies (deve falhar)
        test_without_cookies()

        print("\n" + "="*60)
        print("CONCLUSAO")
        print("="*60)
        print("\nSe TESTE 1 nao mostrou cookies, o problema e no BACKEND.")
        print("Se TESTE 1 mostrou cookies mas TESTE 2 falhou, problema no envio.")
        print("Se TESTE 2 funcionou, o problema e no PROXY VITE.\n")

    except requests.exceptions.ConnectionError:
        print("\n[X] ERRO: Backend nao esta rodando em http://localhost:8000")
        print("   Inicie o backend antes de rodar este teste.\n")
    except Exception as e:
        print(f"\n[X] ERRO: {e}\n")
