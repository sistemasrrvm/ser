"""
Dependencies para FastAPI
Funções reutilizáveis para proteção de rotas e verificação de permissões
"""

from fastapi import Depends, HTTPException, status, Cookie, Header
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import Optional

from .database import get_session
from .security import decode_token
from ..models.user import User


async def get_current_user(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    session: Session = Depends(get_session)
) -> User:
    """
    Dependency para obter usuário autenticado via Authorization header (Bearer token) ou cookie

    Args:
        authorization: Header Authorization (Bearer <token>)
        access_token: Token JWT do cookie (fallback)
        session: Sessão do banco de dados

    Returns:
        User: Usuário autenticado

    Raises:
        HTTPException: Se token inválido ou usuário não encontrado
    """
    # Priorizar Authorization header sobre cookie
    token = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Converter sub (string) de volta para int
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Carregar user com role para evitar erro ao acessar user.role
    statement = select(User).options(selectinload(User.role)).where(User.id == user_id)
    user = session.exec(statement).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )

    return user


SUPORTE_ROLE_NAMES = frozenset({'suporte', 'suporte ao cliente', 'revisor'})
TECNICO_ROLE_NAMES = frozenset({'tecnico', 'usuario'})


def can_create_report(user: User) -> bool:
    """
    Apenas perfil Técnico pode criar relatório (#244).
    Suporte (incl. Suporte ao Cliente) e Administrador: não.
    """
    if not user.role:
        return False

    role_name = user.role.name.strip().lower()
    level = user.role.level

    if level >= 100 or role_name in ('admin', 'administrador'):
        return False

    if role_name in SUPORTE_ROLE_NAMES or (50 <= level < 100):
        return False

    if role_name in TECNICO_ROLE_NAMES or (20 <= level < 50):
        return True

    return False


def require_role_level(min_level: int):
    """
    Dependency factory para verificar nível mínimo de role

    Args:
        min_level: Nível mínimo requerido (20=usuario, 40=revisor, 100=admin)

    Returns:
        Dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Nível mínimo requerido: {min_level}"
            )
        return current_user

    return role_checker


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency para verificar se usuário é admin

    Args:
        current_user: Usuário autenticado

    Returns:
        User: Usuário admin

    Raises:
        HTTPException: Se usuário não for admin
    """
    if current_user.role.level < 100:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores."
        )
    return current_user


def require_suporte_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Suporte, revisor ou administrador (#292 sync NR13)."""
    if not current_user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado.",
        )

    role_name = current_user.role.name.strip().lower()
    level = current_user.role.level

    if level >= 100 or role_name in ("admin", "administrador"):
        return current_user
    if role_name in SUPORTE_ROLE_NAMES or (50 <= level < 100):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Acesso negado. Apenas suporte ou administrador.",
    )
