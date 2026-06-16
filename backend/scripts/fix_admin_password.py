"""
Script para corrigir/atualizar a senha do usuário admin
"""

import sys
import os

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from argon2 import PasswordHasher
import pymysql
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do Argon2 (mesma do core/security.py)
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)

# Senha padrão
password = "Admin@123"
password_hash = ph.hash(password)

print("=" * 80)
print("Atualizando senha do usuário admin no banco de dados")
print("=" * 80)
print(f"\nSenha: {password}")
print(f"Hash gerado: {password_hash}\n")

# Conectar ao banco
try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='1234',
        database='db_a2cb65_laudonr'
    )

    with connection.cursor() as cursor:
        # Verificar se usuário admin existe
        cursor.execute("SELECT id, username FROM users WHERE username = 'admin'")
        user = cursor.fetchone()

        if user:
            print(f"✅ Usuário admin encontrado (ID: {user[0]})")

            # Atualizar senha
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE username = 'admin'",
                (password_hash,)
            )
            connection.commit()

            print("✅ Senha atualizada com sucesso!")
        else:
            print("❌ Usuário admin não encontrado!")
            print("Execute o script SQL primeiro: scripts/mysql/002_seed_admin.sql")

    connection.close()

except Exception as e:
    print(f"❌ Erro ao conectar ao banco de dados: {e}")
    print("\nVerifique:")
    print("- MySQL está rodando?")
    print("- Credenciais corretas? (host: localhost, user: root, pass: 1234)")
    print("- Database db_a2cb65_laudonr existe?")

print("=" * 80)
