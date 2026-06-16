-- Migration 012: Criar Tabela configuracoes
-- Data: 2025-11-17
-- Objetivo: Armazenar configurações do sistema, incluindo views homologadas para Lookup

-- Criar tabela configuracoes
CREATE TABLE IF NOT EXISTS `configuracoes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `chave` VARCHAR(100) NOT NULL COMMENT 'Chave única da configuração',
  `valor` TEXT COMMENT 'Valor da configuração (pode ser texto, número ou JSON)',
  `tipo` ENUM('texto','numero','json','boolean') NOT NULL DEFAULT 'texto',
  `descricao` VARCHAR(255) DEFAULT NULL COMMENT 'Descrição da configuração',
  `categoria` VARCHAR(100) DEFAULT 'geral' COMMENT 'Categoria para agrupar configurações',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `chave` (`chave`),
  KEY `idx_chave` (`chave`),
  KEY `idx_categoria` (`categoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Inserir configuração de views homologadas para Lookup
INSERT INTO configuracoes (chave, valor, tipo, descricao, categoria)
VALUES (
  'lookup_views',
  '{
    "views": [
      {
        "value": "vw_tab_clientes_lookup",
        "label": "Clientes (NR13)",
        "description": "View de lookup para clientes NR13"
      },
      {
        "value": "vw_tab_equipamentos_lookup",
        "label": "Equipamentos (NR13)",
        "description": "View de lookup para equipamentos NR13"
      },
      {
        "value": "vw_tab_tipos_equipamento_lookup",
        "label": "Tipos de Equipamento (NR13)",
        "description": "View de lookup para tipos de equipamento NR13"
      }
    ]
  }',
  'json',
  'Lista de views homologadas para uso em campos Lookup',
  'sistema'
);

-- Verificar tabela criada
SELECT 'Migration 012 concluida: Tabela configuracoes criada e populada' AS status;
