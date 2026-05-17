# Jenkins — Démarrage simple

Pour une démo légère, Jenkins peut
lire le projet depuis GitHub, Gitea ou un dépôt local, puis exécuter le
`Jenkinsfile`.

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

Credential optionnel pour Harbor réel : `harbor-credentials`.
