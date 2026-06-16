"""
Script para gerar migration SQL completa com estrutura e dados
Uso:
  python scripts/generate_full_dump_migration.py > migrations/migration_015_full_dump.sql
  
Ou para gerar arquivo diretamente:
  python scripts/generate_full_dump_migration.py --output migrations/migration_015_full_dump.sql
"""

import pymysql
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Carregar variáveis de ambiente
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

print("=" * 80, file=sys.stderr)
print("📦 GERADOR DE MIGRATION SQL COMPLETA", file=sys.stderr)
print("=" * 80, file=sys.stderr)

# Parsear argumentos
output_file = None
if len(sys.argv) > 1:
    if sys.argv[1] == '--output' and len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    elif sys.argv[1].endswith('.sql'):
        output_file = Path(sys.argv[1])

# Obter DATABASE_URL local
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("❌ ERRO: DATABASE_URL não configurada no .env", file=sys.stderr)
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

    print(f"✅ Conectando em: {host}:{port}/{database}", file=sys.stderr)
except Exception as e:
    print(f"❌ ERRO ao parsear DATABASE_URL: {e}", file=sys.stderr)
    sys.exit(1)

# Conectar ao banco local
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
    print("✅ Conectado ao banco local", file=sys.stderr)
except Exception as e:
    print(f"❌ ERRO ao conectar: {e}", file=sys.stderr)
    sys.exit(1)

# Buffer para SQL gerado
sql_output = []
sql_output.append("-- Migration: Dump completo do banco local")
sql_output.append(f"-- Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
sql_output.append(f"-- Banco: {database}")
sql_output.append("")
sql_output.append("SET FOREIGN_KEY_CHECKS=0;")
sql_output.append("SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';")
sql_output.append("SET AUTOCOMMIT=0;")
sql_output.append("START TRANSACTION;")
sql_output.append("")

try:
    with connection.cursor() as cursor:
        # Listar todas as tabelas
        cursor.execute("SHOW TABLES")
        tables = [list(row.values())[0] for row in cursor.fetchall()]
        
        print(f"📋 Encontradas {len(tables)} tabelas", file=sys.stderr)
        
        for table_name in tables:
            print(f"   🔄 Processando tabela: {table_name}", file=sys.stderr)
            
            # Obter estrutura da tabela (CREATE TABLE)
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            create_table = cursor.fetchone()
            create_sql = create_table[f'Create Table']
            
            sql_output.append(f"-- Tabela: {table_name}")
            sql_output.append(f"DROP TABLE IF EXISTS `{table_name}`;")
            sql_output.append(f"/*!40101 SET @saved_cs_client     = @@character_set_client */;")
            sql_output.append(f"/*!40101 SET character_set_client = utf8mb4 */;")
            sql_output.append(f"{create_sql};")
            sql_output.append(f"/*!40101 SET character_set_client = @saved_cs_client */;")
            sql_output.append("")
            
            # Obter dados da tabela (INSERT)
            cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = cursor.fetchall()
            
            if rows:
                print(f"      📝 {len(rows)} registros", file=sys.stderr)
                
                # Pegar nomes das colunas
                columns = list(rows[0].keys())
                columns_str = ", ".join([f"`{col}`" for col in columns])
                
                # Gerar INSERTs em lotes de 1000
                batch_size = 1000
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]
                    values_list = []
                    
                    for row in batch:
                        values = []
                        for col in columns:
                            value = row[col]
                            if value is None:
                                values.append("NULL")
                            elif isinstance(value, (int, float)):
                                values.append(str(value))
                            elif isinstance(value, bool):
                                values.append("1" if value else "0")
                            else:
                                # Escapar strings
                                escaped = str(value).replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
                                values.append(f"'{escaped}'")
                        
                        values_list.append(f"({', '.join(values)})")
                    
                    sql_output.append(f"INSERT INTO `{table_name}` ({columns_str}) VALUES")
                    sql_output.append(",\n".join(values_list) + ";")
                    sql_output.append("")
            else:
                sql_output.append(f"-- Tabela {table_name} está vazia")
                sql_output.append("")
        
        sql_output.append("COMMIT;")
        sql_output.append("SET FOREIGN_KEY_CHECKS=1;")
        
except Exception as e:
    print(f"❌ ERRO ao gerar dump: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    connection.close()

# Escrever output
output_content = "\n".join(sql_output)

if output_file:
    # Escrever em arquivo
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_content)
    print(f"\n✅ Migration gerada: {output_file}", file=sys.stderr)
    print(f"   Tamanho: {len(output_content) / 1024 / 1024:.2f} MB", file=sys.stderr)
else:
    # Escrever na stdout
    print(output_content)

print("\n✅ Dump completo gerado!", file=sys.stderr)

