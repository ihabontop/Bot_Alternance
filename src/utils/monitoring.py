"""
Système de monitoring et orchestration des scrapers
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from database.manager import DatabaseManager
from scrapers import get_scraper, SCRAPERS
from config.settings import Settings
from discord_bot.webhook import WebhookNotifier

class MonitoringManager:
    """Gestionnaire principal du monitoring des offres d'alternance"""

    def __init__(self, settings: Settings, db_manager: DatabaseManager, webhook_notifier: WebhookNotifier):
        self.settings = settings
        self.db_manager = db_manager
        self.webhook_notifier = webhook_notifier
        self.logger = logging.getLogger(__name__)

        # Statistiques du monitoring
        self.monitoring_stats = {
            'last_run': None,
            'total_jobs_found': 0,
            'total_new_jobs': 0,
            'total_notifications_sent': 0,
            'errors': []
        }

    async def run_monitoring_cycle(self) -> Dict:
        """Exécute un cycle complet de monitoring"""
        self.logger.info("🚀 Démarrage du cycle de monitoring")
        start_time = datetime.now()

        cycle_stats = {
            'start_time': start_time,
            'sites': {},
            'metiers': {},
            'total_new_jobs': 0,
            'total_notifications': 0,
            'errors': []
        }

        try:
            # Récupérer tous les métiers actifs
            metiers = await self.db_manager.get_all_metiers()
            if not metiers:
                self.logger.warning("Aucun métier configuré pour le monitoring")
                return cycle_stats

            # Parcourir chaque site activé
            for site_name in self.settings.get_enabled_sites():
                site_stats = await self._monitor_site(site_name, metiers)
                cycle_stats['sites'][site_name] = site_stats

                # Agréger les statistiques
                cycle_stats['total_new_jobs'] += site_stats.get('new_jobs', 0)

                # Délai entre les sites pour éviter la surcharge
                await asyncio.sleep(self.settings.scraping.request_delay)

            # Envoyer les notifications
            notification_count = await self._send_pending_notifications()
            cycle_stats['total_notifications'] = notification_count

            # Calculer la durée du cycle
            end_time = datetime.now()
            cycle_stats['duration'] = (end_time - start_time).total_seconds()
            cycle_stats['end_time'] = end_time

            # Mettre à jour les statistiques globales
            self.monitoring_stats.update({
                'last_run': end_time,
                'total_jobs_found': self.monitoring_stats['total_jobs_found'] + sum(
                    site.get('jobs_found', 0) for site in cycle_stats['sites'].values()
                ),
                'total_new_jobs': self.monitoring_stats['total_new_jobs'] + cycle_stats['total_new_jobs'],
                'total_notifications_sent': self.monitoring_stats['total_notifications_sent'] + notification_count
            })

            self.logger.info(
                f"✅ Cycle terminé: {cycle_stats['total_new_jobs']} nouvelles offres, "
                f"{notification_count} notifications envoyées en {cycle_stats['duration']:.1f}s"
            )

            # Envoyer un résumé si configuré
            if cycle_stats['total_new_jobs'] > 0:
                await self._send_monitoring_summary(cycle_stats)

        except Exception as e:
            self.logger.error(f"❌ Erreur critique dans le cycle de monitoring: {e}")
            cycle_stats['errors'].append(str(e))
            await self.webhook_notifier.send_error_notification(str(e), "Cycle de monitoring")

        return cycle_stats

    async def _monitor_site(self, site_name: str, metiers: List) -> Dict:
        """Monitore un site spécifique pour tous les métiers"""
        site_stats = {
            'jobs_found': 0,
            'new_jobs': 0,
            'errors': []
        }

        try:
            site_config = self.settings.get_site_config(site_name)
            scraper = get_scraper(site_name, site_config)

            self.logger.info(f"🔍 Monitoring {site_name} pour {len(metiers)} métiers")

            async with scraper:
                # Semaphore pour limiter les requêtes concurrentes
                semaphore = asyncio.Semaphore(self.settings.scraping.max_concurrent_requests)

                # Créer les tâches de monitoring pour chaque métier
                tasks = []
                for metier in metiers:
                    task = self._monitor_metier_on_site(semaphore, scraper, metier, site_stats)
                    tasks.append(task)

                # Exécuter toutes les tâches
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            error_msg = f"Erreur monitoring {site_name}: {e}"
            self.logger.error(error_msg)
            site_stats['errors'].append(error_msg)

        return site_stats

    async def _monitor_metier_on_site(self, semaphore: asyncio.Semaphore, scraper, metier, site_stats: Dict):
        """Monitore un métier spécifique sur un site"""
        async with semaphore:
            try:
                # Rechercher des offres pour ce métier
                jobs = await scraper.search_jobs(metier)
                site_stats['jobs_found'] += len(jobs)

                # Sauvegarder les nouvelles offres
                new_jobs = []
                for job in jobs:
                    saved_job = await self.db_manager.save_offre(job)
                    if saved_job:
                        new_jobs.append(saved_job)

                site_stats['new_jobs'] += len(new_jobs)

                if new_jobs:
                    self.logger.info(
                        f"  📝 {len(new_jobs)} nouvelles offres pour {metier.nom} sur {scraper.site_name}"
                    )

                # Délai entre les métiers
                await asyncio.sleep(self.settings.scraping.request_delay)

            except Exception as e:
                error_msg = f"Erreur métier {metier.nom} sur {scraper.site_name}: {e}"
                self.logger.error(error_msg)
                site_stats['errors'].append(error_msg)

    async def _send_pending_notifications(self) -> int:
        """Envoie les notifications pour les nouvelles offres"""
        try:
            # Récupérer les offres non notifiées des dernières 24h
            recent_jobs = await self.db_manager.get_recent_offres(hours=24)
            unnotified_jobs = [job for job in recent_jobs if not job.is_notified]

            if not unnotified_jobs:
                return 0

            notification_count = 0

            for job in unnotified_jobs:
                try:
                    # Récupérer le métier associé
                    metier = await self.db_manager.get_metier_by_id(job.metier_id)
                    if not metier:
                        continue

                    # Récupérer les utilisateurs intéressés
                    users = await self.db_manager.get_users_for_metier(metier.id)
                    if not users:
                        # Marquer comme notifié même sans utilisateurs
                        job.is_notified = True
                        continue

                    # Créer l'embed de notification
                    embed = self._create_job_embed(job, metier)

                    # Envoyer la notification
                    success = await self.webhook_notifier.send_job_notification(embed, users)

                    if success:
                        # Sauvegarder les notifications individuelles
                        for user in users:
                            await self.db_manager.save_notification(
                                user_id=user.id,
                                offre_id=job.id,
                                webhook_url=self.settings.discord.webhook_url
                            )

                        # Marquer l'offre comme notifiée
                        job.is_notified = True
                        notification_count += len(users)

                        self.logger.info(f"  📢 Notification envoyée pour {job.titre} à {len(users)} utilisateurs")

                    # Délai pour éviter le rate limiting
                    await asyncio.sleep(1)

                except Exception as e:
                    self.logger.error(f"Erreur notification job {job.id}: {e}")

            return notification_count

        except Exception as e:
            self.logger.error(f"Erreur envoi notifications: {e}")
            return 0

    def _create_job_embed(self, job, metier):
        """Crée un embed Discord pour une offre (réutilise la logique du bot)"""
        import discord

        embed = discord.Embed(
            title=f"🎯 Nouvelle offre d'alternance - {metier.nom}",
            description=job.titre,
            color=discord.Color.green(),
            timestamp=datetime.now(),
            url=job.url
        )

        if job.entreprise:
            embed.add_field(name="🏢 Entreprise", value=job.entreprise, inline=True)

        if job.lieu:
            embed.add_field(name="📍 Lieu", value=job.lieu, inline=True)

        if job.salaire:
            embed.add_field(name="💰 Salaire", value=job.salaire, inline=True)

        if job.description:
            desc_short = job.description[:200] + "..." if len(job.description) > 200 else job.description
            embed.add_field(name="📝 Description", value=desc_short, inline=False)

        embed.add_field(name="🌐 Source", value=job.source_site.capitalize(), inline=True)
        embed.add_field(name="🔗 Postuler", value=f"[Voir l'offre]({job.url})", inline=True)

        embed.set_footer(text=f"Bot Alternance • {job.source_site}")

        return embed

    async def _send_monitoring_summary(self, cycle_stats: Dict):
        """Envoie un résumé du cycle de monitoring"""
        try:
            summary = {
                'sites': cycle_stats['sites'],
                'total_new_jobs': cycle_stats['total_new_jobs'],
                'total_notifications': cycle_stats['total_notifications'],
                'duration_minutes': cycle_stats['duration'] / 60,
                'top_metiers': []  # Peut être enrichi avec plus de données
            }

            await self.webhook_notifier.send_monitoring_summary(summary)

        except Exception as e:
            self.logger.error(f"Erreur envoi résumé: {e}")

    async def get_monitoring_health(self) -> Dict:
        """Retourne l'état de santé du monitoring"""
        health = {
            'status': 'healthy',
            'last_run': self.monitoring_stats.get('last_run'),
            'issues': []
        }

        # Vérifier si le dernier run est trop ancien
        if health['last_run']:
            time_since_last = datetime.now() - health['last_run']
            if time_since_last > timedelta(hours=1):
                health['status'] = 'warning'
                health['issues'].append(f"Dernier run il y a {time_since_last}")

        # Vérifier les erreurs récentes
        if self.monitoring_stats.get('errors'):
            health['status'] = 'error' if health['status'] != 'error' else health['status']
            health['issues'].extend(self.monitoring_stats['errors'][-5:])  # 5 dernières erreurs

        return health

    async def test_all_scrapers(self) -> Dict:
        """Teste tous les scrapers configurés"""
        test_results = {}

        metiers = await self.db_manager.get_all_metiers()
        test_metier = metiers[0] if metiers else None

        if not test_metier:
            return {'error': 'Aucun métier configuré pour les tests'}

        for site_name in SCRAPERS.keys():
            if not self.settings.is_site_enabled(site_name):
                test_results[site_name] = {'status': 'disabled'}
                continue

            try:
                site_config = self.settings.get_site_config(site_name)
                scraper = get_scraper(site_name, site_config)

                async with scraper:
                    jobs = await scraper.search_jobs(test_metier, location="Paris")
                    test_results[site_name] = {
                        'status': 'success',
                        'jobs_found': len(jobs)
                    }

            except Exception as e:
                test_results[site_name] = {
                    'status': 'error',
                    'error': str(e)
                }

        return test_results