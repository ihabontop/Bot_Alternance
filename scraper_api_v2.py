"""
API Flask améliorée pour scraper Indeed avec Selenium sur le VPS
Version 2 avec filtres avancés et évitement 403
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import random
import logging
from datetime import datetime, timedelta
import re

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_driver():
    """Crée un driver Selenium Chromium avec options anti-détection"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    # Rotation des user agents
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')

    # Options supplémentaires pour éviter détection
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Masquer webdriver
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

def parse_date_posted(date_text):
    """Parse la date de publication et retourne les minutes écoulées"""
    if not date_text:
        return None

    date_text = date_text.lower()

    # Pattern pour "il y a X heures/minutes/jours"
    if 'minute' in date_text or 'min' in date_text:
        match = re.search(r'(\d+)', date_text)
        if match:
            return int(match.group(1))
    elif 'heure' in date_text or 'hour' in date_text:
        match = re.search(r'(\d+)', date_text)
        if match:
            return int(match.group(1)) * 60
    elif 'jour' in date_text or 'day' in date_text:
        match = re.search(r'(\d+)', date_text)
        if match:
            return int(match.group(1)) * 1440
    elif "aujourd'hui" in date_text or 'today' in date_text:
        return 30  # Estimé à 30 minutes
    elif 'hier' in date_text or 'yesterday' in date_text:
        return 1440  # 24 heures

    return None

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de santé"""
    return jsonify({"status": "ok", "service": "scraper-api-v2"}), 200

@app.route('/scrape/indeed', methods=['POST'])
def scrape_indeed():
    """Scrape Indeed avec Selenium - Version améliorée"""
    data = request.json
    keyword = data.get('keyword', 'développeur')
    location = data.get('location', 'France')
    max_jobs = data.get('max_jobs', 50)
    max_age_minutes = data.get('max_age_minutes', 60)  # Offres de moins d'1h par défaut

    driver = None
    try:
        jobs = []
        page = 0

        # Initialiser le driver
        driver = create_driver()
        logger.info(f"Driver initialisé pour: {keyword}")

        # Scraper jusqu'à avoir max_jobs offres ou 3 pages max
        while len(jobs) < max_jobs and page < 3:
            # Construire l'URL avec pagination
            start = page * 10
            url = f"https://fr.indeed.com/jobs?q={keyword} alternance&l={location}&fromage=1&sort=date&start={start}"
            logger.info(f"📄 Page {page + 1}: {url}")

            # Charger la page
            driver.get(url)

            # Délai aléatoire pour simuler comportement humain
            time.sleep(random.uniform(3, 6))

            # Parser avec BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            job_cards = soup.select('div.job_seen_beacon, div[data-jk], td.resultContent')

            logger.info(f"   Trouvé {len(job_cards)} cartes sur cette page")

            if len(job_cards) == 0:
                logger.info("   Aucune carte trouvée, arrêt pagination")
                break

            page_jobs_count = 0
            for card in job_cards:
                try:
                    # Job ID
                    job_id = card.get('data-jk')
                    if not job_id:
                        link = card.select_one('a[data-jk]')
                        if link:
                            job_id = link.get('data-jk')

                    if not job_id:
                        continue

                    # Titre
                    title_elem = card.select_one('h2.jobTitle span[title], h2.jobTitle a span')
                    titre = title_elem.get_text(strip=True) if title_elem else ""

                    if not titre:
                        continue

                    # Vérifier alternance dans le titre
                    if not any(word in titre.lower() for word in ['alternance', 'apprentissage', 'apprenti']):
                        continue

                    # Entreprise
                    company_elem = card.select_one('span[data-testid="company-name"], span.companyName')
                    entreprise = company_elem.get_text(strip=True) if company_elem else "Non précisé"

                    # Localisation
                    location_elem = card.select_one('div[data-testid="text-location"], div.companyLocation')
                    lieu = location_elem.get_text(strip=True) if location_elem else ""

                    # Date de publication
                    date_elem = card.select_one('span.date, span[data-testid="myJobsStateDate"]')
                    date_text = date_elem.get_text(strip=True) if date_elem else ""
                    minutes_ago = parse_date_posted(date_text)

                    # Filtrer par date si spécifié
                    if max_age_minutes and minutes_ago and minutes_ago > max_age_minutes:
                        continue

                    # URL
                    job_url = f"https://fr.indeed.com/viewjob?jk={job_id}"

                    jobs.append({
                        'titre': titre,
                        'entreprise': entreprise,
                        'lieu': lieu,
                        'url': job_url,
                        'external_id': job_id,
                        'date_posted': date_text,
                        'minutes_ago': minutes_ago
                    })

                    page_jobs_count += 1

                    # Arrêter si on a atteint max_jobs
                    if len(jobs) >= max_jobs:
                        break

                except Exception as e:
                    logger.error(f"Erreur parsing carte: {e}")
                    continue

            logger.info(f"   ✅ {page_jobs_count} offres valides ajoutées (total: {len(jobs)})")

            # Si cette page n'a donné aucun résultat, arrêter
            if page_jobs_count == 0:
                break

            page += 1

            # Délai entre les pages
            if page < 3 and len(jobs) < max_jobs:
                time.sleep(random.uniform(4, 8))

        logger.info(f"🎉 Total final: {len(jobs)} offres trouvées")
        return jsonify({
            "success": True,
            "jobs": jobs,
            "count": len(jobs),
            "pages_scraped": page
        }), 200

    except Exception as e:
        logger.error(f"Erreur scraping: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)