# test_parser.py - Parser Tests
import pytest
from app.core.parser import parse_dwg_file

def test_parse_valid_dwg():
    """Test parsing valid DWG file"""
    # This is a placeholder test
    result = parse_dwg_file("test_file.dwg")
    assert "status" in result

def test_parser_invalid_file():
    """Test parser with invalid file"""
    result = parse_dwg_file("nonexistent.dwg")
    assert "error" in result or "status" in result
