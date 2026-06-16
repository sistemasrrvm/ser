# Frontend - SER (Sistema de Emissão de Relatórios)

## Stack Tecnológico

- **React**: 19.1.1
- **Vite**: 7.1.7
- **TypeScript**: 5.9.3
- **React Router DOM**: 7.9.3
- **TailwindCSS**: 3.4.18
- **Lucide React**: 0.544.0 (ícones)
- **Axios**: 1.7.2 (HTTP client)
- **React Query**: 5.0.0 (gerenciamento de estado server)

## Instalação

### 1. Instalar dependências

```bash
cd frontend
npm install
```

### 2. Executar aplicação

#### Modo Desenvolvimento (com hot reload)

```bash
npm run dev
```

A aplicação estará disponível em: http://localhost:5173

#### Build para Produção

```bash
npm run build
```

O build será gerado na pasta `dist/`.

#### Preview do Build

```bash
npm run preview
```

## Estrutura de Diretórios

```
frontend/
├── src/
│   ├── app/
│   │   ├── guards/          # Guards de rota (ProtectedRoute, AdminRoute)
│   │   ├── layout/          # Componentes de layout (Sidebar, Header)
│   │   └── routes/          # Páginas da aplicação
│   ├── components/          # Componentes reutilizáveis
│   ├── lib/
│   │   ├── api/             # Cliente API (axios) e endpoints
│   │   └── auth/            # Contexto de autenticação
│   ├── App.tsx              # Configuração de rotas
│   ├── main.tsx             # Entry point
│   └── index.css            # Estilos globais (Tailwind)
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## Rotas

### Públicas
- `/login` - Página de login

### Protegidas (requer autenticação)
- `/` - Redireciona para `/dashboard`
- `/dashboard` - Dashboard principal

### Admin (requer role admin - level 100)
- `/formularios` - Gerenciamento de templates de formulários

## Autenticação

### Login
- Endpoint: `POST /api/v1/auth/login`
- Retorna: `access_token`, `refresh_token`, `user`
- Tokens armazenados no `localStorage`

### Refresh Token
- Interceptor do axios detecta 401 e tenta renovar automaticamente
- Se falhar, redireciona para `/login`

### Logout
- Remove tokens do `localStorage`
- Redireciona para `/login`

## Guarda de Rotas

### ProtectedRoute
Protege rotas que requerem autenticação:
```tsx
<Route
  path="/dashboard"
  element={
    <ProtectedRoute>
      <DashboardPage />
    </ProtectedRoute>
  }
/>
```

### AdminRoute
Protege rotas que requerem role admin (level 100):
```tsx
<Route
  path="/formularios"
  element={
    <AdminRoute>
      <FormulariosPage />
    </AdminRoute>
  }
/>
```

## Componentes de Layout

### Sidebar
- Menu lateral de navegação
- Filtro de itens por role (admin/não-admin)
- Destaque visual para rota ativa

### Header
- Nome do usuário e avatar
- Dropdown com opções:
  - Meu Perfil
  - Sair

## API Client

### Configuração (lib/api/client.ts)
```typescript
import { api } from '@/lib/api/client'

// Exemplo de uso
const response = await api.get('/formularios')
```

### Interceptors
- **Request**: Adiciona token JWT automaticamente
- **Response**: Tratamento de erros 401 com refresh automático

## Contexto de Autenticação

### useAuth Hook
```typescript
import { useAuth } from '@/lib/auth/AuthContext'

function MyComponent() {
  const { user, isAuthenticated, login, logout, isAdmin } = useAuth()

  return (
    <div>
      {user && <p>Bem-vindo, {user.full_name}</p>}
      {isAdmin() && <button>Acesso Admin</button>}
    </div>
  )
}
```

## Tailwind CSS

### Cores Customizadas
Conforme identidade visual do SER:
- `primary` - Azul principal (#366595)
- `yellow` - Amarelo (#f2cc2c)
- `green` - Verde (#56991f)
- `background` - Branco (#fefffa)

### Classes Utilitárias
```css
.btn             /* Botão base */
.btn-primary     /* Botão primário (azul) */
.btn-secondary   /* Botão secundário (cinza) */
.btn-danger      /* Botão de perigo (vermelho) */
.input           /* Input de formulário */
.label           /* Label de formulário */
.card            /* Card com sombra */
.sidebar-item    /* Item de menu da sidebar */
```

## Desenvolvimento

### Adicionar Nova Página
1. Criar componente em `src/app/routes/`
2. Adicionar rota em `src/App.tsx`
3. Adicionar item no menu (se necessário) em `src/app/layout/Sidebar.tsx`

### Adicionar Novo Endpoint
1. Definir tipos em `src/lib/api/types.ts`
2. Criar funções em `src/lib/api/` (ex: `src/lib/api/usuarios.ts`)
3. Usar com React Query nas páginas

## Troubleshooting

### Erro de CORS
- Verificar se backend está rodando
- Verificar configuração de proxy em `vite.config.ts`
- Verificar CORS no backend (`.env`)

### Token Expirado
- Refresh automático habilitado
- Se falhar, usuário é redirecionado para login

### Erro 403 Forbidden
- Usuário não tem permissão para acessar rota
- Verificar role do usuário no `/dashboard`

## Scripts NPM

```bash
npm run dev       # Desenvolvimento (hot reload)
npm run build     # Build para produção
npm run preview   # Preview do build
npm run lint      # ESLint
```

## Contato

Para dúvidas sobre o frontend, consulte a documentação em `/docs` ou o README do backend.
