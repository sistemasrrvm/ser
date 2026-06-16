"""
Utilitários para template Excel de mesclagem (formularios.excel_template).
"""

import base64
import re
from typing import Optional, Tuple


def decode_excel_template(excel_template: str) -> bytes:
    """Decodifica template Excel armazenado em base64 (com ou sem prefixo data URL)."""
    if not excel_template or not excel_template.strip():
        raise ValueError("Template Excel vazio")

    payload = excel_template.strip()
    if "," in payload:
        payload = payload.split(",", 1)[1]

    return base64.b64decode(payload)


def excel_template_extension(excel_template: str) -> str:
    """Infere extensão (.xlsx ou .xls) a partir do prefixo data URL, se houver."""
    lowered = excel_template.lower()
    if "application/vnd.ms-excel" in lowered or "application/ms-excel" in lowered:
        return ".xls"
    return ".xlsx"


def excel_template_download_filename(formulario_nome: str, formulario_id: int, excel_template: str) -> str:
    """Gera nome de arquivo seguro para download."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", formulario_nome).strip("-").lower() or "formulario"
    ext = excel_template_extension(excel_template)
    return f"template-mesclagem-{slug}-{formulario_id}{ext}"


def excel_template_media_type(excel_template: str) -> str:
    ext = excel_template_extension(excel_template)
    if ext == ".xls":
        return "application/vnd.ms-excel"
    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
