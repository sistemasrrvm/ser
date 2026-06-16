"""
Teste para decodificar JWT manualmente
"""

import requests
from jose import jwt
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
SECRET_KEY = "dev-secret-key-c8f9e7a2b4d6c1a3e5f7b8d9a1c2e4f6a7b8c9d1e2f3a4b5c6d7e8f9a1b2c3d4"
ALGORITHM = "HS256"

# Fazer login
session = requests.Session()
response = session.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "Admin@123",
    "remember_me": False
})

access_token = session.cookies.get("access_token")

print("="*60)
print("DECODIFICANDO TOKEN JWT")
print("="*60)
print(f"\nToken (primeiros 50 chars): {access_token[:50]}...")

try:
    # Decodificar SEM validar expiracao
    payload_no_verify = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
    print(f"\n[OK] Token decodificado SEM verificar expiracao:")
    print(f"  Payload: {payload_no_verify}")
    print(f"  Exp (timestamp): {payload_no_verify.get('exp')}")

    # Converter exp para datetime
    exp_datetime = datetime.fromtimestamp(payload_no_verify.get('exp'))
    now_datetime = datetime.utcnow()

    print(f"  Exp (datetime): {exp_datetime}")
    print(f"  Now (datetime): {now_datetime}")
    print(f"  Token expira em: {exp_datetime - now_datetime}")

    # Agora COM validacao
    try:
        payload_with_verify = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"\n[OK] Token decodificado COM verificacao de expiracao!")
        print(f"  Token esta valido!")
    except Exception as e:
        print(f"\n[X] Token INVALIDO com verificacao de expiracao:")
        print(f"  Erro: {e}")

except Exception as e:
    print(f"\n[X] Erro ao decodificar token:")
    print(f"  {e}")
