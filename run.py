#!/usr/bin/env python3
"""
Point d'entrée simplifié pour lancer le bot
"""

import sys
import os

# Ajouter le dossier src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Importer et lancer le main
from main import main
import asyncio

if __name__ == "__main__":
    print("🤖 Lancement du Bot Discord - Monitoring d'Alternances")
    print("="*60)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Au revoir!")
    except Exception as e:
        print(f"\n💥 Erreur fatale: {e}")
        sys.exit(1)