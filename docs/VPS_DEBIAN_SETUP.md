# Configuration VPS Debian 13 - Bot Alternance

## 1. Installation PostgreSQL sur Debian 13

### Mise à jour du système
```bash
sudo apt update && sudo apt upgrade -y
```

### Installation PostgreSQL
```bash
# Installation de PostgreSQL et outils
sudo apt install postgresql postgresql-contrib python3-dev libpq-dev -y

# Démarrer et activer PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Vérifier le statut
sudo systemctl status postgresql
```

### Configuration PostgreSQL
```bash
# Se connecter en tant que postgres
sudo -u postgres psql

# Dans psql, créer l'utilisateur et la base
CREATE USER alternance_user WITH PASSWORD 'mot_de_passe_securise';
CREATE DATABASE alternance_bot OWNER alternance_user;
GRANT ALL PRIVILEGES ON DATABASE alternance_bot TO alternance_user;

# Quitter psql
\q
```

### Configuration sécurisée
```bash
# Éditer pg_hba.conf pour autoriser les connexions
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Ajouter cette ligne pour autoriser l'utilisateur (remplacer par votre IP locale si nécessaire)
host    alternance_bot    alternance_user    0.0.0.0/0    md5

# Éditer postgresql.conf pour écouter sur toutes les interfaces
sudo nano /etc/postgresql/*/main/postgresql.conf

# Décommenter et modifier cette ligne :
listen_addresses = '*'

# Redémarrer PostgreSQL
sudo systemctl restart postgresql
```

### Firewall (UFW)
```bash
# Installer et configurer UFW
sudo apt install ufw -y

# Autoriser SSH
sudo ufw allow 22

# Autoriser PostgreSQL (seulement depuis votre IP locale)
sudo ufw allow from 90.90.189.126 to any port 5432

# Activer le firewall
sudo ufw enable

# Vérifier le statut
sudo ufw status
```

## 2. Installation Python et dépendances

### Installation Python 3.11+
```bash
# Python 3.11 devrait être inclus dans Debian 13
sudo apt install python3 python3-pip python3-venv -y

# Vérifier la version
python3 --version
```

### Installation Git
```bash
sudo apt install git -y
```

## 3. Déploiement du bot sur le VPS

### Cloner le projet
```bash
cd /home/votre_utilisateur
git clone https://github.com/ihabontop/Bot_Alternance.git
cd Bot_Alternance
```

### Environnement virtuel
```bash
# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### Configuration
```bash
# Copier et éditer la configuration
cp .env.example .env
nano .env
```

Configuration `.env` pour VPS :
```env
# Discord
DISCORD_BOT_TOKEN=votre_token_bot
DISCORD_WEBHOOK_URL=votre_webhook_url
DISCORD_GUILD_ID=votre_guild_id

# PostgreSQL VPS
DATABASE_URL=postgresql://alternance_user:mot_de_passe_securise@localhost:5432/alternance_bot
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alternance_bot
DB_USER=alternance_user
DB_PASSWORD=mot_de_passe_securise

# Configuration scraping
SCRAPING_INTERVAL=300
MAX_CONCURRENT_REQUESTS=3
REQUEST_DELAY=3

# Logs
LOG_LEVEL=INFO
LOG_FILE=/home/votre_utilisateur/Bot_Alternance/logs/bot.log
```

### Initialisation de la base de données
```bash
# Créer les dossiers nécessaires
mkdir -p logs data

# Initialiser la base de données
python scripts/setup_database.py

# Tester les scrapers
python scripts/test_scrapers.py --system
```

## 4. Service systemd (lancement automatique)

### Créer le service
```bash
sudo nano /etc/systemd/system/alternance-bot.service
```

Contenu du fichier service :
```ini
[Unit]
Description=Bot Discord Alternance
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=votre_utilisateur
Group=votre_utilisateur
WorkingDirectory=/home/votre_utilisateur/Bot_Alternance
Environment=PATH=/home/votre_utilisateur/Bot_Alternance/venv/bin
ExecStart=/home/votre_utilisateur/Bot_Alternance/venv/bin/python run.py
Restart=always
RestartSec=10

# Logs
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=alternance-bot

[Install]
WantedBy=multi-user.target
```

### Activer le service
```bash
# Recharger systemd
sudo systemctl daemon-reload

# Activer le service au démarrage
sudo systemctl enable alternance-bot

# Démarrer le service
sudo systemctl start alternance-bot

# Vérifier le statut
sudo systemctl status alternance-bot

# Voir les logs
sudo journalctl -u alternance-bot -f
```

## 5. Monitoring et maintenance

### Scripts de maintenance
```bash
# Créer un script de sauvegarde quotidienne
nano ~/backup_db.sh
```

Script de sauvegarde :
```bash
#!/bin/bash
BACKUP_DIR="/home/votre_utilisateur/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Sauvegarde PostgreSQL
pg_dump -h localhost -U alternance_user alternance_bot > $BACKUP_DIR/alternance_bot_$DATE.sql

# Garder seulement les 7 dernières sauvegardes
find $BACKUP_DIR -name "alternance_bot_*.sql" -mtime +7 -delete

echo "Sauvegarde terminée: alternance_bot_$DATE.sql"
```

```bash
# Rendre le script exécutable
chmod +x ~/backup_db.sh

# Ajouter au cron pour exécution quotidienne
crontab -e
# Ajouter cette ligne :
0 2 * * * /home/votre_utilisateur/backup_db.sh
```

### Commandes utiles
```bash
# Status du service
sudo systemctl status alternance-bot

# Redémarrer le bot
sudo systemctl restart alternance-bot

# Voir les logs en temps réel
sudo journalctl -u alternance-bot -f

# Logs du bot spécifiques
tail -f /home/votre_utilisateur/Bot_Alternance/logs/bot.log

# Mise à jour du code
cd /home/votre_utilisateur/Bot_Alternance
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart alternance-bot
```

## 6. Sécurité supplémentaire

### SSL/TLS (optionnel pour PostgreSQL)
```bash
# Si vous voulez chiffrer les connexions PostgreSQL
sudo nano /etc/postgresql/*/main/postgresql.conf
# Ajouter :
ssl = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'
```

### Fail2ban (protection contre brute force)
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Mise à jour automatique des paquets de sécurité
```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Configuration locale (.env pour développement)

Pour tester depuis votre machine locale avec la DB sur le VPS :

```env
# Dans votre .env local
DATABASE_URL=postgresql://alternance_user:mot_de_passe_securise@IP_DE_VOTRE_VPS:5432/alternance_bot
DB_HOST=IP_DE_VOTRE_VPS
DB_PORT=5432
DB_NAME=alternance_bot
DB_USER=alternance_user
DB_PASSWORD=mot_de_passe_securise
```

N'oubliez pas d'autoriser votre IP locale dans le firewall du VPS :
```bash
sudo ufw allow from VOTRE_IP_LOCALE to any port 5432
```