"""
Sincronização de clientes e equipamentos NR13 via API Botset (#292).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import httpx
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlmodel import Session, select

from ..models import ManutCliente, ManutEquipamento
from ..schemas.nr13_sync import Nr13NightlySyncResponse, Nr13SyncResponse, SyncEntityResult
from .nr13_config import Nr13RuntimeConfig, get_nr13_runtime_config, is_nr13_configured

logger = logging.getLogger("ser_app")

BATCH_SIZE = 500
TZ_SP = ZoneInfo("America/Sao_Paulo")

SQL_UPSERT_CLIENTE = text(
    """
    INSERT INTO tab_clientes (CLI_ID, CLI_NOME, CLI_CNPJ, CLI_SITE, CLI_DT_INS, CLI_DT_UPD)
    VALUES (:cli_id, :cli_nome, :cli_cnpj, :cli_site, :dt_ins, :dt_upd)
    ON DUPLICATE KEY UPDATE
        CLI_NOME = VALUES(CLI_NOME),
        CLI_CNPJ = VALUES(CLI_CNPJ),
        CLI_SITE = VALUES(CLI_SITE),
        CLI_DT_UPD = VALUES(CLI_DT_UPD)
    """
)

SQL_UPSERT_EQUIPAMENTO = text(
    """
    INSERT INTO tab_equipamentos (
        EQP_ID, EQP_CLI_ID, EQP_TEQP_ID, EQP_TAG, EQP_NOME, EQP_DT_INS, EQP_DT_UPD
    )
    VALUES (:eqp_id, :eqp_cli_id, :eqp_teqp_id, :eqp_tag, :eqp_nome, :dt_ins, :dt_upd)
    ON DUPLICATE KEY UPDATE
        EQP_CLI_ID = VALUES(EQP_CLI_ID),
        EQP_TEQP_ID = VALUES(EQP_TEQP_ID),
        EQP_TAG = VALUES(EQP_TAG),
        EQP_NOME = VALUES(EQP_NOME),
        EQP_DT_UPD = VALUES(EQP_DT_UPD)
    """
)


def compute_data_ref(session: Session, days_back: int | None = None) -> str:
    """Data de referência: hoje (America/Sao_Paulo) menos N dias."""
    cfg = get_nr13_runtime_config(session)
    offset = days_back if days_back is not None else cfg.data_ref_days_back
    ref = datetime.now(TZ_SP).date() - timedelta(days=offset)
    return ref.isoformat()


def ensure_nr13_api_configured(session: Session) -> Nr13RuntimeConfig:
    cfg = get_nr13_runtime_config(session)
    if not is_nr13_configured(session):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Integração NR13 não configurada. "
                "Configure em Configurações → Integração NR13 ou variáveis de ambiente."
            ),
        )
    return cfg


def normalize_cnpj(value: Any) -> str | None:
    if value is None:
        return None
    digits = re.sub(r"\D", "", str(value))
    if not digits:
        return None
    return digits[:14]


def clean_str(value: Any, max_len: int | None = None) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if max_len:
        return s[:max_len]
    return s


def parse_api_records(payload: Any) -> list[dict[str, Any]]:
    """Aceita array JSON, objeto único ou wrapper com chave data/items."""
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "registros", "results"):
            nested = payload.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
        return [payload]
    return []


def parse_json_payload(raw: str) -> Any:
    """
    Parseia corpo JSON da API Botset.
    A API pode retornar objetos separados por vírgula sem array (ticket #292).
    """
    text = raw.strip()
    if not text:
        return []
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if text.startswith("{") and "},{" in text:
            try:
                return json.loads(f"[{text}]")
            except json.JSONDecodeError:
                pass
        raise


def format_nr13_http_error(status_code: int, response_text: str, url: str, body: dict[str, Any]) -> str:
    """Monta mensagem legível a partir da resposta de erro da API Botset."""
    snippet = (response_text or "").strip()[:800]
    filtro = (
        f"dataRef={body.get('dataRef')!r}"
        if "dataRef" in body
        else "sem dataRef"
    )
    try:
        data = json.loads(snippet) if snippet.startswith("{") else None
        if isinstance(data, dict):
            parts: list[str] = []
            title = data.get("title")
            detail = data.get("detail")
            if title:
                parts.append(str(title))
            if detail:
                parts.append(str(detail))
            errors = data.get("errors")
            if errors:
                parts.append(str(errors)[:300])
            trace = data.get("traceId")
            msg = " — ".join(parts) if parts else snippet[:300]
            if trace:
                msg = f"{msg} (traceId: {trace})"
            return (
                f"API NR13 HTTP {status_code} em {url} "
                f"({filtro}): {msg}"
            )
    except json.JSONDecodeError:
        pass
    return (
        f"API NR13 HTTP {status_code} em {url} "
        f"({filtro}): {snippet[:300] or 'sem corpo'}"
    )


def build_nr13_url(base_url: str, path: str) -> str:
    from .nr13_config import normalize_api_base_url

    base = normalize_api_base_url(base_url)
    return f"{base}/{path.lstrip('/')}"


async def _post_nr13_api(
    session: Session,
    path: str,
    body: dict[str, Any],
) -> list[dict[str, Any]]:
    cfg = ensure_nr13_api_configured(session)
    url = build_nr13_url(cfg.api_base_url, path)

    auth = (cfg.basic_user, cfg.basic_password)
    timeout = httpx.Timeout(cfg.timeout_seconds, connect=30.0)

    logger.info("NR13 API POST %s body=%s", url, body)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                json=body,
                auth=auth,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = format_nr13_http_error(
            exc.response.status_code,
            exc.response.text,
            url,
            body,
        )
        logger.error(detail)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        ) from exc
    except httpx.RequestError as exc:
        logger.error("NR13 API request error %s: %s", url, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao conectar à API NR13 ({url}): {exc}",
        ) from exc

    try:
        payload = parse_json_payload(response.text)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Resposta da API NR13 não é JSON válido ({url}): {response.text[:200]}",
        ) from exc

    records = parse_api_records(payload)
    if not records and payload not in (None, [], {}):
        logger.warning("NR13 API resposta sem registros parseáveis: %s", str(payload)[:300])
    return records


async def fetch_clientes_from_api(
    session: Session,
    data_ref: str | None = None,
    *,
    sem_filtro_data: bool = False,
) -> list[dict[str, Any]]:
    if sem_filtro_data:
        body: dict[str, Any] = {}
    else:
        ref = data_ref or compute_data_ref(session)
        body = {"dataRef": ref}
    return await _post_nr13_api(session, "clientes", body)


async def fetch_equipamentos_from_api(
    session: Session,
    data_ref: str | None = None,
    equipamento_tipo: str | None = None,
    *,
    sem_filtro_data: bool = False,
    cliente_id: int | None = None,
) -> list[dict[str, Any]]:
    cfg = get_nr13_runtime_config(session)
    tipo = equipamento_tipo or cfg.equipamento_tipo
    body: dict[str, Any] = {"equipamentoTipo": str(tipo)}
    if not sem_filtro_data:
        ref = data_ref or compute_data_ref(session)
        body["dataRef"] = ref
    if cliente_id is not None:
        body["clienteId"] = cliente_id
    return await _post_nr13_api(session, "equipamentos", body)


def _existing_ids(session: Session, model, id_column, ids: Iterable[int]) -> set[int]:
    id_list = list(ids)
    if not id_list:
        return set()
    rows = session.exec(select(id_column).where(id_column.in_(id_list))).all()
    return set(rows)


def _execute_batches(session: Session, sql, rows: list[dict[str, Any]]) -> None:
    for i in range(0, len(rows), BATCH_SIZE):
        chunk = rows[i : i + BATCH_SIZE]
        for params in chunk:
            session.execute(sql, params)
        session.commit()


def upsert_clientes(session: Session, records: list[dict[str, Any]]) -> SyncEntityResult:
    now = datetime.utcnow()
    params_list: list[dict[str, Any]] = []
    skipped = 0

    for raw in records:
        cli_id = raw.get("id")
        if cli_id is None:
            skipped += 1
            continue
        try:
            cli_id_int = int(cli_id)
        except (TypeError, ValueError):
            skipped += 1
            continue

        params_list.append(
            {
                "cli_id": cli_id_int,
                "cli_nome": clean_str(raw.get("nome"), 200),
                "cli_cnpj": normalize_cnpj(raw.get("cnpj")),
                "cli_site": clean_str(raw.get("site"), 100),
                "dt_ins": now,
                "dt_upd": now,
            }
        )

    if not params_list:
        return SyncEntityResult(
            success=True,
            total=0,
            inserted=0,
            updated=0,
            skipped=skipped,
            message="Nenhum cliente válido retornado pela API",
        )

    existing = _existing_ids(
        session, ManutCliente, ManutCliente.CLI_ID, (p["cli_id"] for p in params_list)
    )
    inserted = sum(1 for p in params_list if p["cli_id"] not in existing)
    updated = len(params_list) - inserted

    try:
        _execute_batches(session, SQL_UPSERT_CLIENTE, params_list)
    except Exception as exc:
        session.rollback()
        logger.exception("Erro ao gravar clientes NR13")
        return SyncEntityResult(
            success=False,
            total=len(params_list),
            inserted=0,
            updated=0,
            skipped=skipped,
            message=str(exc),
        )

    return SyncEntityResult(
        success=True,
        total=len(params_list),
        inserted=inserted,
        updated=updated,
        skipped=skipped,
    )


def upsert_equipamentos(
    session: Session,
    records: list[dict[str, Any]],
    equipamento_tipo: str | None = None,
) -> SyncEntityResult:
    now = datetime.utcnow()
    cfg = get_nr13_runtime_config(session)
    teqp_id = int(equipamento_tipo or cfg.equipamento_tipo)
    params_list: list[dict[str, Any]] = []
    skipped = 0
    missing_cliente = 0

    cliente_ids_needed: set[int] = set()
    parsed_rows: list[dict[str, Any]] = []

    for raw in records:
        eqp_id = raw.get("id")
        cliente_id = raw.get("clienteId")
        tag = clean_str(raw.get("tag"), 200)
        if eqp_id is None or cliente_id is None or not tag:
            skipped += 1
            continue
        try:
            eqp_id_int = int(eqp_id)
            cliente_id_int = int(cliente_id)
        except (TypeError, ValueError):
            skipped += 1
            continue

        parsed_rows.append(
            {
                "eqp_id": eqp_id_int,
                "eqp_cli_id": cliente_id_int,
                "eqp_teqp_id": teqp_id,
                "eqp_tag": tag,
                "eqp_nome": clean_str(raw.get("nome"), 200),
                "dt_ins": now,
                "dt_upd": now,
            }
        )
        cliente_ids_needed.add(cliente_id_int)

    if parsed_rows:
        existing_clientes = _existing_ids(
            session, ManutCliente, ManutCliente.CLI_ID, cliente_ids_needed
        )
        for row in parsed_rows:
            if row["eqp_cli_id"] not in existing_clientes:
                missing_cliente += 1
                skipped += 1
                continue
            params_list.append(row)

    if not params_list:
        msg = "Nenhum equipamento válido retornado pela API"
        if missing_cliente:
            msg += f" ({missing_cliente} sem cliente local)"
        return SyncEntityResult(
            success=True,
            total=0,
            inserted=0,
            updated=0,
            skipped=skipped,
            message=msg,
        )

    existing = _existing_ids(
        session, ManutEquipamento, ManutEquipamento.EQP_ID, (p["eqp_id"] for p in params_list)
    )
    inserted = sum(1 for p in params_list if p["eqp_id"] not in existing)
    updated = len(params_list) - inserted

    try:
        _execute_batches(session, SQL_UPSERT_EQUIPAMENTO, params_list)
    except Exception as exc:
        session.rollback()
        logger.exception("Erro ao gravar equipamentos NR13")
        return SyncEntityResult(
            success=False,
            total=len(params_list),
            inserted=0,
            updated=0,
            skipped=skipped,
            message=str(exc),
        )

    message = None
    if missing_cliente:
        message = f"{missing_cliente} equipamento(s) ignorado(s): cliente não encontrado em tab_clientes"

    return SyncEntityResult(
        success=True,
        total=len(params_list),
        inserted=inserted,
        updated=updated,
        skipped=skipped,
        message=message,
    )


async def sync_clientes(
    session: Session,
    data_ref: str | None = None,
    *,
    sem_filtro_data: bool = False,
) -> Nr13SyncResponse:
    if sem_filtro_data:
        ref_label = "(sem filtro de data)"
        records = await fetch_clientes_from_api(session, sem_filtro_data=True)
    else:
        ref_label = data_ref or compute_data_ref(session)
        records = await fetch_clientes_from_api(session, ref_label)
    result = upsert_clientes(session, records)
    return Nr13SyncResponse(
        success=result.success,
        data_ref=ref_label,
        results=result,
    )


async def sync_equipamentos(
    session: Session,
    data_ref: str | None = None,
    equipamento_tipo: str | None = None,
    *,
    sem_filtro_data: bool = False,
    cliente_id: int | None = None,
) -> Nr13SyncResponse:
    if sem_filtro_data:
        ref_label = "(sem filtro de data)"
        records = await fetch_equipamentos_from_api(
            session,
            equipamento_tipo=equipamento_tipo,
            sem_filtro_data=True,
            cliente_id=cliente_id,
        )
    else:
        ref_label = data_ref or compute_data_ref(session)
        records = await fetch_equipamentos_from_api(
            session, ref_label, equipamento_tipo, cliente_id=cliente_id
        )
    result = upsert_equipamentos(session, records, equipamento_tipo)
    return Nr13SyncResponse(
        success=result.success,
        data_ref=ref_label,
        results=result,
    )


async def sync_nightly(session: Session) -> Nr13NightlySyncResponse:
    ref = compute_data_ref(session)
    clientes_records = await fetch_clientes_from_api(session, ref)
    clientes_result = upsert_clientes(session, clientes_records)
    equipamentos_records = await fetch_equipamentos_from_api(session, ref)
    equipamentos_result = upsert_equipamentos(session, equipamentos_records)

    success = clientes_result.success and equipamentos_result.success
    return Nr13NightlySyncResponse(
        success=success,
        data_ref=ref,
        results={
            "clientes": clientes_result,
            "equipamentos": equipamentos_result,
        },
        message=None if success else "Uma ou mais etapas falharam",
    )
