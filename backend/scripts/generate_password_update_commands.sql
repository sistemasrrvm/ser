-- =====================================================
-- Gerar Comandos UPDATE para Transferir Hashes de Senha
-- =====================================================
-- Este script gera comandos UPDATE que você pode copiar e executar
-- IMPORTANTE: Revisar os comandos antes de executar!
-- =====================================================

SELECT
    CONCAT(
        'UPDATE `users` SET `password_hash` = ''',
        -- IMPORTANTE: REPLACE para escapar aspas simples dentro do hash
        REPLACE(`users`.`password_hash`, '''', ''''''),
        ''' WHERE `id` = ',
        `users`.`id`,
        ';'
    ) AS update_command
FROM `users`
WHERE `users`.`password_hash` IS NOT NULL
    AND `users`.`password_hash` != ''
ORDER BY `users`.`id`;

-- =====================================================
-- INSTRUÇÕES:
-- 1. Execute este SELECT acima
-- 2. Copie os comandos UPDATE gerados
-- 3. Revise cada comando (verifique se os hashes estão completos)
-- 4. Execute os comandos UPDATE no banco de destino
-- =====================================================

