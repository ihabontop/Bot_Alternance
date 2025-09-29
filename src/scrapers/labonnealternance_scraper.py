"""
Scraper pour La Bonne Alternance (API Pôle Emploi)
"""

import json
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from .base import BaseScraper

class LaBonneAlternanceScraper(BaseScraper):
    """Scraper utilisant l'API de La Bonne Alternance"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.site_name = "labonnealternance"
        self.api_url = config.get('api_url', 'https://labonnealternance.pole-emploi.fr/api/v1/jobs')

    async def search_jobs(self, metier: Dict, location: str = None) -> List[Dict]:
        """Recherche via l'API La Bonne Alternance"""
        jobs = []

        # Utiliser les codes ROME si disponibles
        rome_codes = self._get_rome_codes(metier)
        coordinates = await self._get_coordinates(location) if location else None

        for rome_code in rome_codes:
            api_jobs = await self._search_by_rome(rome_code, metier, coordinates)
            jobs.extend(api_jobs)

        # Si pas de codes ROME, recherche par mots-clés
        if not jobs:
            keyword_jobs = await self._search_by_keywords(metier, coordinates)
            jobs.extend(keyword_jobs)

        # Dédupliquer
        unique_jobs = {}
        for job in jobs:
            job_key = f"{job.get('external_id', '')}{job.get('entreprise', '')}"
            if job_key not in unique_jobs:
                unique_jobs[job_key] = job

        self.logger.info(f"La Bonne Alternance: {len(unique_jobs)} offres trouvées pour {metier['nom']}")
        return list(unique_jobs.values())

    async def _search_by_rome(self, rome_code: str, metier: Dict, coordinates: Dict = None) -> List[Dict]:
        """Recherche par code ROME"""
        params = {
            'romes': rome_code,
            'radius': 30,
            'sort': 'date'
        }

        if coordinates:
            params.update(coordinates)
        else:
            # Coordonnées par défaut (Paris)
            params.update({'latitude': 48.8566, 'longitude': 2.3522})

        data = await self.fetch_json(self.api_url, params)
        if not data:
            return []

        return self._parse_api_response(data, metier)

    async def _search_by_keywords(self, metier: Dict, coordinates: Dict = None) -> List[Dict]:
        """Recherche par mots-clés quand pas de code ROME"""
        jobs = []
        keywords = self._build_keywords(metier)

        for keyword in keywords[:2]:
            params = {
                'caller': 'labonnealternance',
                'api': 'jobEtFormation',
                'querystring': f"{keyword} alternance",
                'radius': 30
            }

            if coordinates:
                params.update(coordinates)
            else:
                params.update({'latitude': 48.8566, 'longitude': 2.3522})

            data = await self.fetch_json(self.api_url, params)
            if data:
                keyword_jobs = self._parse_api_response(data, metier)
                jobs.extend(keyword_jobs)

            await asyncio.sleep(1)

        return jobs

    def _parse_api_response(self, data: Dict, metier: Dict) -> List[Dict]:
        """Parse la réponse de l'API"""
        jobs = []

        # L'API peut retourner différents formats
        job_list = data.get('jobs', []) or data.get('peJobs', []) or data.get('matchas', [])

        for job_data in job_list:
            job = self._parse_api_job(job_data, metier)
            if job and self._is_valid_job(job):
                jobs.append(job)

        return jobs

    def _parse_api_job(self, job_data: Dict, metier: Dict) -> Optional[Dict]:
        """Parse un job depuis l'API"""
        try:
            # Extraire les champs selon le format de l'API
            titre = job_data.get('title') or job_data.get('intitule', '')
            entreprise = job_data.get('company', {}).get('name', '') or job_data.get('entreprise', '')
            description = job_data.get('description', '') or job_data.get('description', '')

            # Localisation
            lieu_data = job_data.get('place', {}) or job_data.get('lieuTravail', {})
            if isinstance(lieu_data, dict):
                lieu = f"{lieu_data.get('city', '')} ({lieu_data.get('zipCode', '')})".strip(' ()')
            else:
                lieu = str(lieu_data) if lieu_data else ""

            # URL
            url = job_data.get('url', '') or job_data.get('contact', {}).get('urlPostulation', '')
            if not url:
                # Construire une URL par défaut
                job_id = job_data.get('id', '')
                if job_id:
                    url = f"https://labonnealternance.pole-emploi.fr/offre/{job_id}"

            # ID externe
            external_id = job_data.get('id') or job_data.get('identifier', '')

            # Salaire
            salaire = None
            salary_data = job_data.get('salary') or job_data.get('salaire', {})
            if salary_data:
                if isinstance(salary_data, dict):
                    salaire = salary_data.get('label', '')
                else:
                    salaire = str(salary_data)

            # Date de publication
            date_pub = job_data.get('creationDate') or job_data.get('dateCreation')
            if date_pub:
                try:
                    date_publication = datetime.fromisoformat(date_pub.replace('Z', '+00:00'))
                except:
                    date_publication = datetime.now()
            else:
                date_publication = datetime.now()

            # Vérifier que c'est une alternance
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
                external_id=str(external_id),
                date_publication=date_publication,
                metier_id=metier.get('id')
            )

        except Exception as e:
            self.logger.error(f"Erreur parsing LBA job: {e}")
            return None

    def _get_rome_codes(self, metier: Dict) -> List[str]:
        """Récupère les codes ROME pour un métier"""
        codes = []

        # Code ROME direct du métier
        if metier.get('code_rome'):
            codes.append(metier['code_rome'])

        # Mapping basique des métiers vers codes ROME
        rome_mapping = {
            'développeur web': ['M1805', 'M1806'],
            'data analyst': ['M1403', 'M1805'],
            'marketing digital': ['M1705', 'E1103'],
            'commercial': ['D1402', 'D1407'],
            'comptable': ['M1203', 'M1204']
        }

        metier_lower = metier.get('nom', '').lower()
        for key, rome_list in rome_mapping.items():
            if key in metier_lower:
                codes.extend(rome_list)
                break

        return codes or ['M1805']  # Code par défaut (informatique)

    async def _get_coordinates(self, location: str) -> Optional[Dict]:
        """Récupère les coordonnées d'une ville (API géocodage simple)"""
        if not location:
            return None

        try:
            # Utiliser l'API du gouvernement français
            geo_api = "https://api-adresse.data.gouv.fr/search/"
            params = {'q': location, 'limit': 1}

            data = await self.fetch_json(geo_api, params)
            if data and data.get('features'):
                coords = data['features'][0]['geometry']['coordinates']
                return {
                    'longitude': coords[0],
                    'latitude': coords[1]
                }
        except Exception as e:
            self.logger.warning(f"Erreur géocodage pour {location}: {e}")

        return None

    def _build_keywords(self, metier: Dict) -> List[str]:
        """Construit les mots-clés de recherche"""
        keywords = [metier['nom']]

        if metier.get('keywords'):
            try:
                metier_keywords = json.loads(metier['keywords'])
                keywords.extend(metier_keywords[:3])
            except (json.JSONDecodeError, TypeError):
                pass

        return keywords

    def _is_valid_job(self, job: Dict) -> bool:
        """Valide une offre"""
        return bool(job.get('titre') and job.get('url'))

    def parse_job_details(self, job_element) -> Optional[Dict]:
        """Parse les détails d'une offre (déjà fait via l'API)"""
        pass