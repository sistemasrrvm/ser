"""
Script utilitário para gerar hash Argon2 da senha do admin
"""

import sys
sys.path.append('..')

from argon2 import PasswordHasher

# Configuração do Argon2 (mesma do core/security.py)
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)

# Gerar hash para "Admin@123"
password = "Admin@123"
password_hash = ph.hash(password)

print("=" * 80)
print("Hash Argon2 gerado para senha 'Admin@123'")
print("=" * 80)
print(f"\nHash:\n{password_hash}\n")
print("=" * 80)
print("\nAtualize o arquivo '../scripts/mysql/002_seed_admin.sql'")
print("substituindo o hash placeholder pelo hash gerado acima.")
print("=" * 80)
