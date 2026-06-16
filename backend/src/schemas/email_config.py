"""Schemas para configuração de e-mail (SMTP) na tela de Configurações (#248)."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class EmailIntegracaoSettingsResponse(BaseModel):
    enabled: bool = True
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_use_ssl: bool = True
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_password_configured: bool = False
    from_email: str = ""
    from_name: str = "SER - Sistema de Emissão de Relatórios"
    frontend_base_url: str = ""
    configured: bool = False
    source: str = "env"


class EmailIntegracaoSettingsUpdate(BaseModel):
    enabled: bool = True
    smtp_host: str = Field(..., min_length=1)
    smtp_port: int = Field(465, ge=1, le=65535)
    smtp_use_ssl: bool = True
    smtp_user: str = Field(..., min_length=1)
    smtp_password: str = ""
    from_email: str = Field(..., min_length=3)
    from_name: str = "SER - Sistema de Emissão de Relatórios"
    frontend_base_url: str = ""


class EmailIntegracaoTestRequest(BaseModel):
    report_id: int = Field(..., ge=1)
    evento: Literal["finalizar", "solicitar_correcao", "aprovar"]
    destinatario_teste: EmailStr


class EmailIntegracaoTestResponse(BaseModel):
    success: bool
    message: str
    subject: str = ""
    destinatario: str = ""
    log: list[str] = Field(default_factory=list)
