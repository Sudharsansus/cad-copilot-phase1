# excel_parser.py - LPS Book Excel Parser
import openpyxl
from typing import List, Dict, Any
from app.utils.helpers import log_info, log_error


def parse_excel_file(file_path: str) -> List[Dict[str, Any]]:
    """Parse LPS Book Excel and extract parcel data"""
    try:
        log_info(f"Parsing Excel: {file_path}")
        wb = openpyxl.load_workbook(file_path, data_only=True)

        parcels = []

        # Try OVERALL sheet first — summary of all SF numbers
        if "OVERALL" in wb.sheetnames:
            parcels = _parse_overall_sheet(wb["OVERALL"])

        # Enrich with LPS sheet boundary data
        if "LPS" in wb.sheetnames:
            _enrich_with_lps_data(wb["LPS"], parcels)

        log_info(f"Parsed {len(parcels)} parcels from Excel")
        return parcels

    except Exception as e:
        log_error("Excel parsing failed", e)
        return []


def _parse_overall_sheet(sheet) -> List[Dict[str, Any]]:
    """Extract parcel list from OVERALL summary sheet"""
    parcels = []
    project_name = ""

    for row in sheet.iter_rows(values_only=True):
        # Grab project name from first row
        if row[0] and isinstance(row[0], str) and "KV" in str(row[0]):
            project_name = str(row[0]).strip()

        # Data rows: S.No | SF No | Tower No | Tower Area sq.m | Cent | Corridor sq.m | Cent | Owner | Rate | Amount | Pg
        if row[1] and isinstance(row[1], str) and "/" in str(row[1]):
            sf_no = str(row[1]).strip()
            tower_no = str(row[2]).strip() if row[2] else "-"
            tower_area_sqm = _safe_float(row[3])
            tower_area_cent = _safe_float(row[4])
            corridor_sqm = _safe_float(row[5])
            corridor_cent = _safe_float(row[6])
            owner = str(row[7]).strip() if row[7] else "Unknown"

            parcels.append({
                "sf_no": sf_no,
                "tower_no": tower_no,
                "tower_area_sqm": tower_area_sqm,
                "tower_area_cent": tower_area_cent,
                "corridor_sqm": corridor_sqm,
                "corridor_cent": corridor_cent,
                "owner": owner,
                "project": project_name,
                "district": "",
                "taluk": "",
                "village": "",
                "loc_from": "",
                "loc_to": "",
                "boundaries": {"N": "", "S": "", "E": "", "W": ""}
            })

    return parcels


def _enrich_with_lps_data(sheet, parcels: List[Dict]):
    """Extract district/taluk/village/LOC/boundary info from LPS sheet"""
    try:
        all_rows = list(sheet.iter_rows(values_only=True))
        current_block = {}

        for i, row in enumerate(all_rows):
            row_text = " ".join(str(c) for c in row if c)

            # District
            if "District" in row_text and ":" in row_text:
                current_block["district"] = _extract_after_colon(row_text)

            # Taluk
            if "Taluk" in row_text and ":" in row_text and "District" not in row_text:
                current_block["taluk"] = _extract_after_colon(row_text)

            # Village
            if "Village" in row_text and ":" in row_text:
                current_block["village"] = _extract_after_colon(row_text)

            # Survey Number (SF No)
            if "Survey Number" in row_text and ":" in row_text:
                current_block["sf_no"] = _extract_after_colon(row_text)

            # LOC from-to
            if "LOC" in row_text:
                locs = _extract_locs(row_text)
                if locs:
                    current_block["loc_from"] = locs[0]
                    current_block["loc_to"] = locs[1] if len(locs) > 1 else locs[0]

            # Boundaries
            if "Boundaries" in row_text or "Boundary" in row_text:
                current_block["boundaries"] = _extract_boundaries(all_rows, i)

            # Match to parcel and update
            if "sf_no" in current_block:
                for parcel in parcels:
                    if parcel["sf_no"] == current_block.get("sf_no", "").replace("SF No. ", "").strip():
                        parcel.update({k: v for k, v in current_block.items() if k != "sf_no"})
                        break

    except Exception as e:
        log_error("LPS enrichment failed", e)


def _extract_after_colon(text: str) -> str:
    """Extract value after colon in text"""
    parts = text.split(":")
    if len(parts) > 1:
        return parts[-1].strip().replace("None", "").strip()
    return ""


def _extract_locs(text: str) -> List[str]:
    """Extract LOC numbers from text like 'LOC 6 - LOC 7'"""
    import re
    matches = re.findall(r'LOC\s*(\d+)', text)
    return matches


def _extract_boundaries(rows: list, start_idx: int) -> Dict[str, str]:
    """Extract N/S/E/W boundaries from nearby rows"""
    bounds = {"N": "", "S": "", "E": "", "W": ""}
    directions = {"N -": "N", "S -": "S", "E -": "E", "W -": "W"}

    for row in rows[start_idx:start_idx + 10]:
        row_text = " ".join(str(c) for c in row if c)
        for key, direction in directions.items():
            if key in row_text:
                val = row_text.split(key)[-1].strip().split()[0] if key in row_text else ""
                bounds[direction] = val

    return bounds


def _safe_float(val) -> float:
    try:
        return float(val) if val else 0.0
    except:
        return 0.0