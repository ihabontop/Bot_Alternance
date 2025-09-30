"""
Scraper de base et utilitaires communs
"""

import asyncio
import aiohttp
import logging
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class BaseScraper(ABC):
    """Classe de base pour tous les scrapers"""

    def __init__(self, config: Dict):
        self.config = config
        self.session = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_url = config.get('base_url', '')

        # Headers plus réalistes pour imiter un vrai navigateur
        self.headers = {
            'User-Agent': config.get('user_agent',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        }

    async def __aenter__(self):
        """Contexte async pour gérer la session HTTP"""
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            connector=connector,
            timeout=timeout
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ferme la session HTTP"""
        if self.session:
            await self.session.close()

    @abstractmethod
    async def search_jobs(self, metier: Dict, location: str = None) -> List[Dict]:
        """
        Recherche des offres d'emploi pour un métier donné

        Args:
            metier: Dictionnaire contenant les infos du métier (nom, keywords, etc.)
            location: Localisation de recherche (optionnel)

        Returns:
            Liste des offres trouvées
        """
        pass

    @abstractmethod
    def parse_job_details(self, job_element) -> Optional[Dict]:
        """
        Parse les détails d'une offre depuis l'élément HTML/JSON

        Returns:
            Dictionnaire avec les détails de l'offre ou None si erreur
        """
        pass

    async def fetch_page(self, url: str, params: Dict = None, retry: int = 3) -> Optional[str]:
        """Récupère le contenu HTML d'une page avec retry et délai humain"""
        for attempt in range(retry):
            try:
                # Délai aléatoire entre 1 et 3 secondes pour simuler comportement humain
                if attempt > 0:
                    await asyncio.sleep(random.uniform(2, 5))

                async with self.session.get(url, params=params, allow_redirects=True) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 403 and attempt < retry - 1:
                        self.logger.warning(f"HTTP 403 pour {url}, tentative {attempt + 1}/{retry}")
                        await asyncio.sleep(random.uniform(3, 6))  # Attendre plus longtemps avant retry
                        continue
                    else:
                        self.logger.warning(f"HTTP {response.status} pour {url}")
                        return None
            except Exception as e:
                if attempt < retry - 1:
                    self.logger.warning(f"Erreur fetch {url} (tentative {attempt + 1}/{retry}): {e}")
                    await asyncio.sleep(random.uniform(2, 4))
                else:
                    self.logger.error(f"Erreur finale fetch {url}: {e}")
                    return None
        return None

    async def fetch_json(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Récupère des données JSON depuis une API"""
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.warning(f"HTTP {response.status} pour {url}")
                    return None
        except Exception as e:
            self.logger.error(f"Erreur lors du fetch JSON {url}: {e}")
            return None

    def get_soup(self, html: str) -> BeautifulSoup:
        """Crée un objet BeautifulSoup depuis du HTML"""
        return BeautifulSoup(html, 'html.parser')

    def clean_text(self, text: str) -> str:
        """Nettoie et normalise un texte"""
        if not text:
            return ""
        return ' '.join(text.strip().split())

    def extract_salary(self, text: str) -> Optional[str]:
        """Extrait le salaire depuis un texte"""
        import re
        if not text:
            return None

        # Patterns pour détecter les salaires
        salary_patterns = [
            r'(\d+(?:\s?\d+)*)\s*€',
            r'(\d+(?:\s?\d+)*)\s*euros?',
            r'(\d+k?\s*-\s*\d+k?)\s*€',
            r'(\d+)\s*à\s*(\d+)\s*€'
        ]

        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def is_alternance_related(self, title: str, description: str = "") -> bool:
        """Vérifie si une offre est liée à l'alternance"""
        alternance_keywords = [
            'alternance', 'apprentissage', 'apprenti', 'contrat pro',
            'contrat professionnel', 'formation', 'étudiant', 'bts', 'master'
        ]

        text_to_check = f"{title} {description}".lower()
        return any(keyword in text_to_check for keyword in alternance_keywords)

    def build_job_dict(self, **kwargs) -> Dict:
        """Construit un dictionnaire d'offre standardisé"""
        return {
            'titre': kwargs.get('titre', ''),
            'entreprise': kwargs.get('entreprise', ''),
            'description': kwargs.get('description', ''),
            'lieu': kwargs.get('lieu', ''),
            'salaire': kwargs.get('salaire'),
            'url': kwargs.get('url', ''),
            'source_site': kwargs.get('source_site', ''),
            'external_id': kwargs.get('external_id'),
            'date_publication': kwargs.get('date_publication', datetime.now()),
            'metier_id': kwargs.get('metier_id')
        }

    def get_absolute_url(self, relative_url: str) -> str:
        """Convertit une URL relative en URL absolue"""
        if relative_url.startswith('http'):
            return relative_url
        return urljoin(self.base_url, relative_url)

    async def human_delay(self, min_seconds: float = 1, max_seconds: float = 3):
        """Ajoute un délai aléatoire pour simuler un comportement humain"""
        await asyncio.sleep(random.uniform(min_seconds, max_seconds))

    def _build_keywords(self, metier: Dict) -> List[str]:
        """Construit la liste des mots-clés depuis le métier"""
        import json
        keywords_str = metier.get('keywords', '[]')
        try:
            keywords = json.loads(keywords_str) if isinstance(keywords_str, str) else keywords_str
            return keywords[:5]  # Limiter à 5 mots-clés
        except:
            return [metier['nom']]

    def _is_valid_job(self, job: Dict) -> bool:
        """Vérifie si une offre est valide"""
        return bool(
            job.get('titre') and
            job.get('url') and
            len(job.get('titre', '')) > 5
        )