# Guide de Démarrage — Spam Detector MLOps (Jenkins + Harbor)

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

---

## ÉTAPE 3 — Lancer avec Docker

```bash
cp .env.example .env           # éditer .env avec tes valeurs
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

## ÉTAPE 4 — Installer Harbor

```bash
# Télécharger Harbor
wget https://github.com/goharbor/harbor/releases/download/v2.10.2/harbor-online-installer-v2.10.2.tgz
tar xvf harbor-online-installer-v2.10.2.tgz && cd harbor
cp harbor.yml.tmpl harbor.yml
# Éditer harbor.yml : hostname + harbor_admin_password
sudo ./install.sh --with-trivy
# Interface : http://TON_IP  (admin / ton_mot_de_passe)
```

Créer le projet et le robot account (voir `harbor/README.md`).

---

## ÉTAPE 5 — Installer Jenkins

```bash
docker compose -f jenkins/jenkins-docker-compose.yml up -d
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
# Ouvrir http://localhost:8080 → coller le mot de passe
```

Plugins à installer (Manage Jenkins → Plugins) :
- SSH Agent, Docker Pipeline, HTML Publisher, AnsiColor

Credentials à créer (Manage Jenkins → Credentials → Global) :
| ID | Type | Valeur |
|----|------|--------|
| `harbor-credentials` | Username+Password | robot Harbor |
| `ssh-staging-key` | SSH private key | clé SSH staging |
| `ssh-prod-key` | SSH private key | clé SSH prod |

Variables globales (Manage Jenkins → Configure System → Environment variables) :
```
HARBOR_HOST   = harbor.tondomaine.com
STAGING_HOST  = 192.168.1.10
STAGING_USER  = deploy
STAGING_PATH  = /opt/spam-detector
PROD_HOST     = 10.0.0.5
PROD_USER     = deploy
PROD_PATH     = /opt/spam-detector
```

---

## ÉTAPE 6 — Créer le Pipeline Jenkins

New Item → `spam-detector` → Pipeline → OK

- Definition : `Pipeline script from SCM`
- SCM : Git
- Repository URL : URL de ton repo (GitHub, Gitea, etc.)
- Script Path : `Jenkinsfile`
- Branches : `*/main`, `*/develop`

→ **Build Now** pour lancer le premier build.

---

## ÉTAPE 7 — Préparer les serveurs de déploiement

Sur chaque serveur (staging + prod) :
```bash
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG docker deploy
sudo mkdir -p /opt/spam-detector
sudo chown deploy:deploy /opt/spam-detector

# Copier les fichiers
scp docker-compose.yml .env deploy@SERVEUR:/opt/spam-detector/
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
