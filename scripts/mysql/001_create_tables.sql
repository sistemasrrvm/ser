-- =====================================================
-- SER - Sistema de Emissão de Relatórios
-- Script de Criação de Tabelas
-- Banco: MySQL
-- Data: 2025-10-29
-- =====================================================

USE db_a2cb65_laudonr;

-- =====================================================
-- TABELA: roles
-- Descrição: Perfis de acesso do sistema
-- =====================================================
CREATE TABLE IF NOT EXISTS roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL COMMENT 'Nome do role (admin, revisor, usuario)',
    level INT NOT NULL COMMENT 'Nível hierárquico (100=admin, 40=revisor, 20=usuario)',
    description VARCHAR(255) COMMENT 'Descrição do role',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_level (level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: users
-- Descrição: Usuários do sistema
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT 'Nome de usuário para login',
    password_hash VARCHAR(255) NOT NULL COMMENT 'Hash Argon2 da senha',
    full_name VARCHAR(100) NOT NULL COMMENT 'Nome completo do usuário',
    email VARCHAR(100) UNIQUE COMMENT 'Email do usuário (para recuperação de senha)',
    role_id BIGINT NOT NULL COMMENT 'Role do usuário',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Usuário ativo/inativo',
    last_login DATETIME COMMENT 'Último login do usuário',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: password_reset_tokens
-- Descrição: Tokens para recuperação de senha
-- =====================================================
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT 'Usuário que solicitou recuperação',
    token VARCHAR(255) UNIQUE NOT NULL COMMENT 'Token único temporário',
    expires_at DATETIME NOT NULL COMMENT 'Data/hora de expiração (1 hora)',
    used BOOLEAN DEFAULT FALSE COMMENT 'Token já foi utilizado?',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_expires (expires_at),
    INDEX idx_user_used (user_id, used)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: refresh_tokens
-- Descrição: Tokens de refresh (manter conectado)
-- =====================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT 'Usuário proprietário do token',
    token VARCHAR(500) UNIQUE NOT NULL COMMENT 'Refresh token (JWT)',
    expires_at DATETIME NOT NULL COMMENT 'Data/hora de expiração (7 dias)',
    revoked BOOLEAN DEFAULT FALSE COMMENT 'Token revogado?',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token(255)),
    INDEX idx_user_active (user_id, revoked)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: formularios
-- Descrição: Cadastro de formulários (templates)
-- =====================================================
CREATE TABLE IF NOT EXISTS formularios (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL COMMENT 'Nome do formulário',
    descricao VARCHAR(500) COMMENT 'Descrição do formulário',
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    criado_por BIGINT NOT NULL COMMENT 'Usuário que criou',
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    atualizado_por BIGINT COMMENT 'Último usuário que atualizou',
    FOREIGN KEY (criado_por) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (atualizado_por) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_nome (nome),
    INDEX idx_criado_por (criado_por)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: campos (NÃO USADA - removida)
-- Descrição: Campos das páginas - Tabela antiga, não mais utilizada
--            Substituída por formularios_paginas e formularios_campos
-- =====================================================
-- Tabela campos foi removida - não está mais em uso

-- =====================================================
-- TABELA: show_when_rules
-- Descrição: Regras de visibilidade reutilizáveis (futuro - Sprint 002)
-- =====================================================
CREATE TABLE IF NOT EXISTS show_when_rules (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL UNIQUE COMMENT 'Nome único da regra',
    descricao TEXT COMMENT 'Descrição da regra',
    logica_agrupamento ENUM('AND','OR') DEFAULT 'AND' COMMENT 'Lógica entre condições',
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    criado_por BIGINT NOT NULL COMMENT 'Usuário criador',
    FOREIGN KEY (criado_por) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: show_when_conditions
-- Descrição: Condições das regras de visibilidade (futuro - Sprint 002)
-- =====================================================
CREATE TABLE IF NOT EXISTS show_when_conditions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    show_when_rule_id BIGINT NOT NULL COMMENT 'Regra pai',
    campo_origem_id BIGINT NOT NULL COMMENT 'Campo a ser avaliado (formularios_campos.id)',
    operador ENUM(
        'is','is not','>','>=','<','<=',
        'is filled out','is not filled out',
        'is positive','is positive or zero','is negative'
    ) NOT NULL COMMENT 'Operador da condição',
    valor_comparacao_tipo ENUM('FIXO','CAMPO') NOT NULL COMMENT 'Tipo de comparação',
    valor_fixo TEXT COMMENT 'Valor fixo para comparação',
    campo_comparacao_id BIGINT COMMENT 'Campo para comparação (formularios_campos.id)',
    FOREIGN KEY (show_when_rule_id) REFERENCES show_when_rules(id) ON DELETE CASCADE,
    -- FOREIGN KEY (campo_origem_id) REFERENCES formularios_campos(id) ON DELETE RESTRICT,
    -- FOREIGN KEY (campo_comparacao_id) REFERENCES formularios_campos(id) ON DELETE RESTRICT,
    -- Nota: FKs comentadas porque campos referenciam formularios_campos, não a tabela antiga 'campos'
    INDEX idx_rule (show_when_rule_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- FIM DO SCRIPT
-- =====================================================
