"""Fachada de exportação Excel/PDF — seleciona engine conforme EXPORT_ENGINE."""

from __future__ import annotations

import asyncio
import sys
from typing import Callable

from sqlmodel import Session

from ..core.config import settings
from ..core.export_queue import run_excel_export_job
from ..models.report import Report


class ExportEngineUnavailable(Exception):
    """Engine de exportação indisponível neste ambiente."""


def _normalize_engine() -> str:
    raw = (settings.EXPORT_ENGINE or "").strip().lower()
    if not raw:
        return "excel_com" if sys.platform == "win32" else "none"
    if raw == "excel_com" and sys.platform != "win32":
        return "none"
    return raw


async def export_report_to_xlsx_bytes(
    template_bytes: bytes,
    report: Report,
    session: Session,
    *,
    format_date: Callable,
    format_yes_no: Callable,
    format_lookup: Callable,
) -> bytes:
    engine = _normalize_engine()

    if engine == "excel_com":
        from .excel_com_export import ExcelComError, export_report_via_com

        try:
            return await asyncio.wait_for(
                run_excel_export_job(
                    export_report_via_com,
                    template_bytes,
                    report,
                    session,
                    format_date=format_date,
                    format_yes_no=format_yes_no,
                    format_lookup=format_lookup,
                ),
                timeout=settings.EXCEL_COM_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise ExportEngineUnavailable(
                f"Exportação Excel excedeu {settings.EXCEL_COM_TIMEOUT_SECONDS}s. "
                "Verifique processos EXCEL.EXE órfãos."
            ) from exc
        except ExcelComError as exc:
            raise ExportEngineUnavailable(str(exc)) from exc

    if engine == "openpyxl":
        from .excel_openpyxl_export import export_report_via_openpyxl

        return export_report_via_openpyxl(
            template_bytes,
            report,
            session,
            format_date=format_date,
            format_yes_no=format_yes_no,
            format_lookup=format_lookup,
        )

    raise ExportEngineUnavailable(
        "Exportação Excel não disponível neste ambiente. "
        "Configure EXPORT_ENGINE=excel_com em servidor Windows com Microsoft Excel instalado."
    )


async def export_report_to_pdf_bytes(
    template_bytes: bytes,
    report: Report,
    session: Session,
    *,
    format_date: Callable,
    format_yes_no: Callable,
    format_lookup: Callable,
) -> bytes:
    engine = _normalize_engine()

    if engine == "excel_com":
        from .excel_com_export import ExcelComError, export_report_pdf_via_com

        try:
            return await asyncio.wait_for(
                run_excel_export_job(
                    export_report_pdf_via_com,
                    template_bytes,
                    report,
                    session,
                    format_date=format_date,
                    format_yes_no=format_yes_no,
                    format_lookup=format_lookup,
                ),
                timeout=settings.EXCEL_COM_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise ExportEngineUnavailable(
                f"Exportação PDF excedeu {settings.EXCEL_COM_TIMEOUT_SECONDS}s."
            ) from exc
        except ExcelComError as exc:
            raise ExportEngineUnavailable(str(exc)) from exc

    if engine == "openpyxl":
        from .excel_openpyxl_export import export_report_via_openpyxl
        from .excel_pdf_reportlab import convert_workbook_bytes_to_pdf

        xlsx_bytes = export_report_via_openpyxl(
            template_bytes,
            report,
            session,
            format_date=format_date,
            format_yes_no=format_yes_no,
            format_lookup=format_lookup,
        )
        return convert_workbook_bytes_to_pdf(xlsx_bytes)

    raise ExportEngineUnavailable(
        "Exportação PDF não disponível neste ambiente. "
        "Configure EXPORT_ENGINE=excel_com em servidor Windows com Microsoft Excel instalado."
    )
