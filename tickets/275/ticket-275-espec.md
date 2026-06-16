# Ticket #275 — Revisitar funções liberadas e bloqueadas por status e perfil

**Tipo:** Melhoria  
**Fonte:** E-mail Qualidade RRVM (25/05/2026) + PDF `Sistema SER_14Mai2026---revisao-Breno.pdf`  
**Data da análise:** 2026-05-19  

---

## Resumo executivo

A Qualidade RRVM revisou a matriz de **permissões por perfil × status do relatório**. O sistema precisa alinhar **visualização, edição, exclusão, botões do wizard e dashboard** ao documento anexo, incorporando as **3 revisões do Breno** (destacadas em azul no PDF).

**Situação atual:** regras espalhadas em `reports.py` (nível numérico `< 50` vs `≥ 50`) e no frontend com flags simplificadas (`isSuporte` → export/salvar). Há **divergências graves** em relação ao PDF (Técnico edita após finalizar; Suporte vê rascunhos; Admin edita e exclui; exclusão liberada para Suporte/Admin).

**Tickets relacionados:** #268 (bloqueio pós-finalizar técnico), #244 (só Técnico cria relatório — **já implementado**), #246 (botões Aprovar/Reprovar em revisão — **ainda não implementado**).

**Veredito:** **Pronto para desenvolvimento**, com dependência do #246 para fluxo completo de aprovação.

---

## 1. Entendimento e contexto

### Dor do usuário

Após revisão do fluxo de permissões, perfis e status não refletem o combinado em reunião (25/05/2026): usuários conseguem ações indevidas (editar fora da etapa, ver relatórios que não deveriam, excluir sem ser técnico em elaboração, etc.).

### Matriz alvo (PDF + notas Breno)

Status no banco: `rascunho` (Em Elaboração), `em_revisao` (Em Revisão), `aprovado`, `cancelado`.

#### Técnico

| Status | Ver | Editar | Excluir (lista) | Botões no formulário |
|--------|-----|--------|-----------------|----------------------|
| Em Elaboração | Somente **os seus** | Somente **os seus** | Sim | Navegação; Salvar rascunho; **Finalizar** só na última página |
| Em Revisão | Somente **os que ele elaborou** | **Não** | Não | Ocultar edição/liberação; **só navegação** |
| Aprovado | Somente os seus | Não | Não | Só navegação |
| Cancelado | Somente os seus | Não | Não | Só navegação |

#### Suporte

| Status | Ver | Editar | Botões |
|--------|-----|--------|--------|
| Em Elaboração | **Nada** | **Nada** | **Nenhum** |
| Em Revisão | **Todos** enviados para revisão | **Sim** (corrigir/revisar) | Exportar Excel; navegação; **#246:** Aprovar / Reprovar |
| Aprovado | Todos aprovados | Não | Exportar Excel; navegação |
| Cancelado | Todos cancelados | Não | Navegação |

**Nota Breno (1):** Suporte **edita** em revisão, mas **não** deve ver “Em elaboração” no **dashboard** (nem na prática listar/abrir rascunhos de terceiros).

#### Administrador

| Status | Ver | Editar | Mudar status |
|--------|-----|--------|--------------|
| Todos | **Todos** | **Não** (apenas checagem) | **Não** |

**Nota Breno (2):** Admin **não edita campos** nem altera status — só acompanha com navegação no formulário.

#### Exclusão (nota Breno 3)

| Quem | Quando |
|------|--------|
| **Somente Técnico** | Relatório **Em Elaboração** (`rascunho`), **dele** |
| Suporte / Admin | **Nunca** excluir |

---

## 2. Rastreabilidade de código

### Banco de dados

| Tabela / campo | Impacto |
|----------------|---------|
| `reports.status` | Sem alteração (`rascunho`, `em_revisao`, `aprovado`, `cancelado`) |
| `reports.tecnico_id` | Usado para “somente os seus” (Técnico) |

### Backend — hoje vs alvo

| Arquivo / endpoint | Comportamento atual | Gap vs PDF |
|--------------------|---------------------|------------|
| `GET /reports` `list_reports` | Técnico: só `tecnico_id`; Suporte/Admin: **todos** os status | Suporte vê **rascunhos**; dashboard/lista contam elaboração |
| `GET /reports/{id}` | Técnico: só seu; Suporte/Admin: qualquer | Suporte pode abrir rascunho alheio |
| `PUT /reports/{id}` | Suporte/Admin editam `rascunho` e `em_revisao`; Técnico edita os dois | Técnico ainda edita `em_revisao`; Admin edita |
| `PUT /reports/{id}/status` | Suporte/Admin: **qualquer** transição | Admin não deve mudar status |
| `DELETE /reports/{id}` | Suporte/Admin excluem (exceto aprovado) | Só Técnico em `rascunho` |
| `GET .../export-excel` | Restrições por `user_level` no export | Alinhar: Suporte em revisão/aprovado; Técnico conforme matriz |

### Frontend — hoje vs alvo

| Arquivo | Situação atual | Gap |
|---------|----------------|-----|
| `ReportWizardPage.tsx` | `canSaveDraft = isSuporte` em `rascunho` (invertido); auto-save **sempre** ativo; Finalizar só em `rascunho` | Técnico sem salvar/finalizar correto; campos editáveis em `em_revisao` para técnico; Suporte sem modo revisão claro |
| `ReportListPage.tsx` | Editar/Excluir para todos os itens da lista | Excluir só técnico+rascunho; ícone visualizar vs editar por status |
| `DashboardPage.tsx` | Cards “Em Elaboração” para **todos** os perfis | Suporte: **ocultar** card/contagem de elaboração |
| `lib/auth/permissions.ts` | `canCreateReport`, `isTecnico`, `isSuporte` | Falta matriz `canViewReport` / `canEditReport` / `canDeleteReport` |
| #246 | Botões Aprovar/Reprovar | **Não existem** no wizard |

### Funções a criar (reaproveitar padrão #244)

Centralizar em `frontend/src/lib/reports/reportPermissions.ts` (e espelho no backend):

```typescript
export type ReportAction = 'view' | 'edit' | 'delete' | 'finalize' | 'export_excel' | 'approve' | 'reject'

export function canViewReport(user, report): boolean
export function canEditReport(user, report): boolean
export function canDeleteReport(user, report): boolean
export function canFinalizeReport(user, report): boolean
export function canExportReportExcel(user, report): boolean
export function getDefaultListStatusFilter(user): string[] | undefined  // ex: Suporte exclui 'rascunho'
```

Backend: `backend/src/core/report_permissions.py` com as mesmas regras (fonte da verdade na API).

---

## 3. Análise de impacto e regressão

### Divergências críticas (código × PDF)

| # | Regra PDF | Código hoje |
|---|-----------|-------------|
| 1 | Técnico **não edita** em revisão/aprovado/cancelado | `PUT` aceita `em_revisao`; auto-save grava |
| 2 | Suporte **não vê** elaboração | `list_reports` retorna todos os status |
| 3 | Suporte **edita** só em revisão | Também edita `rascunho` via API |
| 4 | Admin **não edita** nem muda status | `PUT` e `PUT /status` liberados |
| 5 | **Só Técnico** exclui em elaboração | Suporte/Admin podem excluir |
| 6 | Dashboard Suporte sem “Em elaboração” | Card sempre visível |
| 7 | `canSaveDraft` usa `isSuporte` | Deveria ser Técnico em `rascunho` |

### Telas para re-teste

| Cenário | Perfis |
|---------|--------|
| Lista `/relatorios` — itens visíveis por status | Técnico, Suporte, Admin |
| Dashboard — cards e totais | Suporte (sem elaboração), Técnico, Admin |
| Wizard — campos, auto-save, botões | Técnico em elaboração → finalizar → só leitura |
| Wizard — Suporte em revisão | Editar + export; sem Finalizar |
| Wizard — Admin em qualquer status | Somente leitura + navegação |
| Excluir na lista | Só Técnico + rascunho próprio |
| API direta (Postman) | Bypass de UI |
| #246 Aprovar/Reprovar | Suporte em `em_revisao` (quando implementado) |

### O que **não** deve regredir

- #244: criar relatório só Técnico  
- #252: labels Em Elaboração / Em Revisão  
- Export Excel para Suporte em revisão/aprovado  
- Técnico finalizar (`rascunho` → `em_revisao`) na última página  

---

## 4. Lacunas e exceções (checklist)

| # | Pergunta | Recomendação |
|---|----------|--------------|
| 1 | #268 absorvido pelo #275? | **Sim** — implementar matriz única (#275) em vez de só #268 |
| 2 | Suporte abre rascunho via URL direta? | **403** no `GET` e `PUT` |
| 3 | Técnico vê relatório de outro técnico em revisão? | **Não** (só os que elaborou) |
| 4 | Card “Em Elaboração” no dashboard do Suporte | **Ocultar** (Breno) — filtrar stats e lista recente |
| 5 | Auto-save com formulário somente leitura | **Desligar** quando `!canEditReport` |
| 6 | Botões Aprovar/Reprovar (#246) | Escopo #246; #275 reserva hooks em `canApproveReport` |
| 7 | “Reprovar” → qual status? | **Decidido:** volta para `rascunho` (Em Elaboração) |
| 8 | Admin exporta Excel? | PDF: só navegação — **sem** export na matriz Admin |
| 9 | Técnico exporta Excel? | PDF: não listado — manter **sem** export para Técnico |
| 10 | Role `Suporte ao Cliente` | Tratar como `Suporte` (alias, igual #244) |

---

## 5. Segurança e performance

| Aspecto | Avaliação |
|---------|-----------|
| **Segurança** | Obrigatório replicar matriz no **backend**; UI sozinha é insuficiente |
| **Performance** | Filtro `status != rascunho` para Suporte na query — índice em `reports.status` desejável |
| **Manutenção** | Uma matriz documentada + funções únicas evita regressão (#268, #275, #246) |

---

## 6. Sugestão de implementação

### Fase 1 — Backend `report_permissions.py`

```python
def can_edit_report(user: User, report: Report) -> bool:
    level, role = ...
    if is_tecnico_puro(user):
        return report.tecnico_id == user.id and report.status == 'rascunho'
    if is_suporte_only(user):  # não admin
        return report.status == 'em_revisao'
    return False  # admin nunca edita campos

def can_delete_report(user, report) -> bool:
    return is_tecnico_puro(user) and report.tecnico_id == user.id and report.status == 'rascunho'

def can_view_report(user, report) -> bool:
    ...

def can_update_status(user, report, new_status) -> bool:
    # Técnico: rascunho -> em_revisao (próprio)
    # Suporte: em_revisao -> aprovado/cancelado (#246)
    # Admin: negar sempre
```

Aplicar em: `list_reports` (filtro base), `get_report`, `update_report`, `update_report_status`, `delete_report`, `export-excel`.

### Fase 2 — Frontend `reportPermissions.ts`

- Substituir `canSaveDraft = isSuporte` por `canEditReport(user, report)`.
- `readOnly` global no wizard quando `!canEditReport`.
- Desabilitar `handleFieldChange` / auto-save se somente leitura.
- `ReportListPage`: `canDeleteReport` no ícone lixeira; título do botão Editar → Visualizar.
- `DashboardPage`: se Suporte, não renderizar card “Em Elaboração”; filtrar `allReports` para stats.

### Fase 3 — #246 (paralelo ou sequencial)

- Botões **Aprovar** / **Reprovar** visíveis para Suporte em `em_revisao`.
- `update_report_status` restrito às transições permitidas.

### Fase 4 — Documentação

- Atualizar `tickets/268/fluxo-permissoes-relatorio.md` → “DEPOIS (#275)”.
- Remover contradição “Suporte edita em elaboração” da Parte 2 do #268.

**Estimativa:** 1–2 dias (matriz + testes); +0,5 dia se #246 na mesma entrega.

---

## 7. Critérios de aceite e regressão

### Aceite (PDF + Breno)

- [ ] Técnico: edita/exclui/finaliza **apenas** seus relatórios em **Em Elaboração**.
- [ ] Técnico: após finalizar, abre em **somente leitura** (sem auto-save).
- [ ] Suporte: **não** lista, não abre e **não** vê no dashboard relatórios em **Em Elaboração**.
- [ ] Suporte: edita relatórios em **Em Revisão**; exporta Excel.
- [ ] Admin: vê todos; **não** edita campos; **não** altera status; **não** exclui.
- [ ] Exclusão: **apenas** Técnico + `rascunho` + autor.
- [ ] API: tentativas indevidas retornam **403**.
- [ ] #246: Aprovar/Reprovar (se escopo combinado).

### Regressão

- [ ] Login por perfil; #244 criar relatório; labels #252.
- [ ] Finalizar técnico; fluxo completo até aprovado (com #246).
- [ ] Filtros da lista por status; paginação.

---

## 8. Veredito de prontidão

| Critério | Status |
|----------|--------|
| Matriz de negócio no PDF | ✅ |
| Notas Breno incorporadas | ✅ |
| Código mapeado | ✅ |
| Transição “Reprovar” (#246) | ⚠️ Confirmar status destino |
| **Implementado** | **Sim** (2026-05-19) — Reprovar → `rascunho` |

---

## Anexo A — Mapa rápido HOJE × ALVO

| Ação | Técnico (elaboração) | Técnico (revisão+) | Suporte (elaboração) | Suporte (revisão) | Admin |
|------|----------------------|--------------------|----------------------|-------------------|-------|
| Ver | ✅ seu | ✅ seu (hoje) / 👁️ alvo | ❌ alvo | ✅ alvo | ✅ |
| Editar | ✅ | ⚠️ hoje / ❌ alvo | ⚠️ hoje / ❌ alvo | ✅ alvo | ⚠️ hoje / ❌ alvo |
| Excluir | ✅ | ❌ | ⚠️ hoje / ❌ | ❌ | ⚠️ hoje / ❌ |
| Finalizar | ✅ | ❌ | ❌ | ❌ | ❌ |
| Export Excel | ❌ | ❌ | ⚠️ | ✅ | ⚠️ hoje / ❌ alvo |

---

## Anexo B — Referências de código

```292:295:backend/src/api/v1/reports.py
    if user_level < 50:  # INSPETOR (level 10)
        statement = statement.where(Report.tecnico_id == current_user.id)
```

```491:496:backend/src/api/v1/reports.py
    if report.status not in ['rascunho', 'em_revisao']:
        raise HTTPException(...)
```

```47:48:frontend/src/app/routes/ReportWizardPage.tsx
  const canExportExcel = isSuporte(user)
  const canSaveDraft = isSuporte(user)
```

```391:398:frontend/src/app/routes/ReportWizardPage.tsx
    // Auto-save com debounce — sem checagem de perfil/status
    saveTimerRef.current = setTimeout(() => {
      updateMutation.mutate(newData)
    }, 1000)
```

---

## Anexo C — PDF (trecho estruturado)

**Revisões Breno (página 2):**

1. Suporte edita em revisão; dashboard **sem** “Em elaboração”.  
2. Administrador **não** edita campos nem muda status.  
3. **Somente** Técnico exclui, e só em **Em Elaboração**.
