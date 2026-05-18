# Jenkins — Démarrage simple

Pour une démo légère, Jenkins lit le projet depuis GitHub, puis exécute le
`Jenkinsfile`. GitLab CE reste optionnel et peut être lancé en Docker si la
soutenance demande une instance GitLab locale.

Le pipeline est prévu pour le service Docker Compose `jenkins`, car les jobs
Python utilisent `docker run --volumes-from jenkins`.

Pipeline réellement utilisé :

```
Checkout -> Quality and Tests -> Train Model -> Build Docker Image
         -> Security Scan -> Push Harbor optionnel -> Deploy Compose optionnel
```

Paramètres Jenkins optionnels :

| Variable | Exemple | Rôle |
|----------|---------|------|
| `HARBOR_HOST` | `localhost:5000` | Harbor ou registry local compatible |
| `IMAGE_NAME` | `spam-detector/spam-api` | Nom image |
| `PUSH_TO_HARBOR` | `true` | Active le push Docker vers Harbor |
| `HARBOR_LOGIN` | `false` en local, `true` pour Harbor réel | Active `docker login` |
| `DEPLOY` | `true` | Lance `docker compose up -d spam-api` |
| `REMOTE_HOST` | `192.168.1.20` | Serveur de déploiement distant |
| `REMOTE_USER` | `deploy` | Utilisateur SSH |
| `REMOTE_DEPLOY_PATH` | `/opt/spam-detector` | Dossier Compose distant |
| `COMPOSE_FILE` | `docker-compose.prod.yml` | Fichier Compose de déploiement |

Credential optionnel pour Harbor réel : `harbor-credentials`.

Guide complet d'installation Docker : `docs/install_services_docker.md`.
