# Guide d'Installation - Bot Discord Monitoring d'Alternances

## Prérequis

### 1. Python
- **Version**: Python 3.8 ou supérieur
- **Installation**: [Télécharger depuis python.org](https://python.org)
- **Vérification**: `python --version`

### 2. PostgreSQL
- **Version**: PostgreSQL 12 ou supérieur
- **Installation**: [Télécharger depuis postgresql.org](https://postgresql.org)
- **Configuration**: Créer une base de données pour le bot

### 3. Bot Discord
- Créer une application Discord sur [Discord Developer Portal](https://discord.com/developers/applications)
- Créer un bot et récupérer le token
- Configurer les permissions nécessaires (lecture/écriture messages)

### 4. Webhook Discord
- Créer un webhook dans votre serveur Discord
- Récupérer l'URL du webhook

## Installation Automatique (Windows)

```bash
# Cloner le projet
git clone [url-du-repo] Bot_Alternance
cd Bot_Alternance

# Lancer l'installation automatique
install.bat
```

## Installation Manuelle

### 1. Dépendances Python

```bash
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copier le fichier de configuration exemple
cp .env.example .env
```

Éditer le fichier `.env` avec vos paramètres :

```env
# Discord
DISCORD_BOT_TOKEN=votre_token_bot_discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/votre/webhook
DISCORD_GUILD_ID=id_de_votre_serveur

# PostgreSQL
DATABASE_URL=postgresql://username:password@localhost:5432/alternance_bot
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alternance_bot
DB_USER=votre_username
DB_PASSWORD=votre_password

# Monitoring (optionnel)
SCRAPING_INTERVAL=300
MAX_CONCURRENT_REQUESTS=5
```

### 3. Base de données

```bash
# Initialiser la base de données
python scripts/setup_database.py
```

### 4. Test des scrapers

```bash
# Tester tous les scrapers
python scripts/test_scrapers.py --all

# Tester le système complet
python scripts/test_scrapers.py --system
```

## Configuration Avancée

### Métiers personnalisés

Modifiez `config/settings.yml` pour ajouter vos propres métiers et mots-clés :

```yaml
metiers_keywords:
  "Data Scientist":
    - "data scientist"
    - "machine learning"
    - "python"
    - "tensorflow"
```

### Sites de scraping

Activez/désactivez les sites dans `config/settings.yml` :

```yaml
sites:
  indeed:
    enabled: true
  linkedin:
    enabled: false  # Nécessite configuration spéciale
```

## Lancement

### Lancement simple
```bash
python run.py
```

### Lancement avec logging détaillé
```bash
python src/main.py
```

### Lancement en arrière-plan (Linux/Mac)
```bash
nohup python run.py &
```

## Commandes Discord

Une fois le bot lancé, utilisez ces commandes sur votre serveur Discord :

### Commandes utilisateur
- `!alt help` - Aide
- `!alt metiers` - Liste des métiers
- `!alt subscribe <id>` - S'abonner à un métier
- `!alt mes-metiers` - Voir mes abonnements
- `!alt lieu <ville>` - Définir ma localisation
- `!alt recent` - Offres récentes

### Commandes admin
- `!alt status` - Statut du bot
- `!alt admin-stats` - Statistiques (admin seulement)

## Dépannage

### Erreur de connexion PostgreSQL
```bash
# Vérifier que PostgreSQL fonctionne
pg_isready -h localhost -p 5432

# Tester la connexion
psql -h localhost -U votre_username -d alternance_bot
```

### Bot Discord ne répond pas
1. Vérifier le token dans `.env`
2. Vérifier les permissions du bot sur le serveur
3. Vérifier les logs dans `logs/bot.log`

### Scrapers ne fonctionnent pas
```bash
# Tester individuellement
python scripts/test_scrapers.py indeed
python scripts/test_scrapers.py welcometothejungle
```

### Webhook ne fonctionne pas
1. Vérifier l'URL du webhook dans `.env`
2. Vérifier que le webhook existe toujours sur Discord
3. Tester : `python scripts/test_scrapers.py --system`

## Structure des fichiers

```
Bot_Alternance/
├── src/
│   ├── database/        # Modèles et gestion BDD
│   ├── scrapers/        # Scrapers par site
│   ├── discord_bot/     # Bot Discord
│   ├── config/          # Configuration
│   └── utils/           # Utilitaires
├── scripts/             # Scripts d'installation/test
├── config/              # Fichiers de configuration
├── logs/                # Fichiers de logs
└── data/                # Données temporaires
```

## Sécurité

⚠️ **Important** :
- Ne jamais committer le fichier `.env`
- Garder les tokens secrets
- Utiliser des mots de passe forts pour PostgreSQL
- Limiter les permissions du bot Discord au minimum nécessaire

## Support

- Vérifiez les logs dans `logs/bot.log`
- Utilisez les scripts de test pour diagnostiquer
- Consultez la documentation des APIs utilisées

## Mise à jour

```bash
# Sauvegarder la configuration
cp .env .env.backup

# Récupérer les dernières modifications
git pull

# Réinstaller les dépendances si nécessaire
pip install -r requirements.txt

# Mettre à jour la base de données si nécessaire
python scripts/setup_database.py
```