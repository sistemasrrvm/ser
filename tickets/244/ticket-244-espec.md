# Ticket #244 — Bloquear criação de relatório para Suporte ao Cliente

**Tipo:** Melhoria  
**Data da análise:** 2026-05-19  

---

## Resumo executivo

O perfil **Suporte ao Cliente** (no código, em geral o role **Suporte**, nível 50) **não deve criar novos relatórios**. Hoje ele vê o botão **"+ Novo Relatório"** no Dashboard (e na listagem) e consegue abrir `/novo-relatorio` porque o sistema trata Suporte como tendo permissões de Técnico em vários pontos.

A mensagem exigida já existe no projeto: **"Acesso Negado — Você não tem permissão para acessar esta página."** (`RoleRoute.tsx`).

**Escopo:** bloquear **criação** de relatório; **não** remover acesso a listar, visualizar ou editar relatórios existentes (alinha com Ticket #268).

---

## 1. Entendimento e contexto

### Dor do usuário

- Na área de **Suporte ao Cliente**, no **Dashboard**, o botão **"+ Novo Relatório"** não deveria aparecer.
- Se tentar acessar a tela de criação (URL direta), deve ver **Acesso Negado**.

### Perfis no sistema (referência código)

| Role no banco (script seeds) | Nível | Descrição resumida |
|------------------------------|-------|-------------------|
| `Tecnico` | 20 | Dashboard e relatórios — **cria** relatórios |
| `Suporte` | 50 | Dashboard, relatórios, clientes, equipamentos |
| `Administrador` | 100 | Acesso total |

**Lacuna:** o ticket cita **"Suporte ao Cliente"** — pode ser o nome exibido do role `Suporte` ou um **role separado** só em produção. Confirmar `roles.name` no banco (ver seção 4).

### Onde encaixa

- **Frontend:** Dashboard, listagem de relatórios, rota `/novo-relatorio`, `permissions.ts`, `App.tsx`.
- **Backend:** `POST /reports` (criação no kickoff) — deve bloquear Suporte mesmo com bypass da UI.

---

## 2. Rastreabilidade de código

### Banco de dados

| Tabela | Impacto |
|--------|---------|
| `roles` | Sem alteração; usa `name` e `level` já existentes |
| `reports` | Sem alteração |

### Backend

| Arquivo | Situação atual | Ação sugerida |
|---------|----------------|---------------|
| `backend/src/api/v1/reports.py` — `create_report` (POST) | Qualquer usuário autenticado pode criar; `tecnico_id` = usuário logado | Validar perfil: negar criação para Suporte (level ≥ 50 e < 100) |

### Frontend

| Arquivo | Situação atual | Ação sugerida |
|---------|----------------|---------------|
| `frontend/src/app/routes/DashboardPage.tsx` L219–224 | Botão **"+ Novo Relatório"** sempre visível; navega para `/relatorios` | Exibir só se `canCreateReport(user)`; opcional: link correto para `/novo-relatorio` |
| `frontend/src/app/routes/ReportListPage.tsx` L77–80 | Botão **Novo Relatório** sempre visível | Mesma regra |
| `frontend/src/App.tsx` L55–61 | `/novo-relatorio` permite Tecnico, **Suporte** e Admin | Remover Suporte de `allowedRoles`; usar rota só Tecnico + Admin |
| `frontend/src/lib/auth/permissions.ts` | `ROLE_PERMISSIONS['suporte']` inclui `/novo-relatorio` | Remover `/novo-relatorio` do perfil Suporte |
| `frontend/src/lib/auth/permissions.ts` — `canAccessMenuItem` | `/novo-relatorio` permitido para Suporte | Remover Suporte da rota |
| `frontend/src/lib/auth/permissions.ts` — `isTecnico()` | Retorna **true** para Suporte e Admin | **Não usar** `isTecnico` para “pode criar relatório” |
| `frontend/src/app/guards/RoleRoute.tsx` | Já exibe **Acesso Negado** com texto pedido | Reutilizar ao bloquear rota |

### Função a criar (reaproveitamento)

```typescript
// frontend/src/lib/auth/permissions.ts
/** Apenas Técnico e Administrador podem criar novo relatório */
export function canCreateReport(user: User | null): boolean
```

Regra (aprovada):

- **Técnico** (level 20–49 ou alias `tecnico`/`usuario`): ✅ criar  
- **Suporte** / **Suporte ao Cliente** (aliases + level 50–99): ❌ criar  
- **Administrador** (level ≥ 100): ❌ criar  
- Demais: ❌  

---

## 3. Análise de impacto e regressão

### Causa raiz (por que Suporte cria hoje)

1. `ROLE_PERMISSIONS` do Suporte inclui `/novo-relatorio`.
2. `App.tsx` declara `allowedRoles={[TECNICO, SUPORTE, ADMIN]}` em `novo-relatorio`.
3. `isTecnico(user)` retorna `true` para Suporte → `RoleRoute` considera Suporte como Técnico.
4. Botões no Dashboard/Listagem não checam perfil.

### O que NÃO deve quebrar

| Ação | Suporte após #244 |
|------|-------------------|
| Ver Dashboard | ✅ |
| Listar relatórios (`/relatorios`) | ✅ |
| Abrir / editar relatório existente (`/relatorios/:id/preencher`) | ✅ (regras #268) |
| Cadastros NR13, clientes | ✅ |
| Criar **novo** relatório | ❌ |

### Telas para re-teste

| Cenário | Perfil |
|---------|--------|
| Dashboard sem botão "+ Novo Relatório" | Suporte |
| Listagem sem botão "Novo Relatório" | Suporte |
| URL `/novo-relatorio` → Acesso Negado | Suporte |
| POST `/reports` → 403 | Suporte (Postman) |
| Técnico cria relatório normalmente | Tecnico |
| Admin cria relatório | Administrador |

### Observação — botão do Dashboard hoje

O botão **"+ Novo Relatório"** no Dashboard chama `navigate('/relatorios')`, não `/novo-relatorio`. O da **listagem** sim vai para kickoff. Vale alinhar no #244: botão do Dashboard pode passar a `/novo-relatorio` para Técnico/Admin (melhoria opcional).

---

## 4. Lacunas e exceções — decisões do produto (2026-05-19)

| # | Pergunta | Decisão |
|---|----------|---------|
| 1 | "Suporte ao Cliente" = role `Suporte`? | **Sim.** Se houver duplicidade no BD, unificar para `Suporte`. |
| 2 | Administrador pode criar relatório? | **Não** — somente **Técnico** cria. |
| 3 | Suporte pode clicar "Criar Primeiro Relatório"? | **Não** — esconder o fluxo. |
| 4 | API sem bloqueio | **Sim** — `POST /reports` bloqueado; alinhado com frontend. |
| 5 | Múltiplos nomes (`suporte`, `Suporte ao Cliente`) | **Sim** — normalizar em `canCreateReport` / `can_create_report`. |

**Regra final:** `canCreateReport` = apenas `isTecnicoPuro` (nível 20–49 ou alias `tecnico`/`usuario`, sem Admin nem Suporte).

### Estados cobertos

- Usuário Suporte logado → sem botão criar, rota bloqueada ✅  
- URL direta `/novo-relatorio` → Acesso Negado ✅  
- Técnico → sem mudança ✅  

---

## 5. Segurança e performance

| Aspecto | Avaliação |
|---------|-----------|
| **Segurança** | Essencial bloquear no **backend**; só esconder botão é insuficiente |
| **Performance** | Sem impacto |

---

## 6. Sugestão de implementação

### Passo 1 — `permissions.ts`

- Criar `canCreateReport(user)`.
- Remover `/novo-relatorio` de `ROLE_PERMISSIONS` para `Suporte` / `suporte`.
- Em `canAccessMenuItem`, `/novo-relatorio` só via `canCreateReport` (Técnico puro).

### Passo 2 — Rotas `App.tsx`

```tsx
<RoleRoute allowedRoles={[RoleName.TECNICO]}>
  {/* RoleRoute também valida canCreateReport em /novo-relatorio */}
</RoleRoute>
```

### Passo 3 — UI

- `DashboardPage.tsx`: renderizar botão só se `canCreateReport(user)`.
- `ReportListPage.tsx`: idem header e empty state.

### Passo 4 — Backend `create_report`

```python
if not can_create_report(current_user):
    raise HTTPException(403, detail="Seu perfil não tem permissão para criar novos relatórios")
```

Implementado em `backend/src/core/dependencies.py` (`can_create_report`).

### Passo 5 — Mensagem

Reutilizar `RoleRoute` — texto já atende:

> **Acesso Negado**  
> Você não tem permissão para acessar esta página.

**Estimativa:** 2–3 h.

---

## 7. Critérios de aceite e testes de regressão

### Aceite

- [ ] Suporte (ou Suporte ao Cliente): **sem** botão "+ Novo Relatório" no Dashboard.
- [ ] Suporte: **sem** botão "Novo Relatório" na listagem.
- [ ] Suporte: acessar `/novo-relatorio` → **Acesso Negado** com mensagem indicada.
- [ ] Suporte: `POST /api/v1/reports` → **403**.
- [ ] Técnico: cria relatório normalmente.
- [ ] Administrador: **não** cria relatório (403 + Acesso Negado na rota).
- [ ] Suporte continua acessando `/relatorios` e abrindo relatórios existentes.

### Regressão

- [ ] Login por perfil e menu lateral.
- [ ] Kickoff (formulário + cliente/equipamento) só para quem pode criar.

---

## 8. Veredito de prontidão

| Critério | Status |
|----------|--------|
| Problema reproduzível no código | ✅ |
| Solução clara | ✅ |
| Nome exato do role em produção | ⚠️ Confirmar "Suporte" vs "Suporte ao Cliente" |
| **Implementado** | **Sim** (2026-05-19) |

---

## Anexo — Pontos de código

- `frontend/src/lib/auth/permissions.ts` — Suporte tem `/novo-relatorio`; `isTecnico()` retorna true para Suporte.
- `frontend/src/app/routes/DashboardPage.tsx` — botão "+ Novo Relatório" sem checagem de perfil.
- `backend/src/api/v1/reports.py` — `create_report` sem validação de perfil.
