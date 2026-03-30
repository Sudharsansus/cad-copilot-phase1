# helpers.py - Utility Functions
import logging
import json
import uuid
from datetime import datetime
from typing import Any, Dict

# Logging setup
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# File utilities
def generate_file_id() -> str:
    """Generate unique file ID"""
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """Get current timestamp"""
    return datetime.utcnow().isoformat()

# JSON utilities
def safe_json_dumps(data: Any) -> str:
    """Safely convert to JSON"""
    try:
        return json.dumps(data, default=str)
    except Exception as e:
        logger.error(f"JSON dump error: {e}")
        return "{}"

def safe_json_loads(data: str) -> Dict:
    """Safely parse JSON"""
    try:
        return json.loads(data)
    except Exception as e:
        logger.error(f"JSON load error: {e}")
        return {}

# Validation
def is_valid_file_id(file_id: str) -> bool:
    """Check if file ID is valid UUID"""
    try:
        uuid.UUID(file_id)
        return True
    except ValueError:
        return False

# Distance/Area calculations
def calculate_distance(p1: tuple, p2: tuple) -> float:
    """Calculate distance between two points"""
    return ((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)**0.5

def calculate_polygon_area(coords: List[tuple]) -> float:
    """Calculate polygon area using Shoelace formula"""
    if len(coords) < 3:
        return 0.0
    area = 0.0
    for i in range(len(coords)):
        j = (i + 1) % len(coords)
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    return abs(area) / 2.0

# Logging helpers
def log_info(message: str):
    logger.info(message)

def log_error(message: str, error: Exception = None):
    if error:
        logger.error(f"{message}: {str(error)}")
    else:
        logger.error(message)

def log_warning(message: str):
    logger.warning(message)
