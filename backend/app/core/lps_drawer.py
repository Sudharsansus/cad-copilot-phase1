# lps_drawer.py - LPS Corridor and Label Drawer
import ezdxf
from ezdxf import colors
from typing import List, Dict, Any
from app.utils.helpers import log_info, log_error


def draw_lps(dwg_path: str, parcels: List[Dict], output_path: str):
    """Draw LPS corridor and labels on DWG for all parcels"""
    try:
        log_info(f"Drawing LPS for {len(parcels)} parcels")
        doc = ezdxf.readfile(dwg_path)
        msp = doc.modelspace()

        _setup_layers(doc)
        bounds = _get_drawing_bounds(msp)

        for i, parcel in enumerate(parcels):
            _draw_parcel(msp, parcel, i, bounds)

        # Save in R2013 format — compatible with AutoCAD 2013 to 2024
        doc.saveas(output_path)
        log_info(f"LPS drawing saved: {output_path}")

    except Exception as e:
        log_error("LPS drawing failed", e)
        raise


def _setup_layers(doc):
    """Create LPS drawing layers"""
    layers = [
        ("LPS_CORRIDOR", colors.RED),
        ("LPS_BOUNDARY", colors.WHITE),
        ("LPS_TEXT", colors.YELLOW),
        ("LPS_INFOBOX", colors.CYAN),
        ("LPS_TOWER", colors.GREEN),
    ]
    for name, color in layers:
        if name not in doc.layers:
            doc.layers.add(name, color=color)


def _get_drawing_bounds(msp) -> Dict:
    """Get bounding box of existing drawing"""
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    for entity in msp:
        try:
            if entity.dxftype() == 'LWPOLYLINE':
                for pt in entity.get_points():
                    min_x = min(min_x, pt[0])
                    min_y = min(min_y, pt[1])
                    max_x = max(max_x, pt[0])
                    max_y = max(max_y, pt[1])
        except:
            continue

    if min_x == float('inf'):
        return {"min_x": 0, "min_y": 0, "max_x": 1000, "max_y": 1000}

    return {"min_x": min_x, "min_y": min_y, "max_x": max_x, "max_y": max_y}


def _draw_parcel(msp, parcel: Dict, index: int, bounds: Dict):
    """Draw one parcel — boundary + corridor + info box"""
    page_width = 400
    page_height = 300
    cols = 3
    col = index % cols
    row = index // cols

    origin_x = bounds["min_x"] + col * (page_width + 50)
    origin_y = bounds["max_y"] + 100 + row * (page_height + 50)

    _draw_boundary_box(msp, origin_x, origin_y, page_width, page_height, parcel)
    _draw_corridor(msp, origin_x, origin_y, page_width, page_height, parcel)

    if parcel.get("tower_no") and parcel["tower_no"] != "-":
        _draw_tower_marker(msp, origin_x + page_width / 2, origin_y + page_height / 2, parcel["tower_no"])

    _draw_info_box(msp, origin_x, origin_y, parcel)
    _add_text(msp, f"SF No. {parcel['sf_no']}", origin_x + page_width / 2, origin_y + page_height / 2 + 30, 12, "LPS_TEXT")
    _draw_neighbor_labels(msp, origin_x, origin_y, page_width, page_height, parcel)


def _draw_boundary_box(msp, x: float, y: float, w: float, h: float, parcel: Dict):
    """Draw outer parcel boundary"""
    points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    msp.add_lwpolyline(points, dxfattribs={"layer": "LPS_BOUNDARY", "lineweight": 30})


def _draw_corridor(msp, x: float, y: float, w: float, h: float, parcel: Dict):
    """Draw corridor strip diagonally across parcel"""
    corridor_width = _estimate_corridor_width(parcel.get("corridor_sqm", 0), w, h)
    half = corridor_width / 2
    center_y = y + h / 2

    msp.add_line(
        (x, center_y - half), (x + w, center_y + half),
        dxfattribs={"layer": "LPS_CORRIDOR", "lineweight": 25}
    )
    msp.add_line(
        (x, center_y + half), (x + w, center_y - half),
        dxfattribs={"layer": "LPS_CORRIDOR", "lineweight": 25}
    )

    _add_text(
        msp,
        f"{parcel.get('corridor_sqm', 0):.3f} Sq.m",
        x + w / 2, center_y - half - 10, 6, "LPS_TEXT"
    )


def _draw_tower_marker(msp, x: float, y: float, tower_no: str):
    """Draw tower position as circle with label"""
    msp.add_circle((x, y), radius=8, dxfattribs={"layer": "LPS_TOWER"})
    _add_text(msp, f"Tower {tower_no}", x + 10, y + 5, 7, "LPS_TOWER")


def _draw_info_box(msp, x: float, y: float, parcel: Dict):
    """Draw info box below parcel with all LPS details"""
    box_h = 80
    box_w = 200
    box_x = x
    box_y = y - box_h - 10

    pts = [(box_x, box_y), (box_x + box_w, box_y),
           (box_x + box_w, box_y + box_h), (box_x, box_y + box_h), (box_x, box_y)]
    msp.add_lwpolyline(pts, dxfattribs={"layer": "LPS_INFOBOX"})

    line_h = 12
    lines = [
        f"DISTRICT : {parcel.get('district', '')}",
        f"TALUK    : {parcel.get('taluk', '')}",
        f"VILLAGE  : {parcel.get('village', '')}",
        f"S.F.No   : {parcel.get('sf_no', '')}  LOC: {parcel.get('loc_from', '')}-{parcel.get('loc_to', '')}",
        f"TOWER AREA : {parcel.get('tower_area_sqm', 0):.3f} Sq.m  {parcel.get('tower_area_cent', 0):.3f} Cent",
        f"CORRIDOR   : {parcel.get('corridor_sqm', 0):.3f} Sq.m  {parcel.get('corridor_cent', 0):.3f} Cent",
    ]

    for i, line in enumerate(lines):
        _add_text(msp, line, box_x + 5, box_y + box_h - (i + 1) * line_h, 5, "LPS_INFOBOX")


def _draw_neighbor_labels(msp, x: float, y: float, w: float, h: float, parcel: Dict):
    """Draw N/S/E/W neighbor SF numbers around boundary"""
    bounds = parcel.get("boundaries", {})
    cx = x + w / 2
    cy = y + h / 2

    if bounds.get("N"):
        _add_text(msp, bounds["N"], cx, y + h + 5, 7, "LPS_TEXT")
    if bounds.get("S"):
        _add_text(msp, bounds["S"], cx, y - 15, 7, "LPS_TEXT")
    if bounds.get("E"):
        _add_text(msp, bounds["E"], x + w + 5, cy, 7, "LPS_TEXT")
    if bounds.get("W"):
        _add_text(msp, bounds["W"], x - 25, cy, 7, "LPS_TEXT")


def _add_text(msp, text: str, x: float, y: float, height: float, layer: str):
    """Add text entity to drawing"""
    msp.add_text(
        text,
        dxfattribs={
            "insert": (x, y),
            "height": height,
            "layer": layer,
        }
    )


def _estimate_corridor_width(corridor_sqm: float, parcel_w: float, parcel_h: float) -> float:
    """Estimate corridor strip width in drawing units from area"""
    if corridor_sqm <= 0:
        return 20.0
    ratio = min(corridor_sqm / 5000, 0.4)
    return max(15.0, ratio * parcel_h)