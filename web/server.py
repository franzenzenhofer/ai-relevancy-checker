"""FastAPI web server for AI Relevancy Checker.

Provides drag & drop file upload, per-session API keys, real-time progress via SSE.
"""
import asyncio
import json
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("web.server")

app = FastAPI(
    title="AI Relevancy Checker",
    description="Check your brand visibility in AI responses",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Max upload size: 50MB
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

# Upload TTL: 1 hour
_UPLOAD_TTL_SECONDS = 3600

# SSE max duration: 2 hours (at 0.5s intervals = 14400 iterations)
_SSE_MAX_ITERATIONS = 14400


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main frontend."""
    index_path = STATIC_DIR / "index.html"
    return index_path.read_text(encoding="utf-8")


# In-memory upload storage with timestamps
_uploads: dict = {}
_upload_timestamps: dict = {}
_upload_lock = threading.Lock()


def _cleanup_stale_uploads() -> None:
    """Remove uploads older than TTL."""
    now = time.time()
    stale = [uid for uid, ts in _upload_timestamps.items()
             if now - ts > _UPLOAD_TTL_SECONDS]
    for uid in stale:
        _uploads.pop(uid, None)
        _upload_timestamps.pop(uid, None)


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV/XLSX file and detect columns."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(400, f"Unsupported file type: {suffix}. Use CSV, XLSX, or XLS.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, f"File too large ({len(content)} bytes). Max: {MAX_UPLOAD_BYTES // 1024 // 1024}MB")

    from core.spreadsheet_loader import load_spreadsheet
    import io

    try:
        result = load_spreadsheet(
            file_obj=io.BytesIO(content),
            filename=file.filename,
            max_queries=5000,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error("Upload processing failed: %s", e, exc_info=True)
        raise HTTPException(400, "Failed to process file. Ensure it's a valid CSV or Excel file.")

    # Store file content with timestamp for TTL cleanup
    import uuid
    upload_id = str(uuid.uuid4())[:8]
    with _upload_lock:
        _cleanup_stale_uploads()
        _uploads[upload_id] = {
            "content": content,
            "filename": file.filename,
            "records_count": len(result.records),
        }
        _upload_timestamps[upload_id] = time.time()

    # Return detection results + sample queries
    sample_queries = [r.query_text for r in result.records[:20]]

    return {
        "upload_id": upload_id,
        "filename": file.filename,
        "total_queries": result.total_rows,
        "sample_queries": sample_queries,
        "has_clicks": result.detected.clicks_col is not None,
        "has_impressions": result.detected.impressions_col is not None,
        "detected_sheet": result.detected.sheet_name,
        "confidence": round(result.detected.confidence, 2),
        "warnings": result.warnings,
    }


@app.post("/api/run")
async def start_run(
    upload_id: str = Form(...),
    domain: str = Form(...),
    brand_names: str = Form(...),
    openai_api_key: str = Form(""),
    gemini_api_key: str = Form(""),
    providers: str = Form("openai,gemini"),
    max_queries: int = Form(100),
    user_country: str = Form(""),
    user_city: str = Form(""),
    default_language: str = Form("en"),
):
    """Start a new evaluation run."""
    # Validate upload exists
    with _upload_lock:
        upload = _uploads.get(upload_id)
    if not upload:
        raise HTTPException(400, "Upload not found or expired. Please upload a file first.")

    # Validate inputs
    if not domain.strip():
        raise HTTPException(400, "Domain is required")
    brand_list = [b.strip() for b in brand_names.split(",") if b.strip()]
    if not brand_list:
        raise HTTPException(400, "At least one brand name is required")
    provider_list = [p.strip().lower() for p in providers.split(",") if p.strip()]
    if not provider_list:
        raise HTTPException(400, "At least one provider is required")

    # Clamp max_queries to safe range
    max_queries = max(1, min(max_queries, 5000))

    # Need at least one valid API key
    if "openai" in provider_list and not openai_api_key.strip():
        raise HTTPException(400, "OpenAI API key required when OpenAI provider is selected")
    if "gemini" in provider_list and not gemini_api_key.strip():
        raise HTTPException(400, "Gemini API key required when Gemini provider is selected")

    # OpenAI key always needed for prompt generation
    if not openai_api_key.strip():
        raise HTTPException(400, "OpenAI API key is required for prompt generation (even if using Gemini only)")

    # Check if another run is already in progress (config lock would block)
    from web.run_manager import is_run_active
    if is_run_active():
        raise HTTPException(
            409,
            "Another evaluation is currently running. Please wait for it to finish before starting a new one.",
        )

    # Load records from stored upload
    import io
    from core.spreadsheet_loader import load_spreadsheet
    try:
        result = load_spreadsheet(
            file_obj=io.BytesIO(upload["content"]),
            filename=upload["filename"],
            max_queries=max_queries,
            default_url=f"https://www.{domain}/",
            default_country=user_country or "unknown",
        )
    except Exception as e:
        logger.error("Failed to reload spreadsheet: %s", e, exc_info=True)
        raise HTTPException(400, f"Failed to process uploaded file: {e}")

    # Create run
    from web.run_manager import WebRunConfig, create_run, execute_run, update_run
    web_config = WebRunConfig(
        domain=domain.strip(),
        brand_names=brand_list,
        openai_api_key=openai_api_key.strip(),
        gemini_api_key=gemini_api_key.strip(),
        providers=provider_list,
        max_queries=max_queries,
        user_city=user_city.strip(),
        user_city_en=user_city.strip(),
        user_country=user_country.strip(),
        user_country_en=user_country.strip(),
        default_language=default_language.strip() or "en",
    )

    run_id = create_run()
    update_run(
        run_id,
        total_queries=len(result.records),
        detected_columns={
            "query_col": result.detected.query_col,
            "clicks_col": result.detected.clicks_col,
            "sheet": result.detected.sheet_name,
        },
        warnings=result.warnings,
    )

    # Free upload memory now that records are loaded
    with _upload_lock:
        _uploads.pop(upload_id, None)
        _upload_timestamps.pop(upload_id, None)

    # Run in background thread
    def _bg():
        execute_run(run_id, result.records, web_config)

    thread = threading.Thread(target=_bg, daemon=True)
    thread.start()

    return {"run_id": run_id, "total_queries": len(result.records)}


@app.get("/api/status/{run_id}")
async def run_status(run_id: str):
    """Get current run status (poll endpoint)."""
    from web.run_manager import get_run
    run = get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return {
        "run_id": run.run_id,
        "status": run.status,
        "total_queries": run.total_queries,
        "completed_queries": run.completed_queries,
        "message": run.message,
        "errors": run.errors,
        "warnings": run.warnings,
        "has_report": bool(run.report_html),
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }


@app.get("/api/stream/{run_id}")
async def run_stream(run_id: str):
    """SSE stream for real-time run progress."""
    from web.run_manager import get_run

    async def event_generator():
        last_status = ""
        last_message = ""
        last_completed = -1
        iterations = 0

        while iterations < _SSE_MAX_ITERATIONS:
            iterations += 1
            run = get_run(run_id)
            if not run:
                yield f"data: {json.dumps({'error': 'Run not found'})}\n\n"
                break

            # Only send updates when something changed
            changed = (
                run.status != last_status
                or run.message != last_message
                or run.completed_queries != last_completed
            )
            if changed:
                last_status = run.status
                last_message = run.message
                last_completed = run.completed_queries
                yield f"data: {json.dumps({
                    'status': run.status,
                    'total_queries': run.total_queries,
                    'completed_queries': run.completed_queries,
                    'message': run.message,
                    'errors': run.errors,
                    'has_report': bool(run.report_html),
                })}\n\n"

            if run.status in ("completed", "failed"):
                break

            await asyncio.sleep(0.5)

        if iterations >= _SSE_MAX_ITERATIONS:
            yield f"data: {json.dumps({'error': 'Stream timeout - run exceeded maximum duration'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/report/{run_id}", response_class=HTMLResponse)
async def get_report(run_id: str):
    """Get the generated HTML report."""
    from web.run_manager import get_run
    run = get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if not run.report_html:
        raise HTTPException(404, "Report not ready yet")
    return run.report_html


@app.get("/api/csv/{run_id}")
async def get_csv(run_id: str):
    """Download the CSV export."""
    from web.run_manager import get_run
    run = get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if not run.csv_data:
        raise HTTPException(404, "CSV not ready yet")
    return StreamingResponse(
        iter([run.csv_data]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=ai_relevancy_{run_id}.csv"},
    )


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}
