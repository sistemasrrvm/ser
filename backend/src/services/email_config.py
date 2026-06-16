"""Configuração SMTP para notificações de fluxo de relatórios — DB + fallback env (#248)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from ..core.config import settings
from ..models.configuracao import Configuracao

EMAIL_CONFIG_KEY = "email_integracao"
PASSWORD_MASK = "********"


@dataclass
class EmailRuntimeConfig:
    enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_use_ssl: bool
    smtp_user: str
    smtp_password: str
    from_email: str
    from_name: str
    frontend_base_url: str


def _default_frontend_url() -> str:
    origins = settings.cors_origins_list
    return origins[0] if origins else "http://localhost:5173"


def _defaults_from_env() -> dict[str, Any]:
    return {
        "enabled": True,
        "smtp_host": settings.SMTP_HOST,
        "smtp_port": settings.SMTP_PORT,
        "smtp_use_ssl": settings.SMTP_USE_SSL,
        "smtp_user": settings.SMTP_USER,
        "smtp_password": settings.SMTP_PASSWORD,
        "from_email": settings.SMTP_FROM or settings.SMTP_USER,
        "from_name": settings.SMTP_FROM_NAME,
        "frontend_base_url": settings.FRONTEND_URL or _default_frontend_url(),
    }


def _load_stored_json(session: Session) -> dict[str, Any]:
    row = session.exec(
        select(Configuracao).where(Configuracao.chave == EMAIL_CONFIG_KEY)
    ).first()
    if not row or not row.valor:
        return {}
    try:
        data = json.loads(row.valor)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _merge_config(stored: dict[str, Any]) -> tuple[dict[str, Any], str]:
    merged = _defaults_from_env()
    source = "env"
    if stored:
        source = "database"
        for key, value in stored.items():
            if value is not None and value != "":
                merged[key] = value
        if any(_defaults_from_env().get(k) for k in ("smtp_host", "smtp_user", "smtp_password")):
            if stored:
                source = "mixed"
    return merged, source


def get_email_runtime_config(session: Session) -> EmailRuntimeConfig:
    stored = _load_stored_json(session)
    merged, _ = _merge_config(stored)
    return EmailRuntimeConfig(
        enabled=bool(merged.get("enabled", True)),
        smtp_host=str(merged.get("smtp_host") or "").strip(),
        smtp_port=int(merged.get("smtp_port") or 465),
        smtp_use_ssl=bool(merged.get("smtp_use_ssl", True)),
        smtp_user=str(merged.get("smtp_user") or "").strip(),
        smtp_password=str(merged.get("smtp_password") or ""),
        from_email=str(merged.get("from_email") or merged.get("smtp_user") or "").strip(),
        from_name=str(merged.get("from_name") or settings.SMTP_FROM_NAME).strip(),
        frontend_base_url=str(merged.get("frontend_base_url") or _default_frontend_url()).rstrip("/"),
    )


def is_email_configured(session: Session) -> bool:
    cfg = get_email_runtime_config(session)
    return bool(
        cfg.enabled
        and cfg.smtp_host
        and cfg.smtp_user
        and cfg.smtp_password
        and cfg.from_email
    )


def get_email_settings_for_api(session: Session) -> dict[str, Any]:
    stored = _load_stored_json(session)
    merged, source = _merge_config(stored)
    password = str(merged.get("smtp_password") or "")
    return {
        "enabled": bool(merged.get("enabled", True)),
        "smtp_host": merged.get("smtp_host") or "",
        "smtp_port": int(merged.get("smtp_port") or 465),
        "smtp_use_ssl": bool(merged.get("smtp_use_ssl", True)),
        "smtp_user": merged.get("smtp_user") or "",
        "smtp_password": PASSWORD_MASK if password else "",
        "smtp_password_configured": bool(password),
        "from_email": merged.get("from_email") or merged.get("smtp_user") or "",
        "from_name": str(merged.get("from_name") or settings.SMTP_FROM_NAME),
        "frontend_base_url": merged.get("frontend_base_url") or _default_frontend_url(),
        "configured": bool(
            merged.get("smtp_host") and merged.get("smtp_user") and password and merged.get("from_email")
        ),
        "source": source,
    }


def save_email_settings(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    stored = _load_stored_json(session)
    merged_current, _ = _merge_config(stored)

    new_data = {
        "enabled": bool(payload.get("enabled", True)),
        "smtp_host": str(payload.get("smtp_host") or "").strip(),
        "smtp_port": int(payload.get("smtp_port") or 465),
        "smtp_use_ssl": bool(payload.get("smtp_use_ssl", True)),
        "smtp_user": str(payload.get("smtp_user") or "").strip(),
        "from_email": str(payload.get("from_email") or "").strip(),
        "from_name": str(payload.get("from_name") or settings.SMTP_FROM_NAME).strip(),
        "frontend_base_url": str(payload.get("frontend_base_url") or _default_frontend_url()).rstrip("/"),
    }

    password = payload.get("smtp_password") or ""
    if password and password != PASSWORD_MASK:
        new_data["smtp_password"] = password
    elif merged_current.get("smtp_password"):
        new_data["smtp_password"] = merged_current["smtp_password"]

    row = session.exec(
        select(Configuracao).where(Configuracao.chave == EMAIL_CONFIG_KEY)
    ).first()
    now = datetime.utcnow()
    json_value = json.dumps(new_data, ensure_ascii=False)

    if row:
        row.valor = json_value
        row.tipo = "json"
        row.categoria = "integracao"
        row.descricao = "Parâmetros SMTP para notificações de fluxo de relatórios"
        row.updated_at = now
        session.add(row)
    else:
        row = Configuracao(
            chave=EMAIL_CONFIG_KEY,
            valor=json_value,
            tipo="json",
            categoria="integracao",
            descricao="Parâmetros SMTP para notificações de fluxo de relatórios",
            created_at=now,
            updated_at=now,
        )
        session.add(row)

    session.commit()
    session.refresh(row)
    return get_email_settings_for_api(session)
