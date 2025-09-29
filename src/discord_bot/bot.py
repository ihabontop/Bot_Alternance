"""
Bot Discord principal pour le monitoring d'alternances
"""

import asyncio
import logging
from typing import List, Dict
import discord
from discord.ext import commands, tasks
from datetime import datetime

from database.manager import DatabaseManager
from config.settings import Settings
from .commands import setup_commands
from .webhook import WebhookNotifier

class AlternanceBot(commands.Bot):
    """Bot Discord principal"""

    def __init__(self, settings: Settings, db_manager: DatabaseManager):
        # Configuration des intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True

        super().__init__(
            command_prefix='!alt ',
            intents=intents,
            help_command=None
        )

        self.settings = settings
        self.db_manager = db_manager
        self.webhook_notifier = WebhookNotifier(settings.discord.webhook_url)
        self.logger = logging.getLogger(__name__)

        # État du monitoring
        self.monitoring_active = False
        self.monitoring_task = None

        # Configuration des commandes
        setup_commands(self)

    async def setup_hook(self):
        """Initialisation du bot"""
        self.logger.info("Configuration du bot Discord...")

        # Synchroniser les commandes slash si nécessaire
        try:
            synced = await self.tree.sync()
            self.logger.info(f"{len(synced)} commandes slash synchronisées")
        except Exception as e:
            self.logger.error(f"Erreur lors de la synchronisation des commandes: {e}")

        # Démarrer le monitoring si configuré
        if not self.monitoring_task:
            self.monitoring_task = self.start_monitoring.start()

    async def on_ready(self):
        """Événement déclenché quand le bot est prêt"""
        self.logger.info(f"Bot connecté en tant que {self.user}")
        self.logger.info(f"Serveurs: {len(self.guilds)}")

        # Définir le statut du bot
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="les offres d'alternance"
        )
        await self.change_presence(activity=activity)

    async def on_command_error(self, ctx, error):
        """Gestion des erreurs de commandes"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Commande inconnue. Utilisez `!alt help` pour voir les commandes disponibles.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Vous n'avez pas les permissions nécessaires.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Argument invalide: {error}")
        else:
            self.logger.error(f"Erreur commande: {error}")
            await ctx.send("❌ Une erreur est survenue.")

    @tasks.loop(minutes=5)
    async def start_monitoring(self):
        """Tâche de monitoring périodique"""
        if not self.monitoring_active:
            self.monitoring_active = True
            return

        try:
            from ..scrapers import get_scraper

            # Récupérer tous les métiers actifs
            metiers = await self.db_manager.get_all_metiers()
            if not metiers:
                self.logger.warning("Aucun métier configuré pour le monitoring")
                return

            self.logger.info(f"Démarrage du monitoring pour {len(metiers)} métiers")

            # Parcourir chaque site activé
            for site_name in self.settings.get_enabled_sites():
                site_config = self.settings.get_site_config(site_name)

                try:
                    scraper = get_scraper(site_name, site_config)

                    async with scraper:
                        for metier in metiers:
                            await self._monitor_metier(scraper, metier)
                            await asyncio.sleep(2)  # Délai entre les métiers

                except Exception as e:
                    self.logger.error(f"Erreur monitoring {site_name}: {e}")

                await asyncio.sleep(5)  # Délai entre les sites

        except Exception as e:
            self.logger.error(f"Erreur générale monitoring: {e}")

    async def _monitor_metier(self, scraper, metier: Dict):
        """Monitore un métier spécifique avec un scraper"""
        try:
            # Rechercher des offres
            jobs = await scraper.search_jobs(metier)

            new_jobs = []
            for job in jobs:
                # Sauvegarder l'offre (retourne None si déjà existante)
                saved_job = await self.db_manager.save_offre(job)
                if saved_job:
                    new_jobs.append(saved_job)

            if new_jobs:
                self.logger.info(f"{len(new_jobs)} nouvelles offres pour {metier['nom']} sur {scraper.site_name}")

                # Notifier les utilisateurs intéressés
                for job in new_jobs:
                    await self._notify_new_job(job, metier)

        except Exception as e:
            self.logger.error(f"Erreur monitoring métier {metier['nom']}: {e}")

    async def _notify_new_job(self, job, metier: Dict):
        """Notifie les utilisateurs d'une nouvelle offre"""
        try:
            # Récupérer les utilisateurs intéressés par ce métier
            users = await self.db_manager.get_users_for_metier(metier['id'])

            if not users:
                return

            # Créer l'embed Discord
            embed = self._create_job_embed(job, metier)

            # Envoyer via webhook
            success = await self.webhook_notifier.send_job_notification(embed, users)

            if success:
                # Marquer comme notifié et sauvegarder les notifications
                for user in users:
                    await self.db_manager.save_notification(
                        user_id=user.id,
                        offre_id=job.id,
                        webhook_url=self.settings.discord.webhook_url
                    )

                # Mettre à jour le statut de l'offre
                job.is_notified = True

                self.logger.info(f"Notification envoyée pour {job.titre} à {len(users)} utilisateurs")

        except Exception as e:
            self.logger.error(f"Erreur notification job {job.id}: {e}")

    def _create_job_embed(self, job, metier: Dict) -> discord.Embed:
        """Crée un embed Discord pour une offre d'emploi"""
        embed = discord.Embed(
            title=f"🎯 Nouvelle offre d'alternance - {metier['nom']}",
            description=job.titre,
            color=discord.Color.green(),
            timestamp=datetime.now(),
            url=job.url
        )

        # Champs de l'offre
        if job.entreprise:
            embed.add_field(name="🏢 Entreprise", value=job.entreprise, inline=True)

        if job.lieu:
            embed.add_field(name="📍 Lieu", value=job.lieu, inline=True)

        if job.salaire:
            embed.add_field(name="💰 Salaire", value=job.salaire, inline=True)

        # Description (limitée)
        if job.description:
            desc_short = job.description[:200] + "..." if len(job.description) > 200 else job.description
            embed.add_field(name="📝 Description", value=desc_short, inline=False)

        # Source et lien
        embed.add_field(name="🌐 Source", value=job.source_site.capitalize(), inline=True)
        embed.add_field(name="🔗 Postuler", value=f"[Voir l'offre]({job.url})", inline=True)

        # Footer
        embed.set_footer(text=f"Bot Alternance • {job.source_site}")

        return embed

    async def start(self):
        """Démarre le bot"""
        if not self.settings.validate():
            raise ValueError("Configuration invalide")

        await super().start(self.settings.discord.bot_token)

    async def close(self):
        """Ferme le bot proprement"""
        if self.monitoring_task:
            self.monitoring_task.cancel()

        await self.db_manager.close()
        await super().close()

    # Commandes de base intégrées
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Teste la latence du bot"""
        latency = round(self.latency * 1000)
        await ctx.send(f"🏓 Pong! Latence: {latency}ms")

    @commands.command(name='status')
    async def status(self, ctx):
        """Affiche le statut du bot"""
        embed = discord.Embed(
            title="📊 Statut du Bot",
            color=discord.Color.blue()
        )

        # Informations générales
        embed.add_field(
            name="🤖 Bot",
            value=f"Actif depuis {(datetime.now() - self.get_cog('Jishaku').start_time).seconds // 3600}h" if self.get_cog('Jishaku') else "Actif",
            inline=True
        )

        # Sites activés
        enabled_sites = self.settings.get_enabled_sites()
        embed.add_field(
            name="🌐 Sites surveillés",
            value=", ".join(enabled_sites) if enabled_sites else "Aucun",
            inline=True
        )

        # Monitoring
        status_text = "🟢 Actif" if self.monitoring_active else "🔴 Inactif"
        embed.add_field(
            name="🔍 Monitoring",
            value=status_text,
            inline=True
        )

        await ctx.send(embed=embed)