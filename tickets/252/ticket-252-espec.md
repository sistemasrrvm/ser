# Ticket #252 — Especificação Técnica e Análise de Impacto

**Tipo:** Melhoria  
**Data da análise:** 2026-05-18  
**Referência:** [Dashboard produção](https://laudonr13-frontend-prod.up.railway.app/dashboard)

> Cópia espelhada em `t:\tickets\252\ticket-252-espec.md`

---

## Resumo executivo

A demanda pede **renomear os rótulos exibidos ao usuário** para o ciclo de vida do relatório e **separar no dashboard** o totalizador agregado "Em Andamento" em dois cards distintos: **Em Elaboração** e **Em Revisão**.

No código atual, o fluxo funcional **já existe**:

| Momento | Valor no banco (`reports.status`) | Label atual na UI |
|---------|-----------------------------------|-------------------|
| Relatório criado / em preenchimento | `rascunho` | "Rascunho" |
| Após botão **Finalizar** no wizard | `em_revisao` | "Em Revisão" |
| Aprovado | `aprovado` | "Concluído" / "Aprovado" (inconsistente) |
| Cancelado | `cancelado` | "Cancelado" |

A mudança é predominantemente de **apresentação (labels + dashboard)**. **Não é obrigatório** alterar valores persistidos (`rascunho`, `em_revisao`) nem schema do banco, desde que a equipe concorde em manter os códigos internos e mudar apenas o texto exibido.

---

## 1. Entendimento e contexto

### Dor do usuário

- O termo **"Rascunho"** não reflete o negócio: o documento está **em elaboração** (preenchimento ativo).
- O dashboard agrupa `rascunho` + `em_revisao` em um único card **"Em Andamento"**, impedindo visão rápida de quantos relatórios estão em cada fase.

### Onde encaixa no sistema

- **Módulo:** Relatórios (wizard de preenchimento, listagem, dashboard).
- **Entidade central:** tabela `reports`, coluna `status` (VARCHAR, CHECK com 4 valores).
- **Transição crítica:** `ReportWizardPage` → `reportsApi.updateStatus(..., { status: 'em_revisao' })` ao finalizar (já implementado em `backend/src/api/v1/reports.py`).

---

## 2. Rastreabilidade de código

### Banco de dados

| Artefato | Impacto |
|----------|---------|
| Tabela `reports` | Coluna `status` — **sem alteração** se mantiver códigos `rascunho` / `em_revisao` |
| `backend/migrations/003_create_reports_tables.sql` | CHECK `('rascunho', 'em_revisao', 'aprovado', 'cancelado')` — referência histórica apenas |

### Backend (regras de negócio — manter códigos)

| Arquivo | Papel |
|---------|--------|
| `backend/src/models/report.py` | Default `status="rascunho"` |
| `backend/src/schemas/report.py` | `ReportStatusUpdate` — pattern dos 4 status |
| `backend/src/api/v1/reports.py` | CRUD, transição inspetor `rascunho` → `em_revisao`, edição permitida em `rascunho` e `em_revisao` |

**Reaproveitamento:** toda a máquina de estados permanece; apenas mensagens de erro em português que citam "rascunho" podem ser alinhadas ao novo vocabulário (opcional, baixa prioridade).

### Frontend (principal impacto)

| Arquivo | O que alterar |
|---------|----------------|
| `frontend/src/app/routes/DashboardPage.tsx` | `getStatusLabel`: `rascunho` → **"Em Elaboração"**; remover card "Em Andamento"; adicionar cards **Em Elaboração** e **Em Revisão**; ajustar grid (5 cards) |
| `frontend/src/app/routes/ReportWizardPage.tsx` | Badge do header: "Rascunho" → **"Em Elaboração"**; botões "Salvar Rascunho" → avaliar **"Salvar"** ou **"Salvar elaboração"** |
| `frontend/src/app/routes/ReportListPage.tsx` | Options do `<select>` e texto da badge (`report.status.replace` → usar mapa centralizado) |
| `frontend/src/lib/api/reports.ts` | Tipos union — **sem mudança** nos literais |

### Função similar a reaproveitar

**Recomendação:** criar utilitário único `frontend/src/lib/reports/statusLabels.ts` e substituir mapas locais em `DashboardPage`, `ReportWizardPage`, `ReportListPage`.

---

## 3. Análise de impacto e regressão

### Telas / fluxos para re-teste

| Área | Risco |
|------|-------|
| Dashboard — cards e lista recente | Médio — layout com 5 cards; labels na lista recente |
| `/relatorios` — filtro e tabela | Médio — filtro ainda envia `rascunho`/`em_revisao` (correto); label do option deve mudar |
| `/relatorios/:id/preencher` — finalizar | Baixo — transição `em_revisao` inalterada |
| Permissões inspetor (finalizar só em rascunho) | Baixo — lógica usa código, não label |
| Export Excel/PDF | Baixo — regras por código `em_revisao` / `aprovado` |

### Inconsistências atuais (corrigir na mesma entrega, se possível)

- Dashboard: `aprovado` → **"Concluído"**; Wizard: **"Aprovado"**.
- `ReportListPage`: exibe `report.status.replace('_', ' ')` em vez de label amigável.

### Limitação conhecida do dashboard

Estatísticas usam `reportsApi.list({ limit: 100 })` — totais podem estar **subestimados** se houver mais de 100 relatórios. Fora do escopo do #252.

---

## 4. Lacunas e exceções

| # | Pergunta | Recomendação |
|---|----------|--------------|
| 1 | Renomear só UI ou também valor no BD? | **Manter `rascunho`** no BD |
---> só na ui

| 2 | Texto "Salvar Rascunho"? | Definir com negócio |
---> pode manter

| 3 | `aprovado`: "Aprovado" ou "Concluído"? | Padronizar |
---> aprovado

| 4 | `cancelado` no dashboard? | Manter fora dos novos cards |
---> manter como está

| 5 | Reversão `em_revisao` → `rascunho`? | Só admin na API hoje |
---> manter como está


---

## 5. Segurança e performance

- **Segurança:** sem impacto em RBAC.
- **Performance:** impacto irrelevante (contagens em memória).
- **Migration:** desnecessária se mantiver códigos.

---

## 6. Sugestão de implementação

1. Criar `statusLabels.ts` centralizado.
2. `DashboardPage`: dois cards + labels; grid 5 colunas.
3. `ReportWizardPage` e `ReportListPage`: usar helper.
4. (Opcional) Ajustar mensagens de erro no backend.

**Estimativa:** 2–4 h frontend.

---

## 7. Critérios de aceite

- [ ] Status em preenchimento: **"Em Elaboração"** (BD: `rascunho`).
- [ ] Após Finalizar: **"Em Revisão"** (BD: `em_revisao`).
- [ ] Dashboard: cards **Em Elaboração** e **Em Revisão**; sem **Em Andamento**.
- [ ] Filtros e permissões de inspetor intactos.

---

## 8. Veredito de prontidão

**Sim** — pronto para desenvolvimento, com decisões menores de copy (botões e "Concluído").

---

Documento completo: `t:\tickets\252\ticket-252-espec.md`
