#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# SCRIPT : fix-ip.sh
# Rôle   : Met à jour automatiquement l'IP de Harbor après un changement de réseau
# Usage  : bash fix-ip.sh
# ═══════════════════════════════════════════════════════════════════════════

# 1. Détection de la nouvelle IP
NEW_IP=$(hostname -I | awk '{print $1}')

if [ -z "$NEW_IP" ]; then
    echo "❌ Erreur : Impossible de détecter une adresse IP. Vérifiez votre connexion."
    exit 1
fi

echo "🚀 Nouvelle IP détectée : $NEW_IP"

# 2. Mise à jour de harbor.yml
HARBOR_YML="harbor/harbor.yml"
if [ -f "$HARBOR_YML" ]; then
    echo "📝 Mise à jour de $HARBOR_YML..."
    # Remplace la ligne hostname: ... par la nouvelle IP
    sed -i "s/^hostname: .*/hostname: $NEW_IP/" "$HARBOR_YML"
else
    echo "❌ Erreur : Fichier $HARBOR_YML non trouvé."
    exit 1
fi

# 3. Reconfiguration de Harbor
echo "⚙️ Reconfiguration des services Harbor (sudo requis)..."
cd harbor
sudo ./prepare

echo "🔄 Redémarrage des conteneurs..."
sudo docker compose up -d

cd ..

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║  ✅ TERMINÉ !                                                        ║"
echo "║  🌐 Harbor est maintenant accessible sur : http://$NEW_IP        ║"
echo "║  ⚙️  Jenkins détectera cette IP automatiquement au prochain Build.    ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
