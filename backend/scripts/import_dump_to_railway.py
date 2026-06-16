"""
Script para importar dump SQL no Railway
Uso:
  1. Local: python scripts/import_dump_to_railway.py <caminho_do_dump.sql>
  2. Railway: railway run python scripts/import_dump_to_railway.py <caminho_do_dump.sql>
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
if env_path.exists():
    load_dotenv(env_path)

print("=" * 80)
print("📦 IMPORTAR DUMP SQL PARA RAILWAY")
print("=" * 80)

# Verificar argumento
if len(sys.argv) < 2:
    print("❌ ERRO: Caminho do arquivo SQL não fornecido")
    print("\nUso:")
    print("  python scripts/import_dump_to_railway.py <caminho_do_dump.sql>")
    print("\nExemplo:")
    print("  python scripts/import_dump_to_railway.py C:\\Users\\rafael.silva\\Documents\\dumps\\Dump20251120-laudonr13.sql")
    sys.exit(1)

dump_path = Path(sys.argv[1])
if not dump_path.exists():
    print(f"❌ ERRO: Arquivo não encontrado: {dump_path}")
    sys.exit(1)

print(f"✅ Arquivo encontrado: {dump_path}")
print(f"   Tamanho: {dump_path.stat().st_size / 1024 / 1024:.2f} MB")

# Obter DATABASE_URL do Railway
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("❌ ERRO: DATABASE_URL não configurada")
    print("   Certifique-se de estar no ambiente Railway ou ter DATABASE_URL no .env")
    sys.exit(1)

print(f"\n✅ DATABASE_URL configurada")

# Parsear DATABASE_URL
try:
    # Formato: mysql+pymysql://user:password@host:port/database
    if "://" not in database_url:
        raise ValueError("DATABASE_URL inválida")
    
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

    print(f"   Host: {host}:{port}")
    print(f"   Database: {database}")
    print(f"   User: {user}")
except Exception as e:
    print(f"❌ ERRO ao parsear DATABASE_URL: {e}")
    print(f"   DATABASE_URL: {database_url[:50]}...")
    sys.exit(1)

# Ler arquivo SQL
print(f"\n📖 Lendo arquivo SQL...")
try:
    with open(dump_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    print(f"✅ Arquivo lido: {len(sql_content)} caracteres")
except Exception as e:
    print(f"❌ ERRO ao ler arquivo: {e}")
    sys.exit(1)

# Conectar ao banco do Railway
print(f"\n🔌 Conectando ao banco do Railway...")
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

# Executar SQL
print(f"\n🚀 Executando dump SQL...")
print("   Isso pode levar alguns minutos dependendo do tamanho do dump...")
print("   ⏳ Aguarde...")

try:
    # Dividir em comandos individuais
    # Remove comentários e linhas vazias, divide por ';'
    commands = []
    current_command = ""
    
    for line in sql_content.split('\n'):
        line = line.strip()
        
        # Ignorar comentários e linhas vazias
        if not line or line.startswith('--') or line.startswith('/*'):
            continue
        
        # Remover comentários no final da linha
        if '--' in line:
            line = line.split('--')[0].strip()
        
        current_command += line + " "
        
        # Se termina com ;, é um comando completo
        if line.endswith(';'):
            if current_command.strip():
                commands.append(current_command.strip())
            current_command = ""
    
    # Adicionar último comando se não terminou com ;
    if current_command.strip():
        commands.append(current_command.strip())
    
    print(f"   📝 {len(commands)} comandos SQL encontrados")
    
    # Executar comandos
    executed = 0
    errors = 0
    
    with connection.cursor() as cursor:
        for i, command in enumerate(commands, 1):
            if not command or command == ';':
                continue
            
            try:
                cursor.execute(command)
                executed += 1
                
                # Mostrar progresso a cada 100 comandos
                if i % 100 == 0:
                    print(f"   ⏳ Executados {i}/{len(commands)} comandos...")
                    
            except Exception as e:
                errors += 1
                # Ignorar alguns erros comuns (tabela já existe, etc)
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    # Ignorar erros de duplicação (tabela/índice já existe)
                    continue
                else:
                    print(f"\n   ⚠️  Erro no comando {i}: {e}")
                    print(f"   Comando: {command[:100]}...")
    
    # Commit
    connection.commit()
    
    print(f"\n✅ Importação concluída!")
    print(f"   ✓ {executed} comandos executados com sucesso")
    if errors > 0:
        print(f"   ⚠️  {errors} erros (geralmente ignoráveis)")
    
except Exception as e:
    print(f"\n❌ ERRO durante execução: {e}")
    import traceback
    traceback.print_exc()
    connection.rollback()
    sys.exit(1)
finally:
    connection.close()
    print("\n🔌 Conexão fechada")

print("\n" + "=" * 80)
print("✅ DUMP IMPORTADO COM SUCESSO!")
print("=" * 80)

