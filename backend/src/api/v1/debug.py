"""
Debug endpoints para diagnóstico de problemas de autenticação
⚠️ ENDPOINTS SENSÍVEIS - Requerem autenticação de admin
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select, text
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from collections import defaultdict
import time

from ...core.database import get_session
from ...core.dependencies import get_current_user, require_admin
from ...core.security import get_password_hash, validate_password_strength
from ...core.colored_logging import log_info, log_warning, log_error
from ...models import User, Role

router = APIRouter(prefix="/debug", tags=["Debug"])

# Rate limiting simples (em memória - para produção, usar Redis)
_rate_limit_store: Dict[str, List[float]] = defaultdict(list)
_RATE_LIMIT_WINDOW = 60  # 1 minuto
_RATE_LIMIT_MAX_REQUESTS = 5  # Máximo 5 resets por minuto por IP


def check_rate_limit(request: Request) -> None:
    """
    Verifica rate limiting para prevenir abuso
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Limpar requisições antigas
    _rate_limit_store[client_ip] = [
        req_time for req_time in _rate_limit_store[client_ip]
        if now - req_time < _RATE_LIMIT_WINDOW
    ]
    
    # Verificar limite
    if len(_rate_limit_store[client_ip]) >= _RATE_LIMIT_MAX_REQUESTS:
        log_warning(
            f"⚠️ Rate limit excedido para IP {client_ip}",
            context={"ip": client_ip, "requests": len(_rate_limit_store[client_ip])}
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Muitas requisições. Tente novamente em {_RATE_LIMIT_WINDOW} segundos."
        )
    
    # Registrar requisição
    _rate_limit_store[client_ip].append(now)


@router.get("/users-roles", response_model=List[Dict[str, Any]])
async def debug_users_roles(
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Endpoint de debug para verificar usuários e roles
    Lista todos os usuários com suas roles para diagnóstico
    
    ⚠️ Requer: Autenticação de admin
    """
    try:
        # Buscar todos os usuários com roles
        statement = select(User, Role).join(Role)
        results = session.exec(statement).all()
        
        users_data = []
        for user, role in results:
            users_data.append({
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "role_id": user.role_id,
                "role_name": role.name if role else None,
                "role_level": role.level if role else None,
                "role_description": role.description if role else None,
            })
        
        return users_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar usuários e roles: {str(e)}"
        )


@router.get("/roles", response_model=List[Dict[str, Any]])
async def debug_roles(
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Endpoint de debug para verificar todas as roles
    
    ⚠️ Requer: Autenticação de admin
    """
    try:
        statement = select(Role)
        roles = session.exec(statement).all()
        
        roles_data = []
        for role in roles:
            roles_data.append({
                "role_id": role.id,
                "name": role.name,
                "level": role.level,
                "description": role.description,
            })
        
        return roles_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar roles: {str(e)}"
        )


@router.get("/user/{user_id}/role-check")
async def debug_user_role_check(
    user_id: int,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Endpoint de debug para verificar um usuário específico e sua role
    
    ⚠️ Requer: Autenticação de admin
    """
    try:
        # Buscar usuário
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"Usuário com ID {user_id} não encontrado"
            )
        
        # Tentar carregar role com selectinload
        from sqlalchemy.orm import selectinload
        statement = select(User).options(selectinload(User.role)).where(User.id == user_id)
        user_with_role = session.exec(statement).first()
        
        # Verificar role diretamente no banco
        role_direct = session.get(Role, user.role_id)
        
        result = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "role_id": user.role_id,
            "role_direct_from_db": {
                "id": role_direct.id if role_direct else None,
                "name": role_direct.name if role_direct else None,
                "level": role_direct.level if role_direct else None,
            },
            "role_via_relationship": {
                "has_role_attr": hasattr(user, 'role'),
                "role_is_none": user.role is None if hasattr(user, 'role') else True,
                "role_id": user.role.id if hasattr(user, 'role') and user.role else None,
                "role_name": user.role.name if hasattr(user, 'role') and user.role else None,
            },
            "role_via_selectinload": {
                "user_found": user_with_role is not None,
                "has_role_attr": hasattr(user_with_role, 'role') if user_with_role else False,
                "role_is_none": user_with_role.role is None if user_with_role and hasattr(user_with_role, 'role') else True,
                "role_id": user_with_role.role.id if user_with_role and hasattr(user_with_role, 'role') and user_with_role.role else None,
                "role_name": user_with_role.role.name if user_with_role and hasattr(user_with_role, 'role') and user_with_role.role else None,
            }
        }
        
        return result
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/user/{user_id}/password-hash-info")
async def debug_user_password_hash(
    user_id: int,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Endpoint de debug para verificar o hash de senha de um usuário
    NÃO expõe o hash completo por segurança, apenas informações sobre formato
    
    ⚠️ Requer: Autenticação de admin
    """
    try:
        # Buscar usuário
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"Usuário com ID {user_id} não encontrado"
            )
        
        password_hash_sqlmodel = user.password_hash
        
        # Buscar hash diretamente do banco via SQL raw para comparação
        result_raw = session.exec(
            text("SELECT password_hash, CHAR_LENGTH(password_hash) as hash_length FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        ).first()
        
        password_hash_raw = result_raw[0] if result_raw else None
        hash_length_raw = result_raw[1] if result_raw else None
        
        # Função auxiliar para analisar hash
        def analyze_hash(password_hash):
            if not password_hash:
                return {
                    "length": 0,
                    "prefix": None,
                    "suffix": None,
                    "starts_with_argon2id": False,
                    "format": "empty"
                }
            
            hash_info = {
                "length": len(password_hash),
                "prefix": password_hash[:20] if len(password_hash) >= 20 else password_hash,
                "suffix": password_hash[-10:] if len(password_hash) >= 10 else None,
                "starts_with_argon2id": password_hash.startswith("$argon2id$"),
                "format": "unknown"
            }
            
            # Determinar formato
            if hash_info["starts_with_argon2id"]:
                hash_info["format"] = "argon2id (correto)"
            elif hash_info["length"] < 50:
                hash_info["format"] = f"hash muito curto ({hash_info['length']} chars) - possivelmente truncado"
            else:
                hash_info["format"] = "formato desconhecido"
            
            return hash_info
        
        hash_info_sqlmodel = analyze_hash(password_hash_sqlmodel)
        hash_info_raw = analyze_hash(password_hash_raw)
        
        # Verificar se há diferença
        hashes_match = (password_hash_sqlmodel == password_hash_raw) if password_hash_sqlmodel and password_hash_raw else False
        
        result = {
            "user_id": user.id,
            "username": user.username,
            "comparison": {
                "hashes_match": hashes_match,
                "sqlmodel_length": hash_info_sqlmodel["length"],
                "raw_sql_length": hash_info_raw["length"],
            },
            "password_hash_sqlmodel": hash_info_sqlmodel,
            "password_hash_raw_sql": hash_info_raw
        }
        
        return result
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# ============================================================================
# ENDPOINT: Reset de Senha (SEGURO)
# ⚠️ Requer autenticação de admin + rate limiting + logging de auditoria
# ============================================================================

class ResetPasswordRequest(BaseModel):
    """Request para resetar senha de um usuário"""
    username: Optional[str] = Field(None, description="Username do usuário (alternativa a user_id)")
    user_id: Optional[int] = Field(None, description="ID do usuário (alternativa a username)")
    new_password: str = Field(..., min_length=8, description="Nova senha (mínimo 8 caracteres)")


@router.post("/reset-password")
async def debug_reset_password(
    request: ResetPasswordRequest,
    request_obj: Request,
    current_user: User = Depends(require_admin),  # ⚠️ REQUER ADMIN
    session: Session = Depends(get_session)
):
    """
    🔒 Resetar senha de um usuário (SEGURO)
    
    ⚠️ SEGURANÇA:
    - Requer autenticação de admin
    - Rate limiting: máximo 5 resets por minuto por IP
    - Logging de auditoria completo
    - Validação rigorosa de senha
    
    Use este endpoint para corrigir senhas de usuários que tiveram hashes corrompidos.
    
    Uso:
    - Via username: {"username": "usuario.tecnico1", "new_password": "NovaSenha123!"}
    - Via user_id: {"user_id": 7, "new_password": "NovaSenha123!"}
    
    ⚠️ IMPORTANTE: Este endpoint registra todas as ações para auditoria!
    """
    # 1. Rate limiting
    check_rate_limit(request_obj)
    
    # 2. Validar que pelo menos um identificador foi fornecido
    if not request.username and not request.user_id:
        log_warning(
            "❌ Tentativa de reset de senha sem identificador",
            context={
                "admin_user": current_user.username,
                "admin_id": current_user.id,
                "ip": request_obj.client.host if request_obj.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=400,
            detail="Forneça 'username' ou 'user_id' para identificar o usuário"
        )
    
    # 3. Buscar usuário
    if request.user_id:
        target_user = session.get(User, request.user_id)
        if not target_user:
            log_warning(
                f"❌ Tentativa de reset de senha - usuário não encontrado",
                context={
                    "admin_user": current_user.username,
                    "admin_id": current_user.id,
                    "target_user_id": request.user_id,
                    "ip": request_obj.client.host if request_obj.client else "unknown"
                }
            )
            raise HTTPException(
                status_code=404,
                detail=f"Usuário com ID {request.user_id} não encontrado"
            )
    else:
        statement = select(User).where(User.username == request.username)
        target_user = session.exec(statement).first()
        if not target_user:
            log_warning(
                f"❌ Tentativa de reset de senha - usuário não encontrado",
                context={
                    "admin_user": current_user.username,
                    "admin_id": current_user.id,
                    "target_username": request.username,
                    "ip": request_obj.client.host if request_obj.client else "unknown"
                }
            )
            raise HTTPException(
                status_code=404,
                detail=f"Usuário com username '{request.username}' não encontrado"
            )
    
    # 4. Prevenir auto-reset (admin não pode resetar própria senha por este endpoint)
    if target_user.id == current_user.id:
        log_warning(
            f"⚠️ Tentativa de auto-reset de senha bloqueada",
            context={
                "admin_user": current_user.username,
                "admin_id": current_user.id,
                "ip": request_obj.client.host if request_obj.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=400,
            detail="Use o endpoint /api/v1/auth/password/change para alterar sua própria senha"
        )
    
    # 5. Validar força da senha
    is_valid, message = validate_password_strength(request.new_password)
    if not is_valid:
        log_warning(
            f"❌ Tentativa de reset com senha inválida",
            context={
                "admin_user": current_user.username,
                "admin_id": current_user.id,
                "target_user": target_user.username,
                "target_user_id": target_user.id,
                "reason": message,
                "ip": request_obj.client.host if request_obj.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=400,
            detail=f"Senha inválida: {message}"
        )
    
    # 6. Gerar novo hash
    new_hash = get_password_hash(request.new_password)
    
    # 7. Verificar se o hash foi gerado corretamente
    if not new_hash.startswith("$argon2id$"):
        log_error(
            f"❌ Erro ao gerar hash - formato incorreto",
            context={
                "admin_user": current_user.username,
                "admin_id": current_user.id,
                "target_user": target_user.username,
                "target_user_id": target_user.id,
                "ip": request_obj.client.host if request_obj.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao gerar hash - hash gerado não está no formato correto"
        )
    
    # 8. Obter hash antigo para log de auditoria
    old_hash_length = len(target_user.password_hash) if target_user.password_hash else 0
    old_hash_start = target_user.password_hash[:30] if target_user.password_hash and len(target_user.password_hash) >= 30 else target_user.password_hash
    
    # 9. Atualizar senha
    target_user.password_hash = new_hash
    session.add(target_user)
    session.commit()
    session.refresh(target_user)
    
    # 10. Verificar se foi salvo corretamente
    if not target_user.password_hash.startswith("$argon2id$"):
        log_error(
            f"❌ Erro ao salvar hash - hash não foi salvo corretamente",
            context={
                "admin_user": current_user.username,
                "admin_id": current_user.id,
                "target_user": target_user.username,
                "target_user_id": target_user.id,
                "ip": request_obj.client.host if request_obj.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao salvar hash - hash não foi salvo corretamente no banco"
        )
    
    # 11. Log de auditoria (CRÍTICO para segurança)
    log_info(
        f"🔐 AUDITORIA: Senha resetada por admin",
        context={
            "admin_user": current_user.username,
            "admin_id": current_user.id,
            "admin_email": current_user.email,
            "target_user": target_user.username,
            "target_user_id": target_user.id,
            "target_email": target_user.email,
            "old_hash_length": old_hash_length,
            "new_hash_length": len(new_hash),
            "timestamp": datetime.utcnow().isoformat(),
            "ip": request_obj.client.host if request_obj.client else "unknown",
            "user_agent": request_obj.headers.get("user-agent", "unknown")
        }
    )
    
    return {
        "success": True,
        "message": f"Senha resetada com sucesso para o usuário {target_user.username}",
        "audit": {
            "reset_by": {
                "username": current_user.username,
                "id": current_user.id,
                "email": current_user.email
            },
            "target_user": {
                "id": target_user.id,
                "username": target_user.username,
                "email": target_user.email,
                "is_active": target_user.is_active,
                "role_id": target_user.role_id
            },
            "timestamp": datetime.utcnow().isoformat(),
            "ip": request_obj.client.host if request_obj.client else "unknown"
        },
        "hash_info": {
            "old_hash_length": old_hash_length,
            "old_hash_start": old_hash_start,
            "new_hash_length": len(new_hash),
            "new_hash_start": new_hash[:30],
            "new_hash_valid": new_hash.startswith("$argon2id$")
        }
    }
