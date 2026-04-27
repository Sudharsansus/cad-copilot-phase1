"""
dxf_builder.py
Responsible for: Creating DXF file with correct layers and entities
Each function handles one specific layer/entity type
"""
import ezdxf, re, os, tempfile


# ── Layer definitions matching manual DXF exactly ─────────────────
LAYER_DEFS = [
    # (name,                        color, lineweight)
    ("boundry line",                1,     70),   # RED, thick
    ("chain line",                  251,   0),
    ("CHAIN LINE DISTANCE",         251,   0),
    ("S.F.BOUNDARY DISTANCE",       220,   0),
    ("S.F.SEPERATION LINE",         7,     0),
    ("SUB DIVISION",                3,     0),
    ("SUB DIVISION LINE DISTANCE",  200,   0),
    ("SUB DIVISION NUMBER",         130,   0),
    ("SURVEY NUMBER",               6,     0),
    ("WELL and BUILDING",           5,     0),
]


def build_dxf(boundary_polygon, separation_lines, chain_lines,
              subdivision_lines, texts, page_info, sf_no) -> bytes:
    """
    Main entry point — assembles complete DXF from all components.
    Each section handled by dedicated function.
    """
    dxf = ezdxf.new("R2013")
    msp = dxf.modelspace()
    _setup_layers(dxf)

    _draw_boundary(msp, boundary_polygon)
    _draw_separation_ticks(msp, separation_lines)
    _draw_chain_lines(msp, chain_lines)
    _draw_subdivision_lines(msp, subdivision_lines)
    _draw_text_labels(msp, texts, page_info, sf_no)

    return _save_to_bytes(dxf)


# ── Layer Setup ────────────────────────────────────────────────────

def _setup_layers(dxf):
    """Register all layers with correct color and lineweight"""
    for name, color, lw in LAYER_DEFS:
        dxf.layers.add(name, color=color, lineweight=lw)


# ── Line Drawing Functions ─────────────────────────────────────────

def _add_polyline(msp, p1, p2, layer, lw=0):
    """Add a 2-point LWPOLYLINE (standard for all FMB lines)"""
    pl = msp.add_lwpolyline(
        [p1, p2],
        dxfattribs={"layer": layer, "lineweight": lw}
    )
    pl.closed = False


def _draw_boundary(msp, polygon: list):
    """
    Draw outer boundary as connected 2-pt polylines.
    Layer: boundry line | Color: RED | Lineweight: 70
    """
    if len(polygon) < 2:
        return
    for i in range(len(polygon) - 1):
        _add_polyline(msp, polygon[i], polygon[i+1], "boundry line", lw=70)
    # Close: last vertex back to first
    _add_polyline(msp, polygon[-1], polygon[0], "boundry line", lw=70)


def _draw_separation_ticks(msp, lines: list):
    """
    Draw corner tick marks (short lines at boundary corners A-H).
    Layer: S.F.SEPERATION LINE | Color: White
    """
    for x1, y1, x2, y2 in lines:
        _add_polyline(msp, (x1,y1), (x2,y2), "S.F.SEPERATION LINE")


def _draw_chain_lines(msp, lines: list):
    """
    Draw chain survey lines (blue diagonal lines).
    Layer: chain line | Color: 251
    """
    for x1, y1, x2, y2 in lines:
        _add_polyline(msp, (x1,y1), (x2,y2), "chain line")


def _draw_subdivision_lines(msp, lines: list):
    """
    Draw internal subdivision lines (cross lines between chain points).
    Layer: SUB DIVISION | Color: Green
    """
    for x1, y1, x2, y2 in lines:
        _add_polyline(msp, (x1,y1), (x2,y2), "SUB DIVISION")


# ── Text Label Functions ───────────────────────────────────────────

def _add_text(msp, txt, x, y, height, layer):
    """Add a text entity at given position"""
    msp.add_text(str(txt), dxfattribs={
        "insert": (x, y), "height": height, "layer": layer
    })


def _draw_text_labels(msp, texts: list, page_info: dict, sf_no: str):
    """
    Route each OCR text to correct layer based on content and color.
    Calls dedicated function for each text type.
    """
    pt_m = page_info["pt_to_m"]
    ph   = page_info["height"]
    placed = set()

    for t in texts:
        txt   = t["text"].strip()
        color = t.get("color", "black")
        x     = t["x"] * pt_m
        y     = (ph - t["y"]) * pt_m

        if not txt or t["y"] < 115:
            continue

        key = (txt, round(x, 0), round(y, 0))
        if key in placed:
            continue
        placed.add(key)

        if _draw_corner_label(msp, txt, x, y):         continue
        if _draw_chain_point(msp, txt, color, x, y):   continue
        if _draw_chain_distance(msp, txt, color, x, y):continue
        if _draw_survey_number(msp, txt, x, y, sf_no): continue
        if _draw_subdivision_label(msp, txt, x, y):    continue
        _draw_measurement(msp, txt, x, y)

    # Draw own SF number in center of boundary
    _draw_own_sf_number(msp, texts, page_info, sf_no)


def _draw_corner_label(msp, txt, x, y) -> bool:
    """Corner labels A-H → SURVEY NUMBER layer, height 2.0"""
    if re.match(r'^[A-H]$', txt):
        _add_text(msp, txt, x, y, 2.0, "SURVEY NUMBER")
        return True
    return False


def _draw_chain_point(msp, txt, color, x, y) -> bool:
    """
    Chain point numbers (11,12,13,14,16,18) in red
    → S.F.SEPERATION LINE layer, height 2.0
    """
    if color == "red" and re.match(r'^\d{1,2}$', txt):
        _add_text(msp, txt, x, y, 2.0, "S.F.SEPERATION LINE")
        return True
    return False


def _draw_chain_distance(msp, txt, color, x, y) -> bool:
    """
    Chain distances in brackets (70,8) (134,0) or blue text
    → CHAIN LINE DISTANCE layer, height 3.0
    """
    is_bracketed = re.match(r'^\([\d.,]+\)$', txt)
    if color == "blue" or is_bracketed:
        clean = txt.replace(".", ",")
        _add_text(msp, clean, x, y, 3.0, "CHAIN LINE DISTANCE")
        return True
    return False


def _draw_survey_number(msp, txt, x, y, sf_no) -> bool:
    """
    Neighbor SF numbers (3-4 digit numbers like 403,416,417,612)
    → SURVEY NUMBER layer, height 5.0
    """
    if re.match(r'^\d{3,4}$', txt):
        _add_text(msp, txt, x, y, 5.0, "SURVEY NUMBER")
        return True
    return False


def _draw_subdivision_label(msp, txt, x, y) -> bool:
    """
    Subdivision area labels (1, 2, 3, 1A, 2A, 2B)
    → SUB DIVISION NUMBER layer, height 4.0
    """
    if re.match(r'^[123]$', txt) or re.match(r'^[123][AB]$', txt):
        _add_text(msp, txt, x, y, 4.0, "SUB DIVISION NUMBER")
        return True
    return False


def _draw_measurement(msp, txt, x, y) -> bool:
    """
    Boundary/subdivision measurements (44.2, 31.2, 74.0 etc)
    → S.F.BOUNDARY DISTANCE layer, height 3.0
    """
    try:
        val = float(txt.replace(",", "."))
        if 0.5 < val < 500:
            clean = txt.replace(".", ",")
            _add_text(msp, clean, x, y, 3.0, "S.F.BOUNDARY DISTANCE")
            return True
    except:
        pass
    return False


def _draw_own_sf_number(msp, texts, page_info, sf_no):
    """Draw the parcel's own SF number in center of drawing"""
    if not sf_no or sf_no == "?":
        return
    pt_m = page_info["pt_to_m"]
    ph   = page_info["height"]
    # Estimate center from all text positions
    xs = [t["x"]*pt_m for t in texts if t["y"] > 115]
    ys = [(ph-t["y"])*pt_m for t in texts if t["y"] > 115]
    if xs and ys:
        cx = (min(xs)+max(xs))/2
        cy = (min(ys)+max(ys))/2
        _add_text(msp, sf_no, cx, cy, 5.0, "SURVEY NUMBER")


# ── File Output ────────────────────────────────────────────────────

def _save_to_bytes(dxf) -> bytes:
    """Save DXF to temp file and return bytes"""
    tmp = os.path.join(tempfile.gettempdir(), "fmb_out.dxf")
    dxf.saveas(tmp)
    with open(tmp, "rb") as f:
        return f.read()