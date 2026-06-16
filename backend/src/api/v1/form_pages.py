"""
API v1: Páginas de Formulários
Endpoints CRUD para páginas de formulários
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime

from ...core import get_session, require_admin, get_current_user
from ...models import FormPage, Formulario, User, FormField
from ...schemas import (
    FormPageCreate,
    FormPageUpdate,
    FormPageResponse,
    FormPageListResponse
)
from pydantic import BaseModel
from typing import List


class PageReorderItem(BaseModel):
    id: int
    ordem: int


class PageReorderRequest(BaseModel):
    pages: List[PageReorderItem]


router = APIRouter(prefix="/form-templates/{template_id}/pages", tags=["Páginas de Formulários"])


@router.post("", response_model=FormPageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    template_id: int,
    page: FormPageCreate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Criar nova página em um formulário

    Requer: role admin

    Regras de negócio:
    - RN-005: Label deve ser único dentro do formulário
    - RN-006: Ordem deve ser única dentro do formulário
    """
    # Verificar se formulário existe
    statement = select(Formulario).where(Formulario.id == template_id)
    formulario = session.exec(statement).first()

    if not formulario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulário com ID {template_id} não encontrado"
        )

    # RN-005: Verificar unicidade de label dentro do formulário
    statement = select(FormPage).where(
        FormPage.formulario_id == template_id,
        FormPage.nome == page.nome
    )
    existing_page = session.exec(statement).first()

    if existing_page:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe uma página com o label '{page.nome}' neste formulário"
        )

    # RN-006: Verificar unicidade de ordem dentro do formulário
    statement = select(FormPage).where(
        FormPage.formulario_id == template_id,
        FormPage.ordem == page.ordem
    )
    existing_order = session.exec(statement).first()

    if existing_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe uma página com ordem {page.ordem} neste formulário"
        )

    # Criar página
    new_page = FormPage(
        formulario_id=template_id,
        nome=page.nome,
        ordem=page.ordem,
        regra_exibicao_id=page.regra_exibicao_id
    )

    session.add(new_page)
    session.commit()
    session.refresh(new_page)

    return FormPageResponse.from_orm(new_page)


@router.get("", response_model=FormPageListResponse, status_code=status.HTTP_200_OK)
async def list_pages(
    template_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Listar todas as páginas de um formulário

    Requer: autenticação (qualquer usuário autenticado pode ler páginas para preencher relatórios)
    """
    # Verificar se formulário existe
    statement = select(Formulario).where(Formulario.id == template_id)
    formulario = session.exec(statement).first()

    if not formulario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulário com ID {template_id} não encontrado"
        )

    # Buscar páginas ordenadas
    statement = select(FormPage).where(
        FormPage.formulario_id == template_id
    ).order_by(FormPage.ordem)
    paginas = session.exec(statement).all()

    return FormPageListResponse(
        total=len(paginas),
        paginas=[FormPageResponse.from_orm(p) for p in paginas]
    )


@router.get("/{page_id}", response_model=FormPageResponse, status_code=status.HTTP_200_OK)
async def get_page(
    template_id: int,
    page_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Obter página por ID

    Requer: autenticação (qualquer usuário autenticado pode ler páginas para preencher relatórios)
    """
    statement = select(FormPage).where(
        FormPage.id == page_id,
        FormPage.formulario_id == template_id
    )
    page = session.exec(statement).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Página com ID {page_id} não encontrada no formulário {template_id}"
        )

    return FormPageResponse.from_orm(page)


@router.put("/{page_id}", response_model=FormPageResponse, status_code=status.HTTP_200_OK)
async def update_page(
    template_id: int,
    page_id: int,
    page_update: FormPageUpdate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Atualizar página

    Requer: role admin

    Regras de negócio:
    - RN-005: Label deve ser único dentro do formulário
    - RN-006: Ordem deve ser única dentro do formulário
    """
    # Buscar página
    statement = select(FormPage).where(
        FormPage.id == page_id,
        FormPage.formulario_id == template_id
    )
    page = session.exec(statement).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Página com ID {page_id} não encontrada no formulário {template_id}"
        )

    # RN-005: Verificar unicidade de label (se mudou)
    if page_update.nome is not None and page_update.nome != page.nome:
        statement = select(FormPage).where(
            FormPage.formulario_id == template_id,
            FormPage.nome == page_update.nome,
            FormPage.id != page_id
        )
        existing_page = session.exec(statement).first()

        if existing_page:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe uma página com o label '{page_update.nome}' neste formulário"
            )

        page.nome = page_update.nome

    # RN-006: Verificar unicidade de ordem (se mudou)
    if page_update.ordem is not None and page_update.ordem != page.ordem:
        statement = select(FormPage).where(
            FormPage.formulario_id == template_id,
            FormPage.ordem == page_update.ordem,
            FormPage.id != page_id
        )
        existing_order = session.exec(statement).first()

        if existing_order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe uma página com ordem {page_update.ordem} neste formulário"
            )

        page.ordem = page_update.ordem

    # Atualizar show_when_rule_id se fornecido
    if page_update.regra_exibicao_id is not None:
        page.regra_exibicao_id = page_update.regra_exibicao_id

    page.updated_at = datetime.utcnow()

    session.add(page)
    session.commit()
    session.refresh(page)

    return FormPageResponse.from_orm(page)


@router.post("/reorder", status_code=status.HTTP_200_OK)
async def reorder_pages(
    template_id: int,
    reorder_request: PageReorderRequest,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Reordenar páginas em lote

    Requer: role admin

    Este endpoint atualiza a ordem de múltiplas páginas de uma vez,
    evitando conflitos de ordem durante drag-and-drop.
    """
    # Verificar se formulário existe
    statement = select(Formulario).where(Formulario.id == template_id)
    formulario = session.exec(statement).first()

    if not formulario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulário com ID {template_id} não encontrado"
        )

    # Atualizar todas as páginas em uma transação
    for page_update in reorder_request.pages:
        statement = select(FormPage).where(
            FormPage.id == page_update.id,
            FormPage.formulario_id == template_id
        )
        page = session.exec(statement).first()

        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Página com ID {page_update.id} não encontrada"
            )

        page.ordem = page_update.ordem
        page.updated_at = datetime.utcnow()
        session.add(page)

    session.commit()

    return {
        "message": f"{len(reorder_request.pages)} páginas reordenadas com sucesso"
    }


@router.delete("/{page_id}", status_code=status.HTTP_200_OK)
async def delete_page(
    template_id: int,
    page_id: int,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Excluir página

    Requer: role admin

    Regra de negócio:
    - RN-007: Não pode excluir se houver campos associados
    """
    # Buscar página
    statement = select(FormPage).where(
        FormPage.id == page_id,
        FormPage.formulario_id == template_id
    )
    page = session.exec(statement).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Página com ID {page_id} não encontrada no formulário {template_id}"
        )

    # RN-007: Verificar se há campos associados
    statement = select(FormField).where(FormField.pagina_id == page_id)
    campos = session.exec(statement).all()

    if campos:
        campo_labels = [f"• {c.rotulo}" for c in campos[:5]]  # Mostrar até 5 campos
        if len(campos) > 5:
            campo_labels.append(f"• ... e mais {len(campos) - 5} campos")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"❌ Não é possível excluir esta página.\n\n"
                   f"Existem {len(campos)} campos associados:\n" +
                   "\n".join(campo_labels) +
                   "\n\nRemova os campos primeiro."
        )

    # Excluir página
    session.delete(page)
    session.commit()

    return {
        "message": f"Página '{page.nome}' excluída com sucesso",
        "id": page_id
    }
