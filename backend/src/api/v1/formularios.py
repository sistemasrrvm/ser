"""
API v1: Formulários
Endpoints CRUD para formulários
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, func
from datetime import datetime
from typing import List
import io
import json
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from ...core import get_session, get_current_user, require_admin
from ...services.excel_template_storage import (
    decode_excel_template,
    excel_template_download_filename,
    excel_template_media_type,
)
from ...core.colored_logging import log_error, log_success
from ...core.timezone import now_brazil
from ...models import Formulario, User, FormPage, FormField, Report
from ...schemas import (
    FormularioCreate,
    FormularioUpdate,
    FormularioResponse,
    FormularioListResponse
)


router = APIRouter(prefix="/formularios", tags=["Formulários"])


@router.post("", response_model=FormularioResponse, status_code=status.HTTP_201_CREATED)
async def create_formulario(
    formulario: FormularioCreate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Criar novo formulário

    Requer: role admin
    """
    # Criar formulário
    new_formulario = Formulario(
        nome=formulario.nome,
        descricao=formulario.descricao,
        criado_por=current_user.id,
        atualizado_por=current_user.id
    )

    session.add(new_formulario)
    session.commit()
    session.refresh(new_formulario)

    return FormularioResponse.from_orm(new_formulario)


@router.get("", response_model=FormularioListResponse, status_code=status.HTTP_200_OK)
async def list_formularios(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Listar todos os formulários

    Requer: autenticação (qualquer usuário)
    """
    statement = select(Formulario).order_by(Formulario.criado_em.desc())
    formularios = session.exec(statement).all()

    # Criar lista de responses com contagens
    formularios_response = []
    for formulario in formularios:
        # Contar páginas
        statement_pages = select(func.count(FormPage.id)).where(FormPage.formulario_id == formulario.id)
        total_paginas = session.exec(statement_pages).one() or 0
        
        # Contar campos (através das páginas)
        if total_paginas > 0:
            # Buscar IDs das páginas deste formulário
            statement_page_ids = select(FormPage.id).where(FormPage.formulario_id == formulario.id)
            page_ids = session.exec(statement_page_ids).all()
            
            if page_ids:
                statement_fields = select(func.count(FormField.id)).where(FormField.pagina_id.in_(page_ids))
                total_campos = session.exec(statement_fields).one() or 0
            else:
                total_campos = 0
        else:
            total_campos = 0
        
        # Criar response com contagens
        formulario_dict = {
            "id": formulario.id,
            "nome": formulario.nome,
            "descricao": formulario.descricao,
            "excel_template": formulario.excel_template,
            "criado_em": formulario.criado_em,
            "criado_por": formulario.criado_por,
            "atualizado_em": formulario.atualizado_em,
            "atualizado_por": formulario.atualizado_por,
            "total_paginas": total_paginas,
            "total_campos": total_campos
        }
        formularios_response.append(FormularioResponse(**formulario_dict))

    return FormularioListResponse(
        total=len(formularios),
        formularios=formularios_response
    )


@router.get("/import-template", status_code=status.HTTP_200_OK)
async def download_import_template(
    current_user: User = Depends(get_current_user)
):
    """
    Download template Excel para importação de páginas e campos

    Retorna arquivo Excel com:
    - Planilha "Dados" com cabeçalhos e 3 exemplos
    - Planilha "Instruções" com guia completo
    """
    # Criar workbook
    wb = Workbook()

    # ===== PLANILHA: DADOS =====
    ws_dados = wb.active
    ws_dados.title = "Dados"

    # Cabeçalhos
    headers = [
        "Página", "Ordem Página", "Tipo", "Label",
        "Ordem Campo", "Obrigatório", "Valor Padrão", "Config Adicional", "Excel Mapping"
    ]
    ws_dados.append(headers)

    # Estilizar cabeçalhos
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center")

    for col_num, header in enumerate(headers, 1):
        cell = ws_dados.cell(1, col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment

    # Ajustar larguras
    column_widths = [15, 13, 10, 20, 12, 12, 15, 30, 45]
    for i, width in enumerate(column_widths, 1):
        ws_dados.column_dimensions[ws_dados.cell(1, i).column_letter].width = width

    # Exemplos (alguns com ordem vazia para demonstrar auto-preenchimento)
    examples = [
        ["Dados Gerais", "", "textbox", "Nome Completo", "", "SIM", "João Silva",
         '{"max_characters": 100}', '[{"planilha":"Dados","celula":"A5"}]'],
        ["Dados Gerais", "", "separator", "Separador - Dados Pessoais", "", "NÃO", "",
         '{"titulo": "Dados Pessoais", "descricao": "Preencha seus dados pessoais abaixo"}', ''],
        ["Dados Gerais", "", "date", "Data de Nascimento", "", "SIM", "",
         '{"type": "date"}', '[{"planilha":"Dados","celula":"B5"}]'],
        ["Contato", "", "textbox", "Telefone", "", "NÃO", "(11) 9999-9999",
         '{"max_characters": 15}', ''],
    ]

    for row in examples:
        ws_dados.append(row)

    # ===== PLANILHA: INSTRUÇÕES =====
    ws_instrucoes = wb.create_sheet("Instruções")
    ws_instrucoes.column_dimensions['A'].width = 100

    instructions = [
        ["INSTRUÇÕES PARA IMPORTAÇÃO DE PÁGINAS E CAMPOS", "title"],
        ["", ""],
        ["COLUNAS OBRIGATÓRIAS:", "subtitle"],
        ["• Página: Nome da página que agrupa campos (ex: 'Dados Gerais', 'Contato')", "text"],
        ["• Tipo: Tipo do campo (veja lista abaixo)", "text"],
        ["• Label: Texto exibido ao usuário (ex: 'Nome Completo', 'Data de Nascimento')", "text"],
        ["", ""],
        ["COLUNAS OPCIONAIS (com auto-preenchimento):", "subtitle"],
        ["• Ordem Página: Ordem de exibição da página (se vazio, gera automático: 1, 2, 3...)", "text"],
        ["• Ordem Campo: Ordem do campo dentro da página (se vazio, gera automático: 1, 2, 3...)", "text"],
        ["• Obrigatório: SIM ou NÃO (padrão: NÃO)", "text"],
        ["• Valor Padrão: Valor que será pré-preenchido quando criar novo relatório (opcional)", "text"],
        ["• Config Adicional: Configurações específicas do tipo em formato JSON", "text"],
        ["• Excel Mapping: Mapeamento para exportação em formato JSON array", "text"],
        ["", ""],
        ["TIPOS DE CAMPO VÁLIDOS:", "subtitle"],
        ["• textbox - Campo de texto livre", "text"],
        ["• date - Campo de data ou data/hora", "text"],
        ["• number - Campo numérico (inteiro ou decimal)", "text"],
        ["• yes_no - Seleção Sim/Não (radio buttons)", "text"],
        ["• separator - Separador visual para organizar grupos de campos", "text"],
        ["• grid - Tabela editável (avançado)", "text"],
        ["", ""],
        ["EXEMPLOS DE CONFIG ADICIONAL:", "subtitle"],
        ["Para textbox:", "text"],
        ['{"max_characters": 100}', "code"],
        ["", ""],
        ["Para date:", "text"],
        ['{"type": "date"} ou {"type": "datetime-local"}', "code"],
        ["", ""],
        ["Para number:", "text"],
        ['{"decimal_places": 2}', "code"],
        ["", ""],
        ["Para separator:", "text"],
        ['{"titulo": "Dados Pessoais", "descricao": "Preencha seus dados abaixo"}', "code"],
        ["", ""],
        ["Múltiplas configs:", "text"],
        ['{"max_characters": 50, "require": true}', "code"],
        ["", ""],
        ["EXEMPLOS DE EXCEL MAPPING:", "subtitle"],
        ["Um mapeamento:", "text"],
        ['[{"planilha": "Dados", "celula": "A5"}]', "code"],
        ["", ""],
        ["Múltiplos mapeamentos:", "text"],
        ['[{"planilha": "Dados", "celula": "A5"}, {"planilha": "Resumo", "celula": "B10"}]', "code"],
        ["", ""],
        ["DICAS IMPORTANTES:", "subtitle"],
        ["• Não altere os cabeçalhos da planilha 'Dados'", "text"],
        ["• Campos na mesma página devem ter o mesmo 'Ordem Página'", "text"],
        ["• Config Adicional e Excel Mapping podem ficar vazios", "text"],
        ["• Separadores: use 'Ordem Campo' para posicionar entre campos existentes", "text"],
        ["• Separadores: 'Obrigatório' deve ser sempre 'NÃO'", "text"],
        ["• Máximo: 50 páginas e 500 campos por importação", "text"],
        ["• Arquivo máximo: 5MB", "text"],
        ["", ""],
        ["VALIDAÇÃO:", "subtitle"],
        ["Antes de importar, o sistema valida:", "text"],
        ["• Tipos de campo válidos", "text"],
        ["• Formato JSON correto (Config e Mapping)", "text"],
        ["• Campos obrigatórios preenchidos", "text"],
        ["• Limites de páginas e campos", "text"],
        ["", ""],
        ["Se houver erros, nenhum dado será importado e você verá a lista de erros.", "text"],
    ]

    for row_num, (text, style_type) in enumerate(instructions, 1):
        cell = ws_instrucoes.cell(row_num, 1, text)

        if style_type == "title":
            cell.font = Font(bold=True, size=14, color="1F4E78")
            cell.alignment = Alignment(horizontal="center")
        elif style_type == "subtitle":
            cell.font = Font(bold=True, size=12, color="2E75B6")
        elif style_type == "code":
            cell.font = Font(name="Consolas", size=10, color="C65911")
            cell.fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
        else:
            cell.font = Font(size=10)

    # Salvar em memória
    excel_buffer = io.BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)

    # Retornar arquivo
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=Template_Importacao_Paginas_Campos.xlsx"
        }
    )


@router.get("/{formulario_id}/excel-template", status_code=status.HTTP_200_OK)
async def download_excel_template(
    formulario_id: int,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """
    Download do template Excel de mesclagem gravado no formulário.

    Requer: role admin
    """
    statement = select(Formulario).where(Formulario.id == formulario_id)
    formulario = session.exec(statement).first()

    if not formulario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulário com ID {formulario_id} não encontrado",
        )

    if not formulario.excel_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template Excel de mesclagem não configurado para este formulário",
        )

    try:
        excel_bytes = decode_excel_template(formulario.excel_template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao decodificar template Excel: {str(e)}",
        )

    filename = excel_template_download_filename(
        formulario.nome, formulario.id, formulario.excel_template
    )
    excel_buffer = io.BytesIO(excel_bytes)
    excel_buffer.seek(0)

    return StreamingResponse(
        excel_buffer,
        media_type=excel_template_media_type(formulario.excel_template),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{formulario_id}", response_model=FormularioResponse, status_code=status.HTTP_200_OK)
async def get_formulario(
    formulario_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Obter formulário por ID

    Requer: autenticação (qualquer usuário)
    """
    statement = select(Formulario).where(Formulario.id == formulario_id)
    formulario = session.exec(statement).first()

    if not formulario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulário com ID {formulario_id} não encontrado"
        )

    return FormularioResponse.from_orm(formulario)


@router.get("/{formulario_id}/fields", status_code=status.HTTP_200_OK)
async def get_formulario_fields(
    formulario_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Listar todos os campos de um formulário (todas as páginas)

    Usado para configuração de campos Lookup
    Requer: autenticação (qualquer usuário)
    """
    # Verificar se formulário existe
    formulario = session.exec(
        select(Formulario).where(Formulario.id == formulario_id)
    ).first()

    if not formulario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulário com ID {formulario_id} não encontrado"
        )

    # Buscar todas as páginas e seus campos
    statement = select(FormPage).where(FormPage.formulario_id == formulario_id).order_by(FormPage.ordem)
    pages = session.exec(statement).all()

    # Coletar todos os campos de todas as páginas
    all_fields = []
    for page in pages:
        statement_fields = select(FormField).where(FormField.pagina_id == page.id).order_by(FormField.ordem)
        fields = session.exec(statement_fields).all()
        for field in fields:
            all_fields.append({
                "id": field.id,
                "rotulo": field.rotulo,
                "tipo": field.tipo,
                "pagina": page.nome,
                "configuracao": field.configuracao  # Necessário para autocomplete de planilhas Excel
            })

    return all_fields


@router.get("/{formulario_id}/lookup-options", status_code=status.HTTP_200_OK)
async def get_lookup_options(
    formulario_id: int,
    display_field: str = Query(..., description="Campo a ser exibido"),
    value_field: str = Query(default="id", description="Campo usado como valor"),
    search: str = Query(default=None, description="Filtro de busca"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Retornar opções para campo Lookup

    Busca relatórios existentes de um formulário e retorna no formato:
    [{ "label": "Nome Exibido", "value": 123 }, ...]

    Requer: autenticação (qualquer usuário)
    """
    # Verificar se formulário existe
    formulario = session.exec(
        select(Formulario).where(Formulario.id == formulario_id)
    ).first()

    if not formulario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulário com ID {formulario_id} não encontrado"
        )

    # TODO: Implementar busca de relatórios quando tabela 'reports' existir
    # Por enquanto, retornar lista vazia
    # No futuro:
    # 1. Buscar relatórios do formulario_id
    # 2. Extrair campo display_field e value_field de cada relatório
    # 3. Aplicar filtro search se fornecido
    # 4. Retornar [{ "label": report[display_field], "value": report[value_field] }]

    return []


@router.put("/{formulario_id}", response_model=FormularioResponse, status_code=status.HTTP_200_OK)
async def update_formulario(
    formulario_id: int,
    formulario_update: FormularioUpdate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Atualizar formulário

    Requer: role admin
    """
    # Buscar formulário
    statement = select(Formulario).where(Formulario.id == formulario_id)
    formulario = session.exec(statement).first()

    if not formulario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulário com ID {formulario_id} não encontrado"
        )

    # Atualizar campos fornecidos
    if formulario_update.nome is not None:
        formulario.nome = formulario_update.nome

    if formulario_update.descricao is not None:
        formulario.descricao = formulario_update.descricao

    if formulario_update.excel_template is not None:
        formulario.excel_template = formulario_update.excel_template

    formulario.atualizado_em = now_brazil()
    formulario.atualizado_por = current_user.id

    session.add(formulario)
    session.commit()
    session.refresh(formulario)

    return FormularioResponse.from_orm(formulario)


@router.delete("/{formulario_id}", status_code=status.HTTP_200_OK)
async def delete_formulario(
    formulario_id: int,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Excluir formulário

    Requer: role admin

    As páginas e campos associados serão deletados automaticamente via cascade.
    Não é possível excluir formulários que possuem relatórios associados (ON DELETE RESTRICT).
    """
    # Buscar formulário
    statement = select(Formulario).where(Formulario.id == formulario_id)
    formulario = session.exec(statement).first()

    if not formulario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulário com ID {formulario_id} não encontrado"
        )

    # Verificar se há relatórios associados (FK com ON DELETE RESTRICT impede exclusão)
    statement_reports = select(Report).where(Report.form_template_id == formulario_id)
    reports = session.exec(statement_reports).all()
    
    if reports:
        report_labels = [f"• Relatório {r.numero}: {r.status}" for r in reports[:5]]  # Mostrar até 5 relatórios
        if len(reports) > 5:
            report_labels.append(f"• ... e mais {len(reports) - 5} relatórios")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"❌ Não é possível excluir este formulário.\n\n"
                   f"Existem {len(reports)} relatórios associados:\n" +
                   "\n".join(report_labels) +
                   "\n\nPara excluir este formulário, primeiro remova ou altere os relatórios associados."
        )
    
    # Excluir formulário (páginas serão deletadas automaticamente via cascade)
    session.delete(formulario)
    session.commit()

    return {
        "message": f"Formulário '{formulario.nome}' excluído com sucesso",
        "id": formulario_id
    }


@router.post("/{form_template_id}/import-excel", status_code=status.HTTP_200_OK)
async def import_pages_and_fields(
    form_template_id: int,
    file: UploadFile = File(...),
    replace: bool = Query(False, description="Se True, substitui páginas/campos existentes"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Importa páginas e campos de arquivo Excel

    Validações:
    - Arquivo .xlsx válido
    - Tamanho max 5MB
    - Cabeçalhos corretos
    - Tipos de campo válidos
    - JSON válido (config e mapping)
    - Max 50 páginas, 500 campos

    Se replace=True, apaga páginas/campos existentes antes de importar.
    """
    # Validar formulário existe
    statement = select(Formulario).where(Formulario.id == form_template_id)
    formulario = session.exec(statement).first()

    if not formulario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulário com ID {form_template_id} não encontrado"
        )

    # Validar tipo de arquivo
    if not file.filename or not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo deve ser do tipo .xlsx"
        )

    # Ler arquivo
    try:
        contents = await file.read()

        # Validar tamanho (5MB)
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo muito grande. Tamanho máximo: 5MB"
            )

        # Carregar workbook
        wb = load_workbook(io.BytesIO(contents))

        # Validar planilha "Dados" existe
        if "Dados" not in wb.sheetnames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Planilha 'Dados' não encontrada no arquivo"
            )

        ws = wb["Dados"]

        # Validar cabeçalhos
        expected_headers = [
            "Página", "Ordem Página", "Tipo", "Label",
            "Ordem Campo", "Obrigatório", "Valor Padrão", "Config Adicional", "Excel Mapping"
        ]

        actual_headers = [cell.value for cell in ws[1]]

        if actual_headers != expected_headers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cabeçalhos inválidos. Esperado: {expected_headers}"
            )

        # Ler e validar dados
        errors = []
        rows_data = []
        valid_types = ["textbox", "date", "number", "yes_no", "separator", "grid"]

        # Dicionários para auto-incremento
        page_counters = {}  # {nome_pagina: contador_ordem}
        field_counters = {}  # {nome_pagina: contador_campo}

        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            # Pular linhas vazias
            if all(cell is None or str(cell).strip() == '' for cell in row[:5]):
                continue

            pagina, ordem_pagina, tipo, label, ordem_campo, obrigatorio, valor_padrao, config_adicional, excel_mapping = row

            # Validar campos obrigatórios
            if not pagina or str(pagina).strip() == '':
                errors.append({"line": row_num, "message": "Coluna 'Página' é obrigatória"})
                continue

            pagina = str(pagina).strip()

            # Auto-gerar ordem_pagina se vazia
            if not ordem_pagina or str(ordem_pagina).strip() == '':
                if pagina not in page_counters:
                    page_counters[pagina] = len(page_counters) + 1
                ordem_pagina = page_counters[pagina]
            else:
                ordem_pagina = int(ordem_pagina)
                if pagina not in page_counters:
                    page_counters[pagina] = ordem_pagina

            if not tipo or str(tipo).strip() == '':
                errors.append({"line": row_num, "message": "Coluna 'Tipo' é obrigatória"})
                continue

            if not label or str(label).strip() == '':
                errors.append({"line": row_num, "message": "Coluna 'Label' é obrigatória"})
                continue

            # Auto-gerar ordem_campo se vazia
            if not ordem_campo or str(ordem_campo).strip() == '':
                if pagina not in field_counters:
                    field_counters[pagina] = 0
                field_counters[pagina] += 1
                ordem_campo = field_counters[pagina]
            else:
                ordem_campo = int(ordem_campo)

            # Validar tipo
            tipo = str(tipo).strip().lower()
            if tipo not in valid_types:
                errors.append({
                    "line": row_num,
                    "message": f"Tipo '{tipo}' inválido. Use: {', '.join(valid_types)}"
                })
                continue

            # Validar obrigatório
            is_required = False
            if obrigatorio:
                obrigatorio_str = str(obrigatorio).strip().upper()
                if obrigatorio_str in ["SIM", "S", "TRUE", "1"]:
                    is_required = True

            # Processar Valor Padrão
            default_value = ""
            if valor_padrao and str(valor_padrao).strip():
                default_value = str(valor_padrao).strip()

            # Validar Config Adicional (JSON)
            config_dict = {}
            if config_adicional and str(config_adicional).strip():
                try:
                    config_dict = json.loads(str(config_adicional))
                except json.JSONDecodeError:
                    errors.append({
                        "line": row_num,
                        "message": f"Config Adicional inválido (JSON mal formatado): {config_adicional}"
                    })
                    continue

            # Adicionar default_value ao config se fornecido
            if default_value:
                config_dict["default_value"] = default_value

            # Adicionar require ao config se necessário
            if is_required:
                config_dict["require"] = True

            # Validar Excel Mapping (JSON)
            excel_mapping_list = []
            if excel_mapping and str(excel_mapping).strip():
                try:
                    excel_mapping_list = json.loads(str(excel_mapping))
                    if not isinstance(excel_mapping_list, list):
                        errors.append({
                            "line": row_num,
                            "message": "Excel Mapping deve ser um array JSON"
                        })
                        continue
                except json.JSONDecodeError:
                    errors.append({
                        "line": row_num,
                        "message": f"Excel Mapping inválido (JSON mal formatado): {excel_mapping}"
                    })
                    continue

            # Adicionar excel_mapping ao config
            if excel_mapping_list:
                config_dict["excel_mapping"] = excel_mapping_list

            # Tratamento especial para separadores
            if tipo == "separator":
                # Para separador: titulo vem do Label, descricao vem do Config Adicional
                separator_config = {
                    "titulo": str(label).strip()
                }
                # Se tem descricao no config_dict, adicionar
                if config_dict.get("descricao"):
                    separator_config["descricao"] = config_dict["descricao"]
                config_dict = separator_config

            # Armazenar dados validados
            rows_data.append({
                "pagina": pagina,
                "ordem_pagina": ordem_pagina,
                "tipo": tipo,
                "label": str(label).strip(),
                "ordem_campo": ordem_campo,
                "config": config_dict
            })

        # Se houver erros, retornar lista
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": f"Encontrados {len(errors)} erros no arquivo. Corrija e tente novamente.",
                    "errors": errors
                }
            )

        # Validar limites
        unique_pages = set(row["pagina"] for row in rows_data)
        if len(unique_pages) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limite de páginas excedido: {len(unique_pages)} (máximo: 50)"
            )

        if len(rows_data) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limite de campos excedido: {len(rows_data)} (máximo: 500)"
            )

        # Se replace=True, deletar páginas/campos existentes
        if replace:
            # Deletar campos primeiro (FK constraint)
            statement = select(FormPage).where(FormPage.formulario_id == form_template_id)
            existing_pages = session.exec(statement).all()

            for page in existing_pages:
                statement = select(FormField).where(FormField.pagina_id == page.id)
                fields = session.exec(statement).all()
                for field in fields:
                    session.delete(field)

            # Deletar páginas
            for page in existing_pages:
                session.delete(page)

            session.commit()

        # Criar páginas únicas
        page_map = {}  # {nome_pagina: page_id}

        for page_name in unique_pages:
            # Buscar ordem da página (pegar do primeiro campo dessa página)
            ordem = next(row["ordem_pagina"] for row in rows_data if row["pagina"] == page_name)

            new_page = FormPage(
                formulario_id=form_template_id,
                nome=page_name,
                ordem=ordem
            )
            session.add(new_page)
            session.flush()  # Para obter o ID

            page_map[page_name] = new_page.id

        # Criar campos
        for row in rows_data:
            page_id = page_map[row["pagina"]]

            new_field = FormField(
                pagina_id=page_id,
                rotulo=row["label"],
                tipo=row["tipo"],
                ordem=row["ordem_campo"],
                configuracao=row["config"]
            )
            session.add(new_field)

        # Commit
        session.commit()

        # Log de sucesso
        log_success(f"Importação Excel concluída - {len(unique_pages)} páginas, {len(rows_data)} campos criados")

        return {
            "success": True,
            "pages_created": len(unique_pages),
            "fields_created": len(rows_data),
            "message": f"Importação concluída: {len(unique_pages)} páginas e {len(rows_data)} campos criados"
        }

    except HTTPException:
        raise
    except Exception as e:
        # Logar erro em vermelho com traceback completo
        log_error("ERRO NA IMPORTAÇÃO DE EXCEL", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )


@router.get("/{formulario_id}/export", status_code=status.HTTP_200_OK)
async def export_template(
    formulario_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Exporta template completo (formulário + páginas + campos) em JSON

    Sprint 007 - Exportar/Importar Template
    Retorna JSON estruturado com toda hierarquia do template
    """
    # Buscar formulário
    statement = select(Formulario).where(Formulario.id == formulario_id)
    formulario = session.exec(statement).first()

    if not formulario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formulário com ID {formulario_id} não encontrado"
        )

    # Buscar páginas do formulário
    statement_pages = select(FormPage).where(FormPage.formulario_id == formulario_id).order_by(FormPage.ordem)
    paginas = session.exec(statement_pages).all()

    # Montar estrutura JSON (sem IDs, sem dados de auditoria)
    paginas_export = []
    for pagina in paginas:
        # Buscar campos da página
        statement_fields = select(FormField).where(FormField.pagina_id == pagina.id).order_by(FormField.ordem)
        campos = session.exec(statement_fields).all()

        campos_export = []
        for campo in campos:
            campos_export.append({
                "rotulo": campo.rotulo,
                "ordem": campo.ordem,
                "tipo": campo.tipo,
                "configuracao": campo.configuracao,
                "regra_exibicao_id": campo.regra_exibicao_id
            })

        paginas_export.append({
            "nome": pagina.nome,
            "ordem": pagina.ordem,
            "regra_exibicao_id": pagina.regra_exibicao_id,
            "campos": campos_export
        })

    # Retornar JSON completo com metadata
    return {
        "versao": "1.0",
        "exportado_em": now_brazil().isoformat() + "Z",
        "template": {
            "nome": formulario.nome,
            "descricao": formulario.descricao,
            "excel_template": formulario.excel_template,
            "paginas": paginas_export
        }
    }


@router.post("/{formulario_id}/import", status_code=status.HTTP_200_OK)
async def import_template(
    formulario_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Importa template de arquivo JSON SUBSTITUINDO o template existente

    Sprint 007 - Exportar/Importar Template
    DANGER ZONE: Substitui completamente o formulário + páginas + campos existentes
    Mantém o mesmo ID do formulário
    """
    # Validar tipo de arquivo
    if not file.filename or not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo deve ser do tipo .json"
        )

    try:
        # Ler e parsear JSON
        contents = await file.read()

        # Validar tamanho (10MB)
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo muito grande. Tamanho máximo: 10MB"
            )

        data = json.loads(contents)

        # Validar estrutura básica
        if "versao" not in data or "template" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estrutura JSON inválida. Arquivo deve conter 'versao' e 'template'"
            )

        # Validar versão
        if data["versao"] != "1.0":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Versão não suportada: {data['versao']}. Versão esperada: 1.0"
            )

        template_data = data["template"]

        # Validar campos obrigatórios do template
        if "nome" not in template_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campo 'nome' é obrigatório no template"
            )

        if "paginas" not in template_data or not isinstance(template_data["paginas"], list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campo 'paginas' deve ser um array"
            )

        # Usar transação para garantir atomicidade
        try:
            # 1. Verificar se formulário existe
            statement = select(Formulario).where(Formulario.id == formulario_id)
            formulario = session.exec(statement).first()

            if not formulario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Formulário com ID {formulario_id} não encontrado"
                )

            # 2. EXCLUIR todas as páginas existentes (campos serão excluídos por cascade)
            statement_pages = select(FormPage).where(FormPage.formulario_id == formulario_id)
            existing_pages = session.exec(statement_pages).all()

            for page in existing_pages:
                # Excluir campos da página
                statement_fields = select(FormField).where(FormField.pagina_id == page.id)
                existing_fields = session.exec(statement_fields).all()
                for field in existing_fields:
                    session.delete(field)

                # Excluir página
                session.delete(page)

            session.flush()

            # 3. Atualizar informações do formulário (manter ID)
            formulario.nome = template_data["nome"]
            formulario.descricao = template_data.get("descricao", "")
            formulario.excel_template = template_data.get("excel_template")
            formulario.atualizado_por = current_user.id
            formulario.atualizado_em = now_brazil()

            session.add(formulario)
            session.flush()

            # 4. Criar Páginas e Campos do JSON importado
            for pagina_data in template_data["paginas"]:
                # Validar campos obrigatórios da página
                if "nome" not in pagina_data or "ordem" not in pagina_data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Campos 'nome' e 'ordem' são obrigatórios em cada página"
                    )

                pagina = FormPage(
                    formulario_id=formulario.id,
                    nome=pagina_data["nome"],
                    ordem=pagina_data["ordem"],
                    regra_exibicao_id=pagina_data.get("regra_exibicao_id")
                )
                session.add(pagina)
                session.flush()

                # 5. Criar Campos
                if "campos" in pagina_data and isinstance(pagina_data["campos"], list):
                    for campo_data in pagina_data["campos"]:
                        # Validar campos obrigatórios do campo
                        required_fields = ["rotulo", "ordem", "tipo", "configuracao"]
                        for field in required_fields:
                            if field not in campo_data:
                                raise HTTPException(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Campo '{field}' é obrigatório em cada campo"
                                )

                        campo = FormField(
                            pagina_id=pagina.id,
                            rotulo=campo_data["rotulo"],
                            ordem=campo_data["ordem"],
                            tipo=campo_data["tipo"],
                            configuracao=campo_data["configuracao"],
                            regra_exibicao_id=campo_data.get("regra_exibicao_id")
                        )
                        session.add(campo)

            session.commit()
            session.refresh(formulario)

            # Log de sucesso
            log_success(f"Template SUBSTITUÍDO via importação: '{formulario.nome}' (ID: {formulario.id})")

            return {
                "success": True,
                "id": formulario.id,
                "nome": formulario.nome,
                "message": f"Template '{formulario.nome}' importado e substituído com sucesso"
            }

        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            log_error("ERRO NA IMPORTAÇÃO DE TEMPLATE", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erro ao importar template: {str(e)}"
            )

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"JSON inválido: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error("ERRO AO PROCESSAR IMPORTAÇÃO", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )
