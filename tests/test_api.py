"""
Tests unitaires - API FastAPI
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# Mock du modèle avant l'import de app
def make_mock_model():
    mock = MagicMock()
    mock.predict.side_effect = lambda texts: [
        1 if "spam" in t.lower() or "free" in t.lower() else 0 for t in texts
    ]
    mock.predict_proba.side_effect = lambda texts: [
        [0.1, 0.9] if ("spam" in t.lower() or "free" in t.lower()) else [0.95, 0.05]
        for t in texts
    ]
    return mock


@pytest.fixture
def client():
    mock_model = make_mock_model()
    with patch("predict.load_model", return_value=mock_model), patch(
        "app.load_model", return_value=mock_model
    ):
        from app import app

        with TestClient(app) as c:
            yield c


# ── Tests Health ──────────────────────────────────────────────────────────────


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "model_loaded" in data


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200


# ── Tests Predict ─────────────────────────────────────────────────────────────


def test_predict_ham(client):
    response = client.post("/predict", json={"text": "Hey, how are you today?"})
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "ham"
    assert data["is_spam"] is False
    assert 0.0 <= data["spam_probability"] <= 1.0
    assert 0.0 <= data["ham_probability"] <= 1.0


def test_predict_spam(client):
    response = client.post(
        "/predict", json={"text": "FREE prize! Click now to claim your reward!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "spam"
    assert data["is_spam"] is True


def test_predict_has_inference_time(client):
    response = client.post("/predict", json={"text": "Hello there"})
    assert response.status_code == 200
    assert "inference_time_ms" in response.json()


def test_predict_empty_text(client):
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 422  # Validation error


def test_predict_missing_field(client):
    response = client.post("/predict", json={})
    assert response.status_code == 422


# ── Tests Batch Predict ───────────────────────────────────────────────────────


def test_predict_batch(client):
    texts = [
        "Hi, can we schedule a meeting?",
        "FREE money! Call now!",
        "Don't forget to bring the documents.",
    ]
    response = client.post("/predict/batch", json={"texts": texts})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert len(data["results"]) == 3
    assert "inference_time_ms" in data


def test_predict_batch_empty(client):
    response = client.post("/predict/batch", json={"texts": []})
    assert response.status_code == 422


def test_predict_batch_single(client):
    response = client.post("/predict/batch", json={"texts": ["Just one message"]})
    assert response.status_code == 200
    assert response.json()["count"] == 1


# ── Tests Metrics ─────────────────────────────────────────────────────────────


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "spam_api_up" in response.text
