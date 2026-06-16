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

print("TABELAS NO BANCO:")
print("=" * 50)

with connection.cursor() as cursor:
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    for table in tables:
        table_name = list(table.values())[0]
        print(f"  ✓ {table_name}")

connection.close()
