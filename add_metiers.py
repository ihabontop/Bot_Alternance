"""
Script pour ajouter les nouveaux métiers IT/Cybersécurité
"""

import asyncio
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.manager import DatabaseManager
from config.settings import Settings

async def add_new_metiers():
    """Ajoute les nouveaux métiers IT"""
    settings = Settings()
    db_manager = DatabaseManager(settings.database_url)

    await db_manager.initialize()

    # Nouveaux métiers avec beaucoup de mots-clés
    metiers = [
        {
            'nom': 'Technicien Support',
            'description': 'Support technique et assistance utilisateurs',
            'category': 'IT Support',
            'keywords': [
                'technicien support',
                'support technique',
                'support informatique',
                'helpdesk',
                'service desk',
                'assistance informatique',
                'technicien helpdesk',
                'support utilisateurs',
                'support N1',
                'support N2'
            ],
            'code_rome': 'I1401'
        },
        {
            'nom': 'Technicien Helpdesk',
            'description': 'Assistance technique de premier niveau',
            'category': 'IT Support',
            'keywords': [
                'technicien helpdesk',
                'helpdesk',
                'service desk',
                'support N1',
                'assistance technique',
                'technicien assistance',
                'support informatique',
                'hotline',
                'technicien hotline',
                'support client'
            ],
            'code_rome': 'I1401'
        },
        {
            'nom': 'Administrateur Système et Réseaux',
            'description': 'Administration et maintenance des systèmes et réseaux',
            'category': 'Infrastructure',
            'keywords': [
                'administrateur système',
                'administrateur réseau',
                'sysadmin',
                'admin système',
                'admin réseau',
                'ingénieur système',
                'ingénieur réseau',
                'administrateur infrastructure',
                'technicien système',
                'technicien réseau'
            ],
            'code_rome': 'M1801'
        },
        {
            'nom': 'Analyste SOC',
            'description': 'Analyste en centre opérationnel de sécurité',
            'category': 'Cybersécurité',
            'keywords': [
                'analyste soc',
                'soc analyst',
                'analyste cybersécurité',
                'analyste sécurité',
                'cyber analyste',
                'security analyst',
                'analyste cyber',
                'soc',
                'cybersécurité',
                'sécurité informatique'
            ],
            'code_rome': 'M1802'
        }
    ]

    print("🔄 Ajout des nouveaux métiers...")

    for metier_data in metiers:
        # Vérifier si le métier existe déjà
        existing = await db_manager.get_metier_by_name(metier_data['nom'])

        if existing:
            print(f"⚠️  {metier_data['nom']} existe déjà, mise à jour des mots-clés...")
            # Mettre à jour les mots-clés
            await db_manager.update_metier_keywords(existing.id, metier_data['keywords'])
        else:
            # Créer le nouveau métier
            metier = await db_manager.add_metier(
                nom=metier_data['nom'],
                description=metier_data['description'],
                category=metier_data['category'],
                keywords=metier_data['keywords'],
                code_rome=metier_data['code_rome']
            )
            print(f"✅ {metier_data['nom']} ajouté (ID: {metier.id})")

    # Mettre à jour les mots-clés des métiers existants
    print("\n🔄 Mise à jour des mots-clés pour les métiers existants...")

    existing_metiers = {
        'Développeur Web': [
            'développeur web',
            'web developer',
            'développeur',
            'developer',
            'dev web',
            'full stack',
            'front end',
            'backend',
            'fullstack developer',
            'développeur fullstack'
        ],
        'Data Analyst': [
            'data analyst',
            'analyste données',
            'data',
            'analyst',
            'analyste data',
            'data scientist junior',
            'business analyst',
            'analyste business intelligence',
            'bi analyst',
            'data engineer junior'
        ],
        'Marketing Digital': [
            'marketing digital',
            'digital marketing',
            'community manager',
            'social media',
            'marketing',
            'chargé marketing',
            'traffic manager',
            'seo',
            'content manager',
            'marketing web'
        ]
    }

    for nom, keywords in existing_metiers.items():
        metier = await db_manager.get_metier_by_name(nom)
        if metier:
            await db_manager.update_metier_keywords(metier.id, keywords)
            print(f"✅ {nom} - mots-clés mis à jour ({len(keywords)} mots-clés)")

    print("\n🎉 Terminé!")

    # Afficher tous les métiers
    all_metiers = await db_manager.get_all_metiers()
    print(f"\n📋 Total: {len(all_metiers)} métiers disponibles")
    for m in all_metiers:
        print(f"   - {m.nom} (ID: {m.id})")

if __name__ == '__main__':
    asyncio.run(add_new_metiers())