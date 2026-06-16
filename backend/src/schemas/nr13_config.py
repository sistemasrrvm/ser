"""Schemas para configuração NR13 na tela de Configurações."""

from pydantic import BaseModel, Field


class Nr13IntegracaoSettingsResponse(BaseModel):
    api_base_url: str = ""
    api_base_url_resolved: str = ""
    basic_user: str = ""
    basic_password: str = ""
    basic_password_configured: bool = False
    equipamento_tipo: str = "12"
    data_ref_days_back: int = 2
    cron_secret: str = ""
    cron_secret_configured: bool = False
    timeout_seconds: float = 120.0
    enabled: bool = True
    configured: bool = False
    source: str = "env"


class Nr13IntegracaoSettingsUpdate(BaseModel):
    api_base_url: str = Field(..., min_length=1)
    basic_user: str = Field(..., min_length=1)
    basic_password: str = ""
    equipamento_tipo: str = "12"
    data_ref_days_back: int = Field(2, ge=0)
    cron_secret: str = ""
    timeout_seconds: float = Field(120.0, ge=10.0, le=600.0)
    enabled: bool = True


class Nr13IntegracaoTestResponse(BaseModel):
    success: bool
    data_ref: str
    record_count: int
    request_url: str
    message: str = ""
