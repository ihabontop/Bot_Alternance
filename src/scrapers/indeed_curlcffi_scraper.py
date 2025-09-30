"""
Scraper Indeed avec curl_cffi pour contourner les protections anti-bot
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests
from .base import BaseScraper

class IndeedCurlCffiScraper(BaseScraper):
    """Scraper Indeed utilisant curl_cffi pour imiter parfaitement Chrome"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.site_name = "indeed_curlcffi"

    async def search_jobs(self, metier: Dict, location: str = None) -> List[Dict]:
        """Recherche des offres sur Indeed avec curl_cffi"""
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

        self.logger.info(f"Indeed CurlCffi: {len(unique_jobs)} offres trouvées pour {metier['nom']}")
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

            # Faire la requête avec curl_cffi (en thread pour ne pas bloquer)
            html = await asyncio.to_thread(self._fetch_with_curlcffi, url)

            if not html:
                self.logger.warning(f"Pas de contenu reçu pour {url}")
                return jobs

            # Parser avec BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Trouver les cartes d'offres
            job_cards = soup.select('div.job_seen_beacon, div[data-jk], td.resultContent')

            self.logger.info(f"Trouvé {len(job_cards)} cartes d'offres")

            for card in job_cards[:10]:  # Limiter à 10 offres par recherche
                job = self._parse_job_card(card, metier)
                if job and self._is_valid_job(job):
                    jobs.append(job)

        except Exception as e:
            self.logger.error(f"Erreur scraping Indeed CurlCffi: {e}")

        return jobs

    def _fetch_with_curlcffi(self, url: str) -> Optional[str]:
        """Fait une requête avec curl_cffi (méthode synchrone)"""
        try:
            # Utiliser impersonate pour simuler Chrome 120
            response = requests.get(
                url,
                impersonate="chrome120",
                timeout=30,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Referer": "https://fr.indeed.com/",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Upgrade-Insecure-Requests": "1"
                }
            )

            if response.status_code == 200:
                self.logger.info(f"✅ Succès! Status {response.status_code}")
                return response.text
            else:
                self.logger.warning(f"Status code {response.status_code} pour {url}")
                return None
        except Exception as e:
            self.logger.error(f"Erreur curl_cffi: {e}")
            return None

    def _parse_job_card(self, card, metier: Dict) -> Optional[Dict]:
        """Parse une carte d'offre Indeed"""
        try:
            # Récupérer le job ID
            job_id = card.get('data-jk')
            if not job_id:
                # Essayer de trouver un élément enfant avec data-jk
                link = card.select_one('a[data-jk]')
                if link:
                    job_id = link.get('data-jk')

            if not job_id:
                return None

            # Titre
            title_elem = card.select_one('h2.jobTitle span[title], h2.jobTitle a span')
            titre = title_elem.get_text(strip=True) if title_elem else ""

            if not titre:
                return None

            # Entreprise
            company_elem = card.select_one('span[data-testid="company-name"], span.companyName')
            entreprise = company_elem.get_text(strip=True) if company_elem else "Non précisé"

            # Localisation
            location_elem = card.select_one('div[data-testid="text-location"], div.companyLocation')
            lieu = location_elem.get_text(strip=True) if location_elem else ""

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