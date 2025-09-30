#!/usr/bin/env python3
"""
Bot Discord - Monitoring d'Alternances
Point d'entrée principal de l'application
"""

import asyncio
import logging
import os
from discord_bot.bot import AlternanceBot
from database.manager import DatabaseManager
from config.settings import Settings
from utils.monitoring import MonitoringManager
from utils.metier_manager import MetierManager

def setup_logging():
    """Configure le système de logging"""
    # Créer le dossier logs s'il n'existe pas
    os.makedirs('logs', exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # Configurer StreamHandler pour supporter les emojis
    for handler in logging.root.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream.name == '<stderr>':
            handler.stream.reconfigure(encoding='utf-8')

async def main():
    """Fonction principale"""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Charger la configuration
        settings = Settings()
        if not settings.validate():
            logger.error("Configuration invalide. Vérifiez votre fichier .env")
            return

        logger.info("Configuration chargée et validée")

        # Initialiser la base de données
        db_manager = DatabaseManager(settings.database_url)
        await db_manager.initialize()
        logger.info("Base de données initialisée")

        # Initialiser le gestionnaire de métiers
        metier_manager = MetierManager(db_manager)

        # Importer les métiers depuis la configuration si configuré
        if hasattr(settings, 'metiers_keywords'):
            imported = await metier_manager.import_metiers_from_config(settings.metiers_keywords)
            if imported > 0:
                logger.info(f"{imported} métiers importés depuis la configuration")

        # Démarrer le bot Discord avec monitoring intégré
        bot = AlternanceBot(settings, db_manager)
        logger.info("🚀 Démarrage du bot Discord...")
        await bot.start()

    except KeyboardInterrupt:
        logger.info("Arrêt du bot demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur critique: {e}")
        raise
    finally:
        # Nettoyage
        if 'db_manager' in locals():
            await db_manager.close()
        logger.info("Bot arrêté proprement")

if __name__ == "__main__":
    asyncio.run(main())