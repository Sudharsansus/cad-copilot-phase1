# CAD AI Copilot - Phase 1

DWG-Aware Self-Learning AI CAD Copilot for transmission line and land parcel layout work.

## Phase 1 Features

- Upload DWG files
- AI automatically analyzes and draws geometry
- Chat interface for commands
- Geometry operations (buffer, shift, merge, rotate)
- Validation and error checking
- Export to DXF/SVG

## Architecture

- Backend: Python FastAPI
- Plugin: C# .NET (AutoCAD)
- Database: PostgreSQL
- AI: OpenAI GPT-4

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
python -m uvicorn app.main:app --reload
```

### Database

```bash
docker-compose up postgres
```

### Plugin

- Compile with Visual Studio
- Install in AutoCAD
- Run CADCopilotOpen command

## Files

### Backend
- `main.py` - FastAPI server
- `parser.py` - DWG parser
- `command_handler.py` - Chat command parser
- `geometry.py` - Geometry operations
- `validator.py` - Validation
- `database.py` - Database models
- `config.py` - Configuration
- `models.py` - Pydantic models
- `helpers.py` - Utilities

### Plugin
- `Main.cs` - Plugin initialization
- `ChatUI.cs` - Chat interface
- `AutoCADDrawing.cs` - Drawing operations
- `APIClient.cs` - API communication
- `Utilities.cs` - Helpers

## API Endpoints

- `GET /health` - Health check
- `POST /upload` - Upload DWG file
- `POST /parse` - Parse DWG file
- `POST /command` - Execute command
- `POST /validate` - Validate geometries
- `GET /project/{id}` - Get project data

## Development

Simple, clean code. No over-engineering.
~1,900 lines of code total.

## Status

✓ Phase 1 Complete
⏳ Phase 2: Learning + Automation (upcoming)
