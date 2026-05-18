# Installation des services CI/CD avec Docker

Ce projet utilise GitHub comme dépôt source et Jenkins comme moteur CI/CD.
GitLab CE peut être lancé en Docker si le sujet exige de montrer un GitLab
local, mais il n'est pas obligatoire pour faire tourner le pipeline actuel.

## 1. Préparer le réseau Docker

```bash
docker network create mlops-net || true
```

## 2. Jenkins en Docker

```bash
docker compose -f jenkins/jenkins-docker-compose.yml up -d
docker logs jenkins
```

Interface : <http://localhost:8085>

Créer ensuite un job Jenkins de type **Pipeline** :

- Definition : `Pipeline script from SCM`
- SCM : `Git`
- Repository URL : URL du dépôt GitHub
- Script Path : `Jenkinsfile`

Le Jenkinsfile exécute :

```text
Checkout -> black/flake8/pytest -> train -> docker build -> Trivy
         -> push registry/Harbor optionnel -> deploy Compose optionnel
```

## 3. GitLab CE en Docker, optionnel

À utiliser seulement si tu veux montrer une instance GitLab locale pour coller
au sujet initial. Le projet peut rester sur GitHub.

```bash
docker run -d \
  --hostname gitlab.local \
  --name gitlab \
  --restart unless-stopped \
  --network mlops-net \
  -p 8929:80 \
  -p 2224:22 \
  -v gitlab-config:/etc/gitlab \
  -v gitlab-logs:/var/log/gitlab \
  -v gitlab-data:/var/opt/gitlab \
  --shm-size 256m \
  gitlab/gitlab-ce:latest
```

Interface : <http://localhost:8929>

Mot de passe initial root :

```bash
docker exec -it gitlab grep 'Password:' /etc/gitlab/initial_root_password
```

Remarque : GitLab CE consomme beaucoup de RAM. Si la machine est limitée,
garder GitHub + Jenkins est plus simple pour la démo.

## 4. Registry local pour la démo

Le Compose principal contient déjà un registry léger compatible Docker :

```bash
docker compose --profile registry up -d registry
```

Registry : `localhost:5000`

Dans Jenkins :

```text
HARBOR_HOST=localhost:5000
IMAGE_NAME=spam-detector/spam-api
PUSH_TO_HARBOR=true
HARBOR_LOGIN=false
```

## 5. Harbor complet, optionnel mais recommandé pour la soutenance

Harbor n'est pas distribué comme une simple image unique. La méthode propre est
l'installateur officiel, documenté dans `harbor/README.md`.

Résumé :

```bash
wget https://github.com/goharbor/harbor/releases/download/v2.10.2/harbor-online-installer-v2.10.2.tgz
tar xvf harbor-online-installer-v2.10.2.tgz
cd harbor
cp harbor.yml.tmpl harbor.yml
# Modifier hostname et harbor_admin_password
sudo ./install.sh --with-trivy
```

Créer ensuite :

- un projet Harbor `spam-detector`
- un robot account avec droits `push` et `pull`
- un credential Jenkins `harbor-credentials`

Dans Jenkins :

```text
HARBOR_HOST=IP_OU_DNS_HARBOR
PUSH_TO_HARBOR=true
HARBOR_LOGIN=true
```

## 6. Déploiement Docker Compose

Sur le serveur cible :

```bash
sudo mkdir -p /opt/spam-detector
sudo chown "$USER":"$USER" /opt/spam-detector
scp docker-compose.prod.yml .env deploy@SERVEUR:/opt/spam-detector/
```

Paramètres Jenkins pour déploiement distant :

```text
DEPLOY=true
REMOTE_HOST=IP_DU_SERVEUR
REMOTE_USER=deploy
REMOTE_DEPLOY_PATH=/opt/spam-detector
COMPOSE_FILE=docker-compose.prod.yml
```

Le stage Jenkins se connecte en SSH, exporte `HARBOR_HOST` et `IMAGE_TAG`, puis
lance :

```bash
docker compose -f docker-compose.prod.yml pull spam-api
docker compose -f docker-compose.prod.yml up -d spam-api
```

