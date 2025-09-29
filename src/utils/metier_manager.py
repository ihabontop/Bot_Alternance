"""
Gestionnaire des métiers et de leurs mots-clés
"""

import json
import logging
from typing import Dict, List, Optional
from database.models import Metier
from database.manager import DatabaseManager

class MetierManager:
    """Gestionnaire des métiers et de leur configuration"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)

    async def create_metier(self, nom: str, category: str, description: str = None,
                          keywords: List[str] = None, code_rome: str = None) -> Metier:
        """Crée un nouveau métier"""
        # Convertir les mots-clés en JSON
        keywords_json = json.dumps(keywords or [])

        metier_data = {
            'nom': nom,
            'category': category,
            'description': description,
            'keywords': keywords_json,
            'code_rome': code_rome
        }

        # Utiliser directement SQLAlchemy pour créer le métier
        async with self.db_manager.async_session() as session:
            metier = Metier(**metier_data)
            session.add(metier)
            await session.commit()
            await session.refresh(metier)

            self.logger.info(f"Nouveau métier créé: {nom}")
            return metier

    async def update_metier_keywords(self, metier_id: int, keywords: List[str]) -> bool:
        """Met à jour les mots-clés d'un métier"""
        try:
            async with self.db_manager.async_session() as session:
                metier = await self.db_manager.get_metier_by_id(metier_id)
                if not metier:
                    return False

                metier.keywords = json.dumps(keywords)
                await session.commit()

                self.logger.info(f"Mots-clés mis à jour pour {metier.nom}")
                return True

        except Exception as e:
            self.logger.error(f"Erreur mise à jour keywords: {e}")
            return False

    def get_keywords_for_metier(self, metier: Metier) -> List[str]:
        """Récupère les mots-clés d'un métier"""
        if not metier.keywords:
            return [metier.nom]

        try:
            keywords = json.loads(metier.keywords)
            return keywords if isinstance(keywords, list) else [metier.nom]
        except (json.JSONDecodeError, TypeError):
            return [metier.nom]

    async def get_metiers_by_category(self, category: str) -> List[Metier]:
        """Récupère tous les métiers d'une catégorie"""
        metiers = await self.db_manager.get_all_metiers()
        return [m for m in metiers if m.category == category]

    async def search_metiers(self, search_term: str) -> List[Metier]:
        """Recherche des métiers par nom ou mot-clé"""
        metiers = await self.db_manager.get_all_metiers()
        results = []

        search_lower = search_term.lower()

        for metier in metiers:
            # Recherche dans le nom
            if search_lower in metier.nom.lower():
                results.append(metier)
                continue

            # Recherche dans les mots-clés
            keywords = self.get_keywords_for_metier(metier)
            if any(search_lower in keyword.lower() for keyword in keywords):
                results.append(metier)
                continue

            # Recherche dans la description
            if metier.description and search_lower in metier.description.lower():
                results.append(metier)

        return results

    async def get_popular_metiers(self, limit: int = 10) -> List[Dict]:
        """Récupère les métiers les plus populaires (avec le plus d'utilisateurs)"""
        # Cette méthode nécessiterait une requête SQL complexe
        # Pour l'instant, retourne tous les métiers
        metiers = await self.db_manager.get_all_metiers()

        # Simuler la popularité basée sur le nombre d'utilisateurs
        popular_metiers = []
        for metier in metiers[:limit]:
            users = await self.db_manager.get_users_for_metier(metier.id)
            popular_metiers.append({
                'metier': metier,
                'user_count': len(users),
                'keywords': self.get_keywords_for_metier(metier)
            })

        # Trier par nombre d'utilisateurs
        popular_metiers.sort(key=lambda x: x['user_count'], reverse=True)
        return popular_metiers

    def suggest_related_metiers(self, metier: Metier) -> List[Metier]:
        """Suggère des métiers similaires"""
        # Logique simple basée sur la catégorie
        # Peut être améliorée avec des algorithmes plus sophistiqués
        async def get_suggestions():
            related = await self.get_metiers_by_category(metier.category)
            return [m for m in related if m.id != metier.id]

        import asyncio
        return asyncio.run(get_suggestions())

    async def validate_metier_data(self, nom: str, category: str) -> Dict[str, str]:
        """Valide les données d'un métier"""
        errors = {}

        if not nom or len(nom.strip()) < 2:
            errors['nom'] = "Le nom doit contenir au moins 2 caractères"

        if not category or len(category.strip()) < 2:
            errors['category'] = "La catégorie doit contenir au moins 2 caractères"

        # Vérifier l'unicité du nom
        metiers = await self.db_manager.get_all_metiers()
        if any(m.nom.lower() == nom.lower() for m in metiers):
            errors['nom'] = "Un métier avec ce nom existe déjà"

        return errors

    async def import_metiers_from_config(self, metiers_config: Dict) -> int:
        """Importe des métiers depuis la configuration"""
        imported_count = 0

        for metier_nom, config in metiers_config.items():
            # Vérifier si le métier existe déjà
            existing_metiers = await self.db_manager.get_all_metiers()
            if any(m.nom == metier_nom for m in existing_metiers):
                continue

            try:
                # Déterminer la catégorie selon le nom du métier
                category = self._determine_category(metier_nom)

                # Créer le métier
                await self.create_metier(
                    nom=metier_nom,
                    category=category,
                    description=f"Métier importé: {metier_nom}",
                    keywords=config if isinstance(config, list) else [metier_nom]
                )

                imported_count += 1

            except Exception as e:
                self.logger.error(f"Erreur import métier {metier_nom}: {e}")

        self.logger.info(f"{imported_count} métiers importés depuis la configuration")
        return imported_count

    def _determine_category(self, metier_nom: str) -> str:
        """Détermine automatiquement la catégorie d'un métier"""
        metier_lower = metier_nom.lower()

        # Mapping simple basé sur des mots-clés
        if any(word in metier_lower for word in ['développeur', 'developer', 'programmeur', 'data', 'it']):
            return "IT"
        elif any(word in metier_lower for word in ['marketing', 'communication', 'publicité']):
            return "Marketing"
        elif any(word in metier_lower for word in ['commercial', 'vente', 'sales']):
            return "Vente"
        elif any(word in metier_lower for word in ['comptable', 'finance', 'gestion']):
            return "Finance"
        elif any(word in metier_lower for word in ['ressources humaines', 'rh', 'recrutement']):
            return "RH"
        else:
            return "Autres"

    async def get_metier_statistics(self) -> Dict:
        """Récupère des statistiques sur les métiers"""
        metiers = await self.db_manager.get_all_metiers()

        stats = {
            'total_metiers': len(metiers),
            'categories': {},
            'most_popular': None,
            'least_popular': None
        }

        # Statistiques par catégorie
        for metier in metiers:
            cat = metier.category or "Autres"
            if cat not in stats['categories']:
                stats['categories'][cat] = {
                    'count': 0,
                    'metiers': []
                }
            stats['categories'][cat]['count'] += 1
            stats['categories'][cat]['metiers'].append(metier.nom)

        return stats