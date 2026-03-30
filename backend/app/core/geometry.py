# geometry.py - Geometry Operations
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from typing import List, Dict, Tuple, Any
from app.utils.helpers import log_info, log_error

class GeometryEngine:
    def __init__(self):
        self.polygons = []
        self.lines = []
    
    def buffer_operation(self, geometry: Dict, distance: float) -> Dict:
        """Expand geometry by distance"""
        try:
            coords = geometry.get("points", [])
            if len(coords) < 3:
                return {"error": "Invalid polygon"}
            
            polygon = Polygon(coords)
            buffered = polygon.buffer(distance)
            new_coords = list(buffered.exterior.coords)
            
            return {
                "type": "polygon",
                "points": new_coords,
                "original_area": polygon.area,
                "new_area": buffered.area
            }
        except Exception as e:
            log_error("Buffer operation failed", e)
            return {"error": str(e)}
    
    def shift_operation(self, geometry: Dict, direction: str, distance: float) -> Dict:
        """Move geometry in direction"""
        try:
            coords = geometry.get("points", [])
            if not coords:
                return {"error": "No coordinates"}
            
            dx, dy = self._get_direction_offset(direction, distance)
            new_coords = [(x + dx, y + dy) for x, y in coords]
            
            return {
                "type": "polygon",
                "points": new_coords,
                "shift": {"direction": direction, "distance": distance}
            }
        except Exception as e:
            log_error("Shift operation failed", e)
            return {"error": str(e)}
    
    def merge_operation(self, geometries: List[Dict]) -> Dict:
        """Merge multiple geometries"""
        try:
            if len(geometries) < 2:
                return {"error": "Need at least 2 geometries"}
            
            polygons = []
            for geom in geometries:
                coords = geom.get("points", [])
                if len(coords) >= 3:
                    polygons.append(Polygon(coords))
            
            merged = unary_union(polygons)
            coords = list(merged.exterior.coords)
            
            return {
                "type": "polygon",
                "points": coords,
                "merged_count": len(geometries),
                "area": merged.area
            }
        except Exception as e:
            log_error("Merge operation failed", e)
            return {"error": str(e)}
    
    def rotate_operation(self, geometry: Dict, angle: float) -> Dict:
        """Rotate geometry by angle (degrees)"""
        try:
            coords = geometry.get("points", [])
            if len(coords) < 3:
                return {"error": "Invalid polygon"}
            
            polygon = Polygon(coords)
            rotated = self._rotate_shapely(polygon, angle)
            new_coords = list(rotated.exterior.coords)
            
            return {
                "type": "polygon",
                "points": new_coords,
                "angle": angle
            }
        except Exception as e:
            log_error("Rotate operation failed", e)
            return {"error": str(e)}
    
    def dimension_operation(self, point1: Tuple, point2: Tuple) -> Dict:
        """Add dimension between two points"""
        try:
            line = LineString([point1, point2])
            distance = line.length
            
            return {
                "type": "dimension",
                "point1": point1,
                "point2": point2,
                "distance": distance,
                "midpoint": (
                    (point1[0] + point2[0]) / 2,
                    (point1[1] + point2[1]) / 2
                )
            }
        except Exception as e:
            log_error("Dimension operation failed", e)
            return {"error": str(e)}
    
    def _get_direction_offset(self, direction: str, distance: float) -> Tuple[float, float]:
        """Get X, Y offset for direction"""
        direction = direction.lower()
        if direction == "north":
            return (0, distance)
        elif direction == "south":
            return (0, -distance)
        elif direction == "east":
            return (distance, 0)
        elif direction == "west":
            return (-distance, 0)
        else:
            return (0, 0)
    
    def _rotate_shapely(self, geom, angle: float):
        """Rotate Shapely geometry"""
        import math
        radian = math.radians(angle)
        cos_a, sin_a = math.cos(radian), math.sin(radian)
        
        def rotate_point(x, y):
            return (x * cos_a - y * sin_a, x * sin_a + y * cos_a)
        
        coords = geom.exterior.coords
        new_coords = [rotate_point(x, y) for x, y in coords]
        return Polygon(new_coords)

def execute_geometry_operation(operation: str, **kwargs) -> Dict:
    """Execute geometry operation"""
    engine = GeometryEngine()
    
    if operation == "buffer":
        return engine.buffer_operation(kwargs.get("geometry"), kwargs.get("distance", 0))
    elif operation == "shift":
        return engine.shift_operation(kwargs.get("geometry"), kwargs.get("direction"), kwargs.get("distance"))
    elif operation == "merge":
        return engine.merge_operation(kwargs.get("geometries", []))
    elif operation == "rotate":
        return engine.rotate_operation(kwargs.get("geometry"), kwargs.get("angle"))
    elif operation == "dimension":
        return engine.dimension_operation(kwargs.get("point1"), kwargs.get("point2"))
    else:
        return {"error": "Unknown operation"}
