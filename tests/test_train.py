"""
Tests unitaires - Module d'entraînement
"""

import os
import pickle
import tempfile
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Ajout du chemin src au path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from train import build_pipeline, load_data, train


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_csv(tmp_path):
    """Crée un fichier CSV minimal simulant le dataset UCI."""
    data = {
        "v1": ["ham"] * 80 + ["spam"] * 20,
        "v2": [
            "Hey how are you doing today",
            "Let's meet for coffee tomorrow",
            "Can you send me the report please",
            "I'll call you back in 5 minutes",
            "Thanks for your help yesterday",
        ] * 16 + [
            "FREE prize click now to win",
            "Congratulations you have been selected",
            "URGENT claim your reward immediately",
            "Win cash now call this number",
        ] * 5,
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "spam.csv"
    df.to_csv(csv_path, index=False, encoding="latin-1")
    return str(csv_path)


# ── Tests load_data ───────────────────────────────────────────────────────────

def test_load_data_shape(sample_csv):
    df = load_data(sample_csv)
    assert "label" in df.columns
    assert "text" in df.columns
    assert len(df) == 100


def test_load_data_labels(sample_csv):
    df = load_data(sample_csv)
    assert set(df["label"].unique()).issubset({0, 1})


def test_load_data_no_nulls(sample_csv):
    df = load_data(sample_csv)
    assert df.isnull().sum().sum() == 0


# ── Tests build_pipeline ──────────────────────────────────────────────────────

def test_pipeline_has_tfidf_and_clf():
    pipe = build_pipeline()
    assert "tfidf" in pipe.named_steps
    assert "clf" in pipe.named_steps


def test_pipeline_fit_predict(sample_csv):
    df = load_data(sample_csv)
    pipe = build_pipeline()
    pipe.fit(df["text"], df["label"])
    preds = pipe.predict(df["text"])
    assert len(preds) == len(df)
    assert set(preds).issubset({0, 1})


def test_pipeline_predict_proba(sample_csv):
    df = load_data(sample_csv)
    pipe = build_pipeline()
    pipe.fit(df["text"], df["label"])
    probas = pipe.predict_proba(df["text"])
    assert probas.shape == (len(df), 2)
    # Les probabilités doivent sommer à ~1
    assert abs(probas[0].sum() - 1.0) < 1e-6


# ── Tests train ───────────────────────────────────────────────────────────────

def test_train_returns_metrics(sample_csv, tmp_path):
    model_path = str(tmp_path / "model.pkl")
    metrics = train(data_path=sample_csv, model_path=model_path)
    assert "accuracy" in metrics
    assert "confusion_matrix" in metrics
    assert 0.0 <= metrics["accuracy"] <= 1.0


def test_train_saves_model(sample_csv, tmp_path):
    model_path = str(tmp_path / "model.pkl")
    train(data_path=sample_csv, model_path=model_path)
    assert os.path.exists(model_path)


def test_train_model_loadable(sample_csv, tmp_path):
    model_path = str(tmp_path / "model.pkl")
    train(data_path=sample_csv, model_path=model_path)
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    pred = model.predict(["Free prize win now click"])
    assert len(pred) == 1


def test_train_accuracy_above_threshold(sample_csv, tmp_path):
    model_path = str(tmp_path / "model.pkl")
    metrics = train(data_path=sample_csv, model_path=model_path)
    # Sur un jeu propre, on attend au moins 70%
    assert metrics["accuracy"] >= 0.70
