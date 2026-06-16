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

print("🔄 ROLLBACK COMPLETO: Voltando tudo ao estado original...")
print("=" * 70)

with connection.cursor() as cursor:
    try:
        cursor.execute("RENAME TABLE `formularios_paginas` TO `form_pages`")
        print("✅ Tabela formularios_paginas → form_pages")
    except Exception as e:
        print(f"ℹ️  formularios_paginas: {e}")

    try:
        cursor.execute("RENAME TABLE `formularios_campos` TO `form_fields`")
        print("✅ Tabela formularios_campos → form_fields")
    except Exception as e:
        print(f"ℹ️  formularios_campos: {e}")

    # Restaurar FKs originais
    try:
        cursor.execute("""
            ALTER TABLE `form_fields`
              ADD CONSTRAINT `fk_form_fields_page`
              FOREIGN KEY (`form_page_id`) REFERENCES `form_pages`(`id`)
              ON DELETE CASCADE
        """)
        print("✅ FK form_fields restaurada")
    except Exception as e:
        print(f"ℹ️  FK form_fields: {e}")

    try:
        cursor.execute("""
            ALTER TABLE `form_pages`
              ADD CONSTRAINT `fk_form_pages_formulario`
              FOREIGN KEY (`form_template_id`) REFERENCES `formularios`(`id`)
              ON DELETE CASCADE
        """)
        print("✅ FK form_pages restaurada")
    except Exception as e:
        print(f"ℹ️  FK form_pages: {e}")

connection.close()
print("=" * 70)
print("✅ Rollback concluído!")
