"""
Teste para verificar o NOME do cookie sendo enviado
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"

# Fazer login
session = requests.Session()
response = session.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "Admin@123",
    "remember_me": False
})

print("="*60)
print("COOKIES APOS LOGIN:")
print("="*60)
for cookie in session.cookies:
    print(f"Nome: {cookie.name}")
    print(f"Valor: {cookie.value[:50]}...")
    print(f"Domain: {cookie.domain}")
    print(f"Path: {cookie.path}")
    print()

print("="*60)
print("TESTANDO /auth/me:")
print("="*60)

# Testar /auth/me
response2 = session.get(f"{BASE_URL}/auth/me")
print(f"Status: {response2.status_code}")

if response2.status_code == 200:
    print("[OK] Funcionou!")
else:
    print(f"[X] Falhou: {response2.json()}")

# Mostrar headers da requisicao
print("\n" + "="*60)
print("HEADERS ENVIADOS PARA /auth/me:")
print("="*60)
print(f"Cookie header: {session.cookies.get_dict()}")
