"""Spam Detection API — FastAPI (sert aussi l'interface web)."""

import os, time, json, logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from predict import load_model, predict_single, predict_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODEL_PATH  = os.getenv("MODEL_PATH",  "model/spam_model.pkl")
METRICS_PATH = os.getenv("METRICS_PATH", "model/metrics.json")
STATIC_DIR  = os.path.join(os.path.dirname(__file__), "static")

# ── Pydantic schemas ──────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000,
                      example="Congratulations! You won a FREE prize!")

class BatchPredictRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, max_length=100)

class PredictResponse(BaseModel):
    text: str
    label: str
    is_spam: bool
    spam_probability: float
    ham_probability: float
    inference_time_ms: float

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str

# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Démarrage API — chargement modèle...")
    try:
        load_model(MODEL_PATH)
        logger.info("Modèle chargé.")
    except FileNotFoundError as e:
        logger.error(str(e))
    yield
    logger.info("Arrêt API.")

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Spam Detector API",
    description="Détection de spam SMS/email — Projet MLOps (UCI dataset)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    index = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": "Spam Detector API v1.0 — /docs"}


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health():
    try:
        model_ok = load_model(MODEL_PATH) is not None
    except Exception:
        model_ok = False
    return HealthResponse(status="ok" if model_ok else "degraded",
                          model_loaded=model_ok, version="1.0.0")


@app.get("/model/info", tags=["Monitoring"])
async def model_info():
    """Retourne les métriques du dernier entraînement."""
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH) as f:
            return json.load(f)
    return {"detail": "Pas encore de métriques. Lancez train.py d'abord."}


@app.post("/predict", response_model=PredictResponse, tags=["Prédiction"])
async def predict(request: PredictRequest):
    """Prédit si un message est spam ou ham."""
    try:
        model = load_model(MODEL_PATH)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    t0     = time.perf_counter()
    result = predict_single(request.text, model=model)
    ms     = round((time.perf_counter() - t0) * 1000, 3)
    logger.info(f"[PREDICT] {result['label']} {result['spam_probability']} | {request.text[:80]}")
    return PredictResponse(**result, inference_time_ms=ms)


@app.post("/predict/batch", tags=["Prédiction"])
async def predict_batch_endpoint(request: BatchPredictRequest):
    """Prédiction en lot (≤ 100 messages)."""
    try:
        model = load_model(MODEL_PATH)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    t0      = time.perf_counter()
    results = predict_batch(request.texts, model=model)
    ms      = round((time.perf_counter() - t0) * 1000, 3)
    return {"results": results, "count": len(results), "inference_time_ms": ms}


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    return PlainTextResponse(
        "# HELP spam_api_up API is running\n"
        "# TYPE spam_api_up gauge\nspam_api_up 1\n"
    )
