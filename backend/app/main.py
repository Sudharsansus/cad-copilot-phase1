# main.py - FastAPI Server
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import os
import uuid
from app.config import UPLOAD_DIR, API_HOST, API_PORT, API_KEY
from app.core.parser import parse_dwg_file
from app.core.command_handler import parse_command
from app.core.geometry import execute_geometry_operation
from app.utils.helpers import log_info, log_error, generate_file_id

app = FastAPI(
    title="CAD AI Copilot",
    description="AI-powered DWG file parser and LPS drawing automation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== HELPERS ==========
def find_cad_file(file_id: str) -> str:
    """Find uploaded CAD file by ID — checks .dxf first, then .dwg"""
    for ext in (".dxf", ".dwg"):
        path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
        if os.path.exists(path):
            return path
    return None

# ========== HEALTH ==========
@app.get("/health")
async def health():
    return {"status": "ok", "service": "CAD AI Copilot", "version": "1.0.0"}


# ========== UPLOAD DWG / DXF ==========
@app.post("/upload")
async def upload_dwg(file: UploadFile = File(...)):
    try:
        lower = file.filename.lower()
        if not (lower.endswith('.dwg') or lower.endswith('.dxf')):
            raise HTTPException(status_code=400, detail="File must be .dwg or .dxf")

        file_id  = generate_file_id()
        ext      = ".dxf" if lower.endswith('.dxf') else ".dwg"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        log_info(f"CAD file uploaded: {file_id}{ext}")
        return {"status": "success", "file_id": file_id, "filename": file.filename}

    except HTTPException:
        raise
    except Exception as e:
        log_error("Upload failed", e)
        raise HTTPException(status_code=500, detail=str(e))


# ========== UPLOAD EXCEL ==========
@app.post("/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="File must be .xlsx or .xls")

        excel_id  = generate_file_id()
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, f"{excel_id}.xlsx")

        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        log_info(f"Excel uploaded: {excel_id}")
        return {"status": "success", "excel_id": excel_id, "filename": file.filename}

    except HTTPException:
        raise
    except Exception as e:
        log_error("Excel upload failed", e)
        raise HTTPException(status_code=500, detail=str(e))


# ========== PARSE ==========
@app.post("/parse")
async def parse_file(file_id: str):
    try:
        file_path = find_cad_file(file_id)
        if not file_path:
            raise HTTPException(status_code=404, detail="File not found")

        result = parse_dwg_file(file_path)
        log_info(f"File parsed: {file_id}")
        return {"status": "success", "file_id": file_id, "result": result}

    except HTTPException:
        raise
    except Exception as e:
        log_error("Parse failed", e)
        raise HTTPException(status_code=500, detail=str(e))


# ========== AUTO DRAW LPS ==========
@app.post("/auto-draw")
async def auto_draw(file_id: str, excel_id: str):
    try:
        from app.core.excel_parser import parse_excel_file
        from app.core.lps_drawer import draw_lps

        cad_path   = find_cad_file(file_id)
        excel_path = os.path.join(UPLOAD_DIR, f"{excel_id}.xlsx")

        if not cad_path:
            raise HTTPException(status_code=404, detail="CAD file not found. Please re-upload.")
        if not os.path.exists(excel_path):
            raise HTTPException(status_code=404, detail="Excel file not found. Please re-upload.")

        lps_data = parse_excel_file(excel_path)

        output_id   = generate_file_id()
        output_path = os.path.join(UPLOAD_DIR, f"{output_id}_output.dxf")
        draw_lps(cad_path, lps_data, output_path)

        log_info(f"LPS auto-draw complete: {output_id}")
        return {
            "status": "success",
            "output_id": output_id,
            "parcels_drawn": len(lps_data),
            "download_url": f"/download/{output_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        log_error("Auto-draw failed", e)
        raise HTTPException(status_code=500, detail=str(e))


# ========== COMMAND (COPILOT CHAT) ==========
@app.post("/command")
async def execute_command(file_id: str, command_text: str):
    try:
        parsed = parse_command(command_text, API_KEY)
        if not parsed:
            raise HTTPException(status_code=400, detail="Could not understand command")

        operation  = parsed.get("operation")
        parameters = parsed.get("parameters", {})
        result     = execute_geometry_operation(operation, **parameters)

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


# ========== DOWNLOAD OUTPUT ==========
@app.get("/download/{output_id}")
async def download_output(output_id: str):
    # Check for dxf output first, then dwg
    for ext in ("_output.dxf", "_output.dwg"):
        file_path = os.path.join(UPLOAD_DIR, f"{output_id}{ext}")
        if os.path.exists(file_path):
            fname = "lps_output.dxf" if ext.endswith(".dxf") else "lps_output.dwg"
            return FileResponse(file_path, filename=fname,
                                media_type="application/octet-stream")
    raise HTTPException(status_code=404, detail="Output file not found")


# ========== ERROR HANDLERS ==========
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code,
                        content={"status": "error", "detail": exc.detail})

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    log_error("Unhandled error", exc)
    return JSONResponse(status_code=500,
                        content={"status": "error", "detail": "Internal server error"})


# ========== RUN ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)