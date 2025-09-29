#!/bin/bash
# Script de déploiement rapide une fois le VPS configuré

set -e

echo "⚡ Déploiement rapide Bot Alternance"
echo "===================================="

PROJECT_DIR="$HOME/Bot_Alternance"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Répertoire $PROJECT_DIR non trouvé"
    echo "Exécutez d'abord le script de déploiement initial"
    exit 1
fi

cd "$PROJECT_DIR"

echo "📦 Installation des dépendances..."
source venv/bin/activate
pip install -r requirements.txt

echo "🗄️  Initialisation/Mise à jour de la base de données..."
python scripts/setup_database.py

echo "🧪 Test rapide du système..."
python scripts/test_scrapers.py indeed || echo "⚠️  Test Indeed échoué"

echo "🔄 Redémarrage du service..."
if systemctl is-active --quiet alternance-bot; then
    sudo systemctl restart alternance-bot
else
    sudo systemctl start alternance-bot
fi

echo "📊 Status du service..."
sudo systemctl status alternance-bot --no-pager -l

echo ""
echo "✅ Déploiement rapide terminé!"
echo "📋 Vérifiez les logs avec: ./manage.sh logs"