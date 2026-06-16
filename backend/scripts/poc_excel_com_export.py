"""
POC — exportação Excel via xlwings/COM.

Uso (Windows + Excel instalado):
  cd backend
  pip install -r requirements.txt -r requirements-windows.txt
  python scripts/poc_excel_com_export.py --template C:\\caminho\\template.xlsx --output C:\\temp\\saida.xlsx

Opcional — preencher células de teste:
  python scripts/poc_excel_com_export.py --template template.xlsx --output saida.xlsx --patch "Dados,B10,8.6"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permite importar src a partir de backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.excel_com_export import ExcelComError, _run_with_excel
from src.services.report_excel_export import CellPatch


def parse_patch(raw: str) -> CellPatch:
    parts = raw.split(",", 2)
    if len(parts) != 3:
        raise ValueError(f"Patch inválido: {raw!r} (use Planilha,Celula,Valor)")
    sheet, cell, value = parts
    value = value.strip()
    try:
        if "." in value:
            numeric = float(value)
        else:
            numeric = int(value)
        return CellPatch(sheet_name=sheet.strip(), cell=cell.strip().upper(), value=numeric, value_type="number", raw_value=value)
    except ValueError:
        return CellPatch(sheet_name=sheet.strip(), cell=cell.strip().upper(), value=value, value_type="string", raw_value=value)


def main() -> int:
    parser = argparse.ArgumentParser(description="POC export Excel COM (xlwings)")
    parser.add_argument("--template", required=True, help="Caminho do template .xlsx")
    parser.add_argument("--output", required=True, help="Caminho do arquivo de saída .xlsx")
    parser.add_argument(
        "--patch",
        action="append",
        default=[],
        help='Patch de teste: "Planilha,Celula,Valor" (repetível)',
    )
    args = parser.parse_args()

    template_path = Path(args.template)
    output_path = Path(args.output)
    if not template_path.exists():
        print(f"Template não encontrado: {template_path}")
        return 1

    patches = [parse_patch(p) for p in args.patch]
    print(f"Template: {template_path}")
    print(f"Patches: {len(patches)}")

    try:
        result = _run_with_excel(
            template_path.read_bytes(),
            patches,
            output_suffix=".xlsx",
            export_pdf=False,
        )
        output_path.write_bytes(result)
        print(f"OK — arquivo gerado: {output_path} ({len(result)} bytes)")
        return 0
    except ExcelComError as exc:
        print(f"ERRO: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
