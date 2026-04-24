# Architecture Technique — Spam Detector MLOps

## Vue d'ensemble

Le projet implémente une chaîne MLOps complète autour d'un modèle de détection de spam SMS.

## Composants

### 1. Modèle ML

- **Algorithme** : Pipeline scikit-learn composé de :
  - `TfidfVectorizer` (unigrammes + bigrammes, 10 000 features)
  - `MultinomialNB` (Naive Bayes, alpha=0.1)
- **Dataset** : UCI SMS Spam Collection — 5 572 messages (4 825 ham, 747 spam)
- **Sérialisation** : `pickle` → `model/spam_model.pkl`

### 2. API (FastAPI)

- Endpoint `POST /predict` : prédiction unitaire avec probabilités
- Endpoint `POST /predict/batch` : prédiction en lot (≤ 100 messages)
- Endpoint `GET /health` : health check
- Endpoint `GET /metrics` : métriques Prometheus
- Chargement du modèle avec `@lru_cache` (singleton)

### 3. Containerisation (Docker)

Build **multi-stage** pour minimiser la taille de l'image :
- Stage `builder` : compilation des dépendances Python
- Stage `runner` : image finale allégée + utilisateur non-root

### 4. Pipeline CI/CD (GitLab)

```
commit → lint → test → build → scan → push → deploy
```

- **lint** : flake8 + black
- **test** : pytest + coverage + validation accuracy ML
- **build** : `docker build` multi-stage avec cache Harbor
- **scan** : Trivy (CVE HIGH/CRITICAL)
- **push** : Harbor avec tags `SHA` + `latest` + tag sémantique
- **deploy** : SSH → `docker compose up -d` sur staging/prod

### 5. Registry (Harbor)

- Scan de vulnérabilités intégré (Clair/Trivy)
- Rétention d'images configurable
- Authentification par robot account

### 6. Monitoring (optionnel)

- Prometheus scrape `/metrics` toutes les 15s
- Grafana pour la visualisation des métriques API

## Flux de données

```
SMS input
   │
   ▼
FastAPI /predict
   │
   ▼
TfidfVectorizer.transform(text)
   │
   ▼
MultinomialNB.predict_proba()
   │
   ▼
{"label": "spam|ham", "spam_probability": 0.998}
```
