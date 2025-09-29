#!/bin/bash
# Script de déploiement automatique pour VPS Debian 13

set -e  # Arrêter en cas d'erreur

echo "🚀 Déploiement Bot Alternance sur VPS Debian 13"
echo "================================================"

# Variables
PROJECT_DIR="$HOME/Bot_Alternance"
SERVICE_NAME="alternance-bot"
PYTHON_VERSION="python3"

# Vérifications préliminaires
echo "🔍 Vérifications système..."

# Vérifier que nous sommes sur Debian
if ! grep -q "Debian" /etc/os-release; then
    echo "❌ Ce script est conçu pour Debian. OS détecté: $(cat /etc/os-release | grep PRETTY_NAME)"
    exit 1
fi

# Vérifier les permissions sudo
if ! sudo -n true 2>/dev/null; then
    echo "❌ Permissions sudo requises"
    exit 1
fi

echo "✅ Système compatible"

# Installation des dépendances système
echo "📦 Installation des dépendances système..."
sudo apt update
sudo apt install -y \
    postgresql \
    postgresql-contrib \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libpq-dev \
    git \
    nginx \
    ufw \
    htop \
    curl

echo "✅ Dépendances installées"

# Configuration PostgreSQL
echo "🗄️  Configuration PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Vérifier si la base existe déjà
DB_EXISTS=$(sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -w alternance_bot | wc -l)

if [ $DB_EXISTS -eq 0 ]; then
    echo "Création de la base de données..."
    sudo -u postgres createdb alternance_bot
    sudo -u postgres psql << EOF
CREATE USER alternance_user WITH PASSWORD 'ChangeMeInProduction!';
GRANT ALL PRIVILEGES ON DATABASE alternance_bot TO alternance_user;
ALTER USER alternance_user CREATEDB;
EOF
    echo "✅ Base de données créée"
else
    echo "ℹ️  Base de données existe déjà"
fi

# Configuration sécurisée PostgreSQL
echo "🔒 Configuration sécurisée PostgreSQL..."
PG_VERSION=$(sudo -u postgres psql -c "SHOW server_version;" | grep -oP '\d+\.\d+' | head -1)
PG_CONFIG_DIR="/etc/postgresql/$PG_VERSION/main"

# Backup des fichiers de config
sudo cp $PG_CONFIG_DIR/pg_hba.conf $PG_CONFIG_DIR/pg_hba.conf.backup
sudo cp $PG_CONFIG_DIR/postgresql.conf $PG_CONFIG_DIR/postgresql.conf.backup

# Configuration pg_hba.conf
sudo bash -c "cat >> $PG_CONFIG_DIR/pg_hba.conf << EOF

# Bot Alternance
local   alternance_bot   alternance_user                     md5
host    alternance_bot   alternance_user   127.0.0.1/32      md5
EOF"

sudo systemctl restart postgresql
echo "✅ PostgreSQL configuré"

# Préparation du projet
echo "📁 Préparation du projet..."

if [ -d "$PROJECT_DIR" ]; then
    echo "⚠️  Répertoire projet existe déjà. Sauvegarde..."
    mv "$PROJECT_DIR" "$PROJECT_DIR.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Note: Le code est déjà présent localement, on ne clone pas depuis git
if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
fi

echo "✅ Répertoire projet prêt"

# Configuration de l'environnement Python
echo "🐍 Configuration Python..."
cd "$PROJECT_DIR"

# Créer l'environnement virtuel
$PYTHON_VERSION -m venv venv
source venv/bin/activate

# Installer les dépendances (sera fait après copie du code)
echo "✅ Environnement Python prêt"

# Configuration du firewall
echo "🔥 Configuration firewall..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP (si nginx)
sudo ufw allow 443/tcp # HTTPS (si nginx)

# PostgreSQL seulement en local pour sécurité
# sudo ufw allow 5432/tcp  # Décommentez si accès externe nécessaire

echo "✅ Firewall configuré"

# Création des dossiers nécessaires
echo "📁 Création des dossiers..."
mkdir -p "$PROJECT_DIR"/{logs,data,backups}
chmod 755 "$PROJECT_DIR"/{logs,data,backups}

# Script de sauvegarde automatique
cat > "$HOME/backup_bot.sh" << 'EOF'
#!/bin/bash
BACKUP_DIR="$HOME/Bot_Alternance/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Sauvegarde PostgreSQL
pg_dump -h localhost -U alternance_user alternance_bot > "$BACKUP_DIR/alternance_bot_$DATE.sql"

# Garder seulement les 7 dernières sauvegardes
find "$BACKUP_DIR" -name "alternance_bot_*.sql" -mtime +7 -delete

# Logs
echo "$(date): Sauvegarde terminée - alternance_bot_$DATE.sql" >> "$BACKUP_DIR/backup.log"
EOF

chmod +x "$HOME/backup_bot.sh"

# Ajouter au cron
(crontab -l 2>/dev/null; echo "0 2 * * * $HOME/backup_bot.sh") | crontab -

echo "✅ Système de sauvegarde configuré"

# Configuration du service systemd
echo "⚙️  Configuration du service systemd..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=Bot Discord Alternance
After=network.target postgresql.service
Requires=postgresql.service
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=10
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python run.py
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

echo "✅ Service systemd configuré"

# Configuration de base .env si n'existe pas
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "📝 Création du fichier .env par défaut..."
    cat > "$PROJECT_DIR/.env" << EOF
# Discord - À CONFIGURER
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_WEBHOOK_URL=your_webhook_url_here
DISCORD_GUILD_ID=your_server_id_here

# PostgreSQL VPS
DATABASE_URL=postgresql://alternance_user:ChangeMeInProduction!@localhost:5432/alternance_bot
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alternance_bot
DB_USER=alternance_user
DB_PASSWORD=ChangeMeInProduction!

# Configuration scraping
SCRAPING_INTERVAL=300
MAX_CONCURRENT_REQUESTS=3
REQUEST_DELAY=3

# Logs
LOG_LEVEL=INFO
LOG_FILE=$PROJECT_DIR/logs/bot.log
EOF
    echo "⚠️  IMPORTANT: Éditez le fichier .env avec vos vrais tokens Discord!"
fi

# Script de gestion
cat > "$PROJECT_DIR/manage.sh" << 'EOF'
#!/bin/bash
# Script de gestion du bot

case "$1" in
    start)
        sudo systemctl start alternance-bot
        echo "Bot démarré"
        ;;
    stop)
        sudo systemctl stop alternance-bot
        echo "Bot arrêté"
        ;;
    restart)
        sudo systemctl restart alternance-bot
        echo "Bot redémarré"
        ;;
    status)
        sudo systemctl status alternance-bot
        ;;
    logs)
        sudo journalctl -u alternance-bot -f
        ;;
    update)
        echo "Mise à jour du bot..."
        sudo systemctl stop alternance-bot
        source venv/bin/activate
        pip install -r requirements.txt
        python scripts/setup_database.py
        sudo systemctl start alternance-bot
        echo "Mise à jour terminée"
        ;;
    backup)
        ~/backup_bot.sh
        echo "Sauvegarde effectuée"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|update|backup}"
        exit 1
        ;;
esac
EOF

chmod +x "$PROJECT_DIR/manage.sh"

echo ""
echo "🎉 Déploiement terminé avec succès!"
echo "================================================"
echo ""
echo "📋 Prochaines étapes:"
echo "1. Copiez votre code dans: $PROJECT_DIR"
echo "2. Éditez le fichier .env avec vos tokens Discord"
echo "3. Installez les dépendances Python:"
echo "   cd $PROJECT_DIR && source venv/bin/activate && pip install -r requirements.txt"
echo "4. Initialisez la base de données:"
echo "   python scripts/setup_database.py"
echo "5. Testez le bot:"
echo "   python scripts/test_scrapers.py --system"
echo "6. Démarrez le service:"
echo "   ./manage.sh start"
echo ""
echo "🔧 Commandes utiles:"
echo "  ./manage.sh start|stop|restart|status|logs"
echo "  ./manage.sh update  # Met à jour le bot"
echo "  ./manage.sh backup  # Sauvegarde manuelle"
echo ""
echo "📁 Fichiers importants:"
echo "  Configuration: $PROJECT_DIR/.env"
echo "  Logs: $PROJECT_DIR/logs/bot.log"
echo "  Service: sudo systemctl status alternance-bot"
echo ""
echo "⚠️  N'oubliez pas de changer le mot de passe PostgreSQL par défaut!"
EOF