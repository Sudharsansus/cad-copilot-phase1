# main.py - FastAPI Server
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import uuid
from app.config import UPLOAD_DIR, API_HOST, API_PORT
from app.core.parser import parse_dwg_file
from app.core.command_handler import parse_command
from app.core.geometry import execute_geometry_operation
from app.core.validator import validate_geometries
from app.core.database import db
from app.utils.helpers import log_info, log_error, generate_file_id
import openai
from app.config import API_KEY

# FastAPI app
app = FastAPI(
    title="CAD AI Copilot",
    description="AI-powered DWG file parser",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI config
openai.api_key = API_KEY

# ========== HEALTH ==========
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "CAD AI Copilot",
        "version": "1.0.0"
    }

# ========== UPLOAD ==========
@app.post("/upload")
async def upload_dwg(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.dwg'):
            raise HTTPException(status_code=400, detail="File must be .dwg")
        
        file_id = generate_file_id()
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.dwg")
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        db.save_project(file_id, file.filename)
        log_info(f"File uploaded: {file_id}")
        
        return {
            "status": "success",
            "file_id": file_id,
            "filename": file.filename
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error("Upload failed", e)
        raise HTTPException(status_code=500, detail=str(e))

# ========== PARSE ==========
@app.post("/parse")
async def parse_file(file_id: str):
    try:
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.dwg")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        result = parse_dwg_file(file_path)
        
        # Save geometries
        geometries = result.get("boundaries", []) + result.get("corridors", [])
        for i, geom in enumerate(geometries):
            geom_id = str(uuid.uuid4())
            db.save_geometry(geom_id, file_id, geom.get("type", "unknown"), geom, geom.get("layer", "0"))
        
        log_info(f"File parsed: {file_id}")
        
        return {
            "status": "success",
            "file_id": file_id,
            "geometries": geometries
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error("Parse failed", e)
        raise HTTPException(status_code=500, detail=str(e))

# ========== COMMAND ==========
@app.post("/command")
async def execute_command(file_id: str, command_text: str):
    try:
        # Parse command
        parsed = parse_command(command_text, API_KEY)
        
        if not parsed:
            raise HTTPException(status_code=400, detail="Invalid command")
        
        operation = parsed.get("operation")
        parameters = parsed.get("parameters", {})
        
        # Execute geometry operation
        result = execute_geometry_operation(operation, **parameters)
        
        # Save command
        cmd_id = str(uuid.uuid4())
        db.save_command(cmd_id, file_id, command_text, operation, parameters, True)
        
        log_info(f"Command executed: {operation}")
        
        return {
            "status": "success",
            "operation": operation,
            "parameters": parameters,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error("Command execution failed", e)
        raise HTTPException(status_code=500, detail=str(e))

# ========== VALIDATE ==========
@app.post("/validate")
async def validate_file(file_id: str):
    try:
        geometries = db.get_geometries(file_id)
        
        if not geometries:
            raise HTTPException(status_code=404, detail="Geometries not found")
        
        result = validate_geometries(geometries)
        
        # Save validation log
        log_id = str(uuid.uuid4())
        db.save_validation_log(log_id, file_id, "general", result["valid"], str(result["issues"]))
        
        return {
            "status": "success",
            "valid": result["valid"],
            "issues": result["issues"],
            "issue_count": result["issue_count"]
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error("Validation failed", e)
        raise HTTPException(status_code=500, detail=str(e))

# ========== GET PROJECT ==========
@app.get("/project/{file_id}")
async def get_project(file_id: str):
    try:
        geometries = db.get_geometries(file_id)
        
        return {
            "status": "success",
            "file_id": file_id,
            "geometries": geometries
        }
    except Exception as e:
        log_error("Get project failed", e)
        raise HTTPException(status_code=500, detail=str(e))

# ========== ERROR HANDLERS ==========
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    log_error("Unhandled error", exc)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": "Internal server error"}
    )

# ========== RUN ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
