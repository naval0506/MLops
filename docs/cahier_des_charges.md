# Cahier des Charges — Spam Detector MLOps

## 1. Contexte et objectif

Ce projet implémente une chaîne MLOps complète pour la détection de spam SMS/email.
L'objectif est d'automatiser intégralement le cycle : entraînement ML → conteneurisation
→ tests → registre privé → déploiement continu.

## 2. Cas d'usage

Classification binaire de messages texte (SMS ou email) en deux catégories :
- **spam** : message non sollicité, publicitaire ou malveillant
- **ham** : message légitime

## 3. Dataset

**UCI SMS Spam Collection** — 5 572 messages réels annotés manuellement.
- Source : https://archive.ics.uci.edu/ml/datasets/SMS+Spam+Collection
- Distribution : 4 825 ham (86.6%) / 747 spam (13.4%)
- Format : TSV (label \t texte)

## 4. Exigences fonctionnelles

| ID  | Exigence |
|-----|----------|
| F1  | Entraîner un modèle ML sur le dataset UCI avec accuracy ≥ 85% |
| F2  | Exposer une API REST de prédiction (unitaire + batch) |
| F3  | Servir une interface web de chat connectée à l'API |
| F4  | Containeriser l'application via Docker multi-stage |
| F5  | Pipeline CI/CD automatisé (GitLab + Jenkins) |
| F6  | Registre privé Harbor avec scan de sécurité Trivy |
| F7  | Déploiement automatique via Docker Compose + SSH |
| F8  | Monitoring via Prometheus + Grafana |

## 5. Exigences non fonctionnelles

- Temps de réponse API < 100ms par prédiction
- Image Docker finale < 500MB
- Coverage tests ≥ 70%
- Aucune vulnérabilité CRITICAL non traitée

## 6. Stack technique

| Composant | Technologie |
|-----------|-------------|
| ML        | scikit-learn 1.5, TF-IDF + Multinomial Naive Bayes |
| API       | FastAPI 0.115, Python 3.11 |
| Interface | HTML/CSS/JS vanilla (servi par FastAPI) |
| CI/CD     | GitLab CI + Jenkins |
| Registre  | Harbor 2.10 + Trivy |
| Deploy    | Docker Compose + SSH |
| Monitoring| Prometheus + Grafana |
