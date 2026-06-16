"""
Migration 009: Criar tabelas cache SQL Server (NR13)
Data: 2025-11-16 14:30:00
Executar via: python scripts/run_migration_009.py (no container do Railway)
"""

import os
import pymysql
from urllib.parse import urlparse
from pathlib import Path

# Carregar .env se existir (desenvolvimento local)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

# Obter DATABASE_URL do ambiente
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("[ERRO] DATABASE_URL nao definida")
    exit(1)

# Parsear URL: mysql+pymysql://user:pass@host:port/database
parsed = urlparse(database_url.replace("mysql+pymysql://", "mysql://"))
db_config = {
    "host": parsed.hostname,
    "port": parsed.port or 3306,
    "user": parsed.username,
    "password": parsed.password,
    "database": parsed.path.lstrip("/").split("?")[0],
}

def run_migration():
    """Executa migration 009"""

    print("=" * 80)
    print("MIGRATION 009: Criar tabelas cache SQL Server (NR13)")
    print("=" * 80)
    print(f"\nConectando em: {db_config['host']}:{db_config['port']}/{db_config['database']}")

    try:
        # Conectar ao MySQL
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        # ========================================================================
        # TABELA 1: cache_sqlserver_clientes
        # ========================================================================
        print("\n1. Criando tabela 'cache_sqlserver_clientes'...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_sqlserver_clientes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                codigo VARCHAR(50) NOT NULL,
                nome VARCHAR(200) NOT NULL,
                cnpj VARCHAR(18) NULL,
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                criado_em DATETIME NULL,
                atualizado_em DATETIME NULL,
                ultima_sinc DATETIME NULL COMMENT 'Ultima sincronizacao com SQL Server',
                INDEX idx_codigo (codigo),
                INDEX idx_nome (nome)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.commit()
        print("   [OK] Tabela 'cache_sqlserver_clientes' criada")

        # ========================================================================
        # TABELA 2: cache_sqlserver_tipos_equipamento
        # ========================================================================
        print("\n2. Criando tabela 'cache_sqlserver_tipos_equipamento'...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_sqlserver_tipos_equipamento (
                id INT AUTO_INCREMENT PRIMARY KEY,
                codigo VARCHAR(50) NOT NULL,
                nome VARCHAR(200) NOT NULL,
                descricao VARCHAR(500) NULL,
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                criado_em DATETIME NULL,
                atualizado_em DATETIME NULL,
                ultima_sinc DATETIME NULL COMMENT 'Ultima sincronizacao com SQL Server',
                INDEX idx_codigo (codigo),
                INDEX idx_nome (nome)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.commit()
        print("   [OK] Tabela 'cache_sqlserver_tipos_equipamento' criada")

        # ========================================================================
        # TABELA 3: cache_sqlserver_equipamentos
        # ========================================================================
        print("\n3. Criando tabela 'cache_sqlserver_equipamentos'...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_sqlserver_equipamentos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                codigo VARCHAR(50) NOT NULL,
                nome VARCHAR(200) NOT NULL,
                cliente_id INT NOT NULL,
                tipo_equipamento_id INT NOT NULL,
                numero_serie VARCHAR(100) NULL,
                localizacao VARCHAR(200) NULL,
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                criado_em DATETIME NULL,
                atualizado_em DATETIME NULL,
                ultima_sinc DATETIME NULL COMMENT 'Ultima sincronizacao com SQL Server',
                INDEX idx_codigo (codigo),
                INDEX idx_nome (nome),
                INDEX idx_cliente_id (cliente_id),
                INDEX idx_tipo_equipamento_id (tipo_equipamento_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.commit()
        print("   [OK] Tabela 'cache_sqlserver_equipamentos' criada")

        # ========================================================================
        # VERIFICACAO FINAL
        # ========================================================================
        print("\n4. Verificando tabelas criadas...")

        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME IN (
                'cache_sqlserver_clientes',
                'cache_sqlserver_tipos_equipamento',
                'cache_sqlserver_equipamentos'
              )
            ORDER BY TABLE_NAME
        """, (db_config['database'],))

        tables_found = cursor.fetchall()

        for table in tables_found:
            print(f"   [OK] Tabela '{table[0]}' confirmada")

        if len(tables_found) == 3:
            print("\n" + "=" * 80)
            print("[SUCESSO] MIGRATION 009 CONCLUIDA COM SUCESSO!")
            print("=" * 80)
            print("\nTabelas cache SQL Server criadas:")
            print("  - cache_sqlserver_clientes")
            print("  - cache_sqlserver_tipos_equipamento")
            print("  - cache_sqlserver_equipamentos")
        else:
            print(f"\n[AVISO] Esperadas 3 tabelas, encontradas {len(tables_found)}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n[ERRO] ERRO AO EXECUTAR MIGRATION: {e}")
        raise

if __name__ == "__main__":
    run_migration()
