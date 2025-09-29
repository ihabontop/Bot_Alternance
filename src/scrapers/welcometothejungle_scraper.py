"""
Scraper pour Welcome to the Jungle France
"""

import json
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urlencode
from .base import BaseScraper

class WelcomeToTheJungleScraper(BaseScraper):
    """Scraper spécialisé pour Welcome to the Jungle France"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.site_name = "welcometothejungle"
        self.search_path = config.get('search_path', '/fr/jobs')

    async def search_jobs(self, metier: Dict, location: str = None) -> List[Dict]:
        """Recherche des offres sur Welcome to the Jungle"""
        jobs = []
        keywords = self._build_keywords(metier)

        for keyword in keywords[:2]:  # Limiter les recherches
            page_jobs = await self._search_keyword(keyword, metier, location)
            jobs.extend(page_jobs)
            await asyncio.sleep(2)

        # Dédupliquer
        unique_jobs = {}
        for job in jobs:
            if job['url'] not in unique_jobs:
                unique_jobs[job['url']] = job

        self.logger.info(f"WTTJ: {len(unique_jobs)} offres trouvées pour {metier['nom']}")
        return list(unique_jobs.values())

    async def _search_keyword(self, keyword: str, metier: Dict, location: str) -> List[Dict]:
        """Effectue une recherche pour un mot-clé spécifique"""
        jobs = []
        max_pages = self.config.get('max_pages', 3)

        for page in range(1, max_pages + 1):
            params = {
                'query': f"{keyword} alternance",
                'page': page,
                'contractType': 'APPRENTICESHIP,INTERNSHIP',
                'sortBy': 'date'
            }

            if location:
                params['aroundQuery'] = location

            url = f"{self.base_url}{self.search_path}"
            html = await self.fetch_page(url, params)

            if not html:
                break

            page_jobs = self._parse_search_page(html, metier)
            jobs.extend(page_jobs)

            # Arrêter si pas de résultats
            if len(page_jobs) == 0:
                break

            await asyncio.sleep(1)

        return jobs

    def _parse_search_page(self, html: str, metier: Dict) -> List[Dict]:
        """Parse une page de résultats WTTJ"""
        jobs = []
        soup = self.get_soup(html)

        # WTTJ peut utiliser différents sélecteurs
        job_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(
            cls in str(x).lower() for cls in ['job', 'offer', 'card']
        ))

        # Essayer aussi les liens directs vers les offres
        if not job_cards:
            job_links = soup.find_all('a', href=lambda x: x and '/jobs/' in str(x))
            job_cards = [link.find_parent() for link in job_links if link.find_parent()]

        for card in job_cards:
            job = self._parse_job_card(card, metier)
            if job and self._is_valid_job(job):
                jobs.append(job)

        return jobs

    def _parse_job_card(self, card, metier: Dict) -> Optional[Dict]:
        """Parse une carte d'offre WTTJ"""
        try:
            # Lien vers l'offre
            link_elem = card.find('a', href=lambda x: x and '/jobs/' in str(x))
            if not link_elem:
                return None

            job_url = self.get_absolute_url(link_elem['href'])
            external_id = job_url.split('/')[-1] if job_url else None

            # Titre
            title_elem = link_elem.find(['h2', 'h3']) or link_elem
            titre = self.clean_text(title_elem.get_text()) if title_elem else ""

            # Entreprise
            company_elem = card.find(['span', 'div'], class_=lambda x: x and 'company' in str(x).lower()) or \
                          card.find(['span', 'div'], class_=lambda x: x and 'organization' in str(x).lower())
            entreprise = self.clean_text(company_elem.get_text()) if company_elem else ""

            # Localisation
            location_elem = card.find(['span', 'div'], class_=lambda x: x and any(
                loc in str(x).lower() for loc in ['location', 'city', 'address']
            ))
            lieu = self.clean_text(location_elem.get_text()) if location_elem else ""

            # Description
            desc_elem = card.find(['p', 'div'], class_=lambda x: x and any(
                desc in str(x).lower() for desc in ['description', 'excerpt', 'summary']
            ))
            description = self.clean_text(desc_elem.get_text()) if desc_elem else ""

            # Salaire (souvent pas affiché sur WTTJ)
            salary_elem = card.find(['span'], class_=lambda x: x and 'salary' in str(x).lower())
            salaire = self.extract_salary(salary_elem.get_text()) if salary_elem else None

            # Vérifier que c'est une alternance
            if not self.is_alternance_related(titre, description):
                return None

            return self.build_job_dict(
                titre=titre,
                entreprise=entreprise,
                description=description,
                lieu=lieu,
                salaire=salaire,
                url=job_url,
                source_site=self.site_name,
                external_id=external_id,
                date_publication=datetime.now(),
                metier_id=metier.get('id')
            )

        except Exception as e:
            self.logger.error(f"Erreur parsing WTTJ job card: {e}")
            return None

    def _build_keywords(self, metier: Dict) -> List[str]:
        """Construit la liste des mots-clés de recherche"""
        keywords = [metier['nom']]

        if metier.get('keywords'):
            try:
                metier_keywords = json.loads(metier['keywords'])
                keywords.extend(metier_keywords[:3])
            except (json.JSONDecodeError, TypeError):
                pass

        return keywords

    def _is_valid_job(self, job: Dict) -> bool:
        """Valide qu'une offre est acceptable"""
        if not job.get('titre') or not job.get('url'):
            return False

        # Filtres spécifiques à WTTJ
        exclude_keywords = ['stage non rémunéré', 'bénévole']
        title_desc_lower = f"{job.get('titre', '')} {job.get('description', '')}".lower()

        for exclude in exclude_keywords:
            if exclude in title_desc_lower:
                return False

        return True

    def parse_job_details(self, job_element) -> Optional[Dict]:
        """Parse les détails complets d'une offre"""
        # Pourrait être implémenté pour récupérer plus de détails
        pass