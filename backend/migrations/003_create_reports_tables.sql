-- Migration 003: Criar tabelas para módulo de Relatórios
-- Sprint 004 - Entrada de Dados

-- =======================================================
-- TABELAS AUXILIARES (Mock temporário - integração NR-13 futura)
-- =======================================================

-- Tabela: clientes
CREATE TABLE IF NOT EXISTS clientes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nome VARCHAR(200) NOT NULL,
    cnpj VARCHAR(18),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_clientes_codigo (codigo),
    INDEX idx_clientes_nome (nome),
    INDEX idx_clientes_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: filiais
CREATE TABLE IF NOT EXISTS filiais (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cliente_id BIGINT NOT NULL,
    codigo VARCHAR(50) NOT NULL,
    nome VARCHAR(200) NOT NULL,
    cidade VARCHAR(100),
    estado VARCHAR(2),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_filiais_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES clientes(id)
        ON DELETE CASCADE,

    UNIQUE KEY uk_filial (cliente_id, codigo),
    INDEX idx_filiais_cliente (cliente_id),
    INDEX idx_filiais_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: equipamentos
CREATE TABLE IF NOT EXISTS equipamentos (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    filial_id BIGINT NOT NULL,
    codigo VARCHAR(50) NOT NULL,
    nome VARCHAR(200) NOT NULL,
    tipo VARCHAR(100),
    fabricante VARCHAR(100),
    modelo VARCHAR(100),
    numero_serie VARCHAR(100),
    ano_fabricacao INT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_equipamentos_filial
        FOREIGN KEY (filial_id)
        REFERENCES filiais(id)
        ON DELETE CASCADE,

    UNIQUE KEY uk_equipamento (filial_id, codigo),
    INDEX idx_equipamentos_filial (filial_id),
    INDEX idx_equipamentos_tipo (tipo),
    INDEX idx_equipamentos_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =======================================================
-- TABELA PRINCIPAL: RELATÓRIOS
-- =======================================================

-- Tabela: reports
-- Armazena relatórios de inspeção preenchidos pelos técnicos
CREATE TABLE IF NOT EXISTS reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    numero VARCHAR(50) NOT NULL UNIQUE,
    form_template_id BIGINT NOT NULL,
    cliente_id BIGINT NOT NULL,
    filial_id BIGINT NOT NULL,
    equipamento_id BIGINT NOT NULL,
    tipo_inspecao VARCHAR(100) NOT NULL,
    tecnico_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'rascunho',
    respostas JSON NOT NULL,
    observacoes TEXT,
    data_inspecao DATE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign keys
    CONSTRAINT fk_reports_template
        FOREIGN KEY (form_template_id)
        REFERENCES formularios(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_reports_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES clientes(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_reports_filial
        FOREIGN KEY (filial_id)
        REFERENCES filiais(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_reports_equipamento
        FOREIGN KEY (equipamento_id)
        REFERENCES equipamentos(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_reports_tecnico
        FOREIGN KEY (tecnico_id)
        REFERENCES users(id)
        ON DELETE RESTRICT,

    -- Constraints
    CONSTRAINT chk_reports_status
        CHECK (status IN ('rascunho', 'em_revisao', 'aprovado', 'cancelado')),

    -- Indexes
    INDEX idx_reports_numero (numero),
    INDEX idx_reports_cliente (cliente_id),
    INDEX idx_reports_filial (filial_id),
    INDEX idx_reports_equipamento (equipamento_id),
    INDEX idx_reports_tecnico (tecnico_id),
    INDEX idx_reports_status (status),
    INDEX idx_reports_tipo_inspecao (tipo_inspecao),
    INDEX idx_reports_data_inspecao (data_inspecao),
    INDEX idx_reports_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
