"""
Script para executar migration 006: Renomear tabelas para português
"""

import sqlite3
import os
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Caminho do banco de dados
DB_PATH = Path(__file__).parent.parent / "laudonr13.db"
MIGRATION_PATH = Path(__file__).parent.parent / "migrations" / "migration_006_rename_tables_pt.sql"

def run_migration():
    """Executa a migration 006"""

    print("=" * 70)
    print("🔄 MIGRATION 006: Renomear tabelas e campos para português")
    print("=" * 70)

    if not DB_PATH.exists():
        print(f"❌ Banco de dados não encontrado: {DB_PATH}")
        return False

    if not MIGRATION_PATH.exists():
        print(f"❌ Arquivo de migration não encontrado: {MIGRATION_PATH}")
        return False

    # Fazer backup
    backup_path = DB_PATH.with_suffix('.db.backup_migration_006')
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Backup criado: {backup_path}")

    # Conectar ao banco
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Ler SQL da migration
        with open(MIGRATION_PATH, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Executar migration
        print("\n📝 Executando migration...")
        cursor.executescript(migration_sql)

        print("\n✅ Migration executada com sucesso!")

        # Verificar resultados
        print("\n📊 Verificando tabelas...")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'formularios_%'")
        tables = cursor.fetchall()
        print("\nTabelas encontradas:")
        for table in tables:
            print(f"  ✓ {table[0]}")

        cursor.execute("SELECT COUNT(*) FROM formularios_paginas")
        paginas_count = cursor.fetchone()[0]
        print(f"\n📄 Total de páginas: {paginas_count}")

        cursor.execute("SELECT COUNT(*) FROM formularios_campos")
        campos_count = cursor.fetchone()[0]
        print(f"📋 Total de campos: {campos_count}")

        conn.commit()
        print("\n" + "=" * 70)
        print("✅ MIGRATION 006 CONCLUÍDA COM SUCESSO!")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ Erro ao executar migration: {e}")
        conn.rollback()

        # Restaurar backup
        print(f"\n🔄 Restaurando backup...")
        shutil.copy2(backup_path, DB_PATH)
        print(f"✅ Backup restaurado")

        return False

    finally:
        conn.close()

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
