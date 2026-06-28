"""Exportação Excel/PDF via Microsoft Excel (COM/xlwings) — Windows + Excel desktop."""

from __future__ import annotations

import logging
import sys
import tempfile
import time
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


class _ComStepLog:
    """Marca passos da exportação COM com tempo desde o anterior e total."""

    def __init__(self, label: str) -> None:
        self.label = label
        self._started = time.perf_counter()
        self._last = self._started

    def step(self, message: str, **details) -> None:
        now = time.perf_counter()
        since_last = now - self._last
        total = now - self._started
        self._last = now
        extra = ""
        if details:
            extra = " | " + ", ".join(f"{key}={value}" for key, value in details.items())
        logger.info(
            "[EXCEL_COM] %s | +%.1fs (total %.1fs) %s%s",
            self.label,
            since_last,
            total,
            message,
            extra,
        )


def _temp_dir() -> Path:
    base = settings.EXCEL_TEMP_DIR.strip() if settings.EXCEL_TEMP_DIR else ""
    if base:
        path = Path(base)
    else:
        path = Path(tempfile.gettempdir()) / "ser_excel_export"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _break_external_links(wb, steps: _ComStepLog | None = None) -> None:
    """Remove referências a pastas/arquivos externos que quebram ao abrir em outro servidor."""
    try:
        links = wb.api.LinkSources(1)  # xlExcelLinks
        if not links:
            if steps:
                steps.step("nenhum link externo no workbook")
            return
        if isinstance(links, str):
            links = (links,)

        broken = 0
        for link in links:
            try:
                wb.api.BreakLink(link, 1)
                broken += 1
            except Exception:
                pass

        if steps:
            steps.step("links externos processados", removidos=broken, total=len(links))
    except Exception as exc:
        if steps:
            steps.step("aviso ao verificar links externos", erro=str(exc))


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


def _apply_patches(wb, patches: list[CellPatch], steps: _ComStepLog | None = None) -> None:
    if steps:
        steps.step("início preenchimento de células", celulas=len(patches))

    from collections import defaultdict

    by_sheet: dict[str, list[CellPatch]] = defaultdict(list)
    for patch in patches:
        by_sheet[patch.sheet_name].append(patch)

    written = 0
    progress_every = 25

    for sheet_name, sheet_patches in by_sheet.items():
        sheet_started = time.perf_counter()
        resolved = _resolve_sheet_name(wb, sheet_name)
        if not resolved:
            logger.warning(
                "[EXCEL_COM] Planilha não encontrada: %s (%d célula(s))",
                sheet_name,
                len(sheet_patches),
            )
            continue

        sheet = wb.sheets[resolved]
        for index, patch in enumerate(sheet_patches, start=1):
            try:
                sheet.range(patch.cell).value = patch.value
                written += 1
            except Exception as exc:
                logger.error(
                    "[EXCEL_COM] Falha ao escrever %s!%s: %s",
                    sheet_name,
                    patch.cell,
                    exc,
                )
                raise ExcelComError(
                    f"Erro ao escrever célula {patch.cell} na planilha {sheet_name}: {exc}"
                ) from exc

            if steps and len(sheet_patches) > progress_every and index % progress_every == 0:
                steps.step(
                    f"progresso planilha '{resolved}'",
                    preenchidas=f"{index}/{len(sheet_patches)}",
                )

        if steps:
            steps.step(
                f"planilha '{resolved}' concluída",
                celulas=len(sheet_patches),
                duracao_s=f"{time.perf_counter() - sheet_started:.1f}",
            )

    if steps:
        steps.step("preenchimento de células concluído", celulas_escritas=written)


def _run_with_excel(
    template_bytes: bytes,
    patches: list[CellPatch],
    *,
    output_suffix: str,
    export_pdf: bool = False,
    label: str = "",
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
    steps = _ComStepLog(label or f"job-{token[:8]}")

    template_path.write_bytes(template_bytes)
    steps.step(
        "template gravado em disco",
        bytes=len(template_bytes),
        arquivo=template_path.name,
    )
    app = None
    wb = None

    try:
        steps.step("iniciando processo Excel (xw.App)")
        app = xw.App(visible=settings.EXCEL_COM_VISIBLE, add_book=False)
        app.display_alerts = False
        app.screen_updating = False
        try:
            app.api.EnableEvents = False
            app.api.Calculation = -4135  # xlCalculationManual
            app.api.Interactive = False
        except Exception:
            pass
        steps.step("processo Excel iniciado")

        steps.step("abrindo workbook do template")
        wb = app.books.open(str(template_path), update_links=False, read_only=False)
        try:
            sheet_names = [sheet.name for sheet in wb.sheets]
        except Exception:
            sheet_names = []
        steps.step("workbook aberto", planilhas=len(sheet_names), nomes=",".join(sheet_names[:5]))

        _break_external_links(wb, steps)
        _apply_patches(wb, patches, steps)

        if export_pdf:
            steps.step("exportando PDF (ExportAsFixedFormat)")
            wb.api.ExportAsFixedFormat(XL_TYPE_PDF, str(output_path))
        else:
            steps.step("salvando workbook de saída")
            wb.save(str(output_path))
            wb.close()
            wb = None
            steps.step("workbook salvo e fechado", arquivo=output_path.name)

        if not output_path.exists():
            raise ExcelComError("Excel não gerou o arquivo de saída.")

        output_bytes = output_path.read_bytes()
        steps.step("arquivo de saída lido", bytes=len(output_bytes))
        return output_bytes
    finally:
        if wb is not None:
            try:
                wb.close()
            except Exception:
                pass
        if app is not None:
            try:
                steps.step("encerrando processo Excel (app.quit)")
                app.quit()
            except Exception:
                pass
        for path in (template_path, output_path):
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                pass
        steps.step("limpeza de arquivos temporários concluída")


def export_report_via_com(
    template_bytes: bytes,
    report: Report,
    session: Session,
    *,
    format_date: Callable,
    format_yes_no: Callable,
    format_lookup: Callable,
) -> bytes:
    patches_started = time.perf_counter()
    patches = build_export_patches(
        report,
        session,
        format_date=format_date,
        format_yes_no=format_yes_no,
        format_lookup=format_lookup,
    )
    logger.info(
        "[EXCEL_COM] %s | patches montados em %.1fs (%d célula(s))",
        report.numero,
        time.perf_counter() - patches_started,
        len(patches),
    )
    started = time.perf_counter()
    result = _run_with_excel(
        template_bytes,
        patches,
        output_suffix=".xlsx",
        export_pdf=False,
        label=report.numero,
    )
    elapsed = time.perf_counter() - started
    logger.info(
        "[EXCEL_COM] Export relatório %s concluído em %.1fs (%d bytes)",
        report.numero,
        elapsed,
        len(result),
    )
    return result


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
    return _run_with_excel(
        template_bytes,
        patches,
        output_suffix=".pdf",
        export_pdf=True,
        label=f"{report.numero}-pdf",
    )
