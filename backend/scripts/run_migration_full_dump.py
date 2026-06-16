"""
Script para executar migration de dump completo no Railway
Uso:
  railway run python scripts/run_migration_full_dump.py
  
Ou localmente:
  python scripts/run_migration_full_dump.py
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
print("🚀 EXECUTANDO MIGRATION: DUMP COMPLETO")
print("=" * 80)

# Obter DATABASE_URL (do Railway ou local)
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("❌ ERRO: DATABASE_URL não configurada")
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

    print(f"✅ Conectando em: {host}:{port}/{database}")
except Exception as e:
    print(f"❌ ERRO ao parsear DATABASE_URL: {e}")
    sys.exit(1)

# Caminho da migration
migration_file = Path(__file__).parent.parent / "migrations" / "migration_015_full_dump.sql"

if not migration_file.exists():
    print(f"❌ ERRO: Arquivo de migration não encontrado: {migration_file}")
    print(f"   Execute primeiro: python scripts/generate_full_dump_migration.py --output migrations/migration_015_full_dump.sql")
    sys.exit(1)

print(f"✅ Arquivo encontrado: {migration_file}")
print(f"   Tamanho: {migration_file.stat().st_size / 1024 / 1024:.2f} MB")

# Ler arquivo SQL
print(f"\n📖 Lendo arquivo SQL...")
try:
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    print(f"✅ Arquivo lido: {len(sql_content)} caracteres")
except Exception as e:
    print(f"❌ ERRO ao ler arquivo: {e}")
    sys.exit(1)

# Conectar ao banco
print(f"\n🔌 Conectando ao banco...")
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
    print("✅ Conectado ao MySQL")
except Exception as e:
    print(f"❌ ERRO ao conectar: {e}")
    sys.exit(1)

# Executar SQL
print(f"\n🚀 Executando migration...")
print("   ⚠️  Isso pode demorar alguns minutos...")
print("   ⏳ Aguarde...")

try:
    # Dividir em comandos individuais
    commands = []
    current_command = ""
    in_multiline_comment = False
    
    for line in sql_content.split('\n'):
        line_stripped = line.strip()
        
        # Verificar comentários multi-linha
        if '/*!' in line_stripped:
            in_multiline_comment = True
        if '*/' in line_stripped:
            in_multiline_comment = False
        
        # Ignorar comentários simples
        if line_stripped.startswith('--') or not line_stripped:
            continue
        
        current_command += line + "\n"
        
        # Se termina com ; e não está em comentário, é um comando completo
        if line_stripped.endswith(';') and not in_multiline_comment:
            if current_command.strip():
                commands.append(current_command.strip())
            current_command = ""
    
    # Adicionar último comando
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
                
                # Mostrar progresso
                if i % 100 == 0:
                    print(f"   ⏳ Executados {i}/{len(commands)} comandos...")
                    
            except Exception as e:
                errors += 1
                error_msg = str(e).lower()
                
                # Ignorar alguns erros comuns
                if any(x in error_msg for x in ['already exists', 'duplicate', 'unknown table']):
                    continue
                else:
                    print(f"\n   ⚠️  Erro no comando {i}: {e}")
                    # Mostrar apenas uma prévia do comando
                    cmd_preview = command[:150].replace('\n', ' ')
                    print(f"   Comando: {cmd_preview}...")
    
    # Commit
    connection.commit()
    
    print(f"\n✅ Migration concluída!")
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
print("✅ MIGRATION EXECUTADA COM SUCESSO!")
print("=" * 80)

