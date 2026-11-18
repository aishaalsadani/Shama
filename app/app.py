"""
app.py
FastAPI application - Two-Stage Skin Cancer AI System.

Pipeline: every uploaded image goes through Stage 1 (binary) first. If Stage 1 predicts
Benign, that is the final result. If Stage 1 predicts Malignant, Stage 2 (subtype) runs
automatically and its prediction becomes the final result. The frontend never chooses which
model runs - this endpoint decides, always.
"""
import io
import logging
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, UnidentifiedImageError

from config import (
    APP_TITLE,
    APP_VERSION,
    APP_DESCRIPTION,
    ALLOWED_CONTENT_TYPES,
    MAX_UPLOAD_SIZE_MB,
    DEVICE,
    DATASET_METADATA_PATH,
)
from inference_binary import Stage1Predictor
from inference import Stage2Predictor
from dataset_stats import compute_dataset_stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("app")

app = FastAPI(title=APP_TITLE, version=APP_VERSION, description=APP_DESCRIPTION)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Loaded once at startup, reused for every request - never reloaded per-request.
stage1_predictor: Optional[Stage1Predictor] = None
stage2_predictor: Optional[Stage2Predictor] = None

# Computed once at startup from HAM10000_metadata.csv, reused for every /dashboard request.
dataset_stats_cache: Optional[dict] = None


@app.on_event("startup")
def load_models() -> None:
    global stage1_predictor, stage2_predictor, dataset_stats_cache
    logger.info("Loading models on device: %s", DEVICE)
    stage1_predictor = Stage1Predictor(DEVICE)
    stage2_predictor = Stage2Predictor(DEVICE)
    logger.info("Both stages loaded successfully. Ready to serve /predict.")

    dataset_stats_cache = compute_dataset_stats(DATASET_METADATA_PATH)
    if dataset_stats_cache is None:
        logger.warning(
            "GET /dashboard will report 503 until HAM10000_metadata.csv is placed at %s.",
            DATASET_METADATA_PATH,
        )
    else:
        logger.info("Dataset stats ready. Serving /dashboard.")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"app_title": APP_TITLE})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    """Renders the Dataset Analytics page. Reuses the same sidebar/header/footer/CSS
    as the Analyze page via base.html; the chart data itself is fetched client-side
    from GET /api/dashboard."""
    return templates.TemplateResponse(request, "dashboard.html", {"app_title": APP_TITLE})


@app.get("/health")
def health():
    models_loaded = {
        "stage1_binary": stage1_predictor is not None,
        "stage2_multiclass": stage2_predictor is not None,
    }
    return {
        "status": "ok" if all(models_loaded.values()) else "loading",
        "device": str(DEVICE),
        "models_loaded": models_loaded,
    }


@app.get("/api/dashboard")
def dashboard():
    """Dataset analytics computed from HAM10000_metadata.csv: totals, class/gender/age
    distributions, diagnosis type breakdown, and body location breakdown."""
    if dataset_stats_cache is None:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Dataset metadata not available. Place HAM10000_metadata.csv at "
                f"{DATASET_METADATA_PATH} and restart the server."
            ),
        )
    return dataset_stats_cache


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if stage1_predictor is None or stage2_predictor is None:
        raise HTTPException(status_code=503, detail="Models are still loading. Please try again shortly.")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds the {MAX_UPLOAD_SIZE_MB}MB limit.")

    try:
        image = Image.open(io.BytesIO(raw_bytes))
        image.load()
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read the uploaded image.")

    # --- Stage 1: binary screening (always runs) -------------------------------------------
    stage1_result = stage1_predictor.predict(image)

    if not stage1_result["is_malignant"]:
        return {
            "stage1": {
                "prediction": stage1_result["prediction"],
                "confidence": stage1_result["confidence"],
                "probability_benign": stage1_result["probability_benign"],
                "probability_malignant": stage1_result["probability_malignant"],
            },
            "stage2": None,
            "final_prediction": stage1_result["prediction"],
            "recommendation": stage1_result["recommendation"],
        }

    # --- Stage 2: malignant subtype (only runs when Stage 1 says Malignant) ----------------
    stage2_result = stage2_predictor.predict(image)

    return {
        "stage1": {
            "prediction": stage1_result["prediction"],
            "confidence": stage1_result["confidence"],
            "probability_benign": stage1_result["probability_benign"],
            "probability_malignant": stage1_result["probability_malignant"],
        },
        "stage2": {
            "prediction": stage2_result["prediction"],
            "prediction_code": stage2_result["prediction_code"],
            "confidence": stage2_result["confidence"],
            "probabilities": stage2_result["probabilities"],
        },
        "final_prediction": stage2_result["prediction"],
        "recommendation": stage2_result["recommendation"],
    }
