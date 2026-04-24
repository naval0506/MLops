# Spam Detector — MLOps avec Jenkins + Harbor

Détection de spam SMS basée sur le dataset UCI.
Pipeline CI/CD : Jenkins | Registre : Harbor | Deploy : Docker Compose + SSH

## Démarrage rapide

```bash
# 1. Mettre spam.csv dans data/ (voir GUIDE_DEMARRAGE.md)
pip install -r requirements.txt
python3 src/train.py
uvicorn src.app:app --port 8000
# → http://localhost:8000
```

## Lire le guide complet : `GUIDE_DEMARRAGE.md`

## Stack
| Composant | Techno |
|-----------|--------|
| ML | TF-IDF + Naive Bayes (scikit-learn) |
| API + Interface | FastAPI + HTML/JS |
| CI/CD | **Jenkins** |
| Registry | **Harbor** + Trivy |
| Deploy | Docker Compose + SSH |
| Monitoring | Prometheus + Grafana |
