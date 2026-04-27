"""
converter.py
Responsible for: Orchestrating the full PDF → DXF pipeline
Calls each module in sequence
"""
import re
import numpy as np
from PIL import Image
import io

from extractor   import extract_pdf, categorize_lines
from ocr         import ocr_image, detect_text_colors
from geometry    import build_boundary_polygon, get_lines_in_meters
from dxf_builder import build_dxf


def convert(pdf_bytes: bytes, api_key: str = "") -> tuple:
    """
    Full pipeline: PDF bytes → DXF bytes
    Returns: (dxf_bytes, info_dict)
    """

    # ── 1. Extract raw vectors from PDF ──────────────────────────
    lines, page_info, img_bytes = extract_pdf(pdf_bytes)
    cats = categorize_lines(lines, page_info)

    # ── 2. OCR: read all text labels from PDF image ───────────────
    img_arr     = np.array(Image.open(io.BytesIO(img_bytes)))
    ocr_results = ocr_image(img_bytes, api_key)
    ocr_results = detect_text_colors(img_arr, ocr_results,
                                     zoom=page_info["zoom"])

    # Convert OCR pixel coords → PDF space (divide by zoom)
    texts_pdf = _to_pdf_space(ocr_results, page_info["zoom"])

    # ── 3. Parse header info ──────────────────────────────────────
    full_text = " ".join(t["text"] for t in ocr_results)
    sf_no     = _parse_header(r'Survey\s*No\s*[:\-]?\s*(\d+)', full_text)
    district  = _parse_header(r'District\s*[:\-]?\s*(\w+)', full_text)
    taluk     = _parse_header(r'Taluk\s*[:\-]?\s*(\w+)', full_text)
    village   = _parse_header(r'Village\s*[:\-]?\s*([\w.]+)', full_text)

    # ── 4. Build boundary polygon from w=3 lines ──────────────────
    boundary_polygon = build_boundary_polygon(cats["boundary"], page_info)

    # ── 5. Convert all other lines to meters ──────────────────────
    separation_lines  = get_lines_in_meters(cats["separation"],  page_info)
    chain_lines       = get_lines_in_meters(cats["chain"],       page_info)
    subdivision_lines = get_lines_in_meters(cats["subdivision"], page_info)

    # ── 6. Build DXF ──────────────────────────────────────────────
    dxf_bytes = build_dxf(
        boundary_polygon  = boundary_polygon,
        separation_lines  = separation_lines,
        chain_lines       = chain_lines,
        subdivision_lines = subdivision_lines,
        texts             = texts_pdf,
        page_info         = page_info,
        sf_no             = sf_no or "?",
    )

    info = {
        "sf_no":        sf_no or "?",
        "district":     district or "",
        "taluk":        taluk or "",
        "village":      village or "",
        "scale":        page_info["scale"],
        "boundary_pts": len(boundary_polygon),
        "corners":      _count_corners(texts_pdf),
        "measurements": _count_measurements(texts_pdf),
    }
    return dxf_bytes, info


# ── Helper Functions ───────────────────────────────────────────────

def _to_pdf_space(texts: list, zoom: float) -> list:
    """Convert OCR pixel coords back to PDF coordinate space"""
    return [
        {
            "text":  t["text"],
            "x":     t["x"] / zoom,
            "y":     t["y"] / zoom,
            "color": t.get("color", "black"),
        }
        for t in texts
        if t["y"] / zoom > 115  # skip header area
    ]


def _parse_header(pattern: str, text: str) -> str:
    """Extract field from PDF header text using regex"""
    m = re.search(pattern, text, re.I)
    return m.group(1) if m else None


def _count_corners(texts: list) -> int:
    """Count detected corner labels A-H"""
    return len([t for t in texts if re.match(r'^[A-H]$', t["text"])])


def _count_measurements(texts: list) -> int:
    """Count detected numeric measurements"""
    count = 0
    for t in texts:
        try:
            v = float(t["text"].replace(",", "."))
            if 1 < v < 500:
                count += 1
        except:
            pass
    return count