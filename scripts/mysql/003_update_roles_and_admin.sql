-- =====================================================
-- SER - Sistema de Emissão de Relatórios
-- Script de Atualização de Roles e Usuário Admin
-- Banco: MySQL
-- Data: 2025-11-20
-- =====================================================

USE db_a2cb65_laudonr;

-- =====================================================
-- ATUALIZAÇÃO: Roles (Perfis)
-- Descrição: Cria/atualiza os perfis do sistema
-- - Tecnico (nível 20): Dashboard e Relatórios
-- - Suporte (nível 50): Dashboard, Relatórios, Clientes, Equipamentos
-- - Administrador (nível 100): Acesso total
-- =====================================================

-- Criar ou atualizar role Tecnico
INSERT INTO roles (name, level, description) VALUES
('Tecnico', 20, 'Técnico - Dashboard e Relatórios')
ON DUPLICATE KEY UPDATE 
    level=20, 
    description='Técnico - Dashboard e Relatórios';

-- Criar ou atualizar role Suporte
INSERT INTO roles (name, level, description) VALUES
('Suporte', 50, 'Suporte - Dashboard, Relatórios, Clientes, Equipamentos')
ON DUPLICATE KEY UPDATE 
    level=50, 
    description='Suporte - Dashboard, Relatórios, Clientes, Equipamentos';

-- Criar ou atualizar role Administrador
INSERT INTO roles (name, level, description) VALUES
('Administrador', 100, 'Administrador - Acesso total ao sistema')
ON DUPLICATE KEY UPDATE 
    level=100, 
    description='Administrador - Acesso total ao sistema';

-- =====================================================
-- ATUALIZAÇÃO: Usuário Admin
-- Descrição: Atualiza o role_id do usuário admin para o perfil Administrador
-- =====================================================

-- Atualizar usuário admin para usar o role Administrador
-- Usando JOIN para evitar problema com subquery no mesmo UPDATE
UPDATE users u
INNER JOIN roles r ON r.name = 'Administrador'
SET u.role_id = r.id
WHERE u.username = 'admin';

-- =====================================================
-- VERIFICAÇÃO: Verificar se a atualização foi bem-sucedida
-- =====================================================

-- =====================================================
-- RESULTADO: Mostrar o usuário admin atualizado
-- =====================================================

SELECT 
    u.id,
    u.username,
    u.full_name,
    u.email,
    u.role_id,
    r.name as role_name,
    r.level as role_level,
    r.description as role_description,
    u.is_active,
    u.last_login
FROM users u
INNER JOIN roles r ON u.role_id = r.id
WHERE u.username = 'admin';

-- =====================================================
-- RESULTADO: Mostrar todos os roles disponíveis
-- =====================================================

SELECT 
    id,
    name,
    level,
    description,
    created_at
FROM roles
ORDER BY level DESC;

-- =====================================================
-- NOTAS IMPORTANTES
-- =====================================================
-- 1. Este script cria/atualiza os 3 perfis:
--    - Tecnico (nível 20)
--    - Suporte (nível 50)
--    - Administrador (nível 100)
--
-- 2. Atualiza o usuário "admin" para usar o perfil "Administrador"
--
-- 3. Execute este script APENAS UMA VEZ após a migração para o novo sistema de roles
--
-- 4. Os roles antigos (admin, revisor, usuario) podem permanecer no banco
--    mas não serão mais usados pelo sistema
-- =====================================================

-- =====================================================
-- FIM DO SCRIPT
-- =====================================================

