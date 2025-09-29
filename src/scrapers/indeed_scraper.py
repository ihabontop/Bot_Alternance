"""
Scraper pour Indeed France
"""

import json
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode
from .base import BaseScraper

class IndeedScraper(BaseScraper):
    """Scraper spécialisé pour Indeed France"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.site_name = "indeed"
        self.search_path = config.get('search_path', '/jobs')

    async def search_jobs(self, metier: Dict, location: str = None) -> List[Dict]:
        """Recherche des offres sur Indeed"""
        jobs = []
        keywords = self._build_keywords(metier)

        for keyword in keywords[:3]:  # Limiter à 3 recherches par métier
            page_jobs = await self._search_keyword(keyword, metier, location)
            jobs.extend(page_jobs)

            # Délai entre les recherches
            await asyncio.sleep(2)

        # Dédupliquer par URL
        unique_jobs = {}
        for job in jobs:
            if job['url'] not in unique_jobs:
                unique_jobs[job['url']] = job

        self.logger.info(f"Indeed: {len(unique_jobs)} offres trouvées pour {metier['nom']}")
        return list(unique_jobs.values())

    async def _search_keyword(self, keyword: str, metier: Dict, location: str) -> List[Dict]:
        """Effectue une recherche pour un mot-clé spécifique"""
        jobs = []
        max_pages = self.config.get('max_pages', 3)

        for page in range(max_pages):
            params = {
                'q': f"{keyword} alternance",
                'l': location or 'France',
                'fromage': '1',  # Dernières 24h
                'sort': 'date',
                'start': page * 10
            }

            url = f"{self.base_url}{self.search_path}"
            html = await self.fetch_page(url, params)

            if not html:
                break

            page_jobs = self._parse_search_page(html, metier)
            jobs.extend(page_jobs)

            # Arrêter si moins de 10 résultats (dernière page)
            if len(page_jobs) < 10:
                break

            await asyncio.sleep(1)  # Délai entre les pages

        return jobs

    def _parse_search_page(self, html: str, metier: Dict) -> List[Dict]:
        """Parse une page de résultats Indeed"""
        jobs = []
        soup = self.get_soup(html)

        # Indeed utilise différents sélecteurs selon la version
        job_cards = soup.find_all(['div'], {'data-jk': True}) or \
                   soup.find_all(['a'], {'data-jk': True})

        for card in job_cards:
            job = self._parse_job_card(card, metier)
            if job and self._is_valid_job(job):
                jobs.append(job)

        return jobs

    def _parse_job_card(self, card, metier: Dict) -> Optional[Dict]:
        """Parse une carte d'offre Indeed"""
        try:
            # Extraction des données de base
            job_id = card.get('data-jk')
            if not job_id:
                return None

            # Titre
            title_elem = card.find(['h2', 'h3', 'a'], {'data-testid': 'job-title'}) or \
                        card.find(['span', 'a'], title=True)
            titre = self.clean_text(title_elem.get_text()) if title_elem else ""

            # Entreprise
            company_elem = card.find(['span', 'a'], {'data-testid': 'company-name'}) or \
                          card.find(['span'], class_=lambda x: x and 'company' in str(x).lower())
            entreprise = self.clean_text(company_elem.get_text()) if company_elem else ""

            # Localisation
            location_elem = card.find(['div'], {'data-testid': 'job-location'}) or \
                           card.find(['span'], class_=lambda x: x and 'location' in str(x).lower())
            lieu = self.clean_text(location_elem.get_text()) if location_elem else ""

            # Description courte
            summary_elem = card.find(['div'], {'data-testid': 'job-snippet'})
            description = self.clean_text(summary_elem.get_text()) if summary_elem else ""

            # Salaire
            salary_elem = card.find(['span'], class_=lambda x: x and 'salary' in str(x).lower())
            salaire = self.extract_salary(salary_elem.get_text()) if salary_elem else None

            # URL
            url = f"{self.base_url}/viewjob?jk={job_id}"

            # Vérifier que c'est bien une alternance
            if not self.is_alternance_related(titre, description):
                return None

            return self.build_job_dict(
                titre=titre,
                entreprise=entreprise,
                description=description,
                lieu=lieu,
                salaire=salaire,
                url=url,
                source_site=self.site_name,
                external_id=job_id,
                date_publication=datetime.now(),
                metier_id=metier.get('id')
            )

        except Exception as e:
            self.logger.error(f"Erreur parsing Indeed job card: {e}")
            return None

    def _build_keywords(self, metier: Dict) -> List[str]:
        """Construit la liste des mots-clés de recherche"""
        keywords = [metier['nom']]

        # Ajouter les mots-clés depuis la configuration
        if metier.get('keywords'):
            try:
                metier_keywords = json.loads(metier['keywords'])
                keywords.extend(metier_keywords[:5])  # Limiter à 5 mots-clés
            except (json.JSONDecodeError, TypeError):
                pass

        return keywords

    def _is_valid_job(self, job: Dict) -> bool:
        """Valide qu'une offre est acceptable"""
        # Filtres de base
        if not job.get('titre') or not job.get('url'):
            return False

        # Éviter les mots-clés indésirables
        exclude_keywords = ['stage', 'bénévole', 'freelance']
        title_lower = job['titre'].lower()

        for exclude in exclude_keywords:
            if exclude in title_lower:
                return False

        return True

    def parse_job_details(self, job_element) -> Optional[Dict]:
        """Parse les détails complets d'une offre (pour usage futur)"""
        # Cette méthode pourrait être utilisée pour récupérer plus de détails
        # en visitant la page individuelle de chaque offre
        pass