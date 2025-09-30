"""
Scraper Indeed avec Selenium pour contourner les protections anti-bot
"""

import asyncio
import time
from typing import List, Dict, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from .base import BaseScraper

class IndeedSeleniumScraper(BaseScraper):
    """Scraper Indeed utilisant Selenium"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.site_name = "indeed_selenium"
        self.driver = None

    def _init_driver(self):
        """Initialise le driver Selenium Edge"""
        if self.driver:
            return

        edge_options = Options()
        edge_options.add_argument('--headless')  # Mode sans interface
        edge_options.add_argument('--no-sandbox')
        edge_options.add_argument('--disable-dev-shm-usage')
        edge_options.add_argument('--disable-blink-features=AutomationControlled')
        edge_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0')

        service = Service(EdgeChromiumDriverManager().install())
        self.driver = webdriver.Edge(service=service, options=edge_options)
        self.logger.info("Driver Edge initialisé")

    async def __aenter__(self):
        """Initialise le driver au lieu de la session HTTP"""
        self._init_driver()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ferme le driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    async def search_jobs(self, metier: Dict, location: str = None) -> List[Dict]:
        """Recherche des offres sur Indeed avec Selenium"""
        jobs = []
        keywords = self._build_keywords(metier)

        # Prendre les 2 premiers mots-clés
        for keyword in keywords[:2]:
            page_jobs = await self._search_keyword(keyword, metier, location)
            jobs.extend(page_jobs)
            await asyncio.sleep(3)  # Délai entre recherches

        # Dédupliquer
        unique_jobs = {}
        for job in jobs:
            if job['url'] not in unique_jobs:
                unique_jobs[job['url']] = job

        self.logger.info(f"Indeed Selenium: {len(unique_jobs)} offres trouvées pour {metier['nom']}")
        return list(unique_jobs.values())

    async def _search_keyword(self, keyword: str, metier: Dict, location: str) -> List[Dict]:
        """Recherche avec un mot-clé spécifique"""
        jobs = []

        try:
            # Construire l'URL de recherche
            search_query = f"{keyword} alternance"
            location_query = location or "France"
            url = f"https://fr.indeed.com/jobs?q={search_query}&l={location_query}&fromage=7&sort=date"

            self.logger.info(f"Scraping Indeed: {url}")

            # Charger la page
            await asyncio.to_thread(self.driver.get, url)
            await asyncio.sleep(2)  # Attendre le chargement

            # Extraire les offres
            job_cards = await asyncio.to_thread(
                self.driver.find_elements,
                By.CSS_SELECTOR,
                'div.job_seen_beacon, div[data-jk], a[data-jk]'
            )

            self.logger.info(f"Trouvé {len(job_cards)} cartes d'offres")

            for card in job_cards[:10]:  # Limiter à 10 offres par recherche
                job = await self._parse_job_card(card, metier)
                if job and self._is_valid_job(job):
                    jobs.append(job)

        except Exception as e:
            self.logger.error(f"Erreur scraping Indeed Selenium: {e}")

        return jobs

    async def _parse_job_card(self, card, metier: Dict) -> Optional[Dict]:
        """Parse une carte d'offre Indeed"""
        try:
            # Récupérer le job ID
            job_id = await asyncio.to_thread(card.get_attribute, 'data-jk')
            if not job_id:
                # Essayer de trouver un élément enfant avec data-jk
                try:
                    link = await asyncio.to_thread(
                        card.find_element,
                        By.CSS_SELECTOR,
                        'a[data-jk]'
                    )
                    job_id = await asyncio.to_thread(link.get_attribute, 'data-jk')
                except:
                    return None

            if not job_id:
                return None

            # Titre
            try:
                title_elem = await asyncio.to_thread(
                    card.find_element,
                    By.CSS_SELECTOR,
                    'h2.jobTitle, span[title]'
                )
                titre = await asyncio.to_thread(title_elem.text.strip)
            except:
                titre = ""

            if not titre:
                return None

            # Entreprise
            try:
                company_elem = await asyncio.to_thread(
                    card.find_element,
                    By.CSS_SELECTOR,
                    'span[data-testid="company-name"], span.companyName'
                )
                entreprise = await asyncio.to_thread(company_elem.text.strip)
            except:
                entreprise = "Non précisé"

            # Localisation
            try:
                location_elem = await asyncio.to_thread(
                    card.find_element,
                    By.CSS_SELECTOR,
                    'div[data-testid="text-location"], div.companyLocation'
                )
                lieu = await asyncio.to_thread(location_elem.text.strip)
            except:
                lieu = ""

            # URL
            url = f"https://fr.indeed.com/viewjob?jk={job_id}"

            # Vérifier que c'est bien une alternance
            text_to_check = f"{titre}".lower()
            if not any(word in text_to_check for word in ['alternance', 'apprentissage', 'apprenti']):
                return None

            return self.build_job_dict(
                titre=titre,
                entreprise=entreprise,
                description="",
                lieu=lieu,
                salaire=None,
                url=url,
                source_site=self.site_name,
                external_id=job_id,
                date_publication=datetime.now(),
                metier_id=metier.get('id')
            )

        except Exception as e:
            self.logger.error(f"Erreur parsing carte Indeed: {e}")
            return None

    def parse_job_details(self, job_element) -> Optional[Dict]:
        """Non utilisé pour ce scraper"""
        pass