# Bot Discord - Monitoring d'Alternances

Bot Discord intelligent pour le monitoring en temps réel des offres d'alternance sur plusieurs plateformes de recrutement.

## Fonctionnalités

- 🔍 **Monitoring multi-sites** : Indeed, LinkedIn, Welcome to the Jungle, HelloWork, La Bonne Alternance
- 🎯 **Personnalisation par métier** : Les étudiants choisissent leurs métiers cibles
- ⚡ **Notifications instantanées** : Alertes Discord en temps réel via webhook
- 🏷️ **Gestion par rôles** : Notifications ciblées selon les rôles Discord
- 🗄️ **Base de données PostgreSQL** : Stockage persistant des offres et préférences
- 🤖 **Anti-doublons** : Évite les notifications répétitives

## Structure du projet

```
src/
├── database/          # Modèles et gestion PostgreSQL
├── scrapers/          # Modules de scraping par site
├── discord_bot/       # Bot Discord et commandes
├── config/           # Configuration et paramètres
└── utils/            # Utilitaires et helpers
```

## Installation

### Installation locale
1. Cloner le repository
2. Installer les dépendances : `pip install -r requirements.txt`
3. Configurer PostgreSQL et créer la base de données
4. Configurer le fichier `.env`
5. Lancer le bot : `python run.py`

### Déploiement sur VPS Debian 13
1. Configurez `scripts/transfer_to_vps.bat` avec vos informations VPS
2. Transférez : `scripts/transfer_to_vps.bat`
3. Sur le VPS : `chmod +x scripts/deploy_vps.sh && ./scripts/deploy_vps.sh`
4. Configurez `.env` et démarrez : `./manage.sh start`

Voir [docs/VPS_DEBIAN_SETUP.md](docs/VPS_DEBIAN_SETUP.md) pour les détails.

## Configuration requise

- Python 3.8+
- PostgreSQL 12+
- Token Bot Discord
- Webhook Discord configuré