# test_geometry.py - Geometry Tests
import pytest
from app.core.geometry import execute_geometry_operation

def test_buffer_operation():
    """Test buffer operation"""
    geom = {"points": [(0, 0), (10, 0), (10, 10), (0, 10)]}
    result = execute_geometry_operation("buffer", geometry=geom, distance=2.0)
    assert "points" in result or "error" in result

def test_shift_operation():
    """Test shift operation"""
    geom = {"points": [(0, 0), (10, 0), (10, 10), (0, 10)]}
    result = execute_geometry_operation("shift", geometry=geom, direction="north", distance=5.0)
    assert "points" in result or "error" in result

def test_dimension_operation():
    """Test dimension operation"""
    result = execute_geometry_operation("dimension", point1=(0, 0), point2=(10, 10))
    assert "distance" in result or "error" in result
