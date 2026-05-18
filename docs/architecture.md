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

### 4. Pipeline CI/CD (GitHub + Jenkins)

```
push GitHub → checkout Jenkins → lint → test → train → build → scan → push → deploy
```

- **lint** : flake8 + black
- **test** : pytest + validation accuracy ML
- **build** : `docker build` multi-stage
- **scan** : Trivy (CVE HIGH/CRITICAL)
- **push** : Harbor ou registry compatible avec tags `BUILD_NUMBER` + `latest`
- **deploy** : local ou SSH vers le serveur puis `docker compose -f docker-compose.prod.yml up -d`

GitLab CE peut être installé en Docker pour la démonstration si nécessaire,
mais le pipeline de ce dépôt est piloté par Jenkins depuis GitHub.

### 5. Registry (Harbor)

- Registry cible pour stocker les images Docker
- Remplaçable en démo par `registry:2` sur `localhost:5000`
- Scan de vulnérabilités via Trivy dans le pipeline Jenkins
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
