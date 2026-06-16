# Ticket #301 — Ordenação nas listas + padronização de URLs (Clientes, Equipamentos, Tipos)

**Tipo:** Melhoria  
**Data da análise:** 2026-06-08  
**Status:** ✅ Implementado (2026-05-18)  

---

## Resumo executivo

As telas de **cadastros NR13** precisam de **ordenação por coluna** (clique no cabeçalho) e URLs **padronizadas** sem o prefixo `/nr13/` para equipamentos e tipos.

**Situação atual:**
- `/clientes` → `ClientesPage` (lista completa, sem ordenação clicável; ordem fixa `CLI_NOME` no backend).
- `/nr13/equipamentos` e `/nr13/tipos` → páginas paginadas (`Manut*Page`), sem ordenação clicável; ordem fixa no backend (`EQP_TAG`, `TEQP_NOME`).
- `/nr13/clientes` → `ManutClientesPage` existe mas **não está no menu** (sidebar aponta para `/clientes`).

**Resultado esperado:**
1. URLs: `/clientes`, `/equipamentos`, `/tipos` (com redirect dos paths legados `/nr13/*`).
2. Cabeçalhos de coluna clicáveis — ordenar por **qualquer campo** visível.
3. Coluna **ID** ordenada como **número** (não lexicográfica).

**Veredito:** **Pronto para desenvolvimento**, com decisão recomendada sobre unificação das duas telas de clientes e consolidação das APIs duplicadas.

---

## 0. Modelo de dados atual (atualização)

Tabelas legadas foram **removidas** (migration 015: `clientes`, `filiais`, `equipamentos`, `campos`). O sistema hoje persiste cadastros NR13 **somente** nestas três tabelas:

| Tabela física | PK | Modelo ORM (nome legado no código) | Uso |
|---------------|-----|-------------------------------------|-----|
| `tab_clientes` | `CLI_ID` | `ManutCliente` | Clientes; FK em `reports.cliente_id` |
| `tab_equipamentos` | `EQP_ID` | `ManutEquipamento` | Equipamentos; FK em `reports.equipamento_id` |
| `tab_tipos_equipamento` | `TEQP_ID` | `ManutTipoEquipamento` | Tipos; FK em `tab_equipamentos.EQP_TEQP_ID` |

**Views de lookup** (somente leitura, derivadas das `tab_*`):
- `vw_tab_clientes_lookup`
- `vw_tab_equipamentos_lookup`
- `vw_tab_tipos_equipamento_lookup`

**Implicação para o #301:** não há migração de schema. Ordenação e URLs atuam sobre essas três tabelas. Os nomes `Manut*` e o prefixo de API `/manut/*` são **legado** (época do cache SQL Server); a fonte de dados é única.

---

## 1. Entendimento e contexto

### Dor do usuário

Consultar listas grandes (~600 clientes) exige encontrar registros por ID ou outros campos; hoje a ordem é fixa e as URLs de equipamentos/tipos estão inconsistentes (`/nr13/...` vs `/clientes`).

### Mapa de rotas atual vs alvo

| Tela | URL hoje (menu/prod) | URL alvo | Componente | API |
|------|----------------------|----------|------------|-----|
| Clientes | `/clientes` | `/clientes` | `ClientesPage` | `GET /clientes` → `tab_clientes` |
| Clientes (legado) | `/nr13/clientes` | **redirect → `/clientes`** | `ManutClientesPage` | `GET /manut/clientes` → `tab_clientes` |
| Equipamentos | `/nr13/equipamentos` | `/equipamentos` | `ManutEquipamentosPage` | `GET /manut/equipamentos` → `tab_equipamentos` |
| Tipos | `/nr13/tipos` | `/tipos` | `ManutTiposPage` | `GET /manut/tipos-equipamento` → `tab_tipos_equipamento` |

> Existe também `GET /equipamentos` (sem paginação) sobre `tab_equipamentos`, hoje **não usado** pelas páginas de listagem NR13.

### Ordenação hoje (backend — fixa)

| Endpoint | Tabela | `order_by` atual |
|----------|--------|------------------|
| `GET /clientes` | `tab_clientes` | `CLI_NOME` |
| `GET /manut/clientes` | `tab_clientes` | `CLI_NOME` |
| `GET /manut/equipamentos` | `tab_equipamentos` | `EQP_TAG` |
| `GET /manut/tipos-equipamento` | `tab_tipos_equipamento` | `TEQP_NOME` |

Nenhuma tela expõe sort ao usuário.

---

## 2. Rastreabilidade de código

### Banco de dados

**Nenhuma alteração de schema.** Apenas as três tabelas `tab_*` listadas na seção 0. Colunas ID já são `INT` (`CLI_ID`, `EQP_ID`, `TEQP_ID`).

### Backend — alterar

| Arquivo | Tabela | Ação |
|---------|--------|------|
| `api/v1/clientes.py` | `tab_clientes` | `sort_by`, `sort_dir`; whitelist; `ORDER BY` dinâmico |
| `api/v1/manut_data.py` | `tab_clientes`, `tab_equipamentos`, `tab_tipos_equipamento` | Idem nos 3 endpoints paginados |
| `api/v1/equipamentos.py` | `tab_equipamentos` | Idem (se mantido; ou deprecar em favor de um único endpoint) |
| `models/manut_*.py` | — | Sem mudança de tabela; apenas referência ORM |
| **Novo** `core/list_sort.py` (sugerido) | — | Helper: whitelist + `asc`/`desc` |

**Consolidação recomendada:** como só existem as `tab_*`, evitar manter duas APIs para o mesmo recurso (`/clientes` vs `/manut/clientes`). Preferir evoluir `/clientes`, `/equipamentos` e criar `/tipos-equipamento` com paginação + sort; deprecar `/manut/*` nas telas.

Parâmetros sugeridos:

```python
sort_by: Optional[str] = Query(None, description="Campo para ordenação")
sort_dir: Literal["asc", "desc"] = Query("asc", description="Direção")
```

Whitelist por recurso (ex. clientes):

`CLI_ID`, `CLI_NOME`, `CLI_CNPJ`, `CLI_CONTATO`, `CLI_EMAIL`, `CLI_TELEFONE`, `CLI_CIDADE`, `CLI_ESTADO`, …

Campos **numéricos** na whitelist: usar coluna SQL diretamente (já inteiro).  
Campos texto nullable: `ORDER BY col IS NULL, col` para estabilidade.

### Frontend — alterar

| Arquivo | Ação |
|---------|------|
| `App.tsx` | Rotas `/equipamentos`, `/tipos`; `<Navigate>` de `/nr13/*` |
| `Sidebar.tsx` | Paths `/equipamentos`, `/tipos` |
| `lib/auth/permissions.ts` | Atualizar paths permitidos + redirects |
| `ClientesPage.tsx` | Cabeçalhos ordenáveis + params na API |
| `ManutEquipamentosPage.tsx` | Idem |
| `ManutTiposPage.tsx` | Idem |
| `lib/api/clientes.ts` | `sort_by`, `sort_dir` nos params |
| `lib/api/manut.ts` | Idem |
| **Novo** `components/ui/SortableTableHead.tsx` ou `hooks/useTableSort.ts` | Padrão reutilizável (ícone ▲▼, toggle asc/desc) |

### Reaproveitamento

- Paginação e busca já existem em `Manut*Page` e `manut_data.py`.
- `ClientesPage` e `ManutClientesPage` são **duplicatas funcionais** — unificar em `/clientes` (ver seção 4).

### Fora de escopo

- Recriar tabelas antigas (`clientes`, `filiais`, `equipamentos`).
- `ManutClientesPage` como rota principal (deprecar após unificação).
- Ordenação em `ReportListPage`, formulários, lookup (`vw_tab_*_lookup`).
- Renomear modelos `Manut*` no código (opcional, não bloqueia o ticket).

---

## 3. Análise de impacto e regressão

### Riscos

| Risco | Mitigação |
|-------|-----------|
| Bookmarks `/nr13/equipamentos` | Redirect 301/replace no React Router |
| `?cliente_id=` em equipamentos | Manter query string em `/equipamentos?cliente_id=` |
| Sort em coluna não indexada | Aceitável no volume atual; monitorar |
| SQL injection via `sort_by` | **Whitelist estrita** — nunca passar string livre ao SQL |
| Duas telas de clientes | Unificar comportamento (paginação + modal opcional) |

### Re-teste

- Menu CADASTROS NR13 — links corretos
- Suporte e Admin acessam as três listas
- Busca + paginação + sort juntos (equipamentos/tipos)
- Sort por **ID** numérico: 2 antes 10 antes 100
- Redirects `/nr13/equipamentos` → `/equipamentos`, `/nr13/tipos` → `/tipos`

---

## 4. Lacunas e checklist de esclarecimento

| # | Pergunta | Recomendação |
|---|----------|--------------|
| 1 | Unificar `ClientesPage` e `ManutClientesPage`? | **Sim** — uma tela em `/clientes`; absorver paginação/modal de `ManutClientesPage` ou adicionar sort na API `/clientes` |
| 2 | Sort **server-side** ou **client-side**? | **Server-side** em equipamentos/tipos (paginados); **client-side** aceitável em clientes se mantiver lista completa (~600); preferir **server-side** em todos por consistência |
| 3 | Ordenar **página atual** ou **dataset inteiro**? | **Dataset inteiro** via backend (sort antes de `offset/limit`) |
| 4 | Colunas de data (`CLI_DT_INS`)? | Incluir na whitelist como datetime |
| 5 | Terceiro clique no header? | Padrão: asc → desc → (opcional) remover sort / voltar default |
| 6 | Unificar APIs `/clientes` e `/manut/clientes`? | **Sim** — mesma tabela `tab_clientes`; uma API com paginação + sort |
| 7 | Permissão `manut` exige admin no backend | `Manut*Page` usa `SuporteRoute` mas API `require_admin` — **verificar** se Suporte recebe 403 (pré-existente; fora do escopo mas impacta teste) |

---

## 5. Segurança e performance

- **Segurança:** whitelist de `sort_by`; rejeitar campos desconhecidos com 422.
- **Performance:** `ORDER BY` + `LIMIT/OFFSET` em ~600–N registros é adequado; índices existentes em PKs/FKs ajudam em IDs.
- IDs como número: garantido no SQL; se houver sort client-side legado, usar `Number(a) - Number(b)`.

---

## 6. Sugestão de implementação

### Fase 1 — URLs (~1h)

1. `App.tsx`: rotas `equipamentos`, `tipos`; redirects:
   - `/nr13/equipamentos` → `/equipamentos`
   - `/nr13/tipos` → `/tipos`
   - `/nr13/clientes` → `/clientes`
2. `Sidebar.tsx` + `permissions.ts`: atualizar paths.

### Fase 2 — Backend sort (~2h)

1. Criar `apply_list_sort(statement, model, sort_by, sort_dir, allowed: dict[str, Column])`.
2. Aplicar em `list_clientes`, `list_manut_clientes`, `list_manut_equipamentos`, `list_manut_tipos_equipamento`.
3. Aplicar **`order_by` antes de `offset/limit`** (corrigir ordem atual em `manut_data.py` se necessário — hoje `order_by` está após `limit` em alguns trechos, o que é **bug**: ordena só a página).

**Correção importante detectada** em `manut_data.py`:

```python
# Hoje (incorreto para sort global):
statement = statement.offset(offset).limit(page_size)
statement = statement.order_by(...)  # ordena só os N da página

# Correto:
statement = statement.order_by(...)
statement = statement.offset(offset).limit(page_size)
```

Mesmo padrão em `/clientes` se ganhar paginação.

### Fase 3 — Frontend sort (~3h)

1. Hook `useTableSort({ defaultColumn: 'CLI_NOME', defaultDir: 'asc' })`.
2. Componente `SortableTh` — `onClick` alterna asc/desc; ícone de direção.
3. Incluir `sort_by` / `sort_dir` no `queryKey` do React Query.
4. Aplicar nas 3 páginas (e unificar clientes se decidido).

### Fase 4 — Unificação clientes (opcional, ~2h)

- Evoluir `ClientesPage` com paginação + modal “Ver” de `ManutClientesPage`.
- Remover rota/componente `ManutClientesPage` ou mantê-lo só como redirect.

**Estimativa total:** 1,5–2 dias.

---

## 7. Critérios de aceite

### URLs

- [ ] Menu e rotas usam `/clientes`, `/equipamentos`, `/tipos`.
- [ ] URLs antigas `/nr13/equipamentos`, `/nr13/tipos`, `/nr13/clientes` redirecionam.

### Ordenação

- [ ] Clique em qualquer coluna da tabela alterna ordenação asc/desc.
- [ ] Ordenação por **ID** respeita ordem numérica (ex.: 2, 10, 100).
- [ ] Ordenação afeta o **conjunto filtrado completo**, não só a página visível.
- [ ] Busca e paginação continuam funcionando com sort ativo.
- [ ] Indicador visual da coluna/direção ativa.

### Regressão

- [ ] Filtro `cliente_id` em equipamentos via query string.
- [ ] Permissões Suporte/Admin nas três telas.
- [ ] Modal/detalhes de cliente (se mantido após unificação).

---

## 8. Veredito de prontidão

| Critério | Status |
|----------|--------|
| Requisitos do prompt | ✅ |
| Código mapeado | ✅ |
| Bug `order_by` após `limit` identificado | ✅ |
| Conflito duas telas de clientes | ⚠️ Decisão recomendada (unificar) |
| **Pronto para desenvolvimento** | **Sim** |

---

## Anexo — Colunas ordenáveis sugeridas

### `tab_clientes` (modelo `ManutCliente`)

| Coluna UI | Campo / coluna | Tipo sort |
|-----------|----------------|-----------|
| ID | `CLI_ID` | **numérico** |
| Nome | `CLI_NOME` | texto |
| CNPJ | `CLI_CNPJ` | texto |
| Contato | `CLI_CONTATO` | texto |
| Telefone | `CLI_TELEFONE` | texto |
| Email | `CLI_EMAIL` | texto |
| Cidade/Estado | `CLI_CIDADE`, `CLI_ESTADO` | texto |

### `tab_equipamentos` (modelo `ManutEquipamento`)

| Coluna UI | Campo / coluna | Tipo sort |
|-----------|----------------|-----------|
| ID | `EQP_ID` | **numérico** |
| TAG | `EQP_TAG` | texto |
| Nome | `EQP_NOME` | texto |
| Nº Série | `EQP_NUMERO_SERIE` | texto |
| Área | `EQP_AREA` | texto |
| Cliente ID | `EQP_CLI_ID` (FK → `tab_clientes`) | **numérico** |
| Tipo ID | `EQP_TEQP_ID` (FK → `tab_tipos_equipamento`) | **numérico** |

### `tab_tipos_equipamento` (modelo `ManutTipoEquipamento`)

| Coluna UI | Campo / coluna | Tipo sort |
|-----------|----------------|-----------|
| ID | `TEQP_ID` | **numérico** |
| Nome | `TEQP_NOME` | texto |
| Venc. calibração | `TEQP_VENC_CALIBRACAO` | **numérico** |
