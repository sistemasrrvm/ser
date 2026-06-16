"""
Preserva imagens, desenhos e links externos ao salvar workbook openpyxl.

openpyxl não faz round-trip completo de drawings/media/externalLinks e partes
referenciadas por planilhas (printerSettings, embeddings, etc.).
Este módulo restaura esses assets do xlsx original após o save.
"""

from __future__ import annotations

import io
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_DRAWING_REL = f"{_R_NS}/drawing"
_VML_REL = f"{_R_NS}/vmlDrawing"

_PRESERVE_XL_DIRS = (
    "drawings",
    "media",
    "externalLinks",
    "printerSettings",
    "embeddings",
    "comments",
    "ctrlProps",
)
_DRAWING_SHEET_ELEMENTS = frozenset({"drawing", "legacyDrawing", "legacyDrawingHF"})
_IMAGE_EXTENSIONS = frozenset({"jpeg", "jpg", "png", "gif", "emf", "wmf", "bmp", "tif", "tiff"})


def _local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _copy_preserved_xl_dirs(original_dir: Path, modified_dir: Path) -> None:
    xl_orig = original_dir / "xl"
    xl_mod = modified_dir / "xl"
    if not xl_orig.exists():
        return

    for sub in _PRESERVE_XL_DIRS:
        src = xl_orig / sub
        if not src.exists():
            continue
        dst = xl_mod / sub
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)


def _restore_worksheet_rels(original_dir: Path, modified_dir: Path) -> None:
    orig_rels = original_dir / "xl" / "worksheets" / "_rels"
    mod_rels = modified_dir / "xl" / "worksheets" / "_rels"
    if not orig_rels.exists():
        return
    mod_rels.mkdir(parents=True, exist_ok=True)
    for rel_file in orig_rels.glob("*.rels"):
        shutil.copy2(rel_file, mod_rels / rel_file.name)


def _insert_position(mod_root: ET.Element) -> int:
    for index, el in enumerate(mod_root):
        if _local_tag(el.tag) == "tableParts":
            return index
    return len(mod_root)


def _sync_drawing_elements_from_rels(modified_dir: Path) -> None:
    """Recria drawing/legacyDrawing no XML da planilha a partir dos .rels restaurados."""
    mod_rels_dir = modified_dir / "xl" / "worksheets" / "_rels"
    mod_ws_dir = modified_dir / "xl" / "worksheets"
    if not mod_rels_dir.exists():
        return

    for rel_file in mod_rels_dir.glob("sheet*.xml.rels"):
        sheet_file = mod_ws_dir / rel_file.name.replace(".rels", "")
        if not sheet_file.exists():
            continue

        rel_root = ET.parse(rel_file).getroot()
        drawing_rids: list[str] = []
        vml_rids: list[str] = []
        for rel in rel_root:
            rel_type = rel.get("Type", "")
            rel_id = rel.get("Id")
            if not rel_id:
                continue
            if rel_type == _DRAWING_REL:
                drawing_rids.append(rel_id)
            elif rel_type == _VML_REL:
                vml_rids.append(rel_id)

        if not drawing_rids and not vml_rids:
            continue

        mod_tree = ET.parse(sheet_file)
        mod_root = mod_tree.getroot()
        for el in list(mod_root):
            if _local_tag(el.tag) in _DRAWING_SHEET_ELEMENTS:
                mod_root.remove(el)

        insert_at = _insert_position(mod_root)
        offset = 0
        for rel_id in drawing_rids:
            el = ET.Element(f"{{{_MAIN_NS}}}drawing")
            el.set(f"{{{_R_NS}}}id", rel_id)
            mod_root.insert(insert_at + offset, el)
            offset += 1
        for rel_id in vml_rids:
            el = ET.Element(f"{{{_MAIN_NS}}}legacyDrawing")
            el.set(f"{{{_R_NS}}}id", rel_id)
            mod_root.insert(insert_at + offset, el)
            offset += 1

        mod_tree.write(sheet_file, encoding="UTF-8", xml_declaration=True)


def _merge_relationships(orig_path: Path, mod_path: Path, type_keywords: Iterable[str]) -> None:
    if not orig_path.exists() or not mod_path.exists():
        return

    orig_tree = ET.parse(orig_path)
    mod_tree = ET.parse(mod_path)
    orig_root = orig_tree.getroot()
    mod_root = mod_tree.getroot()

    existing_targets = {el.get("Target") for el in mod_root}
    existing_ids = {el.get("Id") for el in mod_root}

    for el in list(orig_root):
        rel_type = el.get("Type", "")
        target = el.get("Target", "")
        rel_id = el.get("Id", "")
        if not any(keyword in rel_type for keyword in type_keywords):
            continue
        if target in existing_targets or rel_id in existing_ids:
            continue
        new_el = ET.Element(el.tag, el.attrib)
        mod_root.append(new_el)
        existing_targets.add(target)
        existing_ids.add(rel_id)

    mod_tree.write(mod_path, encoding="UTF-8", xml_declaration=True)


def _merge_content_types(original_dir: Path, modified_dir: Path) -> None:
    orig_ct = original_dir / "[Content_Types].xml"
    mod_ct = modified_dir / "[Content_Types].xml"
    if not orig_ct.exists() or not mod_ct.exists():
        return

    orig_tree = ET.parse(orig_ct)
    mod_tree = ET.parse(mod_ct)
    orig_root = orig_tree.getroot()
    mod_root = mod_tree.getroot()

    existing_parts = {el.get("PartName") for el in mod_root if el.tag.endswith("Override")}
    existing_defaults = {
        (el.get("Extension"), el.get("ContentType"))
        for el in mod_root
        if el.tag.endswith("Default")
    }

    preserve_prefixes = tuple(f"/xl/{folder}/" for folder in _PRESERVE_XL_DIRS)

    for el in orig_root:
        if el.tag.endswith("Default"):
            ext = el.get("Extension", "")
            if ext in _IMAGE_EXTENSIONS or ext in {"vml", "bin"}:
                key = (ext, el.get("ContentType"))
                if key not in existing_defaults:
                    mod_root.append(el)
                    existing_defaults.add(key)
            continue

        if not el.tag.endswith("Override"):
            continue
        part_name = el.get("PartName", "")
        if not part_name:
            continue
        if not any(part_name.startswith(prefix) for prefix in preserve_prefixes):
            continue
        if part_name not in existing_parts:
            mod_root.append(el)
            existing_parts.add(part_name)

    mod_tree.write(mod_ct, encoding="UTF-8", xml_declaration=True)


def _restore_workbook_external_references(original_dir: Path, modified_dir: Path) -> None:
    orig_wb = original_dir / "xl" / "workbook.xml"
    mod_wb = modified_dir / "xl" / "workbook.xml"
    if not orig_wb.exists() or not mod_wb.exists():
        return

    orig_tree = ET.parse(orig_wb)
    mod_tree = ET.parse(mod_wb)
    orig_root = orig_tree.getroot()
    mod_root = mod_tree.getroot()

    ext_refs = [el for el in orig_root if _local_tag(el.tag) == "externalReference"]
    if not ext_refs:
        return

    for el in list(mod_root):
        if _local_tag(el.tag) == "externalReference":
            mod_root.remove(el)

    insert_at = _insert_position(mod_root)
    for offset, el in enumerate(ext_refs):
        mod_root.insert(insert_at + offset, el)

    mod_tree.write(mod_wb, encoding="UTF-8", xml_declaration=True)


def _zip_directory(directory: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zout:
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                arcname = path.relative_to(directory).as_posix()
                zout.write(path, arcname)
    return buffer.getvalue()


def save_workbook_preserving_template_assets(workbook, original_bytes: bytes) -> bytes:
    """
    Salva workbook openpyxl e restaura assets do template original.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        original_dir = tmp_path / "original"
        modified_dir = tmp_path / "modified"

        with zipfile.ZipFile(io.BytesIO(original_bytes), "r") as zin:
            zin.extractall(original_dir)

        modified_buffer = io.BytesIO()
        workbook.save(modified_buffer)
        modified_buffer.seek(0)

        with zipfile.ZipFile(modified_buffer, "r") as zin:
            zin.extractall(modified_dir)

        _copy_preserved_xl_dirs(original_dir, modified_dir)
        _restore_worksheet_rels(original_dir, modified_dir)
        _sync_drawing_elements_from_rels(modified_dir)
        _merge_relationships(
            original_dir / "xl" / "_rels" / "workbook.xml.rels",
            modified_dir / "xl" / "_rels" / "workbook.xml.rels",
            ("externalLink",),
        )
        _restore_workbook_external_references(original_dir, modified_dir)
        _merge_content_types(original_dir, modified_dir)

        return _zip_directory(modified_dir)
