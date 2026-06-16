-- Migration 014: Adicionar campos de endereço em tab_clientes
-- Data: 2025-11-20
-- Descrição: Adiciona 6 campos de endereço na tabela tab_clientes

USE db_a2cb65_laudonr;

-- Adicionar campos de endereço
ALTER TABLE `tab_clientes`
ADD COLUMN `CLI_ENDERECO` VARCHAR(200) NULL COMMENT 'Endereço (logradouro)',
ADD COLUMN `CLI_NUMERO` VARCHAR(20) NULL COMMENT 'Número do endereço',
ADD COLUMN `CLI_BAIRRO` VARCHAR(100) NULL COMMENT 'Bairro',
ADD COLUMN `CLI_CEP` VARCHAR(10) NULL COMMENT 'CEP',
ADD COLUMN `CLI_CIDADE` VARCHAR(100) NULL COMMENT 'Cidade',
ADD COLUMN `CLI_ESTADO` VARCHAR(2) NULL COMMENT 'Estado (UF)';

-- Verificar alterações
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'db_a2cb65_laudonr'
  AND TABLE_NAME = 'tab_clientes'
  AND COLUMN_NAME IN ('CLI_ENDERECO', 'CLI_NUMERO', 'CLI_BAIRRO', 'CLI_CEP', 'CLI_CIDADE', 'CLI_ESTADO')
ORDER BY ORDINAL_POSITION;
