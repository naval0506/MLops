# Jenkins — Installation et Configuration complète

## 1. Lancer Jenkins avec Docker

```bash
# Dans le dossier jenkins/
docker compose -f jenkins-docker-compose.yml up -d

# Récupérer le mot de passe admin initial
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Ouvrir **http://localhost:8080**, coller le mot de passe → "Install suggested plugins" → créer ton compte admin.

---

## 2. Plugins à installer

Jenkins → Manage Jenkins → Plugins → Available → chercher et installer :

| Plugin | Utilité |
|--------|---------|
| **SSH Agent** | Déploiement SSH sur les serveurs (OBLIGATOIRE) |
| **Docker Pipeline** | Commandes Docker dans le pipeline |
| **HTML Publisher** | Rapport de coverage dans l'interface |
| **AnsiColor** | Logs colorés dans la console |
| **Timestamper** | Horodatage des logs |

Après installation → **Restart Jenkins**.

---

## 3. Configurer les Credentials

Jenkins → **Manage Jenkins** → **Credentials** → System → Global credentials → **Add Credentials**

### 3.1 — Harbor (registre Docker)
- Kind : `Username with password`
- ID : `harbor-credentials`  ← ce nom est utilisé dans le Jenkinsfile
- Username : `robot$ci-spam-detector`  (ton robot account Harbor)
- Password : le token Harbor
- Description : Harbor Registry

### 3.2 — Clé SSH Staging
- Kind : `SSH Username with private key`
- ID : `ssh-staging-key`  ← ce nom est utilisé dans le Jenkinsfile
- Username : `deploy`
- Private Key → Enter directly → coller le contenu de ta clé privée SSH

### 3.3 — Clé SSH Production
- Kind : `SSH Username with private key`
- ID : `ssh-prod-key`
- Username : `deploy`
- Private Key → idem (peut être une clé différente)

---

## 4. Variables d'environnement globales

Jenkins → **Manage Jenkins** → **Configure System** → section **Global properties** → cocher "Environment variables" → Add :

| Nom de variable | Valeur exemple |
|-----------------|----------------|
| `HARBOR_HOST`   | `harbor.mondomaine.com` ou `192.168.1.5:80` |
| `STAGING_HOST`  | `192.168.1.10` |
| `STAGING_USER`  | `deploy` |
| `STAGING_PATH`  | `/opt/spam-detector` |
| `PROD_HOST`     | `10.0.0.5` |
| `PROD_USER`     | `deploy` |
| `PROD_PATH`     | `/opt/spam-detector` |

---

## 5. Créer le Pipeline

Jenkins → **New Item** → Nom : `spam-detector` → **Pipeline** → OK

Dans la configuration du pipeline :

**Section "Build Triggers" :**
- Cocher `Poll SCM` → Schedule : `H/5 * * * *`
- (Optionnel) Cocher `Build when a change is pushed to GitHub/Gitea` pour webhook

**Section "Pipeline" :**
- Definition : `Pipeline script from SCM`
- SCM : `Git`
- Repository URL : URL de ton repo (GitHub, Gitea, Gitea local, etc.)
- Credentials : ajouter si repo privé (token ou SSH)
- Branches to build : `*/main` et `*/develop`
- Script Path : `Jenkinsfile`

Sauvegarder → **Build Now** pour le premier lancement.

---

## 6. Utiliser Gitea à la place de GitLab (recommandé)

Gitea est une alternative légère à GitLab, auto-hébergée.

```bash
# Lancer Gitea avec Docker
docker run -d \
  --name gitea \
  -p 3001:3000 \
  -p 2222:22 \
  -v gitea-data:/data \
  gitea/gitea:latest

# Interface : http://localhost:3001
# Créer un compte admin, créer un repo "spam-detector"
# Pusher le projet dedans
```

### Webhook Gitea → Jenkins

1. Gitea → ton repo → Settings → Webhooks → Add Webhook → Gitea
2. Target URL : `http://TON_JENKINS:8080/gitea-webhook/post`
3. Content-Type : `application/json`
4. Events : `Push` + `Pull Request`

Jenkins → Installer le plugin **Gitea** → Manage Jenkins → Configure System → Gitea Servers → Add.

---

## 7. Vérifier que tout fonctionne

```bash
# Depuis Jenkins, vérifier que Docker est accessible
# Manage Jenkins → Script Console → coller :
def proc = "docker --version".execute()
proc.waitFor()
println proc.text

# Vérifier connexion Harbor
def proc2 = "docker login TON_HARBOR -u USER -p TOKEN".execute()
proc2.waitFor()
println proc2.text
```

---

## 8. Structure du pipeline dans Jenkins Blue Ocean

```
Checkout
   │
   ├── Lint flake8  ─┐ (parallèle)
   └── Lint black   ─┘
         │
   ├── Tests unitaires  ─┐ (parallèle)
   └── Qualité ML       ─┘
         │
      Build Docker
         │
      Scan Trivy
         │
      Push Harbor
         │
   ┌─────┴──────┐
   │            │
Staging      Production
(auto)       (manuel ✋)
```
