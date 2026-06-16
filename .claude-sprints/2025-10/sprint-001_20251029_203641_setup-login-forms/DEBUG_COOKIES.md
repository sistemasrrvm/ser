# DEBUG - Análise de Cookies

## Informações Necessárias

Por favor, siga estes passos e me forneça as informações:

### 1. DevTools - Network Tab (CRÍTICO)

**Durante o Login:**
1. Abra DevTools (F12) → Aba **Network**
2. Marque "Preserve log"
3. Faça login
4. Localize a requisição **POST /api/v1/auth/login**
5. Clique nela → Aba **Headers** → Role até **Response Headers**

**Me envie EXATAMENTE o que aparece em:**
- `set-cookie:` (deve ter 2 linhas)

Exemplo esperado:
```
set-cookie: access_token=ey...; Path=/; HttpOnly; SameSite=lax
set-cookie: refresh_token=ey...; Path=/; HttpOnly; SameSite=lax
```

### 2. DevTools - Application Tab

**Após Login:**
1. DevTools → Aba **Application**
2. Menu lateral → **Cookies** → **http://localhost:5173**

**Me envie screenshot ou lista exata dos cookies:**
- Nome do cookie
- Value (primeiros 20 caracteres)
- Domain
- Path
- HttpOnly
- SameSite

### 3. DevTools - Network Tab (Após Refresh)

**Após dar F5:**
1. Localize a requisição **GET /api/v1/auth/me**
2. Clique nela → Aba **Headers** → Role até **Request Headers**

**Me envie o que aparece em:**
- `cookie:` (deve conter access_token e refresh_token)

### 4. Console do Backend

**Me envie a saída COMPLETA do terminal do backend** desde o momento do login até o refresh.

---

## Por que preciso dessas informações?

- Verificar se cookies estão sendo **definidos** corretamente (headers de response)
- Verificar se cookies estão sendo **armazenados** no navegador
- Verificar se cookies estão sendo **enviados** nas requisições subsequentes
- Identificar exatamente onde o fluxo está quebrando
