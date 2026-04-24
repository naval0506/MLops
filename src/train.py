"""
Spam Detection — Script d'entraînement
Dataset : UCI SMS Spam Collection (data/spam.csv)
"""

import os
import pickle
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODEL_PATH   = os.getenv("MODEL_PATH",   "model/spam_model.pkl")
METRICS_PATH = os.getenv("METRICS_PATH", "model/metrics.json")
DATA_PATH    = os.getenv("DATA_PATH",    "data/spam.csv")


def load_data(path: str) -> pd.DataFrame:
    logger.info(f"Chargement des données : {path}")
    df = pd.read_csv(path, encoding="latin-1", usecols=[0, 1])
    df.columns = ["label", "text"]
    df["label"] = df["label"].map({"ham": 0, "spam": 1})
    df.dropna(inplace=True)
    logger.info(f"Dataset : {len(df)} lignes | spam={df['label'].sum()} | ham={(df['label']==0).sum()}")
    return df


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            strip_accents="unicode", lowercase=True,
            stop_words="english", max_features=10_000, ngram_range=(1, 2),
        )),
        ("clf", MultinomialNB(alpha=0.1)),
    ])


def train(data_path: str = DATA_PATH, model_path: str = MODEL_PATH) -> dict:
    df = load_data(data_path)
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )
    pipeline = build_pipeline()
    logger.info("Entraînement...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=["ham", "spam"])
    cm     = confusion_matrix(y_test, y_pred).tolist()

    logger.info(f"Accuracy : {acc:.4f}")
    logger.info(f"\n{report}")

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump(pipeline, f)

    metrics = {
        "accuracy": round(acc, 4),
        "report": report,
        "confusion_matrix": cm,
        "train_size": len(X_train),
        "test_size": len(X_test),
    }
    os.makedirs(os.path.dirname(METRICS_PATH), exist_ok=True)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Modèle sauvegardé : {model_path}")
    return metrics


if __name__ == "__main__":
    m = train()
    print(f"\nAccuracy : {m['accuracy']}")
    print(m["report"])
