"""
Rotas para gerenciamento de Configurações do Sistema
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime

from ...core.database import get_session
from ...core.dependencies import get_current_user, require_admin
from ...models.user import User
from ...models.configuracao import Configuracao
from ...schemas.configuracao import (
    ConfiguracaoCreate,
    ConfiguracaoUpdate,
    ConfiguracaoResponse,
    ConfiguracaoListResponse
)
from ...schemas.nr13_config import (
    Nr13IntegracaoSettingsResponse,
    Nr13IntegracaoSettingsUpdate,
    Nr13IntegracaoTestResponse,
)
from ...schemas.email_config import (
    EmailIntegracaoSettingsResponse,
    EmailIntegracaoSettingsUpdate,
    EmailIntegracaoTestRequest,
    EmailIntegracaoTestResponse,
)
from ...services.nr13_config import get_nr13_settings_for_api, save_nr13_settings
from ...services.email_config import get_email_settings_for_api, save_email_settings
from ...services.nr13_api_sync import compute_data_ref, fetch_clientes_from_api
from ...core.colored_logging import log_info, log_error

router = APIRouter(prefix="/configuracoes", tags=["Configurações"])


@router.get("", response_model=ConfiguracaoListResponse, status_code=status.HTTP_200_OK)
async def list_configuracoes(
    categoria: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Listar todas as configurações (com filtro opcional por categoria)
    Requer: autenticação
    """
    statement = select(Configuracao)

    if categoria:
        statement = statement.where(Configuracao.categoria == categoria)

    statement = statement.order_by(Configuracao.categoria, Configuracao.chave)
    configuracoes = session.exec(statement).all()

    return ConfiguracaoListResponse(
        total=len(configuracoes),
        configuracoes=configuracoes
    )


@router.get(
    "/nr13-integracao",
    response_model=Nr13IntegracaoSettingsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_nr13_integracao_settings(
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Parâmetros da integração NR13 (API Botset). Requer: admin."""
    return get_nr13_settings_for_api(session)


@router.put(
    "/nr13-integracao",
    response_model=Nr13IntegracaoSettingsResponse,
    status_code=status.HTTP_200_OK,
)
async def update_nr13_integracao_settings(
    payload: Nr13IntegracaoSettingsUpdate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Salvar parâmetros da integração NR13. Requer: admin."""
    current = get_nr13_settings_for_api(session)
    password = payload.basic_password or ""
    if not current["basic_password_configured"] and (not password or password == "********"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha da API NR13 é obrigatória na primeira configuração",
        )

    result = save_nr13_settings(session, payload.model_dump())
    log_info(f"[CONFIGURACAO] Integração NR13 atualizada por {current_user.username}")
    return result


@router.post(
    "/nr13-integracao/test",
    response_model=Nr13IntegracaoTestResponse,
    status_code=status.HTTP_200_OK,
)
async def test_nr13_integracao_settings(
    data_ref: Optional[str] = None,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Testa conexão com a API Botset (busca clientes, sem gravar). Requer: admin."""
    ref = data_ref or compute_data_ref(session)
    from ...services.nr13_config import get_nr13_runtime_config
    from ...services.nr13_api_sync import build_nr13_url

    cfg = get_nr13_runtime_config(session)
    url = build_nr13_url(cfg.api_base_url, "clientes")
    records = await fetch_clientes_from_api(session, ref)
    return Nr13IntegracaoTestResponse(
        success=True,
        data_ref=ref,
        record_count=len(records),
        request_url=url,
        message=f"Conexão OK — {len(records)} cliente(s) retornado(s) para dataRef={ref}",
    )


@router.get(
    "/email-integracao",
    response_model=EmailIntegracaoSettingsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_email_integracao_settings(
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Parâmetros SMTP para notificações de fluxo. Requer: admin."""
    return get_email_settings_for_api(session)


@router.put(
    "/email-integracao",
    response_model=EmailIntegracaoSettingsResponse,
    status_code=status.HTTP_200_OK,
)
async def update_email_integracao_settings(
    payload: EmailIntegracaoSettingsUpdate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Salvar parâmetros SMTP. Requer: admin."""
    current = get_email_settings_for_api(session)
    password = payload.smtp_password or ""
    if not current["smtp_password_configured"] and (not password or password == "********"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha SMTP é obrigatória na primeira configuração",
        )

    result = save_email_settings(session, payload.model_dump())
    log_info(f"[CONFIGURACAO] Integração e-mail atualizada por {current_user.username}")
    return result


@router.post(
    "/email-integracao/test",
    response_model=EmailIntegracaoTestResponse,
    status_code=status.HTTP_200_OK,
)
async def test_email_integracao_settings(
    body: EmailIntegracaoTestRequest,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Envia e-mail de teste para destinatário único. Requer: admin."""
    from ...services.email_service import send_test_report_email

    result = await send_test_report_email(
        session,
        body.report_id,
        body.evento,
        str(body.destinatario_teste),
    )

    if not result.success:
        log_error(f"[CONFIGURACAO] Teste de e-mail falhou: {result.message}")

    return EmailIntegracaoTestResponse(
        success=result.success,
        message=result.message,
        subject=result.subject,
        destinatario=result.destinatario,
        log=result.log,
    )


@router.get("/{config_id}", response_model=ConfiguracaoResponse, status_code=status.HTTP_200_OK)
async def get_configuracao(
    config_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Obter configuração específica por ID
    Requer: autenticação
    """
    config = session.get(Configuracao, config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuração ID '{config_id}' não encontrada"
        )

    return config


@router.get("/chave/{chave}", response_model=ConfiguracaoResponse, status_code=status.HTTP_200_OK)
async def get_configuracao_by_chave(
    chave: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Obter configuração específica por chave
    Requer: autenticação
    """
    statement = select(Configuracao).where(Configuracao.chave == chave)
    config = session.exec(statement).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuração '{chave}' não encontrada"
        )

    return config


@router.post("", response_model=ConfiguracaoResponse, status_code=status.HTTP_201_CREATED)
async def create_configuracao(
    config_data: ConfiguracaoCreate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Criar nova configuração
    Requer: admin
    """
    # Verificar se chave já existe
    statement = select(Configuracao).where(Configuracao.chave == config_data.chave)
    existing = session.exec(statement).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe uma configuração com chave '{config_data.chave}'"
        )

    # Criar configuração
    nova_config = Configuracao(**config_data.model_dump())
    session.add(nova_config)
    session.commit()
    session.refresh(nova_config)

    log_info(f"[CONFIGURACAO] Configuração '{config_data.chave}' criada por {current_user.username}")

    return nova_config


@router.put("/{config_id}", response_model=ConfiguracaoResponse, status_code=status.HTTP_200_OK)
async def update_configuracao(
    config_id: int,
    config_data: ConfiguracaoUpdate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Atualizar configuração
    Requer: admin
    """
    config = session.get(Configuracao, config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuração ID '{config_id}' não encontrada"
        )

    # Atualizar campos
    update_data = config_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    config.updated_at = datetime.utcnow()
    session.add(config)
    session.commit()
    session.refresh(config)

    log_info(f"[CONFIGURACAO] Configuração '{config.chave}' (ID: {config_id}) atualizada por {current_user.username}")

    return config


@router.delete("/{config_id}", status_code=status.HTTP_200_OK)
async def delete_configuracao(
    config_id: int,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Deletar configuração
    Requer: admin
    """
    config = session.get(Configuracao, config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuração ID '{config_id}' não encontrada"
        )

    chave = config.chave
    session.delete(config)
    session.commit()

    log_info(f"[CONFIGURACAO] Configuração '{chave}' (ID: {config_id}) deletada por {current_user.username}")

    return {
        "message": f"Configuração '{chave}' deletada com sucesso",
        "id": config_id
    }
