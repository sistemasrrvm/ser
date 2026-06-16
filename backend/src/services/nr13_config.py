"""Configuração da integração NR13 (API Botset) — DB + fallback env."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from sqlmodel import Session, select

from ..core.config import settings
from ..models.configuracao import Configuracao

NR13_CONFIG_KEY = "nr13_integracao"
PASSWORD_MASK = "********"


def normalize_api_base_url(url: str) -> str:
    """Remove barra final e sufixos /clientes ou /equipamentos (endpoint é acrescentado depois)."""
    u = (url or "").strip().rstrip("/")
    lower = u.lower()
    for suffix in ("/clientes", "/equipamentos"):
        if lower.endswith(suffix):
            u = u[: -len(suffix)].rstrip("/")
            lower = u.lower()
    return u


@dataclass
class Nr13RuntimeConfig:
    api_base_url: str
    basic_user: str
    basic_password: str
    equipamento_tipo: str
    data_ref_days_back: int
    cron_secret: str
    timeout_seconds: float
    enabled: bool = True


def _defaults_from_env() -> dict[str, Any]:
    return {
        "api_base_url": settings.NR13_API_BASE_URL,
        "basic_user": settings.NR13_API_BASIC_USER,
        "basic_password": settings.NR13_API_BASIC_PASSWORD,
        "equipamento_tipo": settings.NR13_EQUIPAMENTO_TIPO,
        "data_ref_days_back": settings.NR13_DATA_REF_DAYS_BACK,
        "cron_secret": settings.NR13_SYNC_CRON_SECRET,
        "timeout_seconds": settings.NR13_API_TIMEOUT_SECONDS,
        "enabled": True,
    }


def _load_stored_json(session: Session) -> dict[str, Any]:
    row = session.exec(
        select(Configuracao).where(Configuracao.chave == NR13_CONFIG_KEY)
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
        if any(_defaults_from_env().get(k) for k in ("basic_user", "basic_password", "api_base_url")):
            if stored:
                source = "mixed"
    return merged, source


def get_nr13_runtime_config(session: Session) -> Nr13RuntimeConfig:
    stored = _load_stored_json(session)
    merged, _ = _merge_config(stored)
    return Nr13RuntimeConfig(
        api_base_url=normalize_api_base_url(str(merged.get("api_base_url") or "")),
        basic_user=str(merged.get("basic_user") or "").strip(),
        basic_password=str(merged.get("basic_password") or ""),
        equipamento_tipo=str(merged.get("equipamento_tipo") or "12").strip(),
        data_ref_days_back=int(merged.get("data_ref_days_back") or 2),
        cron_secret=str(merged.get("cron_secret") or ""),
        timeout_seconds=float(merged.get("timeout_seconds") or 120.0),
        enabled=bool(merged.get("enabled", True)),
    )


def is_nr13_configured(session: Session) -> bool:
    cfg = get_nr13_runtime_config(session)
    return bool(cfg.enabled and cfg.api_base_url and cfg.basic_user and cfg.basic_password)


def get_nr13_settings_for_api(session: Session) -> dict[str, Any]:
    stored = _load_stored_json(session)
    merged, source = _merge_config(stored)
    password = str(merged.get("basic_password") or "")
    cron = str(merged.get("cron_secret") or "")
    return {
        "api_base_url": merged.get("api_base_url") or "",
        "api_base_url_resolved": normalize_api_base_url(str(merged.get("api_base_url") or "")),
        "basic_user": merged.get("basic_user") or "",
        "basic_password": PASSWORD_MASK if password else "",
        "basic_password_configured": bool(password),
        "equipamento_tipo": str(merged.get("equipamento_tipo") or "12"),
        "data_ref_days_back": int(merged.get("data_ref_days_back") or 2),
        "cron_secret": PASSWORD_MASK if cron else "",
        "cron_secret_configured": bool(cron),
        "timeout_seconds": float(merged.get("timeout_seconds") or 120.0),
        "enabled": bool(merged.get("enabled", True)),
        "configured": bool(
            merged.get("api_base_url") and merged.get("basic_user") and password
        ),
        "source": source,
    }


def save_nr13_settings(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    stored = _load_stored_json(session)
    merged_current, _ = _merge_config(stored)

    new_data = {
        "api_base_url": normalize_api_base_url(payload.get("api_base_url") or ""),
        "basic_user": (payload.get("basic_user") or "").strip(),
        "equipamento_tipo": str(payload.get("equipamento_tipo") or "12"),
        "data_ref_days_back": int(payload.get("data_ref_days_back") or 2),
        "timeout_seconds": float(payload.get("timeout_seconds") or 120.0),
        "enabled": bool(payload.get("enabled", True)),
    }

    password = payload.get("basic_password") or ""
    if password and password != PASSWORD_MASK:
        new_data["basic_password"] = password
    elif merged_current.get("basic_password"):
        new_data["basic_password"] = merged_current["basic_password"]

    cron = payload.get("cron_secret") or ""
    if cron and cron != PASSWORD_MASK:
        new_data["cron_secret"] = cron
    elif merged_current.get("cron_secret"):
        new_data["cron_secret"] = merged_current["cron_secret"]

    row = session.exec(
        select(Configuracao).where(Configuracao.chave == NR13_CONFIG_KEY)
    ).first()
    now = datetime.utcnow()
    json_value = json.dumps(new_data, ensure_ascii=False)

    if row:
        row.valor = json_value
        row.tipo = "json"
        row.categoria = "integracao"
        row.descricao = "Parâmetros da integração NR13 (API Botset)"
        row.updated_at = now
        session.add(row)
    else:
        row = Configuracao(
            chave=NR13_CONFIG_KEY,
            valor=json_value,
            tipo="json",
            categoria="integracao",
            descricao="Parâmetros da integração NR13 (API Botset)",
            created_at=now,
            updated_at=now,
        )
        session.add(row)

    session.commit()
    session.refresh(row)
    return get_nr13_settings_for_api(session)


def verify_cron_secret(session: Session, provided: str) -> bool:
    cfg = get_nr13_runtime_config(session)
    expected = cfg.cron_secret or settings.NR13_SYNC_CRON_SECRET
    if not expected:
        return False
    return provided == expected
