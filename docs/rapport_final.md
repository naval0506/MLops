# Rapport Final — Spam Detector MLOps

## Résumé

Ce rapport documente la mise en place d'une chaîne MLOps complète pour la détection
de spam SMS basée sur le dataset UCI, avec GitLab CI/CD, Jenkins, Harbor et Docker.

## Architecture implémentée

```
[Developer]
    │ git push
    ▼
[GitLab / GitHub Repo]
    │
    ├── .gitlab-ci.yml ──► [GitLab Runner]
    │                           │
    └── Jenkinsfile ────► [Jenkins]
                               │
                    ┌──────────┴──────────┐
                    │                     │
              [Lint + Test]         [Build Docker]
                    │                     │
              [ML Quality]         [Scan Trivy]
                                          │
                                   [Push Harbor]
                                          │
                              ┌───────────┴───────────┐
                              │                       │
                        [Staging auto]        [Prod manuel]
                              │
                    [docker compose up]
                              │
                    ┌─────────┴─────────┐
                    │                   │
               [spam-api]        [Prometheus]
               port 8000          [Grafana]
```

## Modèle ML

| Métrique    | Valeur   |
|-------------|----------|
| Algorithme  | TF-IDF (10k features, bigrammes) + Multinomial Naive Bayes |
| Accuracy    | ~98.4%   |
| Precision spam | ~99% |
| Recall spam | ~95%    |
| F1 spam     | ~97%    |
| Temps inférence | < 5ms |

## Pipeline CI/CD

**6 stages séquentiels :**
1. **Lint** : flake8 + black (parallèle)
2. **Test** : pytest + coverage + validation accuracy ML (parallèle)
3. **Build** : Docker multi-stage (image ~200MB)
4. **Scan** : Trivy sur l'image exportée
5. **Push** : Harbor avec tags SHA + latest
6. **Deploy** : SSH + docker compose (staging auto, prod manuel)

## Sécurité

- Image Docker avec utilisateur non-root
- Secrets CI/CD chiffrés (jamais dans le code)
- Scan Trivy HIGH/CRITICAL à chaque build
- Robot account Harbor avec permissions minimales

## Résultats

- Pipeline complet en ~8 minutes
- Déploiement zero-downtime (rolling update via Compose)
- Interface web fonctionnelle sur port 8000
- Health check automatique post-déploiement
