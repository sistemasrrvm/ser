"""
API v1: Roles
Endpoints para gerenciar roles/perfis do sistema
"""

from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select

from ...core import get_session, get_current_user
from ...models import User, Role
from ...schemas.user import RoleResponse, RoleListResponse


router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=RoleListResponse, status_code=status.HTTP_200_OK)
async def list_roles(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Listar todos os roles/perfis disponíveis
    
    Requer: autenticação
    """
    statement = select(Role).order_by(Role.level.desc(), Role.name)
    roles = session.exec(statement).all()

    return RoleListResponse(
        total=len(roles),
        roles=[RoleResponse.from_orm(r) for r in roles]
    )

