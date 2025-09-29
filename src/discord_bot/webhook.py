"""
Gestionnaire de notifications webhook Discord
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict
import discord

class WebhookNotifier:
    """Gestionnaire des notifications via webhook Discord"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)

    async def send_job_notification(self, embed: discord.Embed, users: List) -> bool:
        """
        Envoie une notification d'offre via webhook

        Args:
            embed: Embed Discord à envoyer
            users: Liste des utilisateurs à mentionner (optionnel)

        Returns:
            bool: True si envoyé avec succès
        """
        if not self.webhook_url:
            self.logger.error("URL webhook non configurée")
            return False

        try:
            # Construire le message avec mentions
            content = self._build_mention_content(users)

            # Payload webhook
            payload = {
                "content": content,
                "embeds": [embed.to_dict()],
                "username": "Bot Alternance",
                "avatar_url": "https://cdn.discordapp.com/attachments/placeholder.png"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status in [200, 204]:
                        self.logger.info("Notification webhook envoyée avec succès")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Erreur webhook {response.status}: {error_text}")
                        return False

        except Exception as e:
            self.logger.error(f"Erreur envoi webhook: {e}")
            return False

    def _build_mention_content(self, users: List) -> str:
        """Construit le contenu avec les mentions d'utilisateurs"""
        if not users:
            return "🎯 **Nouvelle offre d'alternance disponible !**"

        # Construire les mentions Discord
        mentions = []
        for user in users[:10]:  # Limiter à 10 mentions
            mentions.append(f"<@{user.discord_id}>")

        content = "🎯 **Nouvelle offre d'alternance !**\n"
        if mentions:
            content += f"Notification pour: {', '.join(mentions)}"

        return content

    async def send_system_notification(self, title: str, message: str, color: discord.Color = discord.Color.blue()) -> bool:
        """
        Envoie une notification système

        Args:
            title: Titre de la notification
            message: Message à envoyer
            color: Couleur de l'embed

        Returns:
            bool: True si envoyé avec succès
        """
        if not self.webhook_url:
            return False

        try:
            embed = discord.Embed(
                title=title,
                description=message,
                color=color,
                timestamp=discord.utils.utcnow()
            )

            embed.set_footer(text="Bot Alternance - Système")

            payload = {
                "embeds": [embed.to_dict()],
                "username": "Bot Alternance - Système"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    return response.status in [200, 204]

        except Exception as e:
            self.logger.error(f"Erreur notification système: {e}")
            return False

    async def send_error_notification(self, error: str, context: str = None) -> bool:
        """Envoie une notification d'erreur"""
        title = "⚠️ Erreur détectée"
        message = f"**Erreur:** {error}"

        if context:
            message += f"\n**Contexte:** {context}"

        return await self.send_system_notification(
            title,
            message,
            discord.Color.red()
        )

    async def send_monitoring_summary(self, summary: Dict) -> bool:
        """
        Envoie un résumé du monitoring

        Args:
            summary: Dictionnaire avec les statistiques du monitoring
        """
        try:
            embed = discord.Embed(
                title="📊 Résumé du monitoring",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )

            # Sites surveillés
            sites_info = []
            for site, stats in summary.get('sites', {}).items():
                sites_info.append(f"• **{site.capitalize()}**: {stats.get('jobs_found', 0)} offres")

            if sites_info:
                embed.add_field(
                    name="🌐 Sites surveillés",
                    value="\n".join(sites_info),
                    inline=False
                )

            # Statistiques globales
            total_jobs = summary.get('total_new_jobs', 0)
            total_notifications = summary.get('total_notifications', 0)

            embed.add_field(
                name="📈 Statistiques",
                value=f"• **Nouvelles offres:** {total_jobs}\n• **Notifications envoyées:** {total_notifications}",
                inline=True
            )

            # Métiers les plus actifs
            top_metiers = summary.get('top_metiers', [])
            if top_metiers:
                metiers_text = "\n".join([
                    f"• {metier['nom']}: {metier['count']} offres"
                    for metier in top_metiers[:5]
                ])
                embed.add_field(
                    name="🎯 Métiers les plus actifs",
                    value=metiers_text,
                    inline=True
                )

            # Durée du monitoring
            duration = summary.get('duration_minutes', 0)
            embed.add_field(
                name="⏱️ Durée du cycle",
                value=f"{duration} minutes",
                inline=True
            )

            embed.set_footer(text="Monitoring automatique")

            payload = {
                "embeds": [embed.to_dict()],
                "username": "Bot Alternance - Monitoring"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    return response.status in [200, 204]

        except Exception as e:
            self.logger.error(f"Erreur résumé monitoring: {e}")
            return False

    async def test_webhook(self) -> bool:
        """Teste la connexion webhook"""
        return await self.send_system_notification(
            "✅ Test webhook",
            "Le webhook fonctionne correctement !",
            discord.Color.green()
        )