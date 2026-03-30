# config.py - Configuration Settings
import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/cadcopilot")
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False") == "True"

# API
API_KEY = os.getenv("OPENAI_API_KEY", "")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# File handling
UPLOAD_DIR = "data/uploads"
EXPORT_DIR = "data/exports"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Geometry
MIN_AREA = 10.0
MAX_AREA = 100000.0
MIN_WIDTH = 2.0
MIN_SPACING = 0.5

# Create directories
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)
