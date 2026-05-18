# Guide de Démarrage — Spam Detector MLOps (GitHub + Jenkins + Harbor)

Le dépôt source peut rester sur GitHub. Jenkins remplace GitLab CI/CD pour
orchestrer le pipeline. Si une instance GitLab est demandée pour la
démonstration, elle peut être lancée en Docker sans changer le pipeline actuel :
voir `docs/install_services_docker.md`.

## ÉTAPE 1 — Ajouter le dataset

```bash
# Télécharger UCI SMS Spam Collection
wget "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip"
unzip smsspamcollection.zip

# Convertir en CSV
python3 -c "
import pandas as pd
df = pd.read_csv('SMSSpamCollection', sep='\t', header=None, names=['v1','v2'])
df.to_csv('data/spam.csv', index=False, encoding='latin-1')
print(f'OK : {len(df)} messages')
"
```

---

## ÉTAPE 2 — Tester en local

```bash
pip install -r requirements.txt
python3 src/train.py           # entraîne le modèle (~10s, accuracy ~98%)
uvicorn src.app:app --port 8000
# → http://localhost:8000        interface de chat
# → http://localhost:8000/docs   API Swagger
```

Endpoints utiles :

```text
GET  /health       statut API + modèle
GET  /model/info   métriques du dernier entraînement
GET  /metrics      métriques Prometheus
POST /predict      prédiction d'un message
POST /predict/batch prédiction en lot
```

---

## ÉTAPE 3 — Lancer avec Docker

```bash
cp .env.example .env         
docker compose up -d spam-api
# → http://localhost:8000
```

Avec monitoring :
```bash
docker compose --profile monitoring up -d
# → Prometheus : http://localhost:9090
# → Grafana    : http://localhost:3000  (admin/admin)
```

---

## ÉTAPE 4 — Registry / Harbor

Pour une démo légère sans gros téléchargement :

```bash
docker compose --profile registry up -d registry
```

Cela lance un registry Docker local sur `localhost:5000`. Harbor complet reste
documenté dans `harbor/README.md`, mais il n'est pas obligatoire pour tester
l'application.

---

## ÉTAPE 5 — Configurer Jenkins

Le pipeline principal du projet est défini dans `Jenkinsfile`.

Pour une démo simple, Jenkins lit directement le dépôt GitHub.

```bash
docker compose -f jenkins/jenkins-docker-compose.yml up -d
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Interface Jenkins : `http://localhost:8085`.

Créer un job Pipeline :

- Definition : `Pipeline script from SCM`
- SCM : `Git`
- Repository URL : ton repo GitHub
- Script Path : `Jenkinsfile`

Pour pousser l'image vers Harbor, ajouter un credential Jenkins :

- ID : `harbor-credentials`
- Type : username/password
- Username/password : robot account Harbor

Paramètres Jenkins optionnels :

| Variable | Exemple |
|----------|---------|
| `HARBOR_HOST` | `harbor.local` ou `192.168.1.5:5000` |
| `IMAGE_NAME` | `spam-detector/spam-api` |
| `PUSH_TO_HARBOR` | `true` pour pousser l'image |
| `HARBOR_LOGIN` | `true` seulement pour Harbor avec authentification |
| `DEPLOY` | `true` pour lancer Docker Compose |
| `REMOTE_HOST` | IP du serveur distant, vide pour deploy local |
| `REMOTE_USER` | utilisateur SSH, ex. `deploy` |
| `REMOTE_DEPLOY_PATH` | `/opt/spam-detector` |
| `COMPOSE_FILE` | `docker-compose.prod.yml` |

---

## ÉTAPE 6 — Lancer le pipeline Jenkins

Le pipeline exécute simplement :

1. `black --check`, `flake8`, `pytest`
3. entraînement du modèle
4. build Docker
5. scan Trivy si Trivy est installé
6. push Harbor si `PUSH_TO_HARBOR=true`
7. déploiement Compose si `DEPLOY=true`

Jenkins couvre toute la partie CI/CD depuis GitHub.

---

## ÉTAPE 7 — Préparer les serveurs de déploiement

Sur chaque serveur (staging + prod) :
```bash
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG docker deploy
sudo mkdir -p /opt/spam-detector
sudo chown deploy:deploy /opt/spam-detector

# Copier les fichiers
scp docker-compose.prod.yml .env deploy@SERVEUR:/opt/spam-detector/
```

Tester l'accès SSH depuis la machine Jenkins :

```bash
ssh deploy@SERVEUR 'docker compose version && docker ps'
```

---

## Commandes utiles

```bash
# Entraîner le modèle
python3 src/train.py

# Lancer les tests
pytest tests/ -v

# Docker Compose
docker compose up -d spam-api
docker compose logs spam-api -f
docker compose down

# Reconstruire l'image
docker compose build spam-api
```
