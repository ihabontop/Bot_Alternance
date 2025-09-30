"""
Module des scrapers pour différents sites d'emploi
"""

from .base import BaseScraper
from .indeed_scraper import IndeedScraper
from .welcometothejungle_scraper import WelcomeToTheJungleScraper
from .labonnealternance_scraper import LaBonneAlternanceScraper
from .test_scraper import TestScraper
from .francetravail_scraper import FranceTravailScraper
from .indeed_selenium_scraper import IndeedSeleniumScraper
from .indeed_cloudscraper import IndeedCloudScraper
from .indeed_vps_scraper import IndeedVPSScraper
# from .indeed_curlcffi_scraper import IndeedCurlCffiScraper  # Incompatible Python 3.13

# Mapping des noms de sites vers leurs classes de scraper
SCRAPERS = {
    'indeed': IndeedScraper,
    'indeed_selenium': IndeedSeleniumScraper,
    'indeed_cloudscraper': IndeedCloudScraper,
    'indeed_vps': IndeedVPSScraper,
    # 'indeed_curlcffi': IndeedCurlCffiScraper,  # Incompatible Python 3.13
    'welcometothejungle': WelcomeToTheJungleScraper,
    'labonnealternance': LaBonneAlternanceScraper,
    'test': TestScraper,
    'francetravail': FranceTravailScraper,
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
    'TestScraper',
    'FranceTravailScraper',
    'SCRAPERS',
    'get_scraper'
]