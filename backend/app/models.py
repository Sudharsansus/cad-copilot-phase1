# models.py - Pydantic Models
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Request Models
class UploadRequest(BaseModel):
    filename: str

class ParseRequest(BaseModel):
    file_id: str

class CommandRequest(BaseModel):
    file_id: str
    command: str

class ExportRequest(BaseModel):
    file_id: str
    format: str = "dxf"

# Response Models
class GeometryData(BaseModel):
    id: str
    type: str
    coordinates: List[tuple]
    layer: str

class OperationResult(BaseModel):
    success: bool
    geometries: List[GeometryData]
    message: str

class CommandResponse(BaseModel):
    status: str
    operation: str
    parameters: Dict[str, Any]
    result: List[GeometryData]

class ProjectResponse(BaseModel):
    file_id: str
    geometries: List[GeometryData]
    created_at: datetime
    updated_at: datetime

class ErrorResponse(BaseModel):
    status: str = "error"
    detail: str
    code: int
