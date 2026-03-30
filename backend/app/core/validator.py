# validator.py - Geometry Validation
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from typing import List, Dict, Any
from app.config import MIN_AREA, MAX_AREA, MIN_SPACING
from app.utils.helpers import log_info

class Validator:
    def validate_geometry(self, geometries: List[Dict], boundary: Dict = None) -> Dict[str, Any]:
        """Validate all geometries"""
        issues = []
        
        # Check overlaps
        overlap_issues = self._check_overlaps(geometries)
        issues.extend(overlap_issues)
        
        # Check spacing
        spacing_issues = self._check_spacing(geometries)
        issues.extend(spacing_issues)
        
        # Check areas
        area_issues = self._check_areas(geometries)
        issues.extend(area_issues)
        
        # Check boundary
        if boundary:
            boundary_issues = self._check_boundary(geometries, boundary)
            issues.extend(boundary_issues)
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "issue_count": len(issues)
        }
    
    def _check_overlaps(self, geometries: List[Dict]) -> List[Dict]:
        """Check for overlapping geometries"""
        issues = []
        polygons = []
        
        for i, geom in enumerate(geometries):
            coords = geom.get("points", [])
            if len(coords) >= 3:
                try:
                    polygons.append((i, Polygon(coords)))
                except:
                    pass
        
        for i in range(len(polygons)):
            for j in range(i + 1, len(polygons)):
                idx1, poly1 = polygons[i]
                idx2, poly2 = polygons[j]
                
                if poly1.intersects(poly2):
                    intersection = poly1.intersection(poly2)
                    if intersection.area > 0.01:
                        issues.append({
                            "type": "overlap",
                            "geometry1": idx1,
                            "geometry2": idx2,
                            "area": intersection.area
                        })
        
        return issues
    
    def _check_spacing(self, geometries: List[Dict]) -> List[Dict]:
        """Check minimum spacing between geometries"""
        issues = []
        
        for i in range(len(geometries)):
            for j in range(i + 1, len(geometries)):
                geom1 = geometries[i]
                geom2 = geometries[j]
                
                coords1 = geom1.get("points", [])
                coords2 = geom2.get("points", [])
                
                if len(coords1) >= 3 and len(coords2) >= 3:
                    try:
                        poly1 = Polygon(coords1)
                        poly2 = Polygon(coords2)
                        distance = poly1.distance(poly2)
                        
                        if distance < MIN_SPACING:
                            issues.append({
                                "type": "spacing",
                                "geometry1": i,
                                "geometry2": j,
                                "distance": distance,
                                "minimum": MIN_SPACING
                            })
                    except:
                        pass
        
        return issues
    
    def _check_areas(self, geometries: List[Dict]) -> List[Dict]:
        """Check area constraints"""
        issues = []
        
        for i, geom in enumerate(geometries):
            coords = geom.get("points", [])
            if len(coords) >= 3:
                try:
                    polygon = Polygon(coords)
                    area = polygon.area
                    
                    if area < MIN_AREA:
                        issues.append({
                            "type": "area_too_small",
                            "geometry": i,
                            "area": area,
                            "minimum": MIN_AREA
                        })
                    elif area > MAX_AREA:
                        issues.append({
                            "type": "area_too_large",
                            "geometry": i,
                            "area": area,
                            "maximum": MAX_AREA
                        })
                except:
                    pass
        
        return issues
    
    def _check_boundary(self, geometries: List[Dict], boundary: Dict) -> List[Dict]:
        """Check if geometries are within boundary"""
        issues = []
        
        boundary_coords = boundary.get("points", [])
        if len(boundary_coords) < 3:
            return issues
        
        try:
            boundary_poly = Polygon(boundary_coords)
            
            for i, geom in enumerate(geometries):
                coords = geom.get("points", [])
                if len(coords) >= 3:
                    try:
                        geom_poly = Polygon(coords)
                        
                        if not boundary_poly.contains(geom_poly):
                            issues.append({
                                "type": "outside_boundary",
                                "geometry": i
                            })
                    except:
                        pass
        except:
            pass
        
        return issues

def validate_geometries(geometries: List[Dict], boundary: Dict = None) -> Dict:
    """Main validation function"""
    validator = Validator()
    result = validator.validate_geometry(geometries, boundary)
    log_info(f"Validation: {result['issue_count']} issues found")
    return result
