"""
API v1: Autenticação
Endpoints para login, recuperação de senha e refresh de tokens
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import Optional

from ...core import (
    get_session,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_password_reset_token,
    validate_password_strength,
    settings,
    get_current_user
)
from ...core.colored_logging import log_info, log_error, log_success, log_warning
from ...core.version import server_version
from ...models import User, Role
from ...schemas import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirm,
    PasswordChangeRequest,
    UserResponse,
    RoleResponse
)


router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    credentials: LoginRequest,
    session: Session = Depends(get_session)
):
    """
    Login do usuário

    Retorna tokens JWT no corpo da resposta (não usa cookies)
    """
    log_info(f"🔐 Tentativa de login: {credentials.username}")

    # Buscar usuário com role carregado
    try:
        statement = select(User).options(selectinload(User.role)).where(User.username == credentials.username)
        user = session.exec(statement).first()
        
        # Log detalhado para debug - CRÍTICO para identificar o problema
        if user:
            log_info(
                f"🔍 Usuário encontrado",
                context={
                    "user_id": user.id,
                    "username": user.username,
                    "role_id": user.role_id,
                    "is_active": user.is_active,
                    "has_role_loaded": hasattr(user, 'role') and user.role is not None
                }
            )
        else:
            log_warning(
                f"❌ Usuário não encontrado no banco de dados",
                context={"username": credentials.username}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário ou senha inválidos"
            )
    except HTTPException:
        # Re-raise HTTP exceptions (usuário não encontrado)
        raise
    except Exception as e:
        log_error(
            f"❌ Erro ao buscar usuário",
            exc=e,
            context={
                "username": credentials.username,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar usuário: {str(e)}"
        )

    # Validar senha - log detalhado antes e depois
    password_hash = user.password_hash
    hash_length = len(password_hash) if password_hash else 0
    hash_format = "unknown"
    hash_starts_with = password_hash[:20] if password_hash and len(password_hash) >= 20 else password_hash if password_hash else None
    
    # Detectar formato do hash
    if password_hash:
        if password_hash.startswith("$argon2id$"):
            hash_format = "argon2id (correto)"
        elif password_hash.startswith("$argon2i$"):
            hash_format = "argon2i"
        elif password_hash.startswith("$argon2"):
            hash_format = "argon2 (genérico)"
        elif password_hash.startswith("$2b$") or password_hash.startswith("$2a$") or password_hash.startswith("$2y$"):
            hash_format = "bcrypt"
        elif hash_length == 32 and all(c in '0123456789abcdef' for c in password_hash.lower()):
            hash_format = "MD5 (hex) - INCORRETO"
        elif hash_length < 50:
            hash_format = f"hash muito curto ({hash_length} chars) - possivelmente truncado ou MD5"
    
    log_info(
        f"🔑 Validando senha",
        context={
            "user_id": user.id,
            "username": user.username,
            "role_id": user.role_id,
            "password_hash_length": hash_length,
            "password_hash_format": hash_format,
            "password_hash_starts_with": hash_starts_with
        }
    )
    
    password_valid = verify_password(credentials.password, user.password_hash)
    
    if not password_valid:
        log_warning(
            f"❌ Login FALHOU: Senha incorreta",
            context={
                "username": credentials.username,
                "user_id": user.id,
                "role_id": user.role_id,
                "password_hash_length": hash_length,
                "password_hash_format": hash_format,
                "password_hash_starts_with": hash_starts_with
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos"
        )
    
    log_info(
        f"✅ Senha validada com sucesso",
        context={
            "user_id": user.id,
            "username": user.username,
            "role_id": user.role_id
        }
    )

    # Verificar se usuário está ativo
    if not user.is_active:
        log_warning(
            f"❌ Login FALHOU: Usuário inativo",
            context={"username": credentials.username, "user_id": user.id, "role_id": user.role_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )

    # Verificar se role foi carregada corretamente
    try:
        role = user.role
        if not role:
            log_error(
                f"❌ Erro: Role não carregada para usuário",
                context={"user_id": user.id, "role_id": user.role_id, "username": user.username}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro: Role não encontrada para role_id={user.role_id}"
            )
        
        log_info(
            f"✅ Role carregada",
            context={
                "role_id": role.id,
                "role_name": role.name,
                "role_level": role.level
            }
        )
    except AttributeError as e:
        log_error(
            f"❌ Erro: AttributeError ao acessar role",
            exc=e,
            context={
                "user_id": user.id,
                "role_id": user.role_id,
                "username": user.username,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar role: {str(e)}"
        )
    except Exception as e:
        log_error(
            f"❌ Erro inesperado ao acessar role",
            exc=e,
            context={
                "user_id": user.id,
                "role_id": user.role_id,
                "username": user.username
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar role: {str(e)}"
        )

    # Atualizar último login
    try:
        user.last_login = datetime.utcnow()
        session.add(user)
        session.commit()
        session.refresh(user)
    except Exception as e:
        log_error(f"❌ Erro ao atualizar último login: {e}", exc=e)
        # Não bloquear login se apenas atualização de last_login falhar

    log_success(
        f"✅ Login bem-sucedido: {user.username}",
        context={
            "user_id": user.id,
            "role": role.name,
            "role_id": role.id,
            "role_level": role.level,
            "full_name": user.full_name
        }
    )

    # Criar tokens
    try:
        token_data = {
            "sub": str(user.id),  # JWT spec exige que 'sub' seja string
            "username": user.username,
            "role": role.name
        }

        # Se "lembrar-me", refresh token de 7 dias, senão 1 dia
        refresh_expires_days = settings.REFRESH_TOKEN_EXPIRE_DAYS if credentials.remember_me else 1

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data, expires_delta=timedelta(days=refresh_expires_days))
    except Exception as e:
        log_error(
            f"❌ Erro ao criar tokens",
            exc=e,
            context={
                "user_id": user.id,
                "username": user.username,
                "role_id": role.id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar tokens: {str(e)}"
        )

    # Retornar tokens no corpo da resposta
    try:
        # Criar RoleResponse primeiro para identificar erro específico
        try:
            role_response = RoleResponse(
                id=role.id,
                name=role.name,
                level=role.level,
                description=role.description if hasattr(role, 'description') else None
            )
            log_info(
                f"✅ RoleResponse criado com sucesso",
                context={
                    "role_id": role.id,
                    "role_name": role.name,
                    "role_level": role.level
                }
            )
        except Exception as e:
            log_error(
                f"❌ Erro ao criar RoleResponse",
                exc=e,
                context={
                    "user_id": user.id,
                    "role_id": role.id,
                    "role_name": role.name if hasattr(role, 'name') else None,
                    "role_level": role.level if hasattr(role, 'level') else None,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao criar RoleResponse: {str(e)}"
            )
        
        # Criar UserResponse
        try:
            user_response = UserResponse(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
                email=user.email,
                role=role_response,
                is_active=user.is_active,
                last_login=user.last_login,
                created_at=user.created_at
            )
            log_info(
                f"✅ UserResponse criado com sucesso",
                context={
                    "user_id": user.id,
                    "username": user.username,
                    "role_id": role.id
                }
            )
        except Exception as e:
            log_error(
                f"❌ Erro ao criar UserResponse",
                exc=e,
                context={
                    "user_id": user.id,
                    "username": user.username,
                    "role_id": role.id,
                    "role_name": role.name,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao criar UserResponse: {str(e)}"
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        log_error(
            f"❌ Erro inesperado ao criar resposta",
            exc=e,
            context={
                "user_id": user.id,
                "username": user.username,
                "role_id": role.id if role else None,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar resposta: {str(e)}"
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_response
    )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    request: RefreshTokenRequest,
    session: Session = Depends(get_session)
):
    """
    Renovar access token usando refresh token
    """
    # Decodificar refresh token
    payload = decode_token(request.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido"
        )

    user_id_str = payload.get("sub")

    # Converter sub (string) de volta para int
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    # Buscar usuário com role carregado
    statement = select(User).options(selectinload(User.role)).where(User.id == user_id)
    user = session.exec(statement).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo"
        )

    # Criar novos tokens
    token_data = {
        "sub": str(user.id),  # JWT spec exige que 'sub' seja string
        "username": user.username,
        "role": user.role.name
    }

    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    # Montar resposta
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        role=RoleResponse(
            id=user.role.id,
            name=user.role.name,
            level=user.role.level,
            description=user.role.description
        ),
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=user_response
    )


@router.post("/password-reset/request", response_model=PasswordResetResponse, status_code=status.HTTP_200_OK)
async def request_password_reset(
    request: PasswordResetRequest,
    session: Session = Depends(get_session)
):
    """
    Solicitar recuperação de senha

    Gera token temporário (1 hora)
    """
    # Buscar usuário
    statement = select(User).where(User.username == request.username)
    user = session.exec(statement).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    # Gerar token de recuperação
    reset_token = generate_password_reset_token()
    expires_at = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)

    # Salvar token no banco (tabela password_reset_tokens)
    # TODO: Implementar salvamento no banco quando modelo estiver pronto
    # Por ora, apenas retornar o token

    return PasswordResetResponse(
        message=f"Token de recuperação gerado para o usuário '{user.username}'",
        reset_token=reset_token,
        expires_in_hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
    )


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    request: PasswordResetConfirm,
    session: Session = Depends(get_session)
):
    """
    Confirmar recuperação de senha com token

    Define nova senha
    """
    # TODO: Validar token no banco (tabela password_reset_tokens)
    # Por ora, implementação simplificada

    # Validar força da senha
    is_valid, message = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    # Gerar novo hash
    new_hash = get_password_hash(request.new_password)

    # TODO: Buscar usuário pelo token e atualizar senha
    # Por ora, retornar sucesso

    return {
        "message": "Senha atualizada com sucesso",
        "detail": "Faça login com sua nova senha"
    }


@router.post("/password/change", status_code=status.HTTP_200_OK)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Trocar senha (usuário autenticado)

    Requer senha atual
    """
    # Verificar senha atual
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha atual incorreta"
        )

    # Validar nova senha
    is_valid, message = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    # Atualizar senha
    current_user.password_hash = get_password_hash(request.new_password)
    current_user.updated_at = datetime.utcnow()

    session.add(current_user)
    session.commit()

    return {
        "message": "Senha atualizada com sucesso"
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    """
    Logout do usuário

    Com token em localStorage, o logout é feito no frontend
    """
    return {"message": "Logout realizado com sucesso"}


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Obter informações do usuário autenticado
    """
    log_info(
        f"📋 Obter informações do usuário autenticado",
        context={
            "username": current_user.username,
            "user_id": current_user.id,
            "role": current_user.role.name
        }
    )

    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        email=current_user.email,
        role=RoleResponse(
            id=current_user.role.id,
            name=current_user.role.name,
            level=current_user.role.level,
            description=current_user.role.description
        ),
        is_active=current_user.is_active,
        last_login=current_user.last_login,
        created_at=current_user.created_at
    )
