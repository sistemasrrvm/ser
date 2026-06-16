"""
API v1: Usuários
Endpoints para gerenciar usuários do sistema
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.exceptions import RequestValidationError
from sqlmodel import Session, select
from datetime import datetime
from typing import Optional

from ...core import get_session, get_current_user, require_admin
from ...core.security import get_password_hash
from ...core.colored_logging import log_error, log_warning, log_success, log_info
from ...models import User
from ...schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse
)


router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.get("", response_model=UserListResponse, status_code=status.HTTP_200_OK)
async def list_usuarios(
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Listar todos os usuários
    
    Parâmetros:
    - is_active: True (apenas ativos), False (apenas inativos), None (todos)
    
    Requer: admin
    """
    statement = select(User)
    
    # Filtrar por status se especificado
    if is_active is not None:
        statement = statement.where(User.is_active == is_active)
    
    statement = statement.order_by(User.is_active.desc(), User.username)
    usuarios = session.exec(statement).all()

    log_info(
        f"📋 Listando usuários",
        context={
            "total": len(usuarios),
            "filter": "ativos" if is_active is True else ("inativos" if is_active is False else "todos"),
            "requested_by": current_user.username
        }
    )

    return UserListResponse(
        total=len(usuarios),
        users=[UserResponse.from_orm(u) for u in usuarios]
    )


@router.get("/{usuario_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_usuario(
    usuario_id: int,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Obter usuário por ID

    Requer: admin
    """
    usuario = session.get(User, usuario_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {usuario_id} não encontrado"
        )

    return UserResponse.from_orm(usuario)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    usuario_data: UserCreate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Criar novo usuário

    Requer: admin
    """
    log_info(
        f"📝 Criando novo usuário",
        context={
            "username": usuario_data.username,
            "full_name": usuario_data.full_name,
            "role_id": usuario_data.role_id,
            "created_by": current_user.username
        }
    )
    
    # Validar role_id
    if not usuario_data.role_id or usuario_data.role_id == 0:
        log_warning(
            "❌ Erro de validação: role_id inválido",
            context={"role_id": usuario_data.role_id}
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="role_id é obrigatório e deve ser um ID válido"
        )
    
    # Verificar se role existe
    from ...models import Role
    role = session.get(Role, usuario_data.role_id)
    if not role:
        log_warning(
            "❌ Role não encontrado",
            context={"role_id": usuario_data.role_id}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role com ID {usuario_data.role_id} não encontrado"
        )
    
    # Verificar se username já existe
    statement = select(User).where(User.username == usuario_data.username)
    existing = session.exec(statement).first()

    if existing:
        log_warning(
            "❌ Username já existe",
            context={"username": usuario_data.username}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe um usuário com username '{usuario_data.username}'"
        )

    # Verificar se email já existe
    if usuario_data.email:
        statement = select(User).where(User.email == usuario_data.email)
        existing_email = session.exec(statement).first()
        if existing_email:
            log_warning(
                "❌ Email já existe",
                context={"email": usuario_data.email}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe um usuário com email '{usuario_data.email}'"
            )

    # Criar usuário
    try:
        user_dict = usuario_data.model_dump(exclude={'password'})
        user_dict['password_hash'] = get_password_hash(usuario_data.password)

        novo_usuario = User(**user_dict)
        session.add(novo_usuario)
        session.commit()
        session.refresh(novo_usuario)

        log_success(
            f"✅ Usuário criado com sucesso",
            context={
                "user_id": novo_usuario.id,
                "username": novo_usuario.username,
                "role": role.name
            }
        )

        return UserResponse.from_orm(novo_usuario)
    except Exception as e:
        log_error(
            "Erro ao criar usuário",
            exc=e,
            context={
                "username": usuario_data.username,
                "role_id": usuario_data.role_id
            }
        )
        raise


@router.put("/{usuario_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_usuario(
    usuario_id: int,
    usuario_data: UserUpdate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Atualizar usuário

    Requer: admin
    """
    usuario = session.get(User, usuario_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {usuario_id} não encontrado"
        )

    # Verificar se email já existe em outro usuário
    if usuario_data.email and usuario_data.email != usuario.email:
        statement = select(User).where(User.email == usuario_data.email)
        existing_email = session.exec(statement).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe um usuário com email '{usuario_data.email}'"
            )

    # Atualizar campos
    update_data = usuario_data.model_dump(exclude_unset=True, exclude={'password'})
    
    # Atualizar senha se fornecida
    if usuario_data.password:
        update_data['password_hash'] = get_password_hash(usuario_data.password)
    
    for key, value in update_data.items():
        setattr(usuario, key, value)

    usuario.updated_at = datetime.utcnow()
    session.add(usuario)
    session.commit()
    session.refresh(usuario)

    return UserResponse.from_orm(usuario)


@router.delete("/{usuario_id}", status_code=status.HTTP_200_OK)
async def delete_usuario(
    usuario_id: int,
    permanent: bool = Query(default=False, description="Exclusão definitiva (hard delete)"),
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Deletar usuário
    
    - Soft delete (permanent=False): Marca como inativo
    - Hard delete (permanent=True): Exclui definitivamente do banco
    
    Requer: admin
    """
    usuario = session.get(User, usuario_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {usuario_id} não encontrado"
        )

    # Não permitir desativar/excluir o próprio usuário
    if usuario.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode desativar ou excluir seu próprio usuário"
        )

    if permanent:
        # Hard delete - exclusão definitiva
        log_warning(
            f"🗑️ Excluindo usuário definitivamente",
            context={
                "user_id": usuario.id,
                "username": usuario.username,
                "deleted_by": current_user.username
            }
        )
        
        session.delete(usuario)
        session.commit()
        
        log_success(
            f"✅ Usuário excluído definitivamente",
            context={
                "user_id": usuario_id,
                "username": usuario.username
            }
        )
        
        return {
            "message": f"Usuário '{usuario.username}' excluído definitivamente",
            "id": usuario_id
        }
    else:
        # Soft delete - apenas marca como inativo
        usuario.is_active = False
        usuario.updated_at = datetime.utcnow()
        session.add(usuario)
        session.commit()
        
        log_info(
            f"📝 Usuário marcado como inativo",
            context={
                "user_id": usuario.id,
                "username": usuario.username,
                "deactivated_by": current_user.username
            }
        )

        return {
            "message": f"Usuário '{usuario.username}' marcado como inativo",
            "id": usuario_id
        }


@router.patch("/{usuario_id}/reactivate", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def reactivate_usuario(
    usuario_id: int,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Reativar usuário inativo
    
    Requer: admin
    """
    usuario = session.get(User, usuario_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {usuario_id} não encontrado"
        )

    if usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Usuário '{usuario.username}' já está ativo"
        )

    # Reativar usuário
    usuario.is_active = True
    usuario.updated_at = datetime.utcnow()
    session.add(usuario)
    session.commit()
    session.refresh(usuario)

    log_success(
        f"✅ Usuário reativado",
        context={
            "user_id": usuario.id,
            "username": usuario.username,
            "reactivated_by": current_user.username
        }
    )

    return UserResponse.from_orm(usuario)
