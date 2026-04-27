"""
extractor.py
Responsible for: Extracting raw vector data from FMB PDF
"""
import fitz, math, re, io, pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extract_pdf(pdf_bytes: bytes) -> tuple:
    """
    Main entry point for PDF extraction.
    Returns: (lines, page_info, img_bytes)
    """
    doc    = fitz.open(stream=pdf_bytes, filetype="pdf")
    page   = doc[0]
    page_h = page.rect.height
    page_w = page.rect.width
    scale  = _detect_scale(page)
    pt_m   = 0.000353 * scale

    img_bytes = _render_image(page)
    lines     = _extract_lines(page, page_w, page_h, pt_m)

    page_info = {
        "height":  page_h,
        "width":   page_w,
        "scale":   scale,
        "pt_to_m": pt_m,
        "zoom":    4.0,
    }
    return lines, page_info, img_bytes


def _render_image(page) -> bytes:
    """Render PDF page at 4x zoom for OCR"""
    pix = page.get_pixmap(matrix=fitz.Matrix(4, 4))
    return pix.tobytes("png")


def _detect_scale(page) -> int:
    """Read scale ratio from PDF header (e.g. 1:1079)"""
    pix  = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img  = Image.open(io.BytesIO(pix.tobytes("png")))
    text = pytesseract.image_to_string(img, config="--psm 6")
    m    = re.search(r'1\s*[:/]\s*(\d{3,5})', text)
    return int(m.group(1)) if m else 1000


def _is_border(p1, p2, page_w, page_h) -> bool:
    """Check if line is a page border or header line"""
    return (
        min(p1.x, p2.x) < 15 or
        max(p1.x, p2.x) > page_w - 15 or
        min(p1.y, p2.y) < 15 or
        max(p1.y, p2.y) > page_h - 15 or
        (p1.y < 115 and p2.y < 115)
    )


def _extract_lines(page, page_w, page_h, pt_m) -> list:
    """Extract all vector lines from PDF with metadata"""
    lines = []
    for d in page.get_drawings():
        color = d.get("color")
        width = d.get("width") or 0
        for item in d.get("items", []):
            if item[0] != "l":
                continue
            p1, p2  = item[1], item[2]
            lenpx   = math.hypot(p2.x - p1.x, p2.y - p1.y)
            if _is_border(p1, p2, page_w, page_h) or lenpx < 5:
                continue
            lines.append({
                "px1":   p1.x,  "py1": p1.y,
                "px2":   p2.x,  "py2": p2.y,
                "lenpx": lenpx, "lenm": lenpx * pt_m,
                "width": width, "color": color,
                "black":   color == (0., 0., 0.),
                "colored": color not in [None, (0.,0.,0.), (1.,1.,1.)],
                "mx": (p1.x + p2.x) / 2,
                "my": (p1.y + p2.y) / 2,
            })
    return lines


def categorize_lines(lines: list, page_info: dict) -> dict:
    """
    Categorize lines by width and color:
      w=3, black, lenm>12  → boundary (thick outer lines)
      w=3, black, lenm<=12 → separation ticks (corner marks)
      w=1, black, lenm<=50 → subdivision (internal cross lines)
      colored              → chain lines (blue diagonal lines)
      w=1, black, lenm>50  → skip (duplicate boundary/long diagonals)
    """
    boundary   = []
    separation = []
    subdivision= []
    chain      = []

    for l in lines:
        w = l["width"]
        if l["colored"]:
            chain.append(l)
        elif l["black"]:
            if abs(w - 3.0) < 0.5:
                if l["lenm"] > 12:
                    boundary.append(l)
                else:
                    separation.append(l)
            elif abs(w - 1.0) < 0.5:
                if 5 < l["lenm"] <= 50:
                    subdivision.append(l)

    return {
        "boundary":    boundary,
        "separation":  separation,
        "subdivision": subdivision,
        "chain":       chain,
    }