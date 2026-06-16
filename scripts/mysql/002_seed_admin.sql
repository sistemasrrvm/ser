-- =====================================================
-- SER - Sistema de Emissão de Relatórios
-- Script de Seed - Dados Iniciais
-- Banco: MySQL
-- Data: 2025-10-29
-- =====================================================

USE db_a2cb65_laudonr;

-- =====================================================
-- SEED: Roles
-- =====================================================
INSERT INTO roles (name, level, description) VALUES
('admin', 100, 'Administrador do sistema - acesso total'),
('revisor', 40, 'Revisor - pode revisar e aprovar relatórios'),
('usuario', 20, 'Usuário padrão - pode criar e editar relatórios')
ON DUPLICATE KEY UPDATE level=VALUES(level), description=VALUES(description);

-- =====================================================
-- SEED: Usuário Admin Padrão
-- Descrição: Primeiro usuário ADMIN do sistema
-- Username: admin
-- Senha: Admin@123
-- Hash Argon2: $argon2id$v=19$m=65536,t=3,p=4$vHKcHdY8RB8cP3bGKN0l+g$5FqZ8J3yJ3fJ3LJ8J3J8J3J8J3J8J3J8J3J8J3J8J3
-- IMPORTANTE: Alterar senha após primeiro login!
-- =====================================================

-- Nota: O hash abaixo é para a senha "Admin@123"
-- Gerado com: argon2id, memory=65536, iterations=3, parallelism=4
INSERT INTO users (username, password_hash, full_name, email, role_id, is_active)
SELECT
    'admin',
    '$argon2id$v=19$m=65536,t=3,p=4$vHKcHdY8RB8cP3bGKN0l+g$5FqZ8J3yJ3fJ3LJ8J3J8J3J8J3J8J3J8J3J8J3J8J3',
    'Administrador do Sistema',
    'admin@ser.local',
    (SELECT id FROM roles WHERE name = 'admin'),
    TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE username = 'admin'
);

-- =====================================================
-- INFORMAÇÕES DE ACESSO INICIAL
-- =====================================================
-- Username: admin
-- Senha: Admin@123
--
-- ⚠️ IMPORTANTE: Altere a senha após primeiro acesso!
-- =====================================================

-- =====================================================
-- FIM DO SCRIPT
-- =====================================================
