# backend/app/utils/helpers.py
import os
import uuid
import logging
import ezdxf
import pandas as pd
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Simple log helpers used across all modules ──
def log_info(message: str):
    logger.info(message)

def log_error(message: str, ex: Exception = None):
    if ex:
        logger.error(f"{message}: {ex}", exc_info=True)
    else:
        logger.error(message)

def generate_file_id() -> str:
    return str(uuid.uuid4())


def save_upload(file_bytes: bytes, extension: str) -> str:
    file_id = generate_file_id()
    path = os.path.join(UPLOAD_DIR, f"{file_id}{extension}")
    with open(path, "wb") as f:
        f.write(file_bytes)
    log_info(f"CAD file uploaded: {file_id}{extension}")
    return file_id


def save_excel_upload(file_bytes: bytes, extension: str) -> str:
    file_id = generate_file_id()
    path = os.path.join(UPLOAD_DIR, f"{file_id}{extension}")
    with open(path, "wb") as f:
        f.write(file_bytes)
    log_info(f"Excel uploaded: {file_id}")
    return file_id


def find_cad_file(file_id: str) -> str:
    for ext in (".dxf", ".dwg"):
        path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
        if os.path.exists(path):
            return path
    return None


def _normalize(col: str) -> str:
    return str(col).lower().replace(" ", "").replace("_", "").replace(".", "")


def _find_col(df, *candidates):
    norm_map = {_normalize(c): c for c in df.columns}
    for cand in candidates:
        key = _normalize(cand)
        if key in norm_map:
            return norm_map[key]
        for nk, orig in norm_map.items():
            if key in nk or nk in key:
                return orig
    return None


def parse_excel(file_path: str) -> List[Dict[str, Any]]:
    log_info(f"Parsing Excel: {file_path}")
    try:
        try:
            df = pd.read_excel(file_path, sheet_name=0)
        except Exception:
            xf = pd.ExcelFile(file_path)
            df = pd.read_excel(xf, sheet_name=xf.sheet_names[0])

        df = df.dropna(how="all").reset_index(drop=True)
        log_info(f"Excel columns found: {list(df.columns)}")

        col_sf      = _find_col(df, "sf_no", "sf no", "sfno", "sf", "survey", "surveyno")
        col_owner   = _find_col(df, "owner", "name", "ownername", "pattadar")
        col_extent  = _find_col(df, "extent", "area", "totalextent", "totalarea", "acres")
        col_acquire = _find_col(df, "acquire", "corridor", "corridorwidth", "width")
        col_village = _find_col(df, "village", "villagename", "mandal", "taluk")
        col_x       = _find_col(df, "x", "xcoord", "longitude", "easting")
        col_y       = _find_col(df, "y", "ycoord", "latitude", "northing")

        parcels = []
        for idx, row in df.iterrows():
            sf_val = str(row[col_sf]).strip() if col_sf else str(idx + 1)
            if sf_val.lower() in ("sf_no", "sf no", "sfno", "nan", ""):
                continue
            parcels.append({
                "sf_no":   sf_val,
                "owner":   str(row[col_owner]).strip()   if col_owner   else "Unknown",
                "extent":  _safe_float(row[col_extent])  if col_extent  else 0.0,
                "acquire": _safe_float(row[col_acquire]) if col_acquire else 0.0,
                "village": str(row[col_village]).strip() if col_village else "",
                "x":       _safe_float(row[col_x])       if col_x       else 0.0,
                "y":       _safe_float(row[col_y])       if col_y       else 0.0,
            })

        log_info(f"Parsed {len(parcels)} parcels from Excel")
        return parcels

    except Exception as ex:
        log_error("Excel parse error", ex)
        return []


def _safe_float(val) -> float:
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


def get_drawing_context(file_id: str) -> Dict[str, Any]:
    path = find_cad_file(file_id)
    if not path:
        return {}
    try:
        doc = ezdxf.readfile(path)
        msp = doc.modelspace()
        return {
            "entity_count": len(list(msp)),
            "layers":       [layer.dxf.name for layer in doc.layers],
            "file_id":      file_id,
        }
    except Exception as ex:
        log_error("Context read error", ex)
        return {}