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


def save_upload(file_bytes: bytes, extension: str) -> str:
    file_id = str(uuid.uuid4())
    path = os.path.join(UPLOAD_DIR, f"{file_id}{extension}")
    with open(path, "wb") as f:
        f.write(file_bytes)
    logger.info(f"CAD file uploaded: {file_id}{extension}")
    return file_id


def save_excel_upload(file_bytes: bytes, extension: str) -> str:
    file_id = str(uuid.uuid4())
    path = os.path.join(UPLOAD_DIR, f"{file_id}{extension}")
    with open(path, "wb") as f:
        f.write(file_bytes)
    logger.info(f"Excel uploaded: {file_id}")
    return file_id


def find_cad_file(file_id: str) -> str:
    for ext in (".dxf", ".dwg"):
        path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
        if os.path.exists(path):
            return path
    return None


def _normalize(col: str) -> str:
    """Lowercase + strip spaces for flexible column matching."""
    return str(col).lower().replace(" ", "").replace("_", "").replace(".", "")


def _find_col(df: pd.DataFrame, *candidates) -> str | None:
    """Return first column name that fuzzy-matches any candidate."""
    norm_map = {_normalize(c): c for c in df.columns}
    for cand in candidates:
        key = _normalize(cand)
        if key in norm_map:
            return norm_map[key]
        # partial match
        for nk, orig in norm_map.items():
            if key in nk or nk in key:
                return orig
    return None


def parse_excel(file_path: str) -> List[Dict[str, Any]]:
    logger.info(f"Parsing Excel: {file_path}")
    try:
        # Try to read — try first sheet, then all sheets
        try:
            df = pd.read_excel(file_path, sheet_name=0)
        except Exception:
            xf = pd.ExcelFile(file_path)
            df = pd.read_excel(xf, sheet_name=xf.sheet_names[0])

        # Drop fully empty rows
        df = df.dropna(how="all").reset_index(drop=True)

        # Log what we actually see
        logger.info(f"Excel columns found: {list(df.columns)}")
        logger.info(f"Excel row count: {len(df)}")

        parcels: List[Dict[str, Any]] = []

        # ── Flexible column detection ──────────────────────────────────
        col_sf      = _find_col(df, "sf_no", "sf no", "sfno", "sf", "survey", "surveyno", "survey no", "s.no", "sno")
        col_owner   = _find_col(df, "owner", "name", "ownername", "owner name", "landowner", "pattadar")
        col_extent  = _find_col(df, "extent", "area", "totalextent", "total extent", "totalarea", "total area", "acres")
        col_acquire = _find_col(df, "acquire", "acquisition", "acquired", "acquiredextent", "acquire extent",
                                 "corridor", "corridorwidth", "width")
        col_village = _find_col(df, "village", "villagename", "village name", "mandal", "taluk")
        col_x       = _find_col(df, "x", "xcoord", "x_coord", "longitude", "easting", "long")
        col_y       = _find_col(df, "y", "ycoord", "y_coord", "latitude", "northing", "lat")

        logger.info(f"Mapped columns → sf:{col_sf}, owner:{col_owner}, extent:{col_extent}, "
                    f"acquire:{col_acquire}, village:{col_village}, x:{col_x}, y:{col_y}")

        for idx, row in df.iterrows():
            # Skip header-like repeated rows
            sf_val = str(row[col_sf]).strip() if col_sf else str(idx + 1)
            if sf_val.lower() in ("sf_no", "sf no", "sfno", "nan", ""):
                continue

            parcel: Dict[str, Any] = {
                "sf_no":   sf_val,
                "owner":   str(row[col_owner]).strip()  if col_owner   else "Unknown",
                "extent":  _safe_float(row[col_extent]) if col_extent  else 0.0,
                "acquire": _safe_float(row[col_acquire])if col_acquire else 0.0,
                "village": str(row[col_village]).strip() if col_village else "",
                "x":       _safe_float(row[col_x])      if col_x       else 0.0,
                "y":       _safe_float(row[col_y])      if col_y       else 0.0,
            }
            parcels.append(parcel)

        logger.info(f"Parsed {len(parcels)} parcels from Excel")
        return parcels

    except Exception as ex:
        logger.error(f"Excel parse error: {ex}", exc_info=True)
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
        entities = list(msp)
        layers = [layer.dxf.name for layer in doc.layers]
        return {
            "entity_count": len(entities),
            "layers":       layers,
            "file_id":      file_id,
        }
    except Exception as ex:
        logger.error(f"Context read error: {ex}")
        return {}