"""
Endpoints internos — sincronização NR13 agendada (#292).
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import Session

from ...core.config import settings
from ...core.database import get_session
from ...schemas.nr13_sync import Nr13NightlySyncResponse
from ...services.nr13_api_sync import ensure_nr13_api_configured, sync_nightly
from ...services.nr13_config import get_nr13_runtime_config, verify_cron_secret

router = APIRouter(prefix="/internal/nr13", tags=["Internal NR13"])


@router.post("/sync-nightly", response_model=Nr13NightlySyncResponse, status_code=status.HTTP_200_OK)
async def sync_nightly_endpoint(
    x_cron_secret: str = Header(..., alias="X-Cron-Secret"),
    session: Session = Depends(get_session),
):
    """
    Carga noturna: clientes + equipamentos (dataRef = hoje - N dias).
    Autenticação via header X-Cron-Secret.
    """
    cfg = get_nr13_runtime_config(session)
    if not cfg.cron_secret and not settings.NR13_SYNC_CRON_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Secret de carga noturna não configurado (Configurações ou NR13_SYNC_CRON_SECRET)",
        )

    if not verify_cron_secret(session, x_cron_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Secret inválido",
        )

    ensure_nr13_api_configured(session)
    return await sync_nightly(session)
