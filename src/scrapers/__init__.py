"""
Module des scrapers pour différents sites d'emploi
"""

from .base import BaseScraper
from .indeed_scraper import IndeedScraper
from .welcometothejungle_scraper import WelcomeToTheJungleScraper
from .labonnealternance_scraper import LaBonneAlternanceScraper

# Mapping des noms de sites vers leurs classes de scraper
SCRAPERS = {
    'indeed': IndeedScraper,
    'welcometothejungle': WelcomeToTheJungleScraper,
    'labonnealternance': LaBonneAlternanceScraper,
}

def get_scraper(site_name: str, config: dict) -> BaseScraper:
    """
    Factory function pour créer un scraper selon le site

    Args:
        site_name: Nom du site ('indeed', 'welcometothejungle', etc.)
        config: Configuration du scraper

    Returns:
        Instance du scraper approprié

    Raises:
        ValueError: Si le site n'est pas supporté
    """
    scraper_class = SCRAPERS.get(site_name.lower())
    if not scraper_class:
        raise ValueError(f"Site '{site_name}' non supporté. Sites disponibles: {list(SCRAPERS.keys())}")

    return scraper_class(config)

__all__ = [
    'BaseScraper',
    'IndeedScraper',
    'WelcomeToTheJungleScraper',
    'LaBonneAlternanceScraper',
    'SCRAPERS',
    'get_scraper'
]