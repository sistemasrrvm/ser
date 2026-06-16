"""Exportação Excel via openpyxl — fallback dev/homolog (sem garantia de fidelidade ao template)."""

from __future__ import annotations

import io
from typing import Callable

from sqlmodel import Session

from ..models.report import Report
from .report_excel_export import fill_workbook_from_report


def export_report_via_openpyxl(
    template_bytes: bytes,
    report: Report,
    session: Session,
    *,
    format_date: Callable,
    format_yes_no: Callable,
    format_lookup: Callable,
) -> bytes:
    from openpyxl import load_workbook

    workbook = load_workbook(io.BytesIO(template_bytes))
    fill_workbook_from_report(
        workbook,
        report,
        session,
        format_date=format_date,
        format_yes_no=format_yes_no,
        format_lookup=format_lookup,
    )
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()
