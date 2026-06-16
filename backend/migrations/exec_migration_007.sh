#!/bin/bash
# Script para executar migration 007 via Railway
# Uso: railway run bash migrations/exec_migration_007.sh

echo "===================================="
echo "Migration 007: ALTER excel_template"
echo "===================================="

# Extrair credenciais da DATABASE_URL
# Formato: mysql+pymysql://user:pass@host:port/database

HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

echo "Conectando ao banco de dados..."
echo "Host: $HOST"
echo "Port: $PORT"
echo "Database: $DB"

mysql -h $HOST -P $PORT -u $USER -p$PASS $DB << EOF
-- Verificar antes
SELECT COLUMN_NAME, COLUMN_TYPE, CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = '$DB'
  AND TABLE_NAME = 'formularios'
  AND COLUMN_NAME = 'excel_template';

-- Executar migração
ALTER TABLE formularios
MODIFY COLUMN excel_template LONGTEXT NULL
COMMENT 'Template Excel em base64 para mesclagem';

-- Verificar após
SELECT COLUMN_NAME, COLUMN_TYPE, CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = '$DB'
  AND TABLE_NAME = 'formularios'
  AND COLUMN_NAME = 'excel_template';
EOF

echo "===================================="
echo "Migration 007 concluída!"
echo "===================================="
