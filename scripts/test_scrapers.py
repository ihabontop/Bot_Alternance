#!/usr/bin/env python3
"""
Script de test des scrapers
"""

import asyncio
import sys
import os

# Ajouter le dossier src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.settings import Settings
from scrapers import get_scraper, SCRAPERS
from database.manager import DatabaseManager
from utils.monitoring import MonitoringManager
from discord_bot.webhook import WebhookNotifier

async def test_individual_scraper(site_name: str):
    """Teste un scraper spécifique"""
    print(f"🧪 Test du scraper {site_name}")

    try:
        settings = Settings()

        if not settings.is_site_enabled(site_name):
            print(f"❌ Site {site_name} désactivé dans la configuration")
            return False

        site_config = settings.get_site_config(site_name)
        scraper = get_scraper(site_name, site_config)

        # Métier de test
        test_metier = {
            'id': 1,
            'nom': 'Développeur Web',
            'keywords': '["développeur", "web", "php", "javascript"]'
        }

        print(f"🔍 Recherche d'offres pour '{test_metier['nom']}'...")

        async with scraper:
            jobs = await scraper.search_jobs(test_metier, location="Paris")

            print(f"✅ {len(jobs)} offres trouvées")

            # Afficher quelques exemples
            for i, job in enumerate(jobs[:3]):
                print(f"\n📋 Offre {i+1}:")
                print(f"   Titre: {job.get('titre', 'N/A')}")
                print(f"   Entreprise: {job.get('entreprise', 'N/A')}")
                print(f"   Lieu: {job.get('lieu', 'N/A')}")
                print(f"   URL: {job.get('url', 'N/A')}")

            return True

    except Exception as e:
        print(f"❌ Erreur test {site_name}: {e}")
        return False

async def test_all_scrapers():
    """Teste tous les scrapers configurés"""
    print("🧪 Test de tous les scrapers\n")

    settings = Settings()
    results = {}

    for site_name in SCRAPERS.keys():
        print(f"{'='*50}")
        success = await test_individual_scraper(site_name)
        results[site_name] = success
        print()

    # Résumé
    print(f"{'='*50}")
    print("📊 Résumé des tests:")
    for site_name, success in results.items():
        status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
        enabled = "🟢" if settings.is_site_enabled(site_name) else "🔴"
        print(f"   {enabled} {site_name}: {status}")

    success_count = sum(results.values())
    total_count = len(results)
    print(f"\n🎯 Résultat global: {success_count}/{total_count} scrapers fonctionnels")

async def test_monitoring_system():
    """Teste le système de monitoring complet"""
    print("🔄 Test du système de monitoring complet\n")

    try:
        settings = Settings()

        if not settings.validate():
            print("❌ Configuration invalide")
            return False

        # Initialiser la base de données
        db_manager = DatabaseManager(settings.database_url)
        await db_manager.initialize()

        # Initialiser le monitoring
        webhook_notifier = WebhookNotifier(settings.discord.webhook_url)
        monitoring = MonitoringManager(settings, db_manager, webhook_notifier)

        # Tester les scrapers
        print("🧪 Test de tous les scrapers...")
        scraper_results = await monitoring.test_all_scrapers()

        print("📊 Résultats des tests:")
        for site_name, result in scraper_results.items():
            status = result.get('status', 'unknown')
            if status == 'success':
                jobs_count = result.get('jobs_found', 0)
                print(f"   ✅ {site_name}: {jobs_count} offres trouvées")
            elif status == 'disabled':
                print(f"   🔴 {site_name}: désactivé")
            elif status == 'error':
                error = result.get('error', 'erreur inconnue')
                print(f"   ❌ {site_name}: {error}")

        # Test du webhook si configuré
        if settings.discord.webhook_url:
            print("\n📡 Test du webhook Discord...")
            webhook_success = await webhook_notifier.test_webhook()
            if webhook_success:
                print("   ✅ Webhook fonctionnel")
            else:
                print("   ❌ Erreur webhook")

        await db_manager.close()
        print("\n🎉 Test du système terminé")
        return True

    except Exception as e:
        print(f"❌ Erreur test système: {e}")
        return False

def main():
    """Point d'entrée du script"""
    if len(sys.argv) > 1:
        site_name = sys.argv[1]
        if site_name == '--all':
            asyncio.run(test_all_scrapers())
        elif site_name == '--system':
            asyncio.run(test_monitoring_system())
        elif site_name in SCRAPERS:
            asyncio.run(test_individual_scraper(site_name))
        else:
            print(f"❌ Site '{site_name}' non reconnu")
            print(f"Sites disponibles: {', '.join(SCRAPERS.keys())}")
            print("Options: --all, --system")
    else:
        print("🧪 Script de test des scrapers")
        print("\nUsage:")
        print(f"  python {sys.argv[0]} <site_name>  # Teste un scraper spécifique")
        print(f"  python {sys.argv[0]} --all        # Teste tous les scrapers")
        print(f"  python {sys.argv[0]} --system     # Teste le système complet")
        print(f"\nSites disponibles: {', '.join(SCRAPERS.keys())}")

if __name__ == "__main__":
    main()