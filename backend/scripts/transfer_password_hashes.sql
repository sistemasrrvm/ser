-- =====================================================
-- Script para Transferir Hashes de Senha
-- Gera comandos UPDATE para copiar hashes de senha de uma tabela para outra
-- =====================================================

-- OPÇÃO 1: Gerar comandos UPDATE (para revisar antes de executar)
SELECT
    CONCAT(
        'UPDATE `users` SET `password_hash` = ''',
        REPLACE(`users`.`password_hash`, '''', ''''''),  -- Escapar aspas simples
        ''' WHERE `id` = ',
        `users`.`id`,
        ';'
    ) AS update_command
FROM `users`
ORDER BY `users`.`id`;

-- OPÇÃO 2: Executar diretamente (DESCOMENTE E AJUSTE O nome_da_base_origem)
-- ATENÇÃO: Execute apenas se tiver certeza que os hashes estão corretos!
/*
UPDATE `users` AS dest
INNER JOIN `nome_da_base_origem`.`users` AS orig ON dest.id = orig.id
SET dest.password_hash = orig.password_hash;
*/

-- OPÇÃO 3: Verificar hashes antes de transferir
-- Use este comando para verificar se os hashes estão completos
SELECT
    `id`,
    `username`,
    CHAR_LENGTH(`password_hash`) AS hash_length,
    LEFT(`password_hash`, 30) AS hash_start,
    CASE
        WHEN `password_hash` LIKE '$argon2id$%' THEN '✅ Válido (Argon2)'
        WHEN `password_hash` LIKE '=19=%' THEN '❌ INVÁLIDO (prefixo truncado)'
        WHEN CHAR_LENGTH(`password_hash`) < 90 THEN '❌ INVÁLIDO (muito curto)'
        ELSE '⚠️ Formato desconhecido'
    END AS status
FROM `users`
ORDER BY `id`;

