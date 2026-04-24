# ── Stage 1 : builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2 : runner ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runner
LABEL maintainer="MLOps Team" description="Spam Detector API" version="1.0.0"

RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

COPY --from=builder /install /usr/local
COPY src/ ./src/
COPY model/ ./model/

ENV MODEL_PATH=/app/model/spam_model.pkl
ENV METRICS_PATH=/app/model/metrics.json
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

RUN chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
