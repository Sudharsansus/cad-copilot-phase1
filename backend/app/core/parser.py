# parser.py - DWG File Parser
import ezdxf
from typing import List, Dict, Any
from app.utils.helpers import log_info, log_error

class DWGParser:
    def __init__(self):
        self.boundaries = []
        self.corridors = []
        self.dimensions = []
        self.labels = []
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse DWG file and extract geometry"""
        try:
            log_info(f"Parsing DWG file: {file_path}")
            dwg = ezdxf.readfile(file_path)
            msp = dwg.modelspace()
            
            # Extract entities by type
            for entity in msp:
                if entity.dxftype() == 'LWPOLYLINE':
                    self._extract_polyline(entity)
                elif entity.dxftype() == 'CIRCLE':
                    self._extract_circle(entity)
                elif entity.dxftype() == 'LINE':
                    self._extract_line(entity)
                elif entity.dxftype() == 'TEXT':
                    self._extract_text(entity)
                elif entity.dxftype() == 'DIMENSION':
                    self._extract_dimension(entity)
            
            result = {
                "status": "success",
                "boundaries": self.boundaries,
                "corridors": self.corridors,
                "dimensions": self.dimensions,
                "labels": self.labels
            }
            log_info(f"Parsed: {len(self.boundaries)} boundaries, {len(self.corridors)} corridors")
            return result
        
        except Exception as e:
            log_error("DWG parsing failed", e)
            return {"status": "error", "message": str(e)}
    
    def _extract_polyline(self, entity):
        """Extract LWPOLYLINE as boundary"""
        points = [(pt[0], pt[1]) for pt in entity.get_points()]
        if len(points) >= 3:
            self.boundaries.append({
                "type": "polygon",
                "points": points,
                "layer": entity.dxf.layer
            })
    
    def _extract_circle(self, entity):
        """Extract CIRCLE"""
        self.corridors.append({
            "type": "circle",
            "center": (entity.dxf.center[0], entity.dxf.center[1]),
            "radius": entity.dxf.radius,
            "layer": entity.dxf.layer
        })
    
    def _extract_line(self, entity):
        """Extract LINE"""
        start = (entity.dxf.start[0], entity.dxf.start[1])
        end = (entity.dxf.end[0], entity.dxf.end[1])
        self.corridors.append({
            "type": "line",
            "start": start,
            "end": end,
            "layer": entity.dxf.layer
        })
    
    def _extract_text(self, entity):
        """Extract TEXT labels"""
        self.labels.append({
            "text": entity.dxf.text,
            "position": (entity.dxf.insert[0], entity.dxf.insert[1]),
            "layer": entity.dxf.layer
        })
    
    def _extract_dimension(self, entity):
        """Extract DIMENSION"""
        self.dimensions.append({
            "type": "dimension",
            "dxf_entity": entity.dxf,
            "layer": entity.dxf.layer
        })

def parse_dwg_file(file_path: str) -> Dict[str, Any]:
    """Main function to parse DWG"""
    parser = DWGParser()
    return parser.parse_file(file_path)
