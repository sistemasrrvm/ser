# Ticket #304 — Campos numéricos exportados como texto no Excel

**Tipo:** Bug  
**Data da análise:** 2026-05-18  
**Status:** ✅ Corrigido (2026-05-18) — inclui fix de regressões (formato OOXML + preservação de assets)  

---

## Resumo executivo

Na exportação de relatórios para Excel (e PDF, que reutiliza o mesmo preenchimento), campos do tipo **`number`** com decimais estão sendo gravados como **texto** — no Excel aparecem com **aspas** no início (`'12,5`) e não participam de fórmulas/somas.

**Causa raiz:** em `reports.py`, apenas `date`, `yes_no` e `lookup` têm formatação específica; `number` cai no `else` e usa `str(field_value)`, que o openpyxl persiste como string.

**Resultado esperado:**
1. Campos `number` exportados como **tipo numérico** no Excel (sem aspas, sem forçar texto).
2. Formato de exibição **pt-BR**: separador decimal **vírgula** na UI do Excel (ex.: `8,6`), via locale + código OOXML com **ponto** (`0.0`, `0.00`).
3. Template preserva **logotipo/imagens** e abre **sem dialog de reparo**.

**Veredito:** **Concluído** — correção na exportação + zip merge para assets do template.

---

## Regressões pós-implementação inicial (REL-2026-000009)

| Sintoma | Causa | Correção |
|---------|-------|----------|
| Excel pede reparo (`externalLink2.xml`, `drawing*.xml`) | `openpyxl` descarta `xl/drawings/`, `xl/media/`, `xl/externalLinks/` no `save()` | `excel_template_preserve.py` — merge zip após save |
| Logotipo sumiu | Mesma causa | Restauração de `xl/media/` e rels de drawing |
| Números como "Personalizado" / `09` em vez de `8,6` | `number_format_pt_br` usava `"0,00"` — no OOXML vírgula = milhar | `number_format_ooxml` com ponto; preservar formato do template quando válido |
| Excel ainda pede reparo (2ª rodada) | openpyxl remove `<drawing>` das planilhas e pastas `printerSettings`/`embeddings`; rels ficam órfãs | `excel_template_preserve.py` ampliado: copia todas as partes referenciadas + `_sync_drawing_elements_from_rels` |

---

## 1. Entendimento e contexto

### Dor do usuário

Após preencher o relatório e exportar para Excel, valores numéricos decimais não podem ser usados em cálculos do template (SOMA, médias, etc.) porque o Excel os trata como texto.

### Fluxo afetado

```
ReportWizard (campo number) → reports.respostas (JSON)
    → GET /reports/{id}/export-excel
    → openpyxl preenche células do template (excel_mapping)
```

O mesmo bloco de preenchimento é **duplicado** em `export-pdf` (antes da conversão para PDF).

### Como o valor é armazenado hoje

| Origem | Formato em `respostas` |
|--------|-------------------------|
| `<Input type="number">` no wizard | String com **ponto** decimal (`"12.5"`) |
| Entrada manual / legado | Pode vir com **vírgula** (`"12,5"`) |
| Inteiro | `"100"` ou `100` |

Configuração do campo (`formularios_campos.configuracao`):

```json
{
  "decimal_places": 2,
  "min_value": null,
  "max_value": null,
  "excel_mapping": [{ "planilha": "Dados", "celula": "B10" }]
}
```

---

## 2. Rastreabilidade de código

### Banco de dados

**Nenhuma alteração.** Valores em `reports.respostas` (JSON) permanecem como estão.

| Tabela | Campo | Uso |
|--------|-------|-----|
| `reports` | `respostas` | Valores dos campos (`campo_{id}`) |
| `formularios_campos` | `tipo`, `configuracao` | `number`, `decimal_places`, `excel_mapping` |

### Backend — alterar

| Arquivo | Trecho | Problema / fix |
|---------|--------|----------------|
| `services/report_excel_export.py` | `apply_number_to_cell` | Formato OOXML com ponto; preserva `number_format` do template |
| `services/excel_template_preserve.py` | **Novo** | Merge zip para restaurar drawings/media/externalLinks |
| `api/v1/reports.py` | `export_report_to_excel` | Usa `save_workbook_preserving_template_assets` |
| `api/v1/reports.py` | `export_report_to_pdf` | Usa `fill_workbook_from_report` (sem zip merge — PDF não renderiza imagens) |

**Código atual (bug):**

```python
elif field.tipo == "lookup":
    value_to_write = _format_lookup_for_export(...)
else:
    value_to_write = str(field_value) if field_value is not None else ""

sheet[celula] = value_to_write
```

### Backend — criar (recomendado)

| Arquivo | Conteúdo |
|---------|----------|
| `services/report_excel_export.py` (ou helpers em `reports.py`) | `_parse_number_value`, `_write_field_to_cell` |
| Funções | Parse BR/US, atribuição numérica + `number_format` |

**Lógica sugerida para `number`:**

```python
def number_format_ooxml(decimal_places: int) -> str:
    # OOXML: ponto = decimal. Excel pt-BR exibe vírgula no locale.
    if decimal_places <= 0:
        return "0"
    return "0." + ("0" * decimal_places)

def apply_number_to_cell(cell, field_value, configuracao):
    # Grava int/float; preserva number_format do template se já numérico
    ...
```

> **Nota:** Não usar `"0,00"` no `number_format` — vírgula no OOXML é separador de milhar e gera formato "Personalizado" inválido.

### Frontend — alterar

**Nenhuma alteração obrigatória** para corrigir o bug (correção no backend na exportação).

Opcional futuro: input numérico com máscara pt-BR no wizard — fora do escopo deste ticket.

### Reaproveitamento

| Existente | Reuso |
|-----------|-------|
| `_format_date_for_excel` | Padrão de formatação por `field.tipo` |
| `_format_yes_no_for_export` | Idem |
| `field.configuracao.decimal_places` | Já usado no wizard (`step` do input) |

---

## 3. Análise de impacto e regressão

### Riscos

| Risco | Mitigação |
|-------|-----------|
| Parse incorreto `1.234,56` vs `1,234.56` | Heurística: se há `.` e `,`, o **último** separador é o decimal |
| `textbox` com conteúdo numérico | Não alterar — só `field.tipo == "number"` |
| Template com célula pré-formatada como texto | Sobrescrever com valor numérico + `number_format` |
| PDF divergir do Excel | Aplicar mesma função nos dois exports |
| Valor inválido (`"abc"`) | Manter string original ou célula vazia + log (definir na implementação) |

### Re-teste

- Exportar relatório com campos `number` inteiros e decimais
- Abrir no Excel: sem aspas na barra de fórmulas; tipo = número
- Fórmula `=SOMA(...)` inclui os valores
- Exibição com vírgula (`12,5` não `12.5`) em locale pt-BR
- Campos `date`, `yes_no`, `lookup`, `textbox` inalterados
- Export PDF continua gerando arquivo
- Relatórios antigos com valores já salvos como `"3,14"` ou `"3.14"`

---

## 4. Lacunas e checklist de esclarecimento

| # | Pergunta | Recomendação |
|---|----------|--------------|
| 1 | Valor inválido na exportação? | Célula vazia + log (não quebrar export inteiro) |
| 2 | `decimal_places` ausente no config? | Default `0` (inteiro), alinhado ao `DEFAULT_CONFIGS` do frontend |
| 3 | Separador de milhar na exibição? | Formato `#.##0,00` se `abs(num) >= 1000`; senão `0,00` |
| 4 | Unificar blocos excel + pdf? | **Sim** — extrair `_fill_workbook_from_report(...)` para evitar regressão futura |
| 5 | Campo `grid` com números? | Tipo `grid` ainda não implementado no wizard — fora de escopo |

---

## 5. Segurança e performance

- **Segurança:** sem impacto; mesmos dados já acessíveis na exportação.
- **Performance:** parse numérico por célula mapeada — custo desprezível frente ao `load_workbook`.

---

## 6. Sugestão de implementação

### Fase 1 — Helpers (~1h)

1. Criar `_parse_number_value(value) -> float | None`.
2. Criar `_write_excel_cell(sheet, celula, field, field_value, session)` centralizando:
   - `date` → string formatada (atual)
   - `yes_no` → string (atual)
   - `lookup` → string (atual)
   - **`number` → valor numérico + `number_format` pt-BR**
   - demais → string (atual)

### Fase 2 — Aplicar nos exports (~1h)

1. Substituir bloco duplicado em `export_report_to_excel`.
2. Substituir bloco duplicado em `export_report_to_pdf`.

### Fase 3 — Testes manuais (~30min)

1. Formulário com campo `number` (`decimal_places: 2`) mapeado para célula.
2. Relatório com valor `12.5` → Excel mostra `12,50` como número.
3. `=SOMA(B10:B20)` funciona.

**Estimativa total:** 0,5 dia.

---

## 7. Critérios de aceite

### Funcional

- [x] Campo `number` exportado como **número** no Excel (sem prefixo `'` / tipo texto).
- [x] Decimais exibidos com **vírgula** em locale pt-BR (código OOXML com ponto).
- [x] Casas decimais inferidas do **valor salvo** (`"8.6"` → 1 casa, `"8.06"` → 2).
- [x] Inteiros exportados sem parte fracionária forçada.
- [x] Template abre sem reparo; logotipo/imagens preservados.

### Regressão

- [x] Exportação Excel/PDF de outros tipos de campo inalterada.
- [x] Relatórios sem `excel_mapping` em campos number não quebram export.
- [x] Template sem campo number configurado continua exportando normalmente.

---

## 8. Veredito de prontidão

| Critério | Status |
|----------|--------|
| Causa raiz identificada | ✅ `str()` no branch `else` |
| Arquivos mapeados | ✅ `reports.py` (2 endpoints) |
| Migração de dados | ✅ Não necessária |
| **Pronto para desenvolvimento** | **Sim** |

---

## Anexo — Comparação antes/depois

| Valor em `respostas` | Hoje (Excel) | Esperado |
|----------------------|--------------|----------|
| `"12.5"` | Texto `'12.5` | Número `12,50` |
| `"12,5"` | Texto `'12,5` | Número `12,50` |
| `"100"` | Texto `'100` | Número `100` |
| `12.5` (float JSON) | Texto `'12.5` | Número `12,50` |
