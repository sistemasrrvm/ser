"""
Script para executar migration 003 e popular dados mock
"""

import pymysql
from pathlib import Path

# Conexão com banco
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='1234',
    database='db_a2cb65_laudonr',
    charset='utf8mb4'
)

try:
    # ===== EXECUTAR MIGRATION =====
    print("[1/2] Executando migration 003...")
    sql_file = Path('backend/migrations/003_create_reports_tables.sql')
    sql_content = sql_file.read_text(encoding='utf-8')

    with connection.cursor() as cursor:
        # Remover comentários e linhas vazias
        lines = [line for line in sql_content.split('\n') if line.strip() and not line.strip().startswith('--')]
        clean_sql = '\n'.join(lines)

        # Separar statements por ';'
        statements = [s.strip() for s in clean_sql.split(';') if s.strip()]

        for i, statement in enumerate(statements, 1):
            print(f"  [{i}/{len(statements)}] Executando: {statement[:80]}...")
            cursor.execute(statement)
            connection.commit()  # Commit após cada statement

    print("[OK] Migration 003 executada com sucesso!\n")

    # ===== POPULAR DADOS MOCK =====
    print("[2/2] Populando dados mock...")

    with connection.cursor() as cursor:
        # Clientes
        clientes = [
            ('CLI001', 'Petrobras S.A.', '33.000.167/0001-01'),
            ('CLI002', 'Vale S.A.', '33.592.510/0001-54'),
            ('CLI003', 'Braskem S.A.', '42.150.391/0001-70'),
            ('CLI004', 'Gerdau S.A.', '33.611.500/0001-19'),
        ]

        for codigo, nome, cnpj in clientes:
            cursor.execute(
                "INSERT INTO clientes (codigo, nome, cnpj) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE nome=nome",
                (codigo, nome, cnpj)
            )

        # Filiais
        filiais = [
            (1, 'FIL001', 'Unidade Rio de Janeiro', 'Rio de Janeiro', 'RJ'),
            (1, 'FIL002', 'Unidade Santos', 'Santos', 'SP'),
            (2, 'FIL001', 'Mina Carajás', 'Parauapebas', 'PA'),
            (2, 'FIL002', 'Mina Itabira', 'Itabira', 'MG'),
            (3, 'FIL001', 'Polo Petroquímico de Triunfo', 'Triunfo', 'RS'),
            (4, 'FIL001', 'Usina Ouro Branco', 'Ouro Branco', 'MG'),
        ]

        for cliente_id, codigo, nome, cidade, estado in filiais:
            cursor.execute(
                "INSERT INTO filiais (cliente_id, codigo, nome, cidade, estado) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE nome=nome",
                (cliente_id, codigo, nome, cidade, estado)
            )

        # Equipamentos
        equipamentos = [
            (1, 'EQ001', 'Caldeira Aquatubular 001', 'Caldeira', 'Dedini', 'CAT-500', 'CAT500-2018-001', 2018),
            (1, 'EQ002', 'Vaso de Pressão VP-101', 'Vaso de Pressão', 'Villares', 'VP-1000', 'VP1000-2019-045', 2019),
            (1, 'EQ003', 'Compressor Centrífugo CP-201', 'Compressor', 'Atlas Copco', 'ZH-6000', 'ZH6K-2020-123', 2020),
            (2, 'EQ001', 'Tanque de Armazenamento TQ-50', 'Tanque', 'CBV', 'TQV-5000', 'TQV5K-2017-089', 2017),
            (2, 'EQ002', 'Bomba Centrífuga BC-101', 'Bomba', 'KSB', 'Megabloc', 'MB200-2019-234', 2019),
            (3, 'EQ001', 'Válvula de Segurança VS-301', 'Válvula', 'Crosby', 'JOS', 'JOS250-2021-456', 2021),
            (4, 'EQ001', 'Trocador de Calor TC-401', 'Trocador', 'Alfa Laval', 'T20-BFG', 'T20-2018-678', 2018),
            (5, 'EQ001', 'Caldeira Flamotubular 002', 'Caldeira', 'Thermomatic', 'FT-300', 'FT300-2016-012', 2016),
            (6, 'EQ001', 'Forno Industrial FI-501', 'Forno', 'Selas', 'SI-750', 'SI750-2015-789', 2015),
        ]

        for filial_id, codigo, nome, tipo, fabricante, modelo, numero_serie, ano in equipamentos:
            cursor.execute(
                """INSERT INTO equipamentos
                   (filial_id, codigo, nome, tipo, fabricante, modelo, numero_serie, ano_fabricacao)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE nome=nome""",
                (filial_id, codigo, nome, tipo, fabricante, modelo, numero_serie, ano)
            )

    connection.commit()
    print("[OK] Dados mock populados com sucesso!\n")

    # ===== SUMMARY =====
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM filiais")
        total_filiais = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM equipamentos")
        total_equipamentos = cursor.fetchone()[0]

    print("=" * 60)
    print("RESUMO:")
    print("=" * 60)
    print(f"  Clientes:     {total_clientes}")
    print(f"  Filiais:      {total_filiais}")
    print(f"  Equipamentos: {total_equipamentos}")
    print("=" * 60)
    print("\nTabelas criadas:")
    print("  - clientes")
    print("  - filiais")
    print("  - equipamentos")
    print("  - reports")
    print("\n[OK] Migration 003 concluida!")

except Exception as e:
    print(f"\n[ERRO] Erro ao executar migration: {e}")
    connection.rollback()

finally:
    connection.close()
