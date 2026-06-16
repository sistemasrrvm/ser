# Backend - SER (Sistema de Emissão de Relatórios)

## Stack Tecnológico

- **Python**: 3.12+
- **Framework**: FastAPI 0.115+
- **ORM**: SQLModel 0.0.20+
- **Banco de Dados**: MySQL
- **Autenticação**: JWT (python-jose) + Argon2
- **Servidor**: Uvicorn (ASGI)

## Instalação

### 1. Criar ambiente virtual

```bash
cd backend
python -m venv venv
```

### 2. Ativar ambiente virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

Copie `.env.example` para `.env` e ajuste conforme necessário:

```bash
cp .env.example .env
```

### 5. Executar scripts SQL

Execute os scripts na pasta `../scripts/mysql/`:

```bash
mysql -u root -p < ../scripts/mysql/001_create_tables.sql
mysql -u root -p < ../scripts/mysql/002_seed_admin.sql
```

## Executar Aplicação

### Modo Desenvolvimento (com reload automático)

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Modo Produção

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Documentação da API

Após iniciar o servidor, acesse:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## Estrutura de Diretórios

```
backend/
├── src/
│   ├── core/           # Configurações, segurança, dependencies
│   ├── models/         # Models SQLModel
│   ├── schemas/        # Schemas Pydantic (request/response)
│   ├── api/
│   │   └── v1/         # Endpoints da API v1
│   └── main.py         # Aplicação FastAPI
├── requirements.txt    # Dependências Python
├── .env                # Variáveis de ambiente
└── README.md
```

## Endpoints Principais

### Autenticação

- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Renovar access token
- `POST /api/v1/auth/password-reset/request` - Solicitar recuperação de senha
- `POST /api/v1/auth/password-reset/confirm` - Confirmar nova senha
- `POST /api/v1/auth/password/change` - Trocar senha (autenticado)
- `GET /api/v1/auth/me` - Dados do usuário autenticado

### Formulários (CRUD)

- `POST /api/v1/formularios` - Criar formulário
- `GET /api/v1/formularios` - Listar formulários
- `GET /api/v1/formularios/{id}` - Obter formulário por ID
- `PUT /api/v1/formularios/{id}` - Atualizar formulário
- `DELETE /api/v1/formularios/{id}` - Excluir formulário

## Credenciais Padrão

### Usuário Admin

- **Username**: `admin`
- **Senha**: `Admin@123`

⚠️ **Altere a senha após primeiro acesso!**

## Roles (Perfis)

- **admin** (level 100): Acesso total ao sistema
- **revisor** (level 40): Pode revisar e aprovar relatórios
- **usuario** (level 20): Pode criar e editar relatórios

## Segurança

### Requisitos de Senha

- Mínimo 8 caracteres
- Pelo menos 1 letra maiúscula
- Pelo menos 1 número
- Pelo menos 1 caractere especial (!@#$%^&*()_+-=[]{}|;:,.<>?)

### Tokens JWT

- **Access Token**: 30 minutos
- **Refresh Token**: 7 dias (ou 1 dia se "lembrar-me" não marcado)

### Hash de Senhas

- **Algoritmo**: Argon2id
- **Parâmetros**: memory=65536, time_cost=3, parallelism=4

## Desenvolvimento

### Adicionar Nova Rota

1. Criar arquivo em `src/api/v1/`
2. Definir router com `APIRouter`
3. Incluir router em `src/api/v1/__init__.py`

### Adicionar Novo Model

1. Criar model em `src/models/`
2. Herdar de `SQLModel` com `table=True`
3. Importar em `src/models/__init__.py`

### Adicionar Novo Schema

1. Criar schema em `src/schemas/`
2. Herdar de `BaseModel` (Pydantic)
3. Importar em `src/schemas/__init__.py`

## Troubleshooting

### Erro de conexão com MySQL

- Verificar se MySQL está rodando
- Verificar credenciais em `.env`
- Verificar se database `db_a2cb65_laudonr` existe

### Erro ao importar módulos

- Verificar se ambiente virtual está ativado
- Reinstalar dependências: `pip install -r requirements.txt`

### Erro 401 Unauthorized

- Verificar se token JWT está sendo enviado no header `Authorization: Bearer <token>`
- Verificar se token não expirou

## Problemas Conhecidos

### ⚠️ Interface do Railway Corrompe Hashes de Senha

**IMPORTANTE:** A interface web do Railway (Database > Tables > Edit) **NÃO deve ser usada para editar dados** que contenham caracteres especiais, especialmente hashes de senha.

**Problema:** Ao editar dados pela UI do Railway, caracteres especiais (como `$` em hashes Argon2) são corrompidos/truncados, resultando em hashes inválidos.

**Solução:** Use sempre a API ou scripts para modificar dados sensíveis:
- Via API: `POST /api/v1/debug/reset-password`
- Via Script: `railway run python backend/scripts/reset_user_password.py username senha`

**Mais detalhes:** Veja `backend/KNOWN_ISSUES.md` para documentação completa.

## Contato

Para dúvidas sobre o backend, consulte a documentação técnica em `/docs`.
