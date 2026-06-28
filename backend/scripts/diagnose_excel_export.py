"""
Diagnóstico do ambiente de exportação Excel (COM / openpyxl).

Uso no servidor do cliente:
  cd backend
  .\\venv\\Scripts\\activate
  python scripts/diagnose_excel_export.py
  python scripts/diagnose_excel_export.py --test-com   # testa abrir Excel (pode demorar)
  python scripts/diagnose_excel_export.py --output diagnostico-excel.txt

Saída: JSON no stdout (ou arquivo com --output).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Permite importar src a partir de backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _pkg_version(name: str) -> str | None:
    try:
        from importlib.metadata import version

        return version(name)
    except Exception:
        return None


def _excel_installed() -> dict:
    info: dict = {"installed": False, "path": None, "version": None, "error": None}
    if sys.platform != "win32":
        info["error"] = "N/A fora do Windows"
        return info
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe",
        )
        excel_path, _ = winreg.QueryValueEx(key, "")
        info["installed"] = Path(excel_path).exists()
        info["path"] = excel_path
        winreg.CloseKey(key)
    except Exception as exc:
        info["error"] = str(exc)
    return info


def _excel_com_runtime() -> dict:
    """Versão/build do Excel via COM (rápido, sem export)."""
    result: dict = {
        "ok": False,
        "application_version": None,
        "build": None,
        "path": None,
        "error": None,
    }
    if sys.platform != "win32":
        result["error"] = "COM só em Windows"
        return result
    app = None
    try:
        import xlwings as xw

        app = xw.App(visible=False, add_book=False)
        api = app.api
        result["ok"] = True
        result["application_version"] = str(getattr(api, "Version", "") or "")
        result["build"] = str(getattr(api, "Build", "") or "")
        result["path"] = str(getattr(api, "Path", "") or "")
    except Exception as exc:
        result["error"] = str(exc)
    finally:
        if app is not None:
            try:
                app.quit()
            except Exception:
                pass
    return result


def _excel_com_smoke_test() -> dict:
    result: dict = {"ok": False, "error": None, "bytes": 0}
    if sys.platform != "win32":
        result["error"] = "COM só em Windows"
        return result
    try:
        from src.services.excel_com_export import ExcelComError, _run_with_excel
        from src.services.report_excel_export import CellPatch

        # Template mínimo gerado via openpyxl (só para testar COM)
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Dados"
        ws["A1"] = "test"
        buf = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        buf.close()
        template_path = Path(buf.name)
        wb.save(template_path)

        try:
            patches = [
                CellPatch(
                    sheet_name="Dados",
                    cell="B1",
                    value=8.6,
                    value_type="number",
                    raw_value="8.6",
                )
            ]
            out = _run_with_excel(
                template_path.read_bytes(),
                patches,
                output_suffix=".xlsx",
                export_pdf=False,
            )
            result["ok"] = len(out) > 0
            result["bytes"] = len(out)
        finally:
            template_path.unlink(missing_ok=True)
    except Exception as exc:
        result["error"] = str(exc)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnóstico exportação Excel")
    parser.add_argument(
        "--test-com",
        action="store_true",
        help="Executa teste real abrindo Excel via COM (pode demorar/travar)",
    )
    parser.add_argument(
        "--output",
        metavar="ARQUIVO",
        help="Grava JSON no arquivo (ex.: diagnostico-excel.txt)",
    )
    args = parser.parse_args()

    from src.core.config import settings
    from src.core.version import server_version
    from src.services.excel_export_service import _normalize_engine

    packages = [
        "fastapi",
        "uvicorn",
        "sqlmodel",
        "pymysql",
        "openpyxl",
        "xlsxwriter",
        "reportlab",
        "xlwings",
        "pywin32",
    ]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hostname": platform.node(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "python": sys.version.replace("\n", " "),
            "python_executable": sys.executable,
        },
        "app": {
            "code_hash": server_version.instance_id,
            "app_version": settings.APP_VERSION,
            "environment": os.getenv("ENVIRONMENT", ""),
        },
        "export": {
            "export_engine_env": os.getenv("EXPORT_ENGINE", ""),
            "export_engine_resolved": _normalize_engine(),
            "excel_com_timeout_seconds": settings.EXCEL_COM_TIMEOUT_SECONDS,
            "excel_temp_dir": settings.EXCEL_TEMP_DIR or "(temp padrão)",
            "excel_com_visible": settings.EXCEL_COM_VISIBLE,
        },
        "packages": {name: _pkg_version(name) for name in packages},
        "excel_desktop": _excel_installed(),
        "excel_com_runtime": _excel_com_runtime() if sys.platform == "win32" else {"skipped": True},
        "com_smoke_test": _excel_com_smoke_test() if args.test_com else {"skipped": True},
        "pip_freeze_sample": None,
    }

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if proc.returncode == 0:
            report["pip_freeze_sample"] = proc.stdout.strip().splitlines()
    except Exception as exc:
        report["pip_freeze_sample"] = [f"erro: {exc}"]

    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        out_path = Path(args.output)
        out_path.write_text(payload, encoding="utf-8")
        print(f"Diagnóstico salvo em: {out_path.resolve()}")
    print(payload)
    smoke = report["com_smoke_test"]
    if smoke.get("skipped"):
        return 0
    if smoke.get("ok"):
        return 0
    if _normalize_engine() == "openpyxl":
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
