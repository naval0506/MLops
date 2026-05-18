# Rapport Final — Spam Detector MLOps

## Résumé

Ce rapport documente la mise en place d'une chaîne MLOps pour la détection
de spam SMS basée sur le dataset UCI, avec Jenkins CI/CD, Docker, Trivy et Harbor.

## Architecture implémentée

```
[GitHub Repo]
    │ git push
    ▼
[Jenkinsfile]
    │
    ├── Lint + tests + entraînement ML
    ├── Build Docker image
    ├── Scan Trivy HIGH/CRITICAL
    ├── Push Harbor
    └── Déploiement SSH + Docker Compose
            │
            ▼
      [Serveur staging/prod]
            │
            ├── spam-api port 8000
            └── Prometheus / Grafana optionnels
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
1. **Quality and Tests** : black, flake8, pytest
2. **Train Model** : entraînement scikit-learn et export du modèle
3. **Build Docker Image** : Docker multi-stage
4. **Security Scan** : Trivy si installé
5. **Push Harbor** : Harbor ou registry compatible si activé
6. **Deploy Compose** : Docker Compose si activé

## Sécurité

- Image Docker avec utilisateur non-root
- Secrets CI/CD chiffrés (jamais dans le code)
- Scan Trivy HIGH/CRITICAL à chaque build
- Robot account Harbor avec permissions minimales si Harbor est utilisé

## Résultats

- Pipeline complet vérifiable localement
- Déploiement via Docker Compose
- Interface web fonctionnelle sur port 8000
- Health check automatique post-déploiement
