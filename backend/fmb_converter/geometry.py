"""
geometry.py
Responsible for: Converting PDF coordinates to real-world DXF coordinates
No geometric reconstruction — direct scaling from PDF vectors
"""
import math


def pdf_to_meters(px: float, py: float, page_info: dict) -> tuple:
    """Convert PDF pixel coordinates to real-world meters"""
    pt_m = page_info["pt_to_m"]
    ph   = page_info["height"]
    return px * pt_m, (ph - py) * pt_m


def line_to_meters(line: dict, page_info: dict) -> tuple:
    """Convert a line dict to (x1,y1,x2,y2) in meters"""
    x1, y1 = pdf_to_meters(line["px1"], line["py1"], page_info)
    x2, y2 = pdf_to_meters(line["px2"], line["py2"], page_info)
    return x1, y1, x2, y2


def build_boundary_polygon(boundary_lines: list, page_info: dict) -> list:
    """
    Chain boundary line segments into an ordered polygon.
    Uses greedy nearest-neighbor walk from topmost point.
    Returns list of (x,y) vertices in meters.
    """
    if not boundary_lines:
        return []

    segments = [
        {"p1": (l["px1"], l["py1"]), "p2": (l["px2"], l["py2"])}
        for l in boundary_lines
    ]

    polygon_px = _chain_segments(segments)
    return [pdf_to_meters(px, py, page_info) for px, py in polygon_px]


def _chain_segments(segments: list, tol: float = 10.0) -> list:
    """
    Walk through segments connecting endpoint to nearest endpoint.
    Returns ordered list of (px,py) pixel coordinates.
    """
    remaining = list(segments)

    # Start from topmost-leftmost point
    all_pts = []
    for s in remaining:
        all_pts.extend([s["p1"], s["p2"]])
    start = min(all_pts, key=lambda p: (p[1], p[0]))

    path = [start]
    curr = start

    while remaining:
        best_i, best_nxt, best_d = -1, None, tol

        for i, s in enumerate(remaining):
            d1 = math.hypot(curr[0]-s["p1"][0], curr[1]-s["p1"][1])
            d2 = math.hypot(curr[0]-s["p2"][0], curr[1]-s["p2"][1])
            if d1 < best_d:
                best_d, best_i, best_nxt = d1, i, s["p2"]
            if d2 < best_d:
                best_d, best_i, best_nxt = d2, i, s["p1"]

        if best_i == -1:
            break

        remaining.pop(best_i)

        # Check if closing the polygon
        dist_to_start = math.hypot(
            best_nxt[0]-path[0][0], best_nxt[1]-path[0][1]
        )
        if dist_to_start < tol and len(path) > 3:
            break

        path.append(best_nxt)
        curr = best_nxt

    return path


def get_lines_in_meters(lines: list, page_info: dict) -> list:
    """Convert a list of line dicts to (x1,y1,x2,y2) meter tuples"""
    return [line_to_meters(l, page_info) for l in lines]