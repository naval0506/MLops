# Harbor — Installation et Configuration

Harbor est le registre Docker privé du projet. Il stocke les images et lance
un scan de sécurité automatique (Trivy) à chaque push.

---

## Option A — Harbor complet avec Trivy (recommandé)

### Prérequis
- Docker + Docker Compose installés
- Port 80 (ou 443) libre
- 4 Go RAM minimum

```bash
# 1. Télécharger Harbor
wget https://github.com/goharbor/harbor/releases/download/v2.10.2/harbor-online-installer-v2.10.2.tgz
tar xvf harbor-online-installer-v2.10.2.tgz
cd harbor

# 2. Configurer (copier le fichier exemple fourni)
cp harbor.yml.tmpl harbor.yml
# Éditer harbor.yml — changer OBLIGATOIREMENT :
#   hostname: TON_IP_OU_DOMAINE
#   harbor_admin_password: MotDePasseAdmin

# 3. Installer avec le scan Trivy intégré
sudo ./install.sh --with-trivy

# Harbor démarre automatiquement avec Docker Compose
# Interface : http://TON_IP  →  admin / MotDePasseAdmin
```

### Vérifier que Harbor tourne
```bash
docker compose -f /chemin/harbor/docker-compose.yml ps
# Tous les services doivent être "healthy"
```

---

## Option B — Registry simple Docker (dev local, 1 minute)

Si tu veux juste tester sans installer Harbor :

```bash
docker run -d -p 5000:5000 --name registry registry:2
# HARBOR_HOST=localhost:5000 dans .env et Jenkins
```

---

## Créer le projet Harbor

1. Ouvrir l'interface : `http://TON_IP`
2. Se connecter : `admin` / ton mot de passe
3. **New Project** :
   - Project Name : `spam-detector`
   - Access Level : **Private**
   - Storage : default
4. Aller dans le projet → **Configuration** :
   - Cocher **"Automatically scan images on push"** ✓

---

## Créer un Robot Account (pour Jenkins)

Les robot accounts sont des comptes techniques pour le CI/CD.

1. **Administration** → **Robot Accounts** → **New Robot Account**
2. Remplir :
   - Name : `ci-spam-detector`
   - Expiration : selon ta politique (ex: 365 jours)
   - Permissions : projet `spam-detector` → cocher **push** + **pull**
3. Cliquer **Add** → **copier immédiatement le token** (affiché une seule fois)
4. Note le nom complet affiché : `robot$ci-spam-detector`

### Mettre le token dans Jenkins
→ Voir `jenkins/README.md` section "3.1 — Harbor credentials"

### Tester manuellement
```bash
docker login TON_HARBOR_HOST -u "robot$ci-spam-detector" -p TON_TOKEN

docker build -f docker/Dockerfile -t TON_HARBOR_HOST/spam-detector/spam-api:test .
docker push TON_HARBOR_HOST/spam-detector/spam-api:test

# Dans Harbor → projet spam-detector → Repositories → vérifier l'image
# L'onglet "Vulnerabilities" montre le rapport Trivy
```

---

## Autoriser les connexions HTTP (si pas de HTTPS)

Si Harbor tourne en HTTP (pas HTTPS), Docker refusera de s'y connecter par défaut.
Ajouter Harbor comme "insecure registry" :

```bash
# Éditer /etc/docker/daemon.json sur TOUS les serveurs (Jenkins, staging, prod)
{
  "insecure-registries": ["TON_HARBOR_HOST"]
}

# Redémarrer Docker
sudo systemctl restart docker
```
