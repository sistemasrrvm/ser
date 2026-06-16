"""
API v1: Reports (Relatórios)
Endpoints CRUD para relatórios de inspeção
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from sqlalchemy import text
from datetime import datetime, date
from typing import List, Optional

from ...core import get_session, get_current_user
from ...core.dependencies import can_create_report
from ...core.report_permissions import (
    can_view_report,
    can_edit_report,
    can_delete_report,
    can_export_excel,
    can_update_report_status,
    can_request_correction,
    list_reports_exclude_rascunho_for_suporte,
    list_reports_owner_only,
)
from ...models.report_correcao import ReportCorrecao
from ...models import Report, ManutCliente, ManutEquipamento, User, Formulario
from ...services.report_field_sync import (
    build_lookup_fields_cache,
    resolve_cliente_equipamento_names,
    sync_report_foreign_keys,
)
from ...models.lookup_list import LookupList
from ...schemas import (
    ReportCreate,
    ReportUpdate,
    ReportStatusUpdate,
    SolicitarCorrecaoRequest,
    ReportCorrecaoResponse,
    ReportCorrecaoListResponse,
    ReportResponse,
    ReportListItem,
    ReportListResponse,
    ClienteResponse,
    EquipamentoResponse,
    TecnicoResponse,
    FormTemplateResponse
)


router = APIRouter(prefix="/reports", tags=["Relatórios"])


def _report_to_response(report: Report) -> ReportResponse:
    """Serializa Report garantindo campos obrigatórios do schema (#246)."""
    if report.respostas is None:
        report.respostas = {}
    return ReportResponse.model_validate(report)


def _format_date_for_excel(value, date_format: str = "dd_mm_yyyy") -> str:
    """
    Formata valor de data para exibição no Excel.
    date_format: dd_mm_yyyy (DD/MM/YYYY), yyyy_mm_dd (YYYY/MM/DD), dd_mmm (DD-MMM)
    Aceita string ISO (AAAA-MM-DD), DD-MM-AAAA ou objeto date/datetime.
    """
    if value is None:
        return ""
    parsed = None
    if isinstance(value, (date, datetime)):
        parsed = value if isinstance(value, datetime) else datetime.combine(value, datetime.min.time())
    else:
        s = str(value).strip().split("T")[0]
        if not s:
            return ""
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y"):
            try:
                parsed = datetime.strptime(s, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            return str(value)
    # Formatar conforme date_format do campo
    month_pt = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")
    if date_format == "yyyy_mm_dd":
        return parsed.strftime("%Y/%m/%d")
    if date_format == "dd_mmm":
        return parsed.strftime("%d") + "-" + month_pt[parsed.month - 1]
    # default: dd_mm_yyyy
    return parsed.strftime("%d/%m/%Y")


def _format_yes_no_for_export(value, export_format: str = "sim_nao") -> str:
    """
    Formata valor yes_no para exportação conforme config do campo.
    export_format: sim_nao, yes_no, true_false, um_zero, s_n, simbolos
    """
    is_true = value in (True, "true", "True", 1)
    if export_format == "yes_no":
        return "Yes" if is_true else "No"
    if export_format == "true_false":
        return "true" if is_true else "false"
    if export_format == "um_zero":
        return "1" if is_true else "0"
    if export_format == "s_n":
        return "S" if is_true else "N"
    if export_format == "simbolos":
        return "■" if is_true else "□"
    # default: sim_nao
    return "Sim" if is_true else "Não"


def _resolve_lookup_label_for_export(session: Session, field, field_value) -> Optional[str]:
    """
    Resolve label de campo lookup para exportação.
    Retorna None quando não consegue resolver.
    """
    config = field.configuracao or {}
    source_type = config.get("source_type")
    if field_value is None or str(field_value).strip() == "":
        return None

    try:
        if source_type == "view":
            target_view = config.get("target_view")
            if not target_view:
                return None
            row = session.execute(
                text(f"SELECT label FROM {target_view} WHERE id = :id LIMIT 1"),
                {"id": field_value}
            ).first()
            return str(row[0]) if row and row[0] is not None else None

        if source_type == "list":
            target_list_id = config.get("target_list_id")
            if not target_list_id:
                return None
            lista = session.get(LookupList, str(target_list_id))
            if not lista or not lista.opcoes:
                return None
            value_str = str(field_value)
            for opcao in lista.opcoes:
                if str(opcao.get("id", "")) == value_str:
                    return str(opcao.get("label", "")) or None
            return None
    except Exception:
        return None

    # source_type=form ainda não possui backend lookup-options implementado
    return None


def _format_lookup_for_export(session: Session, field, field_value) -> str:
    """
    Formata valor de lookup para exportação com base em configuracao.export_lookup_value.
    Opções: id | label | id_label (padrão: label)
    """
    config = field.configuracao or {}
    export_mode = config.get("export_lookup_value", "label")
    value_str = "" if field_value is None else str(field_value)
    label = _resolve_lookup_label_for_export(session, field, field_value)

    if export_mode == "id":
        return value_str
    if export_mode == "id_label":
        if value_str and label:
            return f"{value_str} | {label}"
        return label or value_str
    # default: label
    return label or value_str


def generate_report_number(session: Session) -> str:
    """
    Gerar número único do relatório no formato REL-YYYY-000001
    """
    current_year = datetime.now().year

    # Buscar último número do ano atual
    statement = select(Report).where(
        func.year(Report.created_at) == current_year
    ).order_by(Report.id.desc())

    last_report = session.exec(statement).first()

    if last_report and last_report.numero:
        # Extrair número sequencial
        try:
            last_seq = int(last_report.numero.split('-')[-1])
            next_seq = last_seq + 1
        except (ValueError, IndexError):
            next_seq = 1
    else:
        next_seq = 1

    return f"REL-{current_year}-{next_seq:06d}"


def replace_special_values(value: str, report: Report, user: User) -> str:
    """
    Substituir valores especiais nos campos do formulário

    Valores especiais suportados:
    - {{usuario.login}} -> username do usuário
    - {{usuario.nome}} -> nome completo do usuário
    - {{relatorio.numero}} -> número do relatório
    """
    if not value or not isinstance(value, str):
        return value

    replacements = {
        '{{usuario.login}}': user.username if user else '',
        '{{usuario.nome}}': user.full_name if user else '',
        '{{relatorio.numero}}': report.numero if report else '',
    }

    result = value
    for placeholder, replacement in replacements.items():
        result = result.replace(placeholder, replacement)

    return result


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Criar novo relatório (KICKOFF)

    Requer: autenticação

    Cria um relatório em status 'rascunho' com dados iniciais.
    O técnico é automaticamente o usuário logado.
    """
    if not can_create_report(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para criar novos relatórios",
        )

    # Verificar se template existe (obrigatório)
    template = session.get(Formulario, report_data.form_template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template de formulário com ID {report_data.form_template_id} não encontrado"
        )

    # Verificar se cliente existe (se fornecido)
    if report_data.cliente_id:
        cliente = session.get(ManutCliente, report_data.cliente_id)
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente com ID {report_data.cliente_id} não encontrado"
            )

    # Verificar se equipamento existe (se fornecido)
    if report_data.equipamento_id:
        equipamento = session.get(ManutEquipamento, report_data.equipamento_id)
        if not equipamento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipamento com ID {report_data.equipamento_id} não encontrado"
            )

    # Gerar número do relatório
    numero = generate_report_number(session)

    # Criar relatório
    new_report = Report(
        numero=numero,
        form_template_id=report_data.form_template_id,
        cliente_id=report_data.cliente_id,
        equipamento_id=report_data.equipamento_id,
        tipo_inspecao=report_data.tipo_inspecao,
        tecnico_id=current_user.id,
        status="rascunho",
        respostas={},
        observacoes=report_data.observacoes,
        data_inspecao=report_data.data_inspecao
    )

    session.add(new_report)
    session.commit()
    session.refresh(new_report)

    return ReportResponse.from_orm(new_report)


@router.get("", response_model=ReportListResponse, status_code=status.HTTP_200_OK)
async def list_reports(
    status_filter: Optional[str] = Query(None, alias="status", description="Filtrar por status"),
    cliente_id: Optional[int] = Query(None, description="Filtrar por cliente (CLI_ID)"),
    equipamento_id: Optional[int] = Query(None, description="Filtrar por equipamento (EQP_ID)"),
    tecnico_id: Optional[int] = Query(None, description="Filtrar por técnico"),
    data_inicio: Optional[date] = Query(None, description="Data inicial"),
    data_fim: Optional[date] = Query(None, description="Data final"),
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Listar relatórios com filtros e paginação

    Requer: autenticação

    Regras (#275):
    - Técnico: só seus relatórios
    - Suporte: sem rascunhos (em elaboração)
    - Admin: todos
    """
    statement = select(Report)

    if list_reports_owner_only(current_user):
        statement = statement.where(Report.tecnico_id == current_user.id)
    elif list_reports_exclude_rascunho_for_suporte(current_user):
        statement = statement.where(Report.status != 'rascunho')

    user_level = getattr(current_user.role, 'level', 0) if current_user.role else 0

    # Aplicar filtros
    if status_filter:
        statement = statement.where(Report.status == status_filter)

    if cliente_id:
        statement = statement.where(Report.cliente_id == cliente_id)

    if equipamento_id:
        statement = statement.where(Report.equipamento_id == equipamento_id)

    if tecnico_id and not list_reports_owner_only(current_user):
        statement = statement.where(Report.tecnico_id == tecnico_id)

    if data_inicio:
        statement = statement.where(Report.created_at >= datetime.combine(data_inicio, datetime.min.time()))

    if data_fim:
        statement = statement.where(Report.created_at <= datetime.combine(data_fim, datetime.max.time()))

    # Contar total
    count_statement = select(func.count()).select_from(statement.subquery())
    total = session.exec(count_statement).one()

    # Paginação e ordenação
    statement = statement.order_by(Report.created_at.desc())
    statement = statement.offset((page - 1) * limit).limit(limit)

    reports = session.exec(statement).all()

    lookup_cache = build_lookup_fields_cache(
        session, [r.form_template_id for r in reports]
    )

    # Montar response com joins
    reports_list = []
    for report in reports:
        lookup_fields = lookup_cache.get(report.form_template_id, [])
        cliente_nome, equipamento_nome = resolve_cliente_equipamento_names(
            report, session, lookup_fields
        )
        tecnico = session.get(User, report.tecnico_id)
        form_template = session.get(Formulario, report.form_template_id)

        reports_list.append(ReportListItem(
            id=report.id,
            numero=report.numero,
            cliente_nome=cliente_nome or "N/A",
            equipamento_nome=equipamento_nome or "N/A",
            tipo_inspecao=report.tipo_inspecao,
            form_template_nome=form_template.nome if form_template else "N/A",
            tecnico_nome=tecnico.full_name if tecnico else "N/A",
            tecnico_id=report.tecnico_id,
            status=report.status,
            data_inspecao=report.data_inspecao,
            created_at=report.created_at
        ))

    return ReportListResponse(
        total=total,
        page=page,
        limit=limit,
        reports=reports_list
    )


@router.get("/{report_id}", response_model=ReportResponse, status_code=status.HTTP_200_OK)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Obter relatório por ID com todos os relacionamentos

    Requer: autenticação

    Regras:
    - INSPETOR: só pode ver seus próprios relatórios
    - SUPORTE/ADMIN: pode ver qualquer relatório
    """
    report = session.get(Report, report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relatório com ID {report_id} não encontrado"
        )

    if not can_view_report(current_user, report):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para visualizar este relatório"
        )

    # Carregar relacionamentos
    cliente = session.get(ManutCliente, report.cliente_id) if report.cliente_id else None
    equipamento = session.get(ManutEquipamento, report.equipamento_id) if report.equipamento_id else None
    tecnico = session.get(User, report.tecnico_id)
    template = session.get(Formulario, report.form_template_id)

    # Processar valores padrão com valores especiais
    if template:
        from ...models.form_page import FormPage
        from ...models.form_field import FormField

        # Garantir que respostas não seja None
        if report.respostas is None:
            report.respostas = {}

        # Fazer uma cópia do dicionário de respostas
        respostas_atualizadas = dict(report.respostas)

        # Buscar todas as páginas e campos do template
        paginas = session.exec(
            select(FormPage).where(FormPage.formulario_id == template.id).order_by(FormPage.ordem)
        ).all()

        for pagina in paginas:
            campos = session.exec(
                select(FormField).where(FormField.pagina_id == pagina.id).order_by(FormField.ordem)
            ).all()

            for campo in campos:
                # IMPORTANTE: Frontend usa formato campo_{id}, backend deve seguir o mesmo padrão
                campo_key = f"campo_{campo.id}"
                # Se o campo ainda não tem resposta E tem valor padrão configurado
                if campo_key not in respostas_atualizadas and campo.configuracao:
                    default_value = campo.configuracao.get('default_value', '')
                    if default_value:
                        # Substituir valores especiais
                        processed_value = replace_special_values(default_value, report, current_user)
                        # Adicionar ao dicionário de respostas
                        respostas_atualizadas[campo_key] = processed_value
                # yes_no: "true"/"false" quando respondido; "" quando sem resposta (nada selecionado)
                if campo.tipo == "yes_no":
                    val = respostas_atualizadas.get(campo_key)
                    if val in (True, "true", "True", 1):
                        respostas_atualizadas[campo_key] = "true"
                    elif val in (False, "false", "False"):
                        respostas_atualizadas[campo_key] = "false"
                    else:
                        respostas_atualizadas[campo_key] = ""

        # Atualizar respostas do report
        report.respostas = respostas_atualizadas

    response = ReportResponse.from_orm(report)

    # Adicionar relacionamentos
    if cliente:
        response.cliente = ClienteResponse.model_validate(cliente)
    if equipamento:
        response.equipamento = EquipamentoResponse.model_validate(equipamento)
    if tecnico:
        response.tecnico = TecnicoResponse(
            id=tecnico.id,
            username=tecnico.username,
            nome=tecnico.full_name,
            email=tecnico.email or ""
        )
    if template:
        response.form_template = FormTemplateResponse.from_orm(template)

    return response


@router.put("/{report_id}", response_model=ReportResponse, status_code=status.HTTP_200_OK)
async def update_report(
    report_id: int,
    report_update: ReportUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Atualizar respostas do relatório (WIZARD)

    Requer: autenticação

    Regras (#275): matriz perfil × status em report_permissions
    """
    report = session.get(Report, report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relatório com ID {report_id} não encontrado"
        )

    if not can_edit_report(current_user, report):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para editar este relatório"
        )

    # Atualizar campos (normalizar yes_no para boolean para persistir False corretamente)
    respostas = dict(report_update.respostas)
    template = session.get(Formulario, report.form_template_id)
    if template:
        from ...models.form_page import FormPage
        from ...models.form_field import FormField
        for pagina in session.exec(
            select(FormPage).where(FormPage.formulario_id == template.id).order_by(FormPage.ordem)
        ).all():
            for campo in session.exec(
                select(FormField).where(FormField.pagina_id == pagina.id).order_by(FormField.ordem)
            ).all():
                campo_key = f"campo_{campo.id}"
                if campo.tipo == "yes_no":
                    val = respostas.get(campo_key)
                    if val in (True, "true", "True", 1):
                        respostas[campo_key] = "true"
                    elif val in (False, "false", "False"):
                        respostas[campo_key] = "false"
                    else:
                        # Sem resposta (vazio, None, chave ausente) -> manter vazio
                        respostas[campo_key] = ""
                elif campo.tipo == "textbox" and campo.configuracao:
                    fmt = campo.configuracao.get("format_validation", "none")
                    if fmt == "uppercase":
                        val = respostas.get(campo_key)
                        if isinstance(val, str) and val:
                            respostas[campo_key] = val.upper()
    report.respostas = respostas

    if report_update.observacoes is not None:
        report.observacoes = report_update.observacoes

    if report_update.data_inspecao is not None:
        report.data_inspecao = report_update.data_inspecao

    sync_report_foreign_keys(report, session)
    report.updated_at = datetime.utcnow()

    session.add(report)
    session.commit()
    session.refresh(report)

    return _report_to_response(report)


@router.put("/{report_id}/status", response_model=ReportResponse, status_code=status.HTTP_200_OK)
async def update_report_status(
    report_id: int,
    status_update: ReportStatusUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Atualizar status do relatório

    Requer: autenticação

    Regras (#275 / #246):
    - Técnico: rascunho|em_correcao → em_revisao (próprio)
    - Suporte: em_revisao → aprovado
    - Admin: não altera status
    """
    report = session.get(Report, report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relatório com ID {report_id} não encontrado"
        )

    if not can_view_report(current_user, report):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para alterar status deste relatório"
        )

    if not can_update_report_status(current_user, report, status_update.status):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Transição de status não permitida para seu perfil"
        )

    status_anterior = report.status

    # Atualizar status
    report.status = status_update.status
    report.updated_at = datetime.utcnow()

    session.add(report)
    session.commit()
    session.refresh(report)

    from ...services.email_service import notify_report_event

    if status_update.status == "em_revisao" and status_anterior in ("rascunho", "em_correcao"):
        await notify_report_event(session, report, "finalizar", current_user)
    elif status_update.status == "aprovado" and status_anterior == "em_revisao":
        await notify_report_event(session, report, "aprovar", current_user)

    return _report_to_response(report)


@router.post("/{report_id}/solicitar-correcao", response_model=ReportResponse, status_code=status.HTTP_200_OK)
async def solicitar_correcao(
    report_id: int,
    body: SolicitarCorrecaoRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Suporte solicita correção ao técnico (#246).
    Grava histórico e altera status para em_correcao.
    """
    report = session.get(Report, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relatório com ID {report_id} não encontrado",
        )

    if not can_request_correction(current_user, report):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para solicitar correção neste relatório",
        )

    status_anterior = report.status
    correcao = ReportCorrecao(
        report_id=report.id,
        solicitado_por_id=current_user.id,
        descricao=body.descricao.strip(),
        status_anterior=status_anterior,
        status_novo='em_correcao',
    )
    report.status = 'em_correcao'
    report.updated_at = datetime.utcnow()

    session.add(correcao)
    session.add(report)
    try:
        session.commit()
        session.refresh(report)
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        err = str(e).lower()
        if 'chk_reports_status' in err or 'check constraint' in err:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Status em_correcao bloqueado no banco (CHECK legado). "
                    "Execute migration_020_drop_reports_status_check.sql."
                ),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao solicitar correção: {e}",
        ) from e

    from ...services.email_service import notify_report_event

    await notify_report_event(
        session,
        report,
        "solicitar_correcao",
        current_user,
        correcao_descricao=body.descricao.strip(),
    )

    return _report_to_response(report)


@router.get("/{report_id}/correcoes", response_model=ReportCorrecaoListResponse, status_code=status.HTTP_200_OK)
async def list_report_correcoes(
    report_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Histórico de solicitações de correção (#246)."""
    report = session.get(Report, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relatório com ID {report_id} não encontrado",
        )

    if not can_view_report(current_user, report):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para visualizar este relatório",
        )

    statement = (
        select(ReportCorrecao)
        .where(ReportCorrecao.report_id == report_id)
        .order_by(ReportCorrecao.created_at.desc())
    )
    rows = session.exec(statement).all()

    items = []
    for row in rows:
        solicitante = session.get(User, row.solicitado_por_id)
        items.append(
            ReportCorrecaoResponse(
                id=row.id,
                report_id=row.report_id,
                solicitado_por_id=row.solicitado_por_id,
                solicitado_por_nome=solicitante.full_name if solicitante else "N/A",
                descricao=row.descricao,
                status_anterior=row.status_anterior,
                status_novo=row.status_novo,
                created_at=row.created_at,
            )
        )

    return ReportCorrecaoListResponse(correcoes=items)


@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
async def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Excluir relatório

    Requer: autenticação

    Regras (#275): somente Técnico exclui próprio relatório em rascunho
    """
    report = session.get(Report, report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relatório com ID {report_id} não encontrado"
        )

    if not can_delete_report(current_user, report):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para excluir este relatório"
        )

    session.delete(report)
    session.commit()

    return {
        "message": f"Relatório '{report.numero}' excluído com sucesso",
        "id": report_id
    }


@router.get("/{report_id}/export-excel", status_code=status.HTTP_200_OK)
async def export_report_to_excel(
    report_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Exportar relatório para Excel usando template e data mapping

    Requer: autenticação

    Regras:
    - Template Excel deve estar configurado no formulário
    - Retorna arquivo Excel preenchido para download
    - Pode exportar em qualquer status (rascunho, em_revisao, aprovado)
    """
    import io
    from fastapi.responses import StreamingResponse

    # Buscar relatório
    report = session.get(Report, report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relatório com ID {report_id} não encontrado"
        )

    if not can_view_report(current_user, report):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para visualizar este relatório"
        )

    if not can_export_excel(current_user, report):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para exportar este relatório"
        )

    # Buscar template
    template = session.get(Formulario, report.form_template_id)
    if not template or not template.excel_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template Excel não configurado para este formulário"
        )

    from ...services.excel_template_storage import decode_excel_template

    try:
        excel_bytes = decode_excel_template(template.excel_template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar template Excel: {str(e)}"
        )

    from ...services.excel_export_service import (
        ExportEngineUnavailable,
        export_report_to_xlsx_bytes,
    )

    try:
        output_bytes = await export_report_to_xlsx_bytes(
            excel_bytes,
            report,
            session,
            format_date=_format_date_for_excel,
            format_yes_no=_format_yes_no_for_export,
            format_lookup=_format_lookup_for_export,
        )
    except ExportEngineUnavailable as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao exportar relatório para Excel: {str(e)}",
        )

    output = io.BytesIO(output_bytes)
    output.seek(0)

    # Gerar nome do arquivo
    filename = f"Relatorio_{report.numero}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"

    # Retornar arquivo
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{report_id}/export-pdf", status_code=status.HTTP_200_OK)
async def export_report_to_pdf(
    report_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Exportar relatório para PDF usando template Excel e data mapping

    Requer: autenticação

    Processo:
    1. Gera Excel preenchido (mesmo processo do export-excel)
    2. Converte Excel para PDF
    3. Retorna PDF para download
    """
    import io
    from fastapi.responses import StreamingResponse

    # Buscar relatório (mesma lógica do export-excel)
    report = session.get(Report, report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relatório com ID {report_id} não encontrado"
        )

    if not can_view_report(current_user, report):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para visualizar este relatório"
        )

    if not can_export_excel(current_user, report):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para exportar este relatório"
        )

    # Verificar status
    if report.status not in ['em_revisao', 'aprovado']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Relatório deve estar em 'em_revisao' ou 'aprovado' para exportação. Status atual: {report.status}"
        )

    # Buscar template
    template = session.get(Formulario, report.form_template_id)
    if not template or not template.excel_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template Excel não configurado para este formulário"
        )

    from ...services.excel_template_storage import decode_excel_template

    try:
        excel_bytes = decode_excel_template(template.excel_template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar template Excel: {str(e)}"
        )

    from ...services.excel_export_service import (
        ExportEngineUnavailable,
        export_report_to_pdf_bytes,
    )

    try:
        pdf_bytes = await export_report_to_pdf_bytes(
            excel_bytes,
            report,
            session,
            format_date=_format_date_for_excel,
            format_yes_no=_format_yes_no_for_export,
            format_lookup=_format_lookup_for_export,
        )
    except ExportEngineUnavailable as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao converter Excel para PDF: {str(e)}",
        )

    pdf_buffer = io.BytesIO(pdf_bytes)
    pdf_buffer.seek(0)

    # Gerar nome do arquivo
    filename = f"Relatorio_{report.numero}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

    # Retornar PDF
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
