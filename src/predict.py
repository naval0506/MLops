"""Spam Detection — Module de prédiction."""

import logging
import os
import pickle
from functools import lru_cache
from typing import List

logger = logging.getLogger(__name__)
MODEL_PATH = os.getenv("MODEL_PATH", "model/spam_model.pkl")


@lru_cache(maxsize=1)
def load_model(path: str = MODEL_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Modèle introuvable : {path}. Lancez d'abord python src/train.py"
        )
    with open(path, "rb") as f:
        model = pickle.load(f)
    logger.info(f"Modèle chargé : {path}")
    return model


def predict_single(text: str, model=None) -> dict:
    if model is None:
        model = load_model(MODEL_PATH)
    label_id = model.predict([text])[0]
    proba = model.predict_proba([text])[0]
    return {
        "text": text,
        "label": "spam" if label_id == 1 else "ham",
        "spam_probability": round(float(proba[1]), 4),
        "ham_probability": round(float(proba[0]), 4),
        "is_spam": bool(label_id == 1),
    }


def predict_batch(texts: List[str], model=None) -> List[dict]:
    if model is None:
        model = load_model(MODEL_PATH)
    label_ids = model.predict(texts)
    probas = model.predict_proba(texts)
    return [
        {
            "text": t,
            "label": "spam" if lid == 1 else "ham",
            "spam_probability": round(float(p[1]), 4),
            "ham_probability": round(float(p[0]), 4),
            "is_spam": bool(lid == 1),
        }
        for t, lid, p in zip(texts, label_ids, probas)
    ]


if __name__ == "__main__":
    samples = [
        "Congratulations! You've won a FREE iPhone. Click here NOW to claim.",
        "Hey, are we still on for dinner tonight?",
        "URGENT: Your account has been suspended. Call 0800-XXXX immediately.",
        "Don't forget the meeting tomorrow at 9am.",
    ]
    for s in samples:
        r = predict_single(s)
        print(
            f"{'🚨' if r['is_spam'] else '✅'} [{r['label'].upper()}] "
            f"{r['spam_probability']:.0%} spam | {s[:60]}"
        )
