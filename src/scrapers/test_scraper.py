"""
Scraper de test qui génère des offres factices
Utile pour tester le système sans dépendre de sites externes
"""

import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .base import BaseScraper

class TestScraper(BaseScraper):
    """Scraper de test qui génère des offres d'alternance factices"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.site_name = "test"

        # Templates d'entreprises
        self.entreprises = [
            "TechCorp France", "Digital Solutions", "Innovation Labs",
            "StartupXYZ", "Enterprise Solutions", "Cloud Services SA",
            "DataTech", "WebAgency Pro", "AI Research Group",
            "FinTech Partners", "Marketing Digital Plus"
        ]

        # Templates de villes
        self.villes = [
            "Paris", "Lyon", "Marseille", "Toulouse", "Nantes",
            "Bordeaux", "Lille", "Strasbourg", "Nice", "Rennes"
        ]

        # Templates de descriptions par métier
        self.descriptions_templates = {
            "IT": [
                "Nous recherchons un(e) alternant(e) motivé(e) pour rejoindre notre équipe technique. Vous participerez au développement de nos applications et travaillerez sur des projets innovants.",
                "Dans le cadre de notre croissance, nous ouvrons un poste en alternance. Vous serez formé(e) aux dernières technologies et accompagné(e) par des experts.",
                "Rejoignez une équipe dynamique et participez à la création de solutions digitales innovantes. Formation assurée sur les technologies modernes."
            ],
            "Marketing": [
                "Nous recherchons un(e) alternant(e) en marketing digital pour développer notre présence en ligne. Vous travaillerez sur les réseaux sociaux, le SEO et les campagnes publicitaires.",
                "Rejoignez notre équipe marketing et participez à l'élaboration de nos stratégies digitales. Environnement dynamique et formateur.",
                "Dans le cadre de notre développement, nous recrutons un(e) alternant(e) pour renforcer notre équipe marketing."
            ],
            "Finance": [
                "Nous recherchons un(e) alternant(e) en comptabilité/finance pour assister notre équipe dans la gestion comptable et financière de l'entreprise.",
                "Rejoignez notre département financier et participez à l'analyse financière, la gestion budgétaire et le reporting.",
                "Poste en alternance au sein de notre service comptabilité. Formation complète assurée."
            ],
            "Vente": [
                "Nous recrutons un(e) alternant(e) commercial(e) pour développer notre portefeuille clients. Formation à la négociation et aux techniques de vente.",
                "Rejoignez notre force de vente et apprenez le métier de commercial en accompagnant nos clients professionnels.",
                "Poste en alternance dans la vente B2B. Vous serez formé(e) aux techniques commerciales modernes."
            ]
        }

    async def search_jobs(self, metier: Dict, location: str = None) -> List[Dict]:
        """Génère des offres factices pour un métier donné"""
        # Générer entre 2 et 5 offres par métier
        num_jobs = random.randint(2, 5)
        jobs = []

        category = metier.get('category', 'IT')
        descriptions = self.descriptions_templates.get(category, self.descriptions_templates['IT'])

        for i in range(num_jobs):
            job = self._generate_fake_job(metier, category, descriptions, location)
            if job:
                jobs.append(job)

        self.logger.info(f"Test Scraper: {len(jobs)} offres générées pour {metier['nom']}")
        return jobs

    def _generate_fake_job(self, metier: Dict, category: str, descriptions: List[str], location: str = None) -> Dict:
        """Génère une offre factice"""
        entreprise = random.choice(self.entreprises)
        ville = location if location else random.choice(self.villes)
        description = random.choice(descriptions)

        # Variations de titres selon le métier
        titre_variations = [
            f"{metier['nom']} en Alternance (H/F)",
            f"Alternance - {metier['nom']}",
            f"{metier['nom']} - Contrat d'Apprentissage",
            f"Recherche Alternant(e) {metier['nom']}"
        ]
        titre = random.choice(titre_variations)

        # Salaire aléatoire entre 800 et 1500€
        salaire = f"{random.randint(800, 1500)}€ par mois" if random.random() > 0.3 else None

        # URL factice unique
        job_id = f"test-{metier['id']}-{random.randint(10000, 99999)}"
        url = f"https://example.com/jobs/{job_id}"

        # Date de publication récente (entre aujourd'hui et 7 jours avant)
        days_ago = random.randint(0, 7)
        date_publication = datetime.now() - timedelta(days=days_ago)

        return self.build_job_dict(
            titre=titre,
            entreprise=entreprise,
            description=description,
            lieu=ville,
            salaire=salaire,
            url=url,
            source_site=self.site_name,
            external_id=job_id,
            date_publication=date_publication,
            metier_id=metier.get('id')
        )

    def parse_job_details(self, job_element) -> Optional[Dict]:
        """Non utilisé pour le scraper de test"""
        pass