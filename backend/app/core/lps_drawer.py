# lps_drawer.py - LPS Info Box Drawer ON TOP of real survey DXF
import ezdxf
from ezdxf import colors
from typing import List, Dict, Any
from app.utils.helpers import log_info, log_error


def draw_lps(dwg_path: str, parcels: List[Dict], output_path: str):
    """Add LPS info boxes and labels ON TOP of existing real survey DXF"""
    try:
        log_info(f"Drawing LPS info boxes for {len(parcels)} parcels")
        doc = ezdxf.readfile(dwg_path)
        msp = doc.modelspace()

        _setup_layers(doc)

        # Get drawing bounds and SF number positions from existing DXF
        bounds      = _get_drawing_bounds(msp)
        sf_positions = _find_sf_positions(msp)

        log_info(f"Drawing bounds: {bounds}")
        log_info(f"Found {len(sf_positions)} SF positions in DXF")

        # Place info boxes — use real SF positions if found, else grid layout
        info_box_w = (bounds["max_x"] - bounds["min_x"]) * 0.06
        info_box_h = info_box_w * 0.5
        text_h     = info_box_h * 0.09

        for i, parcel in enumerate(parcels):
            sf = parcel.get("sf_no", "")

            # Try to find real position from DXF
            pos = _find_parcel_position(sf, sf_positions, bounds)

            if pos:
                # Place info box below/near real parcel location
                box_x = pos[0] - info_box_w / 2
                box_y = pos[1] - info_box_h * 3
            else:
                # Fallback: grid below drawing
                cols  = 3
                col   = i % cols
                row   = i // cols
                gap_x = (bounds["max_x"] - bounds["min_x"]) / cols
                box_x = bounds["min_x"] + col * gap_x
                box_y = bounds["min_y"] - (row + 1) * (info_box_h + info_box_h * 0.3) - info_box_h

            _draw_info_box(msp, box_x, box_y, info_box_w, info_box_h, text_h, parcel)

            # Tower marker on real position
            if pos and parcel.get("tower_no") and parcel["tower_no"] != "-":
                r = info_box_w * 0.06
                msp.add_circle(
                    (pos[0], pos[1]), radius=r,
                    dxfattribs={"layer": "LPS_TOWER"}
                )
                _add_text(msp, parcel["tower_no"],
                          pos[0] + r * 1.2, pos[1], text_h * 1.2, "LPS_TOWER")

        doc.saveas(output_path)
        log_info(f"LPS drawing saved: {output_path}")

    except Exception as e:
        log_error("LPS drawing failed", e)
        raise


def _setup_layers(doc):
    layers = [
        ("LPS_TEXT",    colors.YELLOW),
        ("LPS_INFOBOX", colors.CYAN),
        ("LPS_TOWER",   colors.GREEN),
    ]
    for name, color in layers:
        if name not in doc.layers:
            doc.layers.add(name, color=color)


def _get_drawing_bounds(msp) -> Dict:
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    for e in msp:
        try:
            if e.dxftype() == 'LWPOLYLINE':
                for pt in e.get_points():
                    min_x = min(min_x, pt[0]); max_x = max(max_x, pt[0])
                    min_y = min(min_y, pt[1]); max_y = max(max_y, pt[1])
        except:
            continue
    if min_x == float('inf'):
        return {"min_x": 0, "min_y": 0, "max_x": 1000, "max_y": 1000}
    return {"min_x": min_x, "min_y": min_y, "max_x": max_x, "max_y": max_y}


def _find_sf_positions(msp) -> Dict[str, tuple]:
    """Find X,Y positions of SF numbers from SURVEY NUMBER and SUB DIVISION NUMBER layers"""
    import re
    positions = {}
    survey_layers = {"SURVEY NUMBER", "SUB DIVISION NUMBER", "SUB DIVISION"}

    for e in msp:
        if e.dxftype() != 'TEXT':
            continue
        if e.dxf.layer not in survey_layers:
            continue
        text = e.dxf.text.strip()
        pos  = e.dxf.insert

        # Match SF number patterns: 403, 611, 612, 2B, 1E, 3A2 etc
        if re.match(r'^\d+(/\w+)?$', text) or re.match(r'^\d+[A-Z]\d*[A-Z]?\d*$', text):
            if text not in positions:
                positions[text] = (pos[0], pos[1])

    return positions


def _find_parcel_position(sf_no: str, sf_positions: Dict, bounds: Dict):
    """Find position for a parcel SF number in the DXF"""
    # Try exact match first
    if sf_no in sf_positions:
        return sf_positions[sf_no]

    # Try just the number part (e.g. "403/2B" → "403" or "2B")
    parts = sf_no.replace("/", " ").split()
    for part in parts:
        if part in sf_positions:
            return sf_positions[part]

    return None


def _draw_info_box(msp, x: float, y: float, w: float, h: float,
                   text_h: float, parcel: Dict):
    """Draw info box with parcel details"""
    # Box outline
    pts = [(x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y)]
    msp.add_lwpolyline(pts, dxfattribs={"layer": "LPS_INFOBOX", "lineweight": 18})

    # Content lines
    pad    = w * 0.03
    line_h = h / 7
    sf     = parcel.get("sf_no", "")
    lines  = [
        f"DISTRICT : {parcel.get('district', 'Vellore')}",
        f"TALUK    : {parcel.get('taluk', '')}",
        f"VILLAGE  : {parcel.get('village', '')}",
        f"S.F.No   : {sf}   LOC: {parcel.get('loc_from','')}-{parcel.get('loc_to','')}",
        f"OWNER    : {parcel.get('owner', '')[:35]}",
        f"TWR AREA : {parcel.get('tower_area_sqm', 0):.3f} Sqm  {parcel.get('tower_area_cent', 0):.3f} Cent",
        f"CORRIDOR : {parcel.get('corridor_sqm', 0):.3f} Sqm  {parcel.get('corridor_cent', 0):.3f} Cent",
    ]

    for i, line in enumerate(lines):
        ty = y + h - (i + 1) * line_h + line_h * 0.2
        _add_text(msp, line, x + pad, ty, text_h, "LPS_INFOBOX")

    # SF number as large label above box
    _add_text(msp, f"SF No. {sf}", x + w * 0.1, y + h + text_h * 0.5,
              text_h * 2, "LPS_TEXT")

    # N/S/E/W boundary labels around box
    bounds_data = parcel.get("boundaries", {})
    cx = x + w / 2
    cy = y + h / 2
    off = text_h * 1.5
    if bounds_data.get("N"):
        _add_text(msp, bounds_data["N"], cx, y + h + off, text_h, "LPS_TEXT")
    if bounds_data.get("S"):
        _add_text(msp, bounds_data["S"], cx, y - off, text_h, "LPS_TEXT")
    if bounds_data.get("E"):
        _add_text(msp, bounds_data["E"], x + w + off, cy, text_h, "LPS_TEXT")
    if bounds_data.get("W"):
        _add_text(msp, bounds_data["W"], x - off * 3, cy, text_h, "LPS_TEXT")


def _add_text(msp, text: str, x: float, y: float, height: float, layer: str):
    msp.add_text(
        str(text),
        dxfattribs={"insert": (x, y), "height": height, "layer": layer}
    )