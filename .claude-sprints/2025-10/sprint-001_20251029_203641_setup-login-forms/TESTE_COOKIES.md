# Teste - Login com httpOnly Cookies

**Data:** 2025-10-29
**Objetivo:** Validar migração de localStorage para httpOnly cookies

---

## ✅ Pré-requisitos

1. Backend rodando: `cd backend && python -m uvicorn src.main:app --reload`
2. Frontend rodando: `cd frontend && npm run dev`
3. Banco de dados com admin criado (senha: Admin@123)

---

## 📋 Roteiro de Testes

### Teste 1: Login e Criação de Cookies

**Passos:**
1. Abrir navegador em **modo anônimo** (Ctrl+Shift+N no Chrome)
2. Acessar: http://localhost:5173/login
3. Abrir DevTools (F12) → Aba **Application** → **Cookies** → http://localhost:5173
4. Fazer login:
   - Username: `admin`
   - Password: `Admin@123`

**Resultado Esperado:**
- ✅ Redirecionamento para http://localhost:5173/dashboard
- ✅ Console mostra: `✅ Login bem-sucedido: Administrador`
- ✅ DevTools → Cookies mostra **2 cookies**:
  - `access_token` (httpOnly: ✓, secure: vazio em dev, sameSite: lax)
  - `refresh_token` (httpOnly: ✓, secure: vazio em dev, sameSite: lax)

---

### Teste 2: Navegação com Cookies

**Passos:**
1. Após login bem-sucedido, clicar em **"Formulários"** no sidebar
2. Verificar console do navegador

**Resultado Esperado:**
- ✅ Página http://localhost:5173/formularios carrega normalmente
- ✅ Console mostra requisição para `/api/v1/formularios` com cookies
- ✅ DevTools → Network → Selecionar requisição `/formularios` → Aba **Headers**:
  - Request Headers deve conter: `Cookie: access_token=...; refresh_token=...`

---

### Teste 3: Persistência Após Refresh

**Passos:**
1. Estando em http://localhost:5173/formularios
2. Apertar **F5** (refresh da página)
3. Observar console

**Resultado Esperado:**
- ✅ Console mostra: `🔄 Verificando autenticação via cookie...`
- ✅ Console mostra: `✅ Usuário autenticado: Administrador`
- ✅ Página recarrega e permanece em /formularios (NÃO redireciona para /login)
- ✅ Cookies continuam presentes no DevTools

---

### Teste 4: Logout e Limpeza de Cookies

**Passos:**
1. Clicar no botão de logout (ícone no header)
2. Verificar cookies no DevTools

**Resultado Esperado:**
- ✅ Console mostra: `✅ Logout realizado`
- ✅ Redirecionamento para http://localhost:5173/login
- ✅ DevTools → Cookies: **access_token e refresh_token foram removidos**

---

### Teste 5: Acesso Direto a Rota Protegida (Sem Login)

**Passos:**
1. Após logout, tentar acessar diretamente: http://localhost:5173/formularios

**Resultado Esperado:**
- ✅ Console mostra: `❌ Não autenticado (cookie inválido ou expirado)`
- ✅ Redirecionamento automático para http://localhost:5173/login

---

## 🐛 Problemas Conhecidos (Se Ocorrerem)

### Problema: Cookies não aparecem no DevTools

**Causa:** SameSite cookies só funcionam em mesma origem
**Solução:** Garantir que frontend está em http://localhost:5173 (não 127.0.0.1)

---

### Problema: 401 Unauthorized mesmo com cookies

**Causa:** Backend não está lendo cookies corretamente
**Debug:**
1. Verificar console do backend (terminal onde uvicorn está rodando)
2. Adicionar print temporário em `dependencies.py`:

```python
async def get_current_user(
    access_token: Optional[str] = Cookie(None),
    session: Session = Depends(get_session)
) -> User:
    print(f"🔍 Cookie recebido: {access_token[:20] if access_token else 'NENHUM'}...")
    # ... resto do código
```

---

### Problema: CORS error

**Erro no console:** `Access to XMLHttpRequest blocked by CORS policy`
**Solução:** Verificar se vite.config.ts tem proxy correto:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

---

## ✅ Checklist Final

Após todos os testes:

- [ ] Login cria cookies httpOnly
- [ ] Navegação entre páginas funciona com cookies
- [ ] Refresh mantém autenticação
- [ ] Logout limpa cookies
- [ ] Acesso sem login redireciona para /login
- [ ] localStorage **NÃO** contém mais tokens (verificar no DevTools → Application → Local Storage)

---

## 📊 Resultado

**Status:** [PENDENTE / APROVADO / FALHOU]

**Observações:**
[Anotar aqui qualquer problema encontrado ou comportamento inesperado]
