"""
Configuration du bot alternance
"""

import os
import yaml
from dataclasses import dataclass
from typing import Dict, List
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

@dataclass
class DatabaseConfig:
    """Configuration base de données"""
    url: str
    host: str
    port: int
    name: str
    user: str
    password: str

@dataclass
class DiscordConfig:
    """Configuration Discord"""
    bot_token: str
    webhook_url: str
    guild_id: str

@dataclass
class ScrapingConfig:
    """Configuration scraping"""
    interval: int  # Secondes
    max_concurrent_requests: int
    request_delay: int  # Secondes
    timeout: int  # Secondes
    user_agent: str

@dataclass
class LinkedInConfig:
    """Configuration LinkedIn (optionnelle)"""
    email: str
    password: str

class Settings:
    """Gestionnaire de configuration principal"""

    def __init__(self, config_file: str = None):
        self.config_file = config_file or "config/settings.yml"
        self._load_config()

    def _load_config(self):
        """Charge la configuration depuis les variables d'environnement et fichier YAML"""
        # Configuration base de données
        self.database = DatabaseConfig(
            url=os.getenv('DATABASE_URL', 'postgresql://localhost:5432/alternance_bot'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            name=os.getenv('DB_NAME', 'alternance_bot'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )

        # Configuration Discord
        self.discord = DiscordConfig(
            bot_token=os.getenv('DISCORD_BOT_TOKEN', ''),
            webhook_url=os.getenv('DISCORD_WEBHOOK_URL', ''),
            guild_id=os.getenv('DISCORD_GUILD_ID', '')
        )

        # Configuration scraping
        self.scraping = ScrapingConfig(
            interval=int(os.getenv('SCRAPING_INTERVAL', 300)),
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', 5)),
            request_delay=int(os.getenv('REQUEST_DELAY', 2)),
            timeout=int(os.getenv('REQUEST_TIMEOUT', 30)),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        # Configuration LinkedIn (optionnelle)
        linkedin_email = os.getenv('LINKEDIN_EMAIL')
        linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        if linkedin_email and linkedin_password:
            self.linkedin = LinkedInConfig(
                email=linkedin_email,
                password=linkedin_password
            )
        else:
            self.linkedin = None

        # Configuration des sites de scraping
        self.sites_config = {
            'indeed': {
                'enabled': True,
                'base_url': 'https://fr.indeed.com',
                'search_path': '/jobs',
                'params': {
                    'q': '{keywords} alternance',
                    'l': '{location}',
                    'fromage': '1',  # Dernières 24h
                    'sort': 'date'
                }
            },
            'welcometothejungle': {
                'enabled': True,
                'base_url': 'https://www.welcometothejungle.com',
                'search_path': '/fr/jobs',
                'params': {
                    'query': '{keywords} alternance',
                    'aroundQuery': '{location}',
                    'contractType': 'APPRENTICESHIP'
                }
            },
            'hellowork': {
                'enabled': True,
                'base_url': 'https://www.hellowork.com',
                'search_path': '/fr-fr/emploi/recherche.html',
                'params': {
                    'k': '{keywords} alternance',
                    'l': '{location}',
                    'date': '1'
                }
            },
            'labonnealternance': {
                'enabled': True,
                'base_url': 'https://labonnealternance.pole-emploi.fr',
                'api_url': 'https://labonnealternance.pole-emploi.fr/api/v1/jobs',
                'params': {
                    'romes': '{rome_codes}',
                    'longitude': '{longitude}',
                    'latitude': '{latitude}',
                    'radius': '30'
                }
            },
            'linkedin': {
                'enabled': bool(self.linkedin),
                'base_url': 'https://www.linkedin.com',
                'search_path': '/jobs/search/',
                'params': {
                    'keywords': '{keywords} alternance',
                    'location': '{location}',
                    'f_TPR': 'r86400',  # Dernières 24h
                    'sortBy': 'DD'  # Tri par date
                }
            }
        }

        # Charger configuration YAML si elle existe
        if os.path.exists(self.config_file):
            self._load_yaml_config()

    def _load_yaml_config(self):
        """Charge la configuration depuis un fichier YAML"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                yaml_config = yaml.safe_load(file)

            # Mettre à jour les configurations spécifiques
            if 'sites' in yaml_config:
                for site, config in yaml_config['sites'].items():
                    if site in self.sites_config:
                        self.sites_config[site].update(config)

            if 'scraping' in yaml_config:
                scraping_config = yaml_config['scraping']
                for key, value in scraping_config.items():
                    if hasattr(self.scraping, key):
                        setattr(self.scraping, key, value)

        except Exception as e:
            print(f"Erreur lors du chargement de {self.config_file}: {e}")

    @property
    def database_url(self) -> str:
        """URL de connexion à la base de données"""
        return self.database.url

    def get_site_config(self, site_name: str) -> Dict:
        """Récupère la configuration d'un site spécifique"""
        return self.sites_config.get(site_name, {})

    def is_site_enabled(self, site_name: str) -> bool:
        """Vérifie si un site est activé"""
        return self.sites_config.get(site_name, {}).get('enabled', False)

    def get_enabled_sites(self) -> List[str]:
        """Retourne la liste des sites activés"""
        return [
            site for site, config in self.sites_config.items()
            if config.get('enabled', False)
        ]

    def validate(self) -> bool:
        """Valide que la configuration est correcte"""
        errors = []

        # Vérifications obligatoires
        if not self.discord.bot_token:
            errors.append("DISCORD_BOT_TOKEN manquant")

        if not self.discord.webhook_url:
            errors.append("DISCORD_WEBHOOK_URL manquant")

        if not self.database.url:
            errors.append("DATABASE_URL manquant")

        if errors:
            print("Erreurs de configuration:")
            for error in errors:
                print(f"  - {error}")
            return False

        return True