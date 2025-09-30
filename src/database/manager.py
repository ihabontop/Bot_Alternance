"""
Gestionnaire de base de données PostgreSQL
"""

import asyncio
import logging
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, desc
from datetime import datetime, timedelta

from .models import Base, User, Metier, OffreEmploi, Notification, ScrapingSession, Configuration

class DatabaseManager:
    """Gestionnaire principal de la base de données"""

    def __init__(self, database_url: str):
        self.database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_size=10,
            max_overflow=20
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialise la base de données et crée les tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await self._populate_default_data()
        self.logger.info("Base de données initialisée")

    async def _populate_default_data(self):
        """Ajoute les données par défaut (métiers, etc.)"""
        default_metiers = [
            {
                "nom": "Développeur Web",
                "category": "IT",
                "description": "Développement d'applications web front-end et back-end",
                "keywords": '["développeur", "developer", "web", "php", "javascript", "react", "vue", "angular", "symfony", "laravel"]'
            },
            {
                "nom": "Data Analyst",
                "category": "IT",
                "description": "Analyse et traitement de données",
                "keywords": '["data", "analyst", "python", "sql", "tableau", "power bi", "excel"]'
            },
            {
                "nom": "Marketing Digital",
                "category": "Marketing",
                "description": "Marketing en ligne, SEO, réseaux sociaux",
                "keywords": '["marketing", "digital", "seo", "sem", "social media", "google ads", "facebook ads"]'
            },
            {
                "nom": "Commercial",
                "category": "Vente",
                "description": "Vente et relation client",
                "keywords": '["commercial", "vente", "sales", "relation client", "négociation"]'
            },
            {
                "nom": "Comptabilité",
                "category": "Finance",
                "description": "Gestion comptable et financière",
                "keywords": '["comptable", "comptabilité", "finance", "gestion", "audit"]'
            }
        ]

        async with self.async_session() as session:
            for metier_data in default_metiers:
                result = await session.execute(
                    select(Metier).where(Metier.nom == metier_data["nom"])
                )
                if not result.scalar_one_or_none():
                    metier = Metier(**metier_data)
                    session.add(metier)

            await session.commit()

    async def get_user_by_discord_id(self, discord_id: str) -> Optional[User]:
        """Récupère un utilisateur par son ID Discord"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User)
                .options(selectinload(User.metiers))
                .where(User.discord_id == discord_id)
            )
            return result.scalar_one_or_none()

    async def create_or_update_user(self, discord_id: str, username: str, **kwargs) -> User:
        """Crée ou met à jour un utilisateur"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.discord_id == discord_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.username = username
                for key, value in kwargs.items():
                    setattr(user, key, value)
            else:
                user = User(discord_id=discord_id, username=username, **kwargs)
                session.add(user)

            await session.commit()
            await session.refresh(user)
            return user

    async def get_all_metiers(self) -> List[Metier]:
        """Récupère tous les métiers actifs"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Metier).where(Metier.is_active == True).order_by(Metier.category, Metier.nom)
            )
            return result.scalars().all()

    async def get_metier_by_id(self, metier_id: int) -> Optional[Metier]:
        """Récupère un métier par son ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Metier).where(Metier.id == metier_id)
            )
            return result.scalar_one_or_none()

    async def get_metier_by_name(self, nom: str) -> Optional[Metier]:
        """Récupère un métier par son nom"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Metier).where(Metier.nom == nom)
            )
            return result.scalar_one_or_none()

    async def add_metier(self, nom: str, description: str, category: str, keywords: List[str], code_rome: str = None) -> Metier:
        """Ajoute un nouveau métier"""
        import json
        async with self.async_session() as session:
            metier = Metier(
                nom=nom,
                description=description,
                category=category,
                keywords=json.dumps(keywords),
                code_rome=code_rome,
                is_active=True
            )
            session.add(metier)
            await session.commit()
            await session.refresh(metier)
            return metier

    async def update_metier_keywords(self, metier_id: int, keywords: List[str]) -> bool:
        """Met à jour les mots-clés d'un métier"""
        import json
        async with self.async_session() as session:
            result = await session.execute(
                select(Metier).where(Metier.id == metier_id)
            )
            metier = result.scalar_one_or_none()
            if metier:
                metier.keywords = json.dumps(keywords)
                await session.commit()
                return True
            return False

    async def add_user_metier(self, discord_id: str, metier_id: int) -> bool:
        """Ajoute un métier aux préférences d'un utilisateur"""
        async with self.async_session() as session:
            # Récupérer user et metier dans la même session
            user_result = await session.execute(
                select(User)
                .options(selectinload(User.metiers))
                .where(User.discord_id == discord_id)
            )
            user = user_result.scalar_one_or_none()

            metier_result = await session.execute(
                select(Metier).where(Metier.id == metier_id)
            )
            metier = metier_result.scalar_one_or_none()

            if user and metier and metier not in user.metiers:
                user.metiers.append(metier)
                await session.commit()
                return True
            return False

    async def remove_user_metier(self, discord_id: str, metier_id: int) -> bool:
        """Retire un métier des préférences d'un utilisateur"""
        async with self.async_session() as session:
            # Récupérer user et metier dans la même session
            user_result = await session.execute(
                select(User)
                .options(selectinload(User.metiers))
                .where(User.discord_id == discord_id)
            )
            user = user_result.scalar_one_or_none()

            metier_result = await session.execute(
                select(Metier).where(Metier.id == metier_id)
            )
            metier = metier_result.scalar_one_or_none()

            if user and metier and metier in user.metiers:
                user.metiers.remove(metier)
                await session.commit()
                return True
            return False

    async def save_offre(self, offre_data: Dict) -> OffreEmploi:
        """Sauvegarde une nouvelle offre d'emploi"""
        async with self.async_session() as session:
            # Vérifier si l'offre existe déjà
            existing = await session.execute(
                select(OffreEmploi).where(
                    and_(
                        OffreEmploi.url == offre_data.get('url'),
                        OffreEmploi.source_site == offre_data.get('source_site')
                    )
                )
            )

            if existing.scalar_one_or_none():
                return None  # Offre déjà existante

            offre = OffreEmploi(**offre_data)
            session.add(offre)
            await session.commit()
            await session.refresh(offre)
            return offre

    async def get_users_for_metier(self, metier_id: int) -> List[User]:
        """Récupère tous les utilisateurs intéressés par un métier"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User)
                .join(User.metiers)
                .where(
                    and_(
                        Metier.id == metier_id,
                        User.is_active == True
                    )
                )
            )
            return result.scalars().all()

    async def save_notification(self, user_id: int, offre_id: int, **kwargs) -> Notification:
        """Sauvegarde une notification envoyée"""
        async with self.async_session() as session:
            notification = Notification(
                user_id=user_id,
                offre_id=offre_id,
                **kwargs
            )
            session.add(notification)
            await session.commit()
            return notification

    async def get_recent_offres(self, metier_id: int = None, hours: int = 24) -> List[OffreEmploi]:
        """Récupère les offres récentes"""
        async with self.async_session() as session:
            query = select(OffreEmploi).where(
                and_(
                    OffreEmploi.date_scraped >= datetime.utcnow() - timedelta(hours=hours),
                    OffreEmploi.is_active == True
                )
            )

            if metier_id:
                query = query.where(OffreEmploi.metier_id == metier_id)

            result = await session.execute(query.order_by(desc(OffreEmploi.date_scraped)))
            return result.scalars().all()

    async def close(self):
        """Ferme la connexion à la base de données"""
        await self.engine.dispose()