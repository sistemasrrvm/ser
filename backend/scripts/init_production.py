"""
Script de inicialização para produção (Railway)
Executa migrations e seeds necessários
"""

import pymysql
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Carregar variáveis de ambiente
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

print("=" * 70)
print("🚀 INICIALIZAÇÃO - PRODUÇÃO (Railway)")
print("=" * 70)

# Parsear DATABASE_URL
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("❌ ERRO: DATABASE_URL não configurada")
    sys.exit(1)

print(f"✅ DATABASE_URL configurada")

# Extrair credenciais
try:
    # Formato: mysql+pymysql://user:password@host:port/database
    _, connection_string = database_url.split("://")
    user_pass, host_db = connection_string.split("@")
    user, password = user_pass.split(":")
    host_port, database = host_db.split("/")

    if ":" in host_port:
        host, port = host_port.split(":")
        port = int(port)
    else:
        host = host_port
        port = 3306

    print(f"✅ Host: {host}:{port}")
    print(f"✅ Database: {database}")
    print(f"✅ User: {user}")
except Exception as e:
    print(f"❌ ERRO ao parsear DATABASE_URL: {e}")
    sys.exit(1)

# Conectar ao banco
try:
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    connection.autocommit(True)
    print("✅ Conectado ao MySQL")
except Exception as e:
    print(f"❌ ERRO ao conectar: {e}")
    sys.exit(1)

# Verificar se tabelas existem
with connection.cursor() as cursor:
    cursor.execute("SHOW TABLES")
    tables = [row[f'Tables_in_{database}'] for row in cursor.fetchall()]

    print(f"\n📋 Tabelas encontradas: {len(tables)}")
    for table in tables:
        print(f"   - {table}")

# Executar migrations se necessário
migrations_path = Path(__file__).parent.parent / "migrations"

if len(tables) == 0:
    print("\n⚠️  Nenhuma tabela encontrada - Executando migrations iniciais...")

    # Lista de migrations na ordem correta
    migration_files = [
        "migration_001_create_users.sql",
        "migration_002_create_formularios.sql",
        # Adicionar outras migrations conforme necessário
    ]

    for migration_file in migration_files:
        migration_path = migrations_path / migration_file
        if migration_path.exists():
            print(f"\n🔧 Executando: {migration_file}")
            with open(migration_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

                # Executar cada statement separadamente
                statements = [s.strip() for s in sql_content.split(';') if s.strip()]
                with connection.cursor() as cursor:
                    for statement in statements:
                        if statement:
                            try:
                                cursor.execute(statement)
                                print(f"   ✅ OK")
                            except Exception as e:
                                print(f"   ⚠️  {e}")
        else:
            print(f"   ⚠️  Arquivo não encontrado: {migration_file}")
else:
    print("\n✅ Tabelas já existem - Pulando migrations")

# Verificar usuário admin
print("\n👤 Verificando usuário admin...")
with connection.cursor() as cursor:
    cursor.execute("SELECT * FROM users WHERE username = 'admin' LIMIT 1")
    admin = cursor.fetchone()

    if not admin:
        print("⚠️  Usuário admin não encontrado - Criando...")
        from argon2 import PasswordHasher

        ph = PasswordHasher()
        hashed_password = ph.hash("admin123")  # Senha padrão - TROCAR EM PRODUÇÃO!

        cursor.execute("""
            INSERT INTO users (username, email, full_name, hashed_password, role, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ("admin", "admin@example.com", "Administrador", hashed_password, "admin", True))

        print("✅ Usuário admin criado")
        print("   Username: admin")
        print("   Password: admin123")
        print("   ⚠️  IMPORTANTE: Trocar a senha após primeiro login!")
    else:
        print("✅ Usuário admin encontrado")

connection.close()

print("\n" + "=" * 70)
print("✅ INICIALIZAÇÃO CONCLUÍDA")
print("=" * 70)
