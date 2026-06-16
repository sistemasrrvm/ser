-- Migration 002: Criar tabelas form_pages e form_fields
-- Tabelas para o sistema de construtor de formulários dinâmicos

-- Tabela: form_pages
-- Representa páginas dentro de um formulário (tabs)
CREATE TABLE IF NOT EXISTS form_pages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    form_template_id BIGINT NOT NULL,
    label VARCHAR(100) NOT NULL,
    ordem INT NOT NULL,
    show_when_rule_id BIGINT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign keys
    CONSTRAINT fk_form_pages_formulario
        FOREIGN KEY (form_template_id)
        REFERENCES formularios(id)
        ON DELETE CASCADE,

    -- Indexes
    INDEX idx_form_pages_template (form_template_id),
    INDEX idx_form_pages_ordem (ordem),
    INDEX idx_form_pages_label (label)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: form_fields
-- Representa campos dentro de uma página
CREATE TABLE IF NOT EXISTS form_fields (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    form_page_id BIGINT NOT NULL,
    label VARCHAR(100) NOT NULL,
    ordem INT NOT NULL,
    type VARCHAR(20) NOT NULL,
    config JSON NULL,
    show_when_rule_id BIGINT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign keys
    CONSTRAINT fk_form_fields_page
        FOREIGN KEY (form_page_id)
        REFERENCES form_pages(id)
        ON DELETE CASCADE,

    -- Indexes
    INDEX idx_form_fields_page (form_page_id),
    INDEX idx_form_fields_ordem (ordem),
    INDEX idx_form_fields_type (type),
    INDEX idx_form_fields_label (label)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
