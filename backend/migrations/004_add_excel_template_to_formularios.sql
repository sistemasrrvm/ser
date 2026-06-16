-- Migration 004: Adicionar campo excel_template na tabela formularios
-- Data: 2025-11-12
-- Descrição: Adiciona coluna para armazenar template Excel em base64 para mesclagem de dados

-- Adicionar coluna excel_template
ALTER TABLE formularios
ADD COLUMN excel_template TEXT NULL COMMENT 'Template Excel em base64 para mesclagem com dados do formulario';
