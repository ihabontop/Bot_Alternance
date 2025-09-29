"""
Modèles de base de données pour le bot alternance
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Table d'association many-to-many entre users et métiers
user_metiers = Table(
    'user_metiers',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('metier_id', Integer, ForeignKey('metiers.id'), primary_key=True)
)

class User(Base):
    """Utilisateur Discord avec ses préférences"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    discord_id = Column(String(20), unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    notification_role = Column(String(100))  # Rôle Discord pour les notifications

    # Préférences de recherche
    preferred_location = Column(String(100))
    max_distance = Column(Integer, default=50)  # En km

    # Relations
    metiers = relationship("Metier", secondary=user_metiers, back_populates="users")
    notifications = relationship("Notification", back_populates="user")

class Metier(Base):
    """Métiers/domaines d'activité disponibles"""
    __tablename__ = 'metiers'

    id = Column(Integer, primary_key=True)
    nom = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    category = Column(String(50))  # Ex: "IT", "Marketing", "Commercial"
    keywords = Column(Text)  # Mots-clés pour la recherche (JSON array as text)
    code_rome = Column(String(10))  # Code ROME Pôle Emploi si applicable
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relations
    users = relationship("User", secondary=user_metiers, back_populates="metiers")
    offres = relationship("OffreEmploi", back_populates="metier")

class OffreEmploi(Base):
    """Offres d'emploi scrapées"""
    __tablename__ = 'offres_emploi'

    id = Column(Integer, primary_key=True)
    titre = Column(String(200), nullable=False)
    entreprise = Column(String(100))
    description = Column(Text)
    lieu = Column(String(100))
    salaire = Column(String(50))
    url = Column(String(500), nullable=False)
    source_site = Column(String(50), nullable=False)  # "indeed", "linkedin", etc.
    external_id = Column(String(100))  # ID externe du site source

    # Dates
    date_publication = Column(DateTime)
    date_scraped = Column(DateTime, default=datetime.utcnow)
    date_expiration = Column(DateTime)

    # Status
    is_active = Column(Boolean, default=True)
    is_notified = Column(Boolean, default=False)

    # Relations
    metier_id = Column(Integer, ForeignKey('metiers.id'))
    metier = relationship("Metier", back_populates="offres")
    notifications = relationship("Notification", back_populates="offre")

class Notification(Base):
    """Historique des notifications envoyées"""
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    offre_id = Column(Integer, ForeignKey('offres_emploi.id'), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    discord_message_id = Column(String(20))  # ID du message Discord
    webhook_url = Column(String(500))

    # Relations
    user = relationship("User", back_populates="notifications")
    offre = relationship("OffreEmploi", back_populates="notifications")

class ScrapingSession(Base):
    """Sessions de scraping pour tracking"""
    __tablename__ = 'scraping_sessions'

    id = Column(Integer, primary_key=True)
    site_name = Column(String(50), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    offres_found = Column(Integer, default=0)
    offres_new = Column(Integer, default=0)
    status = Column(String(20), default='running')  # 'running', 'completed', 'failed'
    error_message = Column(Text)

class Configuration(Base):
    """Configuration dynamique du bot"""
    __tablename__ = 'configuration'

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)