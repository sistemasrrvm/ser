"""
Script SIMPLIFICADO para importar dump SQL no Railway
Conecta direto usando DATABASE_URL ou dados do Railway

Uso:
  # Via Railway (recomendado - usa DATABASE_URL automaticamente)
  railway run python scripts/import_dump_railway_simple.py <dump.sql>
  
  # Ou localmente (se tiver DATABASE_URL do Railway no .env)
  python scripts/import_dump_railway_simple.py <dump.sql>
  
  # Ou com credenciais manuais
  python scripts/import_dump_railway_simple.py <dump.sql> --host shinkansen.proxy.rlwy.net --port 19259 --user root --password <senha> --database <nome_db>
"""

import pymysql
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("📦 IMPORTAR DUMP SQL - RAILWAY (Versão Simplificada)")
print("=" * 80)

# Parsear argumentos
parser = argparse.ArgumentParser(description='Importar dump SQL no Railway')
parser.add_argument('dump_file', help='Caminho do arquivo SQL')
parser.add_argument('--host', help='Host do MySQL')
parser.add_argument('--port', type=int, help='Porta do MySQL')
parser.add_argument('--user', help='Usuário do MySQL')
parser.add_argument('--password', help='Senha do MySQL')
parser.add_argument('--database', help='Nome do banco de dados')
parser.add_argument('--from-env', action='store_true', help='Usar DATABASE_URL do .env')

args = parser.parse_args()

dump_path = Path(args.dump_file)
if not dump_path.exists():
    print(f"❌ ERRO: Arquivo não encontrado: {dump_path}")
    sys.exit(1)

print(f"✅ Arquivo: {dump_path}")
print(f"   Tamanho: {dump_path.stat().st_size / 1024 / 1024:.2f} MB")

# Determinar credenciais
host = args.host
port = args.port
user = args.user
password = args.password
database = args.database

# Se não informou manualmente, tentar DATABASE_URL
if not all([host, port, user, password, database]):
    # Carregar .env se existir
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERRO: DATABASE_URL não configurada e credenciais não fornecidas")
        print("\nOpções:")
        print("  1. Configure DATABASE_URL no .env")
        print("  2. Execute via Railway: railway run python scripts/import_dump_railway_simple.py <dump.sql>")
        print("  3. Informe credenciais: --host --port --user --password --database")
        sys.exit(1)
    
    # Parsear DATABASE_URL
    try:
        _, connection_string = database_url.split("://", 1)
        user_pass, host_db = connection_string.split("@", 1)
        user, password = user_pass.split(":", 1)
        host_port, database = host_db.rsplit("/", 1)
        
        if ":" in host_port:
            host, port = host_port.split(":", 1)
            port = int(port)
        else:
            host = host_port
            port = 3306
        
        print(f"\n✅ Usando DATABASE_URL")
    except Exception as e:
        print(f"❌ ERRO ao parsear DATABASE_URL: {e}")
        sys.exit(1)

print(f"\n🔌 Conectando...")
print(f"   Host: {host}:{port}")
print(f"   Database: {database}")
print(f"   User: {user}")

# Conectar
try:
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=30
    )
    print("✅ Conectado ao MySQL do Railway")
except Exception as e:
    print(f"❌ ERRO ao conectar: {e}")
    sys.exit(1)

# Ler e executar dump
print(f"\n📖 Lendo arquivo...")
try:
    with open(dump_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    print(f"✅ Arquivo lido: {len(sql_content)} caracteres")
except Exception as e:
    print(f"❌ ERRO ao ler arquivo: {e}")
    sys.exit(1)

print(f"\n🚀 Executando dump SQL...")
print("   ⏳ Isso pode demorar alguns minutos...")

try:
    # Dividir em comandos
    commands = []
    current_command = ""
    
    for line in sql_content.split('\n'):
        line = line.strip()
        
        # Ignorar comentários
        if not line or line.startswith('--') or (line.startswith('/*') and line.endswith('*/')):
            continue
        
        # Remover comentários no final
        if '--' in line:
            line = line.split('--')[0].strip()
        
        current_command += line + " "
        
        if line.endswith(';'):
            cmd = current_command.strip()
            if cmd and cmd != ';':
                commands.append(cmd)
            current_command = ""
    
    if current_command.strip():
        commands.append(current_command.strip())
    
    print(f"   📝 {len(commands)} comandos encontrados")
    
    # Executar
    executed = 0
    errors = 0
    
    with connection.cursor() as cursor:
        for i, command in enumerate(commands, 1):
            if not command:
                continue
            
            try:
                cursor.execute(command)
                executed += 1
                
                if i % 100 == 0:
                    print(f"   ⏳ {i}/{len(commands)} comandos...")
                    
            except Exception as e:
                errors += 1
                error_msg = str(e).lower()
                
                # Ignorar erros comuns
                if any(x in error_msg for x in ['already exists', 'duplicate', 'unknown table']):
                    continue
                
                # Mostrar erros importantes
                if errors <= 10:  # Limitar a 10 erros
                    print(f"\n   ⚠️  Comando {i}: {str(e)[:100]}")
    
    connection.commit()
    
    print(f"\n✅ Concluído!")
    print(f"   ✓ {executed} comandos executados")
    if errors > 0:
        print(f"   ⚠️  {errors} erros ignorados")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    connection.rollback()
    sys.exit(1)
finally:
    connection.close()

print("\n" + "=" * 80)
print("✅ DUMP IMPORTADO COM SUCESSO!")
print("=" * 80)

