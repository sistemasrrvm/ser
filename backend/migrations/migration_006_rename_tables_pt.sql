-- ========================================
-- Migration 006: Renomear tabelas e campos para português
-- Data: 2025-11-14
-- ========================================

-- Desabilitar verificação de foreign keys temporariamente
PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- ========================================
-- 1. RENOMEAR TABELA form_fields → formularios_campos
-- ========================================

-- Criar nova tabela com nomes em português
CREATE TABLE IF NOT EXISTS formularios_campos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pagina_id INTEGER NOT NULL,
    rotulo VARCHAR(100) NOT NULL,
    ordem INTEGER NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    configuracao JSON NOT NULL,
    regra_exibicao_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pagina_id) REFERENCES formularios_paginas(id) ON DELETE CASCADE,
    FOREIGN KEY (regra_exibicao_id) REFERENCES show_when_rules(id) ON DELETE SET NULL
);

-- Copiar dados da tabela antiga para nova
INSERT INTO formularios_campos (
    id, pagina_id, rotulo, ordem, tipo, configuracao, regra_exibicao_id, created_at, updated_at
)
SELECT
    id, form_page_id, label, ordem, type, config, show_when_rule_id, created_at, updated_at
FROM form_fields;

-- Remover tabela antiga
DROP TABLE form_fields;

-- ========================================
-- 2. RENOMEAR TABELA form_pages → formularios_paginas
-- ========================================

-- Criar nova tabela com nomes em português
CREATE TABLE IF NOT EXISTS formularios_paginas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formulario_id INTEGER NOT NULL,
    nome VARCHAR(100) NOT NULL,
    ordem INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (formulario_id) REFERENCES form_templates(id) ON DELETE CASCADE
);

-- Copiar dados da tabela antiga para nova
INSERT INTO formularios_paginas (
    id, formulario_id, nome, ordem, created_at, updated_at
)
SELECT
    id, form_template_id, name, ordem, created_at, updated_at
FROM form_pages;

-- Remover tabela antiga
DROP TABLE form_pages;

-- ========================================
-- 3. CRIAR ÍNDICES
-- ========================================

CREATE INDEX IF NOT EXISTS idx_formularios_paginas_formulario_id ON formularios_paginas(formulario_id);
CREATE INDEX IF NOT EXISTS idx_formularios_paginas_ordem ON formularios_paginas(ordem);

CREATE INDEX IF NOT EXISTS idx_formularios_campos_pagina_id ON formularios_campos(pagina_id);
CREATE INDEX IF NOT EXISTS idx_formularios_campos_ordem ON formularios_campos(ordem);
CREATE INDEX IF NOT EXISTS idx_formularios_campos_tipo ON formularios_campos(tipo);

COMMIT;

-- Reabilitar verificação de foreign keys
PRAGMA foreign_keys = ON;

-- ========================================
-- VERIFICAÇÃO
-- ========================================

SELECT '✅ Migration 006 concluída com sucesso!' as status;
SELECT 'Tabelas renomeadas:' as info;
SELECT '  - form_pages → formularios_paginas' as tabela1;
SELECT '  - form_fields → formularios_campos' as tabela2;

SELECT COUNT(*) as total_paginas FROM formularios_paginas;
SELECT COUNT(*) as total_campos FROM formularios_campos;
