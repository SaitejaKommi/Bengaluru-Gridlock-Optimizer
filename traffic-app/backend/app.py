"""
app.py — FastAPI application entry point.

Endpoints:
  GET  /          → serves frontend/index.html
  GET  /health    → health check
  POST /analyze   → run full detection pipeline on uploaded image

Models are loaded once at startup via FastAPI lifespan event.
"""

import logging
import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.pipeline import run_pipeline
from backend.utils import decode_image
from backend.services import vehicle_service, helmet_service, seatbelt_service, plate_service

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("traffic_app")

# ── Lifespan: pre-load all models at startup ──────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("═" * 60)
    logger.info("  Traffic Violation Detection — Starting up")
    logger.info("═" * 60)

    logger.info("Loading vehicle model...")
    vehicle_service.load_model()
    logger.info("Vehicle model loaded.")

    logger.info("Loading helmet model...")
    helmet_service.load_model()
    logger.info("Helmet model loaded.")

    logger.info("Loading seatbelt model...")
    seatbelt_service.load_model()
    logger.info("Seatbelt model loaded.")

    logger.info("Loading plate detection model...")
    plate_service.load_model()
    logger.info("Plate detection model loaded.")

    logger.info("Initialising OCR engine...")
    plate_service.load_ocr()
    logger.info("OCR engine ready.")

    logger.info("═" * 60)
    logger.info("  All models loaded. Application ready.")
    logger.info("═" * 60)

    yield  # Application runs here

    logger.info("Shutting down...")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Traffic Violation Detection API",
    description="Automated traffic violation detection using YOLO + EasyOCR",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend HTML file and static assets
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
@app.get("/upload", response_class=HTMLResponse)
@app.get("/results", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend UI."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            html = f.read()
        return HTMLResponse(content=html)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "ok",
        "models_loaded": True,
        "services": ["vehicle", "helmet", "seatbelt", "plate", "ocr"],
    })


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    Analyze an uploaded traffic image.

    Input:  multipart/form-data with field 'file' (image)
    Output: JSON with vehicles, helmets, seatbelts, plates, violations, annotated_image
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type: {file.content_type}. Please upload an image.",
        )

    # Read raw bytes
    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    logger.info(f"Received image: {file.filename!r} ({len(raw) / 1024:.1f} KB)")

    # Decode to numpy
    try:
        image = decode_image(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Run the full pipeline
    try:
        result = run_pipeline(image)
    except Exception as exc:
        logger.exception(f"Pipeline error: {exc}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(exc)}")

    return JSONResponse(content=result)
