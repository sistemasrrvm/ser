"""
Timezone utilities
Garante que todas as datas sejam gravadas no timezone do Brasil
"""

from datetime import datetime
from zoneinfo import ZoneInfo

# Timezone do Brasil
BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


def now_brazil() -> datetime:
    """
    Retorna datetime atual no timezone do Brasil (America/Sao_Paulo)

    Returns:
        datetime com timezone do Brasil (UTC-3)
    """
    return datetime.now(BRAZIL_TZ)


def utc_to_brazil(dt: datetime) -> datetime:
    """
    Converte datetime UTC para timezone do Brasil

    Args:
        dt: datetime em UTC

    Returns:
        datetime no timezone do Brasil
    """
    if dt.tzinfo is None:
        # Assume UTC se não tiver timezone
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))

    return dt.astimezone(BRAZIL_TZ)
