"""
Commandes Discord pour la gestion des métiers et préférences
"""

import discord
from discord.ext import commands
from typing import List

def setup_commands(bot):
    """Configure toutes les commandes du bot"""

    @bot.command(name='help')
    async def help_command(ctx):
        """Affiche l'aide du bot"""
        embed = discord.Embed(
            title="🤖 Bot Alternance - Aide",
            description="Bot de monitoring d'offres d'alternance en temps réel",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📋 Commandes principales",
            value="""
            `!alt help` - Affiche cette aide
            `!alt ping` - Teste la latence
            `!alt status` - Statut du bot
            """,
            inline=False
        )

        embed.add_field(
            name="🎯 Gestion des métiers",
            value="""
            `!alt metiers` - Liste des métiers disponibles
            `!alt subscribe <id>` - S'abonner à un métier
            `!alt unsubscribe <id>` - Se désabonner d'un métier
            `!alt mes-metiers` - Mes métiers suivis
            """,
            inline=False
        )

        embed.add_field(
            name="⚙️ Préférences",
            value="""
            `!alt profil` - Voir mon profil
            `!alt lieu <ville>` - Définir ma localisation
            `!alt recent [métier]` - Offres récentes
            """,
            inline=False
        )

        embed.set_footer(text="Préfixe des commandes: !alt")
        await ctx.send(embed=embed)

    @bot.command(name='metiers')
    async def list_metiers(ctx):
        """Liste tous les métiers disponibles"""
        try:
            metiers = await bot.db_manager.get_all_metiers()

            if not metiers:
                await ctx.send("❌ Aucun métier configuré.")
                return

            # Grouper par catégorie
            categories = {}
            for metier in metiers:
                cat = metier.category or "Autres"
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(metier)

            embed = discord.Embed(
                title="🎯 Métiers disponibles",
                description="Utilisez `!alt subscribe <id>` pour vous abonner",
                color=discord.Color.green()
            )

            for category, metiers_list in categories.items():
                metiers_text = "\n".join([
                    f"`{metier.id}` - {metier.nom}"
                    for metier in metiers_list
                ])
                embed.add_field(
                    name=f"📂 {category}",
                    value=metiers_text,
                    inline=False
                )

            await ctx.send(embed=embed)

        except Exception as e:
            bot.logger.error(f"Erreur liste métiers: {e}")
            await ctx.send("❌ Erreur lors de la récupération des métiers.")

    @bot.command(name='subscribe')
    async def subscribe_metier(ctx, metier_id: int = None):
        """S'abonner à un métier"""
        if metier_id is None:
            await ctx.send("❌ Veuillez spécifier l'ID du métier. Utilisez `!alt metiers` pour voir la liste.")
            return

        try:
            # Créer ou récupérer l'utilisateur
            user = await bot.db_manager.create_or_update_user(
                discord_id=str(ctx.author.id),
                username=ctx.author.display_name
            )

            # Vérifier que le métier existe
            metier = await bot.db_manager.get_metier_by_id(metier_id)
            if not metier:
                await ctx.send(f"❌ Métier avec l'ID {metier_id} introuvable.")
                return

            # Ajouter le métier
            success = await bot.db_manager.add_user_metier(str(ctx.author.id), metier_id)

            if success:
                await ctx.send(f"✅ Vous êtes maintenant abonné au métier **{metier.nom}**!")
            else:
                await ctx.send(f"ℹ️ Vous êtes déjà abonné au métier **{metier.nom}**.")

        except Exception as e:
            bot.logger.error(f"Erreur subscribe: {e}")
            await ctx.send("❌ Erreur lors de l'abonnement.")

    @bot.command(name='unsubscribe')
    async def unsubscribe_metier(ctx, metier_id: int = None):
        """Se désabonner d'un métier"""
        if metier_id is None:
            await ctx.send("❌ Veuillez spécifier l'ID du métier.")
            return

        try:
            # Vérifier que le métier existe
            metier = await bot.db_manager.get_metier_by_id(metier_id)
            if not metier:
                await ctx.send(f"❌ Métier avec l'ID {metier_id} introuvable.")
                return

            # Retirer le métier
            success = await bot.db_manager.remove_user_metier(str(ctx.author.id), metier_id)

            if success:
                await ctx.send(f"✅ Vous êtes maintenant désabonné du métier **{metier.nom}**.")
            else:
                await ctx.send(f"ℹ️ Vous n'étiez pas abonné au métier **{metier.nom}**.")

        except Exception as e:
            bot.logger.error(f"Erreur unsubscribe: {e}")
            await ctx.send("❌ Erreur lors du désabonnement.")

    @bot.command(name='mes-metiers')
    async def my_metiers(ctx):
        """Affiche les métiers suivis par l'utilisateur"""
        try:
            user = await bot.db_manager.get_user_by_discord_id(str(ctx.author.id))

            if not user or not user.metiers:
                await ctx.send("ℹ️ Vous ne suivez aucun métier. Utilisez `!alt metiers` pour voir la liste disponible.")
                return

            embed = discord.Embed(
                title="🎯 Vos métiers suivis",
                description=f"{ctx.author.display_name}, voici vos abonnements:",
                color=discord.Color.blue()
            )

            metiers_text = "\n".join([
                f"• **{metier.nom}** (ID: {metier.id})"
                for metier in user.metiers
            ])

            embed.add_field(
                name="📋 Métiers",
                value=metiers_text,
                inline=False
            )

            if user.preferred_location:
                embed.add_field(
                    name="📍 Localisation préférée",
                    value=user.preferred_location,
                    inline=True
                )

            await ctx.send(embed=embed)

        except Exception as e:
            bot.logger.error(f"Erreur mes-metiers: {e}")
            await ctx.send("❌ Erreur lors de la récupération de vos métiers.")

    @bot.command(name='profil')
    async def show_profile(ctx):
        """Affiche le profil utilisateur"""
        try:
            user = await bot.db_manager.get_user_by_discord_id(str(ctx.author.id))

            if not user:
                await ctx.send("ℹ️ Profil non trouvé. Utilisez une commande pour créer votre profil.")
                return

            embed = discord.Embed(
                title="👤 Votre profil",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="🆔 Nom d'utilisateur",
                value=user.username,
                inline=True
            )

            embed.add_field(
                name="📅 Membre depuis",
                value=user.created_at.strftime("%d/%m/%Y"),
                inline=True
            )

            embed.add_field(
                name="🎯 Métiers suivis",
                value=str(len(user.metiers)) if user.metiers else "0",
                inline=True
            )

            if user.preferred_location:
                embed.add_field(
                    name="📍 Localisation",
                    value=user.preferred_location,
                    inline=True
                )

            if user.max_distance:
                embed.add_field(
                    name="📏 Rayon de recherche",
                    value=f"{user.max_distance} km",
                    inline=True
                )

            embed.add_field(
                name="🔔 Statut",
                value="Actif" if user.is_active else "Inactif",
                inline=True
            )

            await ctx.send(embed=embed)

        except Exception as e:
            bot.logger.error(f"Erreur profil: {e}")
            await ctx.send("❌ Erreur lors de la récupération du profil.")

    @bot.command(name='lieu')
    async def set_location(ctx, *, location: str = None):
        """Définit la localisation préférée"""
        if not location:
            await ctx.send("❌ Veuillez spécifier une ville. Exemple: `!alt lieu Paris`")
            return

        try:
            # Créer ou mettre à jour l'utilisateur
            user = await bot.db_manager.create_or_update_user(
                discord_id=str(ctx.author.id),
                username=ctx.author.display_name,
                preferred_location=location
            )

            await ctx.send(f"✅ Votre localisation a été définie sur **{location}**.")

        except Exception as e:
            bot.logger.error(f"Erreur set location: {e}")
            await ctx.send("❌ Erreur lors de la sauvegarde de la localisation.")

    @bot.command(name='recent')
    async def show_recent_jobs(ctx, metier_id: int = None):
        """Affiche les offres récentes"""
        try:
            jobs = await bot.db_manager.get_recent_offres(metier_id=metier_id, hours=24)

            if not jobs:
                await ctx.send("ℹ️ Aucune offre récente trouvée.")
                return

            embed = discord.Embed(
                title="📋 Offres récentes (24h)",
                color=discord.Color.orange()
            )

            # Limiter à 10 offres pour éviter de dépasser la limite Discord
            for job in jobs[:10]:
                job_info = f"🏢 {job.entreprise or 'N/A'}\n📍 {job.lieu or 'N/A'}\n🌐 {job.source_site}"

                embed.add_field(
                    name=job.titre,
                    value=job_info,
                    inline=True
                )

            if len(jobs) > 10:
                embed.set_footer(text=f"... et {len(jobs) - 10} autres offres")

            await ctx.send(embed=embed)

        except Exception as e:
            bot.logger.error(f"Erreur recent jobs: {e}")
            await ctx.send("❌ Erreur lors de la récupération des offres récentes.")

    # Commandes administrateur
    @bot.command(name='admin-stats')
    @commands.has_permissions(administrator=True)
    async def admin_stats(ctx):
        """Statistiques administrateur (réservé aux admins)"""
        try:
            # Statistiques de base (à implémenter selon les besoins)
            embed = discord.Embed(
                title="📊 Statistiques administrateur",
                color=discord.Color.gold()
            )

            # Compter les utilisateurs actifs
            # (nécessiterait une méthode dans le database manager)

            embed.add_field(
                name="🤖 Statut bot",
                value="Opérationnel",
                inline=True
            )

            embed.add_field(
                name="🔍 Monitoring",
                value="Actif" if bot.monitoring_active else "Inactif",
                inline=True
            )

            embed.add_field(
                name="🌐 Sites surveillés",
                value=", ".join(bot.settings.get_enabled_sites()),
                inline=False
            )

            await ctx.send(embed=embed)

        except Exception as e:
            bot.logger.error(f"Erreur admin stats: {e}")
            await ctx.send("❌ Erreur lors de la récupération des statistiques.")