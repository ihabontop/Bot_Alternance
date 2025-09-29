#!/usr/bin/env python3
"""
Script d'initialisation de la base de données PostgreSQL
"""

import asyncio
import sys
import os

# Ajouter le dossier src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.manager import DatabaseManager
from config.settings import Settings
from utils.metier_manager import MetierManager

async def setup_database():
    """Initialise la base de données avec les données par défaut"""
    print("🗄️  Configuration de la base de données PostgreSQL...")

    try:
        # Charger la configuration
        settings = Settings()

        if not settings.validate():
            print("❌ Configuration invalide. Vérifiez votre fichier .env")
            return False

        print(f"📡 Connexion à: {settings.database.host}:{settings.database.port}/{settings.database.name}")

        # Initialiser la base de données
        db_manager = DatabaseManager(settings.database_url)
        await db_manager.initialize()
        print("✅ Tables créées avec succès")

        # Initialiser le gestionnaire de métiers
        metier_manager = MetierManager(db_manager)

        # Vérifier les métiers existants
        existing_metiers = await db_manager.get_all_metiers()
        print(f"📋 {len(existing_metiers)} métiers trouvés dans la base")

        if len(existing_metiers) == 0:
            print("📥 Importation des métiers par défaut...")
            # Importer depuis la configuration
            if hasattr(settings, 'metiers_keywords'):
                imported = await metier_manager.import_metiers_from_config(settings.metiers_keywords)
                print(f"✅ {imported} métiers importés")
            else:
                print("ℹ️  Aucune configuration de métiers trouvée")

        # Afficher un résumé
        final_metiers = await db_manager.get_all_metiers()
        print(f"\n📊 Résumé de la base de données:")
        print(f"   • Métiers configurés: {len(final_metiers)}")

        if final_metiers:
            categories = {}
            for metier in final_metiers:
                cat = metier.category or "Autres"
                categories[cat] = categories.get(cat, 0) + 1

            for cat, count in categories.items():
                print(f"   • {cat}: {count} métiers")

        await db_manager.close()
        print("\n🎉 Base de données configurée avec succès!")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        return False

async def reset_database():
    """Remet à zéro la base de données (ATTENTION: supprime toutes les données)"""
    print("⚠️  ATTENTION: Cette opération va supprimer TOUTES les données!")
    confirm = input("Tapez 'CONFIRMER' pour continuer: ")

    if confirm != 'CONFIRMER':
        print("❌ Opération annulée")
        return

    try:
        settings = Settings()
        db_manager = DatabaseManager(settings.database_url)

        # Supprimer toutes les tables
        from database.models import Base
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            print("🗑️  Tables supprimées")

        # Recréer les tables
        await db_manager.initialize()
        print("✅ Tables recréées")

        await db_manager.close()
        print("🎉 Base de données remise à zéro!")

    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    """Point d'entrée du script"""
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        asyncio.run(reset_database())
    else:
        asyncio.run(setup_database())

if __name__ == "__main__":
    main()