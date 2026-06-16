# Guia: Como Resetar Senhas via Console

## Opção 1: Via Script Python (Recomendado - Railway)

### No Railway:

```bash
# Modo não-interativo (recomendado)
railway run python backend/scripts/reset_user_password.py usuario.tecnico1 NovaSenha123!

# Modo interativo
railway run python backend/scripts/reset_user_password.py
```

### Exemplo de uso:

```bash
# Resetar senha do usuario.tecnico1 (ID: 7)
railway run python backend/scripts/reset_user_password.py usuario.tecnico1 NovaSenha123!

# Resetar senha do usuario.suporte1 (ID: 9)
railway run python backend/scripts/reset_user_password.py usuario.suporte1 NovaSenha123!

# Resetar senha do admin (ID: 1)
railway run python backend/scripts/reset_user_password.py admin NovaSenha123!
```

---

## Opção 2: Via cURL (Se tiver curl instalado)

### Windows (PowerShell):

```powershell
# Resetar senha via username
$body = @{
    username = "usuario.tecnico1"
    new_password = "NovaSenha123!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://laudonr13-production.up.railway.app/api/v1/debug/reset-password" -Method Post -Body $body -ContentType "application/json"

# Resetar senha via user_id
$body = @{
    user_id = 7
    new_password = "NovaSenha123!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://laudonr13-production.up.railway.app/api/v1/debug/reset-password" -Method Post -Body $body -ContentType "application/json"
```

### Linux/Mac:

```bash
# Via username
curl -X POST https://laudonr13-production.up.railway.app/api/v1/debug/reset-password \
  -H "Content-Type: application/json" \
  -d '{"username": "usuario.tecnico1", "new_password": "NovaSenha123!"}'

# Via user_id
curl -X POST https://laudonr13-production.up.railway.app/api/v1/debug/reset-password \
  -H "Content-Type: application/json" \
  -d '{"user_id": 7, "new_password": "NovaSenha123!"}'
```

---

## Opção 3: Via Python requests (Script simples)

Crie um arquivo `reset_password_simple.py`:

```python
import requests
import sys

def reset_password(username=None, user_id=None, new_password=None):
    url = "https://laudonr13-production.up.railway.app/api/v1/debug/reset-password"
    
    data = {"new_password": new_password}
    if username:
        data["username"] = username
    elif user_id:
        data["user_id"] = user_id
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Sucesso!")
        print(f"Usuário: {result['user']['username']}")
        print(f"Hash antigo: {result['hash_info']['old_hash_length']} chars")
        print(f"Hash novo: {result['hash_info']['new_hash_length']} chars")
        print(f"Hash válido: {result['hash_info']['new_hash_valid']}")
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python reset_password_simple.py <username ou user_id> <senha>")
        sys.exit(1)
    
    identifier = sys.argv[1]
    password = sys.argv[2]
    
    if identifier.isdigit():
        reset_password(user_id=int(identifier), new_password=password)
    else:
        reset_password(username=identifier, new_password=password)
```

### Usar:

```bash
python reset_password_simple.py usuario.tecnico1 NovaSenha123!
python reset_password_simple.py 7 NovaSenha123!
```

---

## Requisitos da Senha

- ✅ Mínimo 8 caracteres
- ✅ Pelo menos 1 letra maiúscula
- ✅ Pelo menos 1 número
- ✅ Pelo menos 1 caractere especial (`!@#$%^&*()_+-=[]{}|;:,.<>?`)

---

## Exemplos de Senhas Válidas

- `NovaSenha123!`
- `Admin@2024`
- `Tecnico#1`
- `Suporte$123`

---

## Usuários que Precisam de Reset

Baseado nos IDs que tiveram problemas:

1. **ID 1** - `admin` - Admin do sistema
2. **ID 7** - `usuario.tecnico1` - Técnico 1
3. **ID 9** - `usuario.suporte1` - Suporte 1
4. **ID 10** - `usuario.suporte2` - Suporte 2

---

## Verificação Após Reset

Após resetar, teste o login:

```bash
# Via endpoint de debug
GET https://laudonr13-production.up.railway.app/api/v1/debug/user/7/password-hash-info

# Deve mostrar:
# - hash_length: ~97 caracteres
# - format: "argon2id (correto)"
# - starts_with_argon2id: true
```

