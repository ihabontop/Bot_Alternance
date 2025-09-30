"""
Scraper pour France Travail API (ex Pôle Emploi)
API officielle pour récupérer les offres d'emploi
"""

import json
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .base import BaseScraper

class FranceTravailScraper(BaseScraper):
    """Scraper pour l'API France Travail"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.site_name = "francetravail"
        self.api_base_url = "https://api.francetravail.io/partenaire"
        self.api_offres = f"{self.api_base_url}/offresdemploi/v2/offres/search"
        self.api_token_url = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"

        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.access_token = None
        self.token_expires_at = None

    async def get_access_token(self) -> str:
        """Obtient un token d'accès OAuth2"""
        # Si le token est encore valide, le retourner
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token

        # Sinon, demander un nouveau token
        # Utiliser le scope spécifique à l'application pour l'API v2
        scope = f"application_{self.client_id}"
        data = f"grant_type=client_credentials&client_id={self.client_id}&client_secret={self.client_secret}&scope={scope}"

        try:
            async with self.session.post(
                self.api_token_url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data['access_token']
                    expires_in = data.get('expires_in', 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                    self.logger.info("Token France Travail obtenu avec succès")
                    return self.access_token
                else:
                    error = await response.text()
                    self.logger.error(f"Erreur obtention token France Travail: {response.status} - {error}")
                    return None
        except Exception as e:
            self.logger.error(f"Exception lors de l'obtention du token: {e}")
            return None

    async def search_jobs(self, metier: Dict, location: str = None) -> List[Dict]:
        """Recherche des offres sur France Travail API"""
        token = await self.get_access_token()
        if not token:
            self.logger.error("Impossible d'obtenir le token d'accès")
            return []

        jobs = []
        keywords = self._build_keywords(metier)

        # Utiliser le premier mot-clé principal
        keyword = keywords[0] if keywords else metier['nom']

        # Construire les paramètres de recherche
        params = {
            'motsCles': f"{keyword} alternance",
            'typeContrat': 'E2,FS',  # E2=Apprentissage, FS=Contrat pro
            'minCreationDate': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'range': '0-149',  # Récupérer jusqu'à 150 résultats
            'sort': '2',  # Tri par date
        }

        if location:
            params['commune'] = location

        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        self.logger.info(f"Recherche France Travail: {params}")

        try:
            async with self.session.get(self.api_offres, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    resultats = data.get('resultats', [])

                    for offre_data in resultats:
                        job = self._parse_offre(offre_data, metier)
                        if job and self._is_valid_job(job):
                            jobs.append(job)

                    self.logger.info(f"France Travail: {len(jobs)} offres trouvées pour {metier['nom']}")
                else:
                    error = await response.text()
                    self.logger.warning(f"Erreur API France Travail: {response.status} - {error}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche France Travail: {e}")

        return jobs

    def _parse_offre(self, offre_data: Dict, metier: Dict) -> Optional[Dict]:
        """Parse une offre France Travail"""
        try:
            # Extraire les données principales
            titre = offre_data.get('intitule', '')
            entreprise_data = offre_data.get('entreprise', {})
            entreprise = entreprise_data.get('nom', 'Non précisé')

            # Localisation
            lieu_travail = offre_data.get('lieuTravail', {})
            ville = lieu_travail.get('libelle', '')

            # Description
            description = offre_data.get('description', '')

            # Salaire
            salaire_data = offre_data.get('salaire', {})
            salaire = None
            if salaire_data:
                libelle_salaire = salaire_data.get('libelle')
                if libelle_salaire:
                    salaire = libelle_salaire

            # URL de l'offre
            offre_id = offre_data.get('id')
            url = f"https://candidat.francetravail.fr/offres/recherche/detail/{offre_id}"

            # Date de création
            date_creation_str = offre_data.get('dateCreation')
            date_publication = None
            if date_creation_str:
                try:
                    date_publication = datetime.fromisoformat(date_creation_str.replace('Z', '+00:00'))
                except:
                    date_publication = datetime.now()

            return self.build_job_dict(
                titre=titre,
                entreprise=entreprise,
                description=self.clean_text(description)[:500],  # Limiter la description
                lieu=ville,
                salaire=salaire,
                url=url,
                source_site=self.site_name,
                external_id=offre_id,
                date_publication=date_publication or datetime.now(),
                metier_id=metier.get('id')
            )
        except Exception as e:
            self.logger.error(f"Erreur parsing offre France Travail: {e}")
            return None

    def parse_job_details(self, job_element) -> Optional[Dict]:
        """Non utilisé pour l'API"""
        pass