"""
Script para atualizar configuração lookup_views no banco de dados
Altera de array simples para array de objetos com value/label/description
"""

import pymysql
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("[ERRO] DATABASE_URL nao encontrada")
    sys.exit(1)

try:
    parts = database_url.replace("mysql+pymysql://", "").split("@")
    user_pass = parts[0].split(":")
    host_db = parts[1].split("/")

    connection = pymysql.connect(
        host=host_db[0],
        user=user_pass[0],
        password=user_pass[1],
        database=host_db[1],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    print("[INFO] Conectado ao MySQL\n")

    with connection.cursor() as cursor:
        print("=" * 80)
        print("ATUALIZAR CONFIGURACAO: lookup_views")
        print("=" * 80)

        # Novo formato JSON
        new_config = {
            "views": [
                {
                    "value": "vw_tab_clientes_lookup",
                    "label": "Clientes (NR13)",
                    "description": "View de lookup para clientes NR13"
                },
                {
                    "value": "vw_tab_equipamentos_lookup",
                    "label": "Equipamentos (NR13)",
                    "description": "View de lookup para equipamentos NR13"
                },
                {
                    "value": "vw_tab_tipos_equipamento_lookup",
                    "label": "Tipos de Equipamento (NR13)",
                    "description": "View de lookup para tipos de equipamento NR13"
                }
            ]
        }

        new_config_json = json.dumps(new_config, ensure_ascii=False, indent=2)

        print("\n[INFO] Novo formato JSON:")
        print(new_config_json)

        # Atualizar configuração
        print("\n[INFO] Atualizando configuracao 'lookup_views'...")
        cursor.execute("""
            UPDATE configuracoes
            SET valor = %s
            WHERE chave = 'lookup_views'
        """, (new_config_json,))

        affected_rows = cursor.rowcount

        if affected_rows > 0:
            print(f"   [OK] {affected_rows} registro(s) atualizado(s)")
            connection.commit()
            print("   [OK] Commit realizado!")
        else:
            print("   [AVISO] Nenhum registro foi atualizado")
            print("   [INFO] Verificando se configuracao existe...")

            cursor.execute("SELECT * FROM configuracoes WHERE chave = 'lookup_views'")
            result = cursor.fetchone()

            if not result:
                print("   [AVISO] Configuracao 'lookup_views' nao existe. Inserindo...")
                cursor.execute("""
                    INSERT INTO configuracoes (chave, valor, tipo, descricao, categoria)
                    VALUES ('lookup_views', %s, 'json', 'Lista de views homologadas para uso em campos Lookup', 'sistema')
                """, (new_config_json,))
                connection.commit()
                print("   [OK] Configuracao inserida com sucesso!")
            else:
                print(f"   [INFO] Configuracao existe: {result}")

        # Verificar resultado final
        print("\n[INFO] Verificando configuracao atualizada...")
        cursor.execute("SELECT * FROM configuracoes WHERE chave = 'lookup_views'")
        result = cursor.fetchone()

        if result:
            print(f"\n   [OK] Configuracao atualizada:")
            print(f"      ID: {result['id']}")
            print(f"      Chave: {result['chave']}")
            print(f"      Tipo: {result['tipo']}")
            print(f"      Valor:")
            valor_parsed = json.loads(result['valor'])
            print(json.dumps(valor_parsed, indent=8, ensure_ascii=False))
        else:
            print("   [ERRO] Configuracao nao encontrada apos update")

        print("\n" + "=" * 80)
        print("[OK] ATUALIZACAO CONCLUIDA!")
        print("=" * 80)

    connection.close()

except Exception as e:
    print(f"\n[ERRO] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
