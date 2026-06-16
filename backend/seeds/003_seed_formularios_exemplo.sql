-- ========================================
-- Seed: Formulário de Exemplo
-- Sprint 003 - CRUD Páginas e Campos Básicos
-- ========================================
--
-- Este script cria um formulário de exemplo completo:
-- - 1 formulário: "Cadastro de Cliente"
-- - 3 páginas: "Dados Básicos", "Endereço", "Informações Adicionais"
-- - 10 campos de tipos variados (Textbox, Date)
--
-- IMPORTANTE: Execute este script APÓS ter um usuário admin criado
-- O script assume que existe um usuário com id = 1
-- ========================================

-- Limpar dados anteriores (se existirem)
DELETE FROM form_fields WHERE form_page_id IN (
    SELECT id FROM form_pages WHERE form_template_id IN (
        SELECT id FROM formularios WHERE nome = 'Cadastro de Cliente'
    )
);

DELETE FROM form_pages WHERE form_template_id IN (
    SELECT id FROM formularios WHERE nome = 'Cadastro de Cliente'
);

DELETE FROM formularios WHERE nome = 'Cadastro de Cliente';

-- ========================================
-- FORMULÁRIO
-- ========================================

INSERT INTO formularios (nome, descricao, criado_em, criado_por, atualizado_em, atualizado_por)
VALUES (
    'Cadastro de Cliente',
    'Formulário completo para cadastro de novos clientes com validações',
    NOW(),
    1,  -- Assumindo usuário admin com id = 1
    NOW(),
    1
);

-- Capturar ID do formulário criado
SET @form_id = LAST_INSERT_ID();

-- ========================================
-- PÁGINA 1: Dados Básicos
-- ========================================

INSERT INTO form_pages (form_template_id, label, ordem, show_when_rule_id, created_at, updated_at)
VALUES (
    @form_id,
    'Dados Básicos',
    1,
    NULL,
    NOW(),
    NOW()
);

SET @page1_id = LAST_INSERT_ID();

-- Campos da Página 1
INSERT INTO form_fields (form_page_id, label, ordem, type, config, show_when_rule_id, created_at, updated_at)
VALUES
    (
        @page1_id,
        'Nome Completo',
        1,
        'textbox',
        JSON_OBJECT(
            'format_validation', 'none',
            'min_characters', 3,
            'max_characters', 100,
            'require', true,
            'read_only', false,
            'unique', false
        ),
        NULL,
        NOW(),
        NOW()
    ),
    (
        @page1_id,
        'CPF',
        2,
        'textbox',
        JSON_OBJECT(
            'format_validation', 'cpf',
            'min_characters', 11,
            'max_characters', 14,
            'require', true,
            'read_only', false,
            'unique', true
        ),
        NULL,
        NOW(),
        NOW()
    ),
    (
        @page1_id,
        'Data de Nascimento',
        3,
        'date',
        JSON_OBJECT(
            'type', 'date',
            'require', true,
            'read_only', false
        ),
        NULL,
        NOW(),
        NOW()
    ),
    (
        @page1_id,
        'E-mail',
        4,
        'textbox',
        JSON_OBJECT(
            'format_validation', 'email',
            'min_characters', 5,
            'max_characters', 100,
            'require', true,
            'read_only', false,
            'unique', true
        ),
        NULL,
        NOW(),
        NOW()
    );

-- ========================================
-- PÁGINA 2: Endereço
-- ========================================

INSERT INTO form_pages (form_template_id, label, ordem, show_when_rule_id, created_at, updated_at)
VALUES (
    @form_id,
    'Endereço',
    2,
    NULL,
    NOW(),
    NOW()
);

SET @page2_id = LAST_INSERT_ID();

-- Campos da Página 2
INSERT INTO form_fields (form_page_id, label, ordem, type, config, show_when_rule_id, created_at, updated_at)
VALUES
    (
        @page2_id,
        'CEP',
        1,
        'textbox',
        JSON_OBJECT(
            'format_validation', 'cep',
            'min_characters', 8,
            'max_characters', 9,
            'require', true,
            'read_only', false,
            'unique', false
        ),
        NULL,
        NOW(),
        NOW()
    ),
    (
        @page2_id,
        'Rua',
        2,
        'textbox',
        JSON_OBJECT(
            'format_validation', 'none',
            'min_characters', 3,
            'max_characters', 200,
            'require', true,
            'read_only', false,
            'unique', false
        ),
        NULL,
        NOW(),
        NOW()
    ),
    (
        @page2_id,
        'Número',
        3,
        'textbox',
        JSON_OBJECT(
            'format_validation', 'none',
            'min_characters', 1,
            'max_characters', 10,
            'require', true,
            'read_only', false,
            'unique', false
        ),
        NULL,
        NOW(),
        NOW()
    ),
    (
        @page2_id,
        'Complemento',
        4,
        'textbox',
        JSON_OBJECT(
            'format_validation', 'none',
            'min_characters', 0,
            'max_characters', 100,
            'require', false,
            'read_only', false,
            'unique', false
        ),
        NULL,
        NOW(),
        NOW()
    );

-- ========================================
-- PÁGINA 3: Informações Adicionais
-- ========================================

INSERT INTO form_pages (form_template_id, label, ordem, show_when_rule_id, created_at, updated_at)
VALUES (
    @form_id,
    'Informações Adicionais',
    3,
    NULL,
    NOW(),
    NOW()
);

SET @page3_id = LAST_INSERT_ID();

-- Campos da Página 3
INSERT INTO form_fields (form_page_id, label, ordem, type, config, show_when_rule_id, created_at, updated_at)
VALUES
    (
        @page3_id,
        'Telefone',
        1,
        'textbox',
        JSON_OBJECT(
            'format_validation', 'phone',
            'min_characters', 10,
            'max_characters', 15,
            'require', true,
            'read_only', false,
            'unique', false
        ),
        NULL,
        NOW(),
        NOW()
    ),
    (
        @page3_id,
        'Observações',
        2,
        'textbox',
        JSON_OBJECT(
            'format_validation', 'none',
            'min_characters', 0,
            'max_characters', 500,
            'require', false,
            'read_only', false,
            'unique', false
        ),
        NULL,
        NOW(),
        NOW()
    );

-- ========================================
-- VERIFICAÇÃO
-- ========================================

-- Mostrar resultado
SELECT
    f.id AS form_id,
    f.nome AS formulario,
    COUNT(DISTINCT p.id) AS total_paginas,
    COUNT(c.id) AS total_campos
FROM formularios f
LEFT JOIN form_pages p ON p.form_template_id = f.id
LEFT JOIN form_fields c ON c.form_page_id = p.id
WHERE f.nome = 'Cadastro de Cliente'
GROUP BY f.id, f.nome;

SELECT
    p.id AS page_id,
    p.label AS pagina,
    p.ordem,
    COUNT(c.id) AS total_campos
FROM form_pages p
LEFT JOIN form_fields c ON c.form_page_id = p.id
WHERE p.form_template_id = @form_id
GROUP BY p.id, p.label, p.ordem
ORDER BY p.ordem;

-- ========================================
-- FIM
-- ========================================
