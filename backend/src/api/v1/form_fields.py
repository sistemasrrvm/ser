"""
API v1: Campos de Formulários
Endpoints CRUD para campos de formulários
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime

from ...core import get_session, require_admin, get_current_user
from ...core.colored_logging import log_error, log_warning
from ...models import FormField, FormPage, User
from ...schemas import (
    FormFieldCreate,
    FormFieldUpdate,
    FormFieldResponse,
    FormFieldListResponse
)
from pydantic import BaseModel
from typing import List


class FieldReorderItem(BaseModel):
    id: int
    ordem: int


class FieldReorderRequest(BaseModel):
    fields: List[FieldReorderItem]


router = APIRouter(prefix="/form-pages/{page_id}/fields", tags=["Campos de Formulários"])


@router.post("", response_model=FormFieldResponse, status_code=status.HTTP_201_CREATED)
async def create_field(
    page_id: int,
    field: FormFieldCreate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Criar novo campo em uma página

    Requer: role admin

    Regras de negócio:
    - RN-011: Label deve ser único dentro da página
    - RN-012: Ordem deve ser única dentro da página
    """
    # Verificar se página existe
    statement = select(FormPage).where(FormPage.id == page_id)
    page = session.exec(statement).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Página com ID {page_id} não encontrada"
        )

    # RN-011: Verificar unicidade de label dentro da página
    statement = select(FormField).where(
        FormField.pagina_id == page_id,
        FormField.rotulo == field.rotulo
    )
    existing_field = session.exec(statement).first()

    if existing_field:
        log_warning(f"Tentativa de criar campo com label duplicado: '{field.rotulo}' na página {page_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe um campo com o label '{field.rotulo}' nesta página"
        )

    # RN-012: Verificar unicidade de ordem dentro da página
    statement = select(FormField).where(
        FormField.pagina_id == page_id,
        FormField.ordem == field.ordem
    )
    existing_order = session.exec(statement).first()

    if existing_order:
        log_warning(f"Tentativa de criar campo com ordem duplicada: {field.ordem} na página {page_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe um campo com ordem {field.ordem} nesta página"
        )

    # Criar campo
    new_field = FormField(
        pagina_id=page_id,
        rotulo=field.rotulo,
        ordem=field.ordem,
        tipo=field.tipo,
        configuracao=field.configuracao,
        regra_exibicao_id=field.regra_exibicao_id
    )

    session.add(new_field)
    session.commit()
    session.refresh(new_field)

    return FormFieldResponse.from_orm(new_field)


@router.get("", response_model=FormFieldListResponse, status_code=status.HTTP_200_OK)
async def list_fields(
    page_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Listar todos os campos de uma página

    Requer: autenticação (qualquer usuário autenticado pode ler campos para preencher relatórios)
    """
    # Verificar se página existe
    statement = select(FormPage).where(FormPage.id == page_id)
    page = session.exec(statement).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Página com ID {page_id} não encontrada"
        )

    # Buscar campos ordenados
    statement = select(FormField).where(
        FormField.pagina_id == page_id
    ).order_by(FormField.ordem)
    campos = session.exec(statement).all()

    return FormFieldListResponse(
        total=len(campos),
        campos=[FormFieldResponse.from_orm(c) for c in campos]
    )


@router.get("/{field_id}", response_model=FormFieldResponse, status_code=status.HTTP_200_OK)
async def get_field(
    page_id: int,
    field_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Obter campo por ID

    Requer: autenticação (qualquer usuário autenticado pode ler campos para preencher relatórios)
    """
    statement = select(FormField).where(
        FormField.id == field_id,
        FormField.pagina_id == page_id
    )
    field = session.exec(statement).first()

    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campo com ID {field_id} não encontrado na página {page_id}"
        )

    return FormFieldResponse.from_orm(field)


@router.put("/{field_id}", response_model=FormFieldResponse, status_code=status.HTTP_200_OK)
async def update_field(
    page_id: int,
    field_id: int,
    field_update: FormFieldUpdate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Atualizar campo

    Requer: role admin

    Regras de negócio:
    - RN-011: Label deve ser único dentro da página
    - RN-012: Ordem deve ser única dentro da página
    """
    # Buscar campo
    statement = select(FormField).where(
        FormField.id == field_id,
        FormField.pagina_id == page_id
    )
    field = session.exec(statement).first()

    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campo com ID {field_id} não encontrado na página {page_id}"
        )

    # RN-011: Verificar unicidade de label (se mudou)
    if field_update.rotulo is not None and field_update.rotulo != field.rotulo:
        statement = select(FormField).where(
            FormField.pagina_id == page_id,
            FormField.rotulo == field_update.rotulo,
            FormField.id != field_id
        )
        existing_field = session.exec(statement).first()

        if existing_field:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe um campo com o label '{field_update.rotulo}' nesta página"
            )

        field.rotulo = field_update.rotulo

    # RN-012: Verificar unicidade de ordem (se mudou)
    if field_update.ordem is not None and field_update.ordem != field.ordem:
        statement = select(FormField).where(
            FormField.pagina_id == page_id,
            FormField.ordem == field_update.ordem,
            FormField.id != field_id
        )
        existing_order = session.exec(statement).first()

        if existing_order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe um campo com ordem {field_update.ordem} nesta página"
            )

        field.ordem = field_update.ordem

    # Atualizar type se fornecido
    if field_update.tipo is not None:
        field.tipo = field_update.tipo

    # Atualizar config se fornecido
    if field_update.configuracao is not None:
        field.configuracao = field_update.configuracao

    # Atualizar show_when_rule_id se fornecido
    if field_update.regra_exibicao_id is not None:
        field.regra_exibicao_id = field_update.regra_exibicao_id

    field.updated_at = datetime.utcnow()

    session.add(field)
    session.commit()
    session.refresh(field)

    return FormFieldResponse.from_orm(field)


@router.post("/reorder", status_code=status.HTTP_200_OK)
async def reorder_fields(
    page_id: int,
    reorder_request: FieldReorderRequest,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Reordenar campos em lote

    Requer: role admin

    Este endpoint atualiza a ordem de múltiplos campos de uma vez,
    evitando conflitos de ordem durante drag-and-drop.
    """
    # Verificar se página existe
    statement = select(FormPage).where(FormPage.id == page_id)
    page = session.exec(statement).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Página com ID {page_id} não encontrada"
        )

    # Atualizar todos os campos em uma transação
    for field_update in reorder_request.fields:
        statement = select(FormField).where(
            FormField.id == field_update.id,
            FormField.pagina_id == page_id
        )
        field = session.exec(statement).first()

        if not field:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campo com ID {field_update.id} não encontrado"
            )

        field.ordem = field_update.ordem
        field.updated_at = datetime.utcnow()
        session.add(field)

    session.commit()

    return {
        "message": f"{len(reorder_request.fields)} campos reordenados com sucesso"
    }


@router.delete("/{field_id}", status_code=status.HTTP_200_OK)
async def delete_field(
    page_id: int,
    field_id: int,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Excluir campo

    Requer: role admin

    Regra de negócio:
    - RN-013: Não pode excluir se estiver em uso em condições de regras
    (Validação será implementada na Sprint 004 quando Regras forem criadas)
    """
    # Buscar campo
    statement = select(FormField).where(
        FormField.id == field_id,
        FormField.pagina_id == page_id
    )
    field = session.exec(statement).first()

    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campo com ID {field_id} não encontrado na página {page_id}"
        )

    # TODO Sprint 004: Verificar se campo está em uso em condições de regras
    # RN-013: Campo não pode ser excluído se estiver sendo usado como campo_origem
    # em alguma condição de regra de visibilidade

    # Excluir campo
    session.delete(field)
    session.commit()

    return {
        "message": f"Campo '{field.rotulo}' excluído com sucesso",
        "id": field_id
    }
