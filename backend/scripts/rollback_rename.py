import pymysql
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

database_url = os.getenv("DATABASE_URL")
_, connection_string = database_url.split("://")
user_pass, host_db = connection_string.split("@")
user, password = user_pass.split(":")
host, database = host_db.split("/")

connection = pymysql.connect(
    host=host,
    user=user,
    password=password,
    database=database,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

connection.autocommit(True)

print("🔄 ROLLBACK: Voltando formularios_campos para form_fields...")

with connection.cursor() as cursor:
    try:
        cursor.execute("RENAME TABLE `formularios_campos` TO `form_fields`")
        print("✅ Tabela renomeada de volta para form_fields")
    except Exception as e:
        print(f"ℹ️  Tabela formularios_campos não existe ou já foi revertida: {e}")

connection.close()
print("✅ Rollback concluído")
