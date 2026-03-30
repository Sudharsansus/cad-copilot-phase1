# exporter.py - Export Geometry to DXF/SVG
import ezdxf
from typing import List, Dict
from app.utils.helpers import log_info, log_error

class Exporter:
    def export_to_dxf(self, geometries: List[Dict], output_path: str) -> bool:
        """Export geometries to DXF file"""
        try:
            doc = ezdxf.new()
            msp = doc.modelspace()
            
            for geom in geometries:
                geom_type = geom.get("type", "unknown")
                
                if geom_type == "polygon":
                    points = geom.get("points", [])
                    if len(points) >= 3:
                        msp.add_lwpolyline(points)
                
                elif geom_type == "circle":
                    center = geom.get("center", (0, 0))
                    radius = geom.get("radius", 1.0)
                    msp.add_circle(center, radius)
                
                elif geom_type == "line":
                    start = geom.get("start", (0, 0))
                    end = geom.get("end", (0, 0))
                    msp.add_line(start, end)
                
                elif geom_type == "dimension":
                    p1 = geom.get("point1", (0, 0))
                    p2 = geom.get("point2", (0, 0))
                    msp.add_line(p1, p2)
            
            doc.saveas(output_path)
            log_info(f"Exported to DXF: {output_path}")
            return True
        
        except Exception as e:
            log_error("DXF export failed", e)
            return False
    
    def export_to_svg(self, geometries: List[Dict], output_path: str) -> bool:
        """Export geometries to SVG file"""
        try:
            svg_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
            svg_content += '<svg width="1000" height="1000" xmlns="http://www.w3.org/2000/svg">\n'
            
            for geom in geometries:
                geom_type = geom.get("type", "unknown")
                
                if geom_type == "polygon":
                    points = geom.get("points", [])
                    points_str = " ".join([f"{x},{y}" for x, y in points])
                    svg_content += f'<polygon points="{points_str}" fill="none" stroke="black"/>\n'
                
                elif geom_type == "circle":
                    center = geom.get("center", (0, 0))
                    radius = geom.get("radius", 1.0)
                    svg_content += f'<circle cx="{center[0]}" cy="{center[1]}" r="{radius}" fill="none" stroke="black"/>\n'
                
                elif geom_type == "line":
                    start = geom.get("start", (0, 0))
                    end = geom.get("end", (0, 0))
                    svg_content += f'<line x1="{start[0]}" y1="{start[1]}" x2="{end[0]}" y2="{end[1]}" stroke="black"/>\n'
            
            svg_content += '</svg>'
            
            with open(output_path, 'w') as f:
                f.write(svg_content)
            
            log_info(f"Exported to SVG: {output_path}")
            return True
        
        except Exception as e:
            log_error("SVG export failed", e)
            return False

def export_geometries(geometries: List[Dict], output_path: str, format_type: str = "dxf") -> bool:
    """Export geometries"""
    exporter = Exporter()
    
    if format_type == "dxf":
        return exporter.export_to_dxf(geometries, output_path)
    elif format_type == "svg":
        return exporter.export_to_svg(geometries, output_path)
    else:
        log_error(f"Unknown format: {format_type}")
        return False
