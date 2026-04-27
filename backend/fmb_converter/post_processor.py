"""
post_processor.py - FMB PDFIMPORT DXF Post Processor
Applies correct scale, layers, colors, linetypes.
Classification based on lineweight + color (verified from imported DXF).
Usage: python post_processor.py input.dxf 1079 output.dxf
"""
import ezdxf, math, sys

# Verified scale formula (ground truth: A→B=44.2m, PDF=1.783units)
PDFIMPORT_FACTOR = 0.022975

LAYER_DEFS = {
    "boundry line":               {"color": 1,   "lw": 70,  "linetype": "Continuous"},
    "chain line":                 {"color": 251, "lw": 0,   "linetype": "ACAD_ISO06W100"},
    "CHAIN LINE DISTANCE":        {"color": 7,   "lw": 0,   "linetype": "Continuous"},
    "S.F.BOUNDARY DISTANCE":      {"color": 6,   "lw": 0,   "linetype": "Continuous"},
    "S.F.SEPERATION LINE":        {"color": 7,   "lw": 0,   "linetype": "DASHDOT"},
    "SUB DIVISION":               {"color": 3,   "lw": 0,   "linetype": "Continuous"},
    "SUB DIVISION LINE DISTANCE": {"color": 200, "lw": 0,   "linetype": "Continuous"},
    "SUB DIVISION NUMBER":        {"color": 130, "lw": 0,   "linetype": "Continuous"},
    "SURVEY NUMBER":              {"color": 6,   "lw": 0,   "linetype": "Continuous"},
    "WELL and BUILDING":          {"color": 5,   "lw": 0,   "linetype": "Continuous"},
}


def process(input_path: str, scale_ratio: float, output_path: str):
    scale = scale_ratio * PDFIMPORT_FACTOR
    print(f"Scale 1:{scale_ratio:.0f} → {scale:.6f} m/unit")

    doc = ezdxf.readfile(input_path)
    msp = doc.modelspace()
    polys = [e for e in msp if e.dxftype() == "LWPOLYLINE"]
    texts = [e for e in msp if e.dxftype() in ("TEXT","MTEXT")]
    print(f"Polylines: {len(polys)}, Texts: {len(texts)}")

    out     = ezdxf.new("R2013")
    out_msp = out.modelspace()
    setup_linetypes(out)
    setup_layers(out)

    boundary, chain, separation, subdivision, well, skipped = classify(polys)
    print(f"boundary={len(boundary)} chain={len(chain)} "
          f"sep={len(separation)} sub={len(subdivision)} "
          f"well={len(well)} skipped={len(skipped)}")

    draw_boundary_lines(out_msp, boundary, scale)
    draw_chain_lines(out_msp, chain, scale)
    draw_separation_lines(out_msp, separation, scale)
    draw_subdivision_lines(out_msp, subdivision, scale)
    draw_well_and_building(out_msp, well, scale)
    draw_all_texts(out_msp, texts, scale)

    out.saveas(output_path)
    print(f"✅ Saved: {output_path}")


# ── Setup ──────────────────────────────────────────────────────────

def setup_linetypes(doc):
    doc.linetypes.add("DASHDOT",
        pattern=[0.5, 0.25, -0.125, 0.0, -0.125],
        description="Dash dot")
    doc.linetypes.add("ACAD_ISO06W100",
        pattern=[12.0, 6.0, -3.0, 0.0, -3.0],
        description="ISO dash dot")

def setup_layers(doc):
    for name, props in LAYER_DEFS.items():
        l = doc.layers.add(name)
        l.dxf.color      = props["color"]
        l.dxf.lineweight = props["lw"]
        l.dxf.linetype   = props["linetype"]


# ── Classification (based on lineweight + color) ───────────────────

def classify(polys: list) -> tuple:
    """
    Classification rules verified from PDFIMPORT output:
      color=5                  → WELL and BUILDING (blue chain line)
      color=250, large area    → PAGE BORDER (skip)
      lw=70, large area/closed → PAGE BORDER (skip)
      lw=106, pts>=10, closed  → BOUNDARY (main polygon)
      lw=106, pts=2, short     → S.F.SEPERATION LINE (corner ticks)
      lw=106, pts=2, long      → PAGE BORDER (skip)
      lw=35, pts>=3            → SUB DIVISION
      lw=35, pts=2             → SUB DIVISION (short lines)
    """
    boundary   = []
    chain      = []
    separation = []
    subdivision= []
    well       = []
    skipped    = []

    # Get max area to detect page border
    areas = []
    for p in polys:
        pts = list(p.get_points())
        if len(pts) < 2:
            areas.append(0)
            continue
        xs=[pt[0] for pt in pts]; ys=[pt[1] for pt in pts]
        areas.append((max(xs)-min(xs))*(max(ys)-min(ys)))
    max_area = max(areas) if areas else 1

    for p, area in zip(polys, areas):
        pts = list(p.get_points())
        try: color = p.dxf.color
        except: color = 256
        try: lw = p.dxf.lineweight
        except: lw = 0

        length = _length(pts)

        # Blue chain survey line
        if color == 5:
            well.append(p)
            continue

        # Page border — large area gray/dark line
        if color == 250 or area > max_area * 0.5:
            skipped.append(p)
            continue

        # lw=106 (heavy lines from PDFIMPORT)
        if lw == 106:
            if len(pts) >= 10 and p.closed:
                # Main boundary polygon
                boundary.append(p)
            elif len(pts) == 2 and length < 0.5:
                # Short tick marks at corners
                separation.append(p)
            else:
                # Long single lines = page border parts
                skipped.append(p)
            continue

        # lw=35 (normal lines)
        if lw == 35:
            subdivision.append(p)
            continue

        skipped.append(p)

    return boundary, chain, separation, subdivision, well, skipped


# ── Drawing functions — one per layer ─────────────────────────────

def draw_boundary_lines(msp, polys, scale):
    """
    BOUNDARY: each vertex pair = separate polyline
    Layer: boundry line | Color: RED(1) | lw=70 | Continuous
    """
    for p in polys:
        pts = [(pt[0]*scale, pt[1]*scale) for pt in p.get_points()]
        for i in range(len(pts)-1):
            _pl(msp, [pts[i], pts[i+1]],
                layer="boundry line", color=1, lw=70, lt="Continuous")
        if p.closed and len(pts) > 1:
            _pl(msp, [pts[-1], pts[0]],
                layer="boundry line", color=1, lw=70, lt="Continuous")


def draw_chain_lines(msp, polys, scale):
    """
    CHAIN LINES: survey measurement lines
    Layer: chain line | Color: ByLayer(256) | ACAD_ISO06W100
    """
    for p in polys:
        pts = [(pt[0]*scale, pt[1]*scale) for pt in p.get_points()]
        _pl(msp, pts, layer="chain line", color=256, lw=0,
            lt="ACAD_ISO06W100")


def draw_separation_lines(msp, polys, scale):
    """
    SEPARATION TICKS: corner marks at A,B,C...H
    Layer: S.F.SEPERATION LINE | Color: ByLayer(256) | DASHDOT
    """
    for p in polys:
        pts = [(pt[0]*scale, pt[1]*scale) for pt in p.get_points()]
        _pl(msp, pts, layer="S.F.SEPERATION LINE", color=256, lw=0,
            lt="DASHDOT")


def draw_subdivision_lines(msp, polys, scale):
    """
    SUBDIVISION: internal cross lines between chain points
    Layer: SUB DIVISION | Color: ByLayer(256=Green) | Continuous
    """
    for p in polys:
        pts = [(pt[0]*scale, pt[1]*scale) for pt in p.get_points()]
        _pl(msp, pts, layer="SUB DIVISION", color=256, lw=0,
            lt="Continuous")


def draw_well_and_building(msp, polys, scale):
    """
    WELL AND BUILDING: blue diagonal chain survey line
    Layer: WELL and BUILDING | Color: ByLayer(256=Blue) | Continuous
    """
    for p in polys:
        pts = [(pt[0]*scale, pt[1]*scale) for pt in p.get_points()]
        _pl(msp, pts, layer="WELL and BUILDING", color=256, lw=0,
            lt="Continuous")


def draw_all_texts(msp, texts, scale):
    """Route all text labels to correct layer"""
    for e in texts:
        if e.dxftype() == "TEXT":
            txt = e.dxf.text.strip()
            x, y = e.dxf.insert[0]*scale, e.dxf.insert[1]*scale
        else:
            txt = e.text.strip()
            x, y = e.dxf.insert[0]*scale, e.dxf.insert[1]*scale
        if txt:
            _route_text(msp, txt, x, y)


# ── Text routing — one function per text type ──────────────────────

def _route_text(msp, txt, x, y):
    import re
    if re.match(r'^[A-H]$', txt):
        draw_corner_label(msp, txt, x, y)
    elif re.match(r'^\([\d.,]+\)$', txt):
        draw_chain_distance(msp, txt, x, y)
    elif re.match(r'^\d{3,4}$', txt):
        draw_survey_number(msp, txt, x, y)
    elif re.match(r'^[123]$', txt) or re.match(r'^[123][AB]$', txt):
        draw_subdivision_number(msp, txt, x, y)
    else:
        try:
            v = float(txt.replace(",","."))
            if 0.5 < v < 500:
                draw_boundary_distance(msp, txt, x, y)
        except: pass

def draw_corner_label(msp, txt, x, y):
    """A,B,C,D,E,F,G,H → SURVEY NUMBER | Magenta | h=2"""
    _txt(msp, txt, x, y, h=2.0, layer="SURVEY NUMBER", color=256)

def draw_survey_number(msp, txt, x, y):
    """400,403,416,417,612 → SURVEY NUMBER | Magenta | h=5"""
    _txt(msp, txt, x, y, h=5.0, layer="SURVEY NUMBER", color=256)

def draw_boundary_distance(msp, txt, x, y):
    """44,2 / 31,2 / 74,0 → S.F.BOUNDARY DISTANCE | Magenta | h=3"""
    _txt(msp, txt.replace(".",","), x, y, h=3.0,
         layer="S.F.BOUNDARY DISTANCE", color=256)

def draw_chain_distance(msp, txt, x, y):
    """(70,8) (134,0) → CHAIN LINE DISTANCE | White | h=3"""
    _txt(msp, txt.replace(".",","), x, y, h=3.0,
         layer="CHAIN LINE DISTANCE", color=256)

def draw_subdivision_number(msp, txt, x, y):
    """1,2,3,2A,2B → SUB DIVISION NUMBER | Cyan | h=4"""
    _txt(msp, txt, x, y, h=4.0, layer="SUB DIVISION NUMBER", color=256)


# ── Primitives ─────────────────────────────────────────────────────

def _pl(msp, pts, layer, color=256, lw=0, lt="Continuous", closed=False):
    pl = msp.add_lwpolyline(pts, dxfattribs={
        "layer": layer, "color": color,
        "lineweight": lw, "linetype": lt
    })
    pl.closed = closed

def _txt(msp, txt, x, y, h, layer, color=256):
    msp.add_text(str(txt), dxfattribs={
        "insert": (x,y), "height": h,
        "layer": layer, "color": color
    })

def _length(pts):
    return sum(math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1])
               for i in range(len(pts)-1))


# ── Entry point ────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python post_processor.py input.dxf scale_ratio output.dxf")
        print("Example: python post_processor.py FMB_405_imported.dxf 1079 FMB_405_final.dxf")
        sys.exit(1)
    process(sys.argv[1], float(sys.argv[2]), sys.argv[3]) 