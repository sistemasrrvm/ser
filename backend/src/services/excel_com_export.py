"""Exportação Excel/PDF via Microsoft Excel (COM/xlwings) — Windows + Excel desktop."""

from __future__ import annotations

import logging
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Callable, Optional

from sqlmodel import Session

from ..core.config import settings
from ..models.report import Report
from .report_excel_export import CellPatch, build_export_patches

logger = logging.getLogger("ser_app")

XL_TYPE_PDF = 0


class ExcelComError(Exception):
    """Erro na automação COM do Excel."""


def _temp_dir() -> Path:
    base = settings.EXCEL_TEMP_DIR.strip() if settings.EXCEL_TEMP_DIR else ""
    if base:
        path = Path(base)
    else:
        path = Path(tempfile.gettempdir()) / "ser_excel_export"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _resolve_sheet_name(wb, planilha: str) -> Optional[str]:
    name = planilha.strip()
    if not name:
        return None
    for sheet in wb.sheets:
        if sheet.name == name:
            return sheet.name
        if sheet.name.upper() == name.upper():
            return sheet.name
    return None


def _apply_patches(wb, patches: list[CellPatch]) -> None:
    for patch in patches:
        resolved = _resolve_sheet_name(wb, patch.sheet_name)
        if not resolved:
            logger.warning(
                "[EXCEL_COM] Planilha não encontrada: %s (célula %s)",
                patch.sheet_name,
                patch.cell,
            )
            continue
        try:
            target = wb.sheets[resolved].range(patch.cell)
            target.value = patch.value
        except Exception as exc:
            logger.error(
                "[EXCEL_COM] Falha ao escrever %s!%s: %s",
                patch.sheet_name,
                patch.cell,
                exc,
            )
            raise ExcelComError(
                f"Erro ao escrever célula {patch.cell} na planilha {patch.sheet_name}: {exc}"
            ) from exc


def _run_with_excel(
    template_bytes: bytes,
    patches: list[CellPatch],
    *,
    output_suffix: str,
    export_pdf: bool = False,
) -> bytes:
    if sys.platform != "win32":
        raise ExcelComError(
            "Exportação via Excel COM requer Windows com Microsoft Excel instalado."
        )

    try:
        import xlwings as xw
    except ImportError as exc:
        raise ExcelComError(
            "Pacote xlwings não instalado. Execute: pip install -r requirements-windows.txt"
        ) from exc

    work_dir = _temp_dir()
    token = uuid.uuid4().hex
    template_path = work_dir / f"{token}_template.xlsx"
    output_path = work_dir / f"{token}_output{output_suffix}"

    template_path.write_bytes(template_bytes)
    app = None
    wb = None

    try:
        app = xw.App(visible=settings.EXCEL_COM_VISIBLE, add_book=False)
        app.display_alerts = False
        app.screen_updating = False

        wb = app.books.open(str(template_path), update_links=False, read_only=False)
        _apply_patches(wb, patches)

        if export_pdf:
            wb.api.ExportAsFixedFormat(XL_TYPE_PDF, str(output_path))
        else:
            wb.save(str(output_path))
            wb.close()
            wb = None

        if not output_path.exists():
            raise ExcelComError("Excel não gerou o arquivo de saída.")

        return output_path.read_bytes()
    finally:
        if wb is not None:
            try:
                wb.close()
            except Exception:
                pass
        if app is not None:
            try:
                app.quit()
            except Exception:
                pass
        for path in (template_path, output_path):
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                pass


def export_report_via_com(
    template_bytes: bytes,
    report: Report,
    session: Session,
    *,
    format_date: Callable,
    format_yes_no: Callable,
    format_lookup: Callable,
) -> bytes:
    patches = build_export_patches(
        report,
        session,
        format_date=format_date,
        format_yes_no=format_yes_no,
        format_lookup=format_lookup,
    )
    logger.info(
        "[EXCEL_COM] Export relatório %s — %d célula(s)",
        report.numero,
        len(patches),
    )
    return _run_with_excel(template_bytes, patches, output_suffix=".xlsx", export_pdf=False)


def export_report_pdf_via_com(
    template_bytes: bytes,
    report: Report,
    session: Session,
    *,
    format_date: Callable,
    format_yes_no: Callable,
    format_lookup: Callable,
) -> bytes:
    patches = build_export_patches(
        report,
        session,
        format_date=format_date,
        format_yes_no=format_yes_no,
        format_lookup=format_lookup,
    )
    logger.info(
        "[EXCEL_COM] Export PDF relatório %s — %d célula(s)",
        report.numero,
        len(patches),
    )
    return _run_with_excel(template_bytes, patches, output_suffix=".pdf", export_pdf=True)
