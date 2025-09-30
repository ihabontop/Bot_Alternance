"""
Scraper Indeed qui utilise l'API Selenium sur le VPS
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime
from .base import BaseScraper

class IndeedVPSScraper(BaseScraper):
    """Scraper Indeed utilisant l'API Selenium sur le VPS"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.site_name = "indeed_vps"
        self.vps_api_url = config.get('vps_api_url', 'http://45.158.77.193:5000')

    async def search_jobs(self, metier: Dict, location: str = None) -> List[Dict]:
        """Recherche des offres sur Indeed via l'API VPS"""
        jobs = []
        keywords = self._build_keywords(metier)

        # Prendre les 3 premiers mots-clés (augmenté de 2 à 3)
        for keyword in keywords[:3]:
            page_jobs = await self._search_keyword(keyword, metier, location)
            jobs.extend(page_jobs)
            await asyncio.sleep(3)  # Délai entre recherches

        # Dédupliquer
        unique_jobs = {}
        for job in jobs:
            if job['url'] not in unique_jobs:
                unique_jobs[job['url']] = job

        self.logger.info(f"Indeed VPS: {len(unique_jobs)} offres trouvées pour {metier['nom']}")
        return list(unique_jobs.values())

    async def _search_keyword(self, keyword: str, metier: Dict, location: str) -> List[Dict]:
        """Recherche avec un mot-clé spécifique via l'API VPS"""
        jobs = []

        try:
            # Appeler l'API du VPS
            location_query = location or "France"

            self.logger.info(f"Appel API VPS pour: {keyword}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.vps_api_url}/scrape/indeed",
                    json={
                        'keyword': keyword,
                        'location': location_query,
                        'max_jobs': 50,  # Augmenté à 50 offres
                        'max_age_minutes': 60  # Offres de moins d'1h
                    },
                    timeout=aiohttp.ClientTimeout(total=120)  # Timeout augmenté pour plusieurs pages
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get('success'):
                            api_jobs = data.get('jobs', [])
                            self.logger.info(f"API VPS a retourné {len(api_jobs)} offres")

                            # Convertir les jobs de l'API au format attendu
                            for api_job in api_jobs:
                                job = self._convert_api_job(api_job, metier)
                                if job and self._is_valid_job(job):
                                    jobs.append(job)
                        else:
                            self.logger.error(f"Erreur API VPS: {data.get('error')}")
                    else:
                        self.logger.error(f"Status {response.status} de l'API VPS")

        except asyncio.TimeoutError:
            self.logger.error(f"Timeout lors de l'appel à l'API VPS")
        except Exception as e:
            self.logger.error(f"Erreur appel API VPS: {e}")

        return jobs

    def _convert_api_job(self, api_job: Dict, metier: Dict) -> Optional[Dict]:
        """Convertit un job de l'API au format du bot"""
        try:
            return self.build_job_dict(
                titre=api_job.get('titre', ''),
                entreprise=api_job.get('entreprise', 'Non précisé'),
                description="",
                lieu=api_job.get('lieu', ''),
                salaire=None,
                url=api_job.get('url', ''),
                source_site=self.site_name,
                external_id=api_job.get('external_id', ''),
                date_publication=datetime.now(),
                metier_id=metier.get('id')
            )
        except Exception as e:
            self.logger.error(f"Erreur conversion job API: {e}")
            return None

    def parse_job_details(self, job_element) -> Optional[Dict]:
        """Non utilisé pour ce scraper"""
        pass