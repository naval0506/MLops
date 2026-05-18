# Spam Detector — MLOps avec GitHub + Jenkins CI/CD + Harbor

Détection de spam SMS basée sur le dataset UCI.
Source : GitHub | Pipeline CI/CD : Jenkins | Registre : Harbor | Deploy : Docker Compose

## Démarrage rapide

```bash
# 1. Mettre spam.csv dans data/ (voir GUIDE_DEMARRAGE.md)
pip install -r requirements.txt
python3 src/train.py
uvicorn src.app:app --port 8000
# → http://localhost:8000
```

## Guides

- Démarrage du projet : `GUIDE_DEMARRAGE.md`
- Installation Docker de Jenkins/GitLab/Harbor : `docs/install_services_docker.md`

## Ce que fait l'application

L'application analyse un texte de type SMS/email et prédit s'il s'agit d'un
message normal (`ham`) ou d'un spam. Le modèle utilise un pipeline
scikit-learn : vectorisation TF-IDF puis classification Naive Bayes.

## Interfaces disponibles

| Interface | URL | Rôle |
|-----------|-----|------|
| Web UI | `http://localhost:8000/` | Tester un message dans le navigateur |
| Swagger API | `http://localhost:8000/docs` | Documentation interactive FastAPI |
| Healthcheck | `http://localhost:8000/health` | Vérifier que l'API et le modèle répondent |
| Infos modèle | `http://localhost:8000/model/info` | Voir accuracy et métriques d'entraînement |
| Métriques Prometheus | `http://localhost:8000/metrics` | Exposer les métriques MLOps |
| Prometheus optionnel | `http://localhost:9090` | Scraper les métriques |
| Grafana optionnel | `http://localhost:3001` | Dashboard monitoring |

Test API rapide :

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"FREE prize! Click now to claim your reward"}'
```

## Stack
| Composant | Techno |
|-----------|--------|
| ML | TF-IDF + Naive Bayes (scikit-learn) |
| API + Interface | FastAPI + HTML/JS |
| Source | GitHub |
| CI/CD | **Jenkins CI/CD** |
| Registry | **Harbor** + Trivy |
| Deploy | Docker Compose |
| Monitoring | Prometheus + Grafana |

## Pipeline Jenkins CI/CD

Le fichier `Jenkinsfile` automatise la chaîne demandée :

1. qualité : `black`, `flake8`, `pytest`
2. entraînement du modèle
3. build Docker
4. scan Trivy si installé
5. push Harbor si paramétré
6. déploiement Docker Compose

Variables Jenkins (Paramètres du build) :

| Variable | Rôle |
|----------|------|
| `HARBOR_HOST` | Harbor ou registry compatible, ex. `localhost:5000` |
| `IMAGE_NAME` | Nom de l'image Docker |
| `PUSH_TO_HARBOR` | Booléen pour pousser l'image |
| `HARBOR_LOGIN` | Booléen pour s'authentifier au registre |
| `DEPLOY` | Booléen pour lancer le déploiement local via Docker Compose |
| `REMOTE_HOST` | Serveur distant SSH, vide pour déploiement local |
| `REMOTE_USER` | Utilisateur SSH du serveur distant |
| `REMOTE_DEPLOY_PATH` | Dossier Compose distant |
| `COMPOSE_FILE` | Fichier Compose à utiliser |

Pour la démonstration, les credentials Harbor peuvent être configurés sous l'ID `harbor-credentials` dans Jenkins si nécessaire.
