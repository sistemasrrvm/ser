# Problemas Conhecidos

## ⚠️ Interface do Railway Corrompe Hashes de Senha

### Problema
**Data:** 2025-11-21  
**Status:** Identificado e Documentado

A interface web do Railway (Database > Tables > Edit) **NÃO deve ser usada para editar dados** que contenham caracteres especiais, especialmente hashes de senha.

### Sintomas
- Hash de senha é truncado durante a edição
- Prefixo `$argon2id$v$m` é removido/corrompido
- Hash fica no formato incorreto: `=19=65536,t=3,p=4...` (sem o prefixo `$argon2id$v$m`)
- Usuários não conseguem fazer login após edição pela interface

### Causa Raiz
A interface do Railway não preserva corretamente caracteres especiais (especialmente `$`) ao editar dados pela UI. Isso causa truncamento/corrupção de dados.

### Solução
**NUNCA edite hashes de senha ou outros dados sensíveis pela interface do Railway!**

Use uma das seguintes alternativas:

1. **Via API (Recomendado):**
   ```bash
   # Via endpoint temporário de debug
   POST /api/v1/debug/reset-password
   {
     "username": "usuario.tecnico1",
     "new_password": "NovaSenha123!"
   }
   ```

2. **Via Script Python:**
   ```bash
   railway run python backend/scripts/reset_user_password.py usuario.tecnico1 NovaSenha123!
   ```

3. **Via SQL direto (se necessário):**
   ```sql
   -- Use apenas se souber o que está fazendo
   UPDATE users SET password_hash = '$argon2id$v=19$m=65536,t=3,p=4$...' WHERE id = 7;
   ```

### Como Verificar se o Hash Está Corrompido
```bash
# Via endpoint de debug
GET /api/v1/debug/user/{user_id}/password-hash-info

# Hash válido deve ter:
# - length: ~97 caracteres
# - format: "argon2id (correto)"
# - starts_with_argon2id: true
# - prefix: "$argon2id$v=19$m=65536,t=3,p=4$"

# Hash corrompido tem:
# - length: ~33 caracteres ou menos
# - format: "hash muito curto" ou "MD5 (hex) - INCORRETO"
# - starts_with_argon2id: false
# - prefix: "=19=65536,t=3,p=4" (sem o $argon2id$v$m)
```

### Como Corrigir Hash Corrompido

1. Use o endpoint de reset de senha:
   ```bash
   POST /api/v1/debug/reset-password
   {
     "user_id": 7,
     "new_password": "NovaSenha123!"
   }
   ```

2. Ou use o script Python:
   ```bash
   railway run python backend/scripts/reset_user_password.py username NovaSenha123!
   ```

### Prevenção
- ✅ **SEMPRE** use a API ou scripts para modificar dados sensíveis
- ✅ **NUNCA** edite hashes, tokens ou outros dados com caracteres especiais pela UI do Railway
- ✅ **SEMPRE** verifique os dados após qualquer modificação manual

### Notas Adicionais
- Este problema foi descoberto em 2025-11-21 após transferir o banco de dados
- A transferência do dump SQL em si não corrompe os dados - apenas a edição pela UI
- O problema afeta qualquer campo que contenha caracteres especiais, não apenas hashes

---

## Outros Problemas Conhecidos

_(Adicione outros problemas conhecidos aqui conforme surgirem)_

