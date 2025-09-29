# Makefile pour Bot Discord Monitoring d'Alternances

.PHONY: help install setup test run clean

# Variables
PYTHON := python
PIP := pip
VENV := venv

help: ## Affiche cette aide
	@echo "Bot Discord - Monitoring d'Alternances"
	@echo "====================================="
	@echo ""
	@echo "Commandes disponibles:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Installe toutes les dépendances
	@echo "📦 Installation des dépendances..."
	$(PIP) install -r requirements.txt
	@echo "✅ Installation terminée"

venv: ## Crée un environnement virtuel
	@echo "🐍 Création de l'environnement virtuel..."
	$(PYTHON) -m venv $(VENV)
	@echo "✅ Environnement virtuel créé dans ./$(VENV)"
	@echo "💡 Activez-le avec: source venv/bin/activate (Linux/Mac) ou venv\\Scripts\\activate (Windows)"

setup: ## Configure la base de données
	@echo "🗄️ Configuration de la base de données..."
	$(PYTHON) scripts/setup_database.py
	@echo "✅ Base de données configurée"

test: ## Teste tous les scrapers
	@echo "🧪 Test de tous les scrapers..."
	$(PYTHON) scripts/test_scrapers.py --all

test-system: ## Teste le système complet
	@echo "🔄 Test du système complet..."
	$(PYTHON) scripts/test_scrapers.py --system

test-site: ## Teste un site spécifique (usage: make test-site SITE=indeed)
	@echo "🧪 Test du site $(SITE)..."
	$(PYTHON) scripts/test_scrapers.py $(SITE)

run: ## Lance le bot
	@echo "🚀 Lancement du bot..."
	$(PYTHON) run.py

run-dev: ## Lance le bot en mode développement
	@echo "🚀 Lancement du bot (mode dev)..."
	$(PYTHON) src/main.py

clean: ## Nettoie les fichiers temporaires
	@echo "🧹 Nettoyage..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/
	@echo "✅ Nettoyage terminé"

logs: ## Affiche les logs récents
	@echo "📋 Logs récents:"
	@tail -n 50 logs/bot.log 2>/dev/null || echo "Aucun log trouvé"

check-config: ## Vérifie la configuration
	@echo "⚙️ Vérification de la configuration..."
	@$(PYTHON) -c "from src.config.settings import Settings; s=Settings(); print('✅ Configuration valide' if s.validate() else '❌ Configuration invalide')"

db-reset: ## Remet à zéro la base de données (ATTENTION: supprime tout!)
	@echo "⚠️ Remise à zéro de la base de données..."
	$(PYTHON) scripts/setup_database.py --reset

format: ## Formate le code avec black (optionnel)
	@echo "🎨 Formatage du code..."
	@black src/ scripts/ || echo "Black non installé, ignoré"

lint: ## Vérifie la qualité du code (optionnel)
	@echo "🔍 Vérification du code..."
	@flake8 src/ scripts/ || echo "Flake8 non installé, ignoré"

requirements: ## Met à jour le fichier requirements.txt
	@echo "📋 Génération de requirements.txt..."
	$(PIP) freeze > requirements.txt
	@echo "✅ Requirements mis à jour"

backup-db: ## Sauvegarde la base de données (PostgreSQL)
	@echo "💾 Sauvegarde de la base de données..."
	@pg_dump -h localhost -U postgres alternance_bot > backup_$(shell date +%Y%m%d_%H%M%S).sql || echo "Erreur sauvegarde DB"

# Commandes pour le développement
dev-install: venv ## Installation complète pour développement
	@echo "🔧 Installation développement..."
	./$(VENV)/bin/pip install -r requirements.txt
	./$(VENV)/bin/pip install black flake8 pytest
	@echo "✅ Environnement de dev prêt"

# Aide détaillée
info: ## Informations sur le projet
	@echo "Bot Discord - Monitoring d'Alternances"
	@echo "====================================="
	@echo "Version Python: $(shell python --version 2>&1)"
	@echo "Répertoire: $(shell pwd)"
	@echo "Config: $(shell test -f .env && echo '✅ .env trouvé' || echo '❌ .env manquant')"
	@echo "Logs: $(shell test -f logs/bot.log && echo '✅ Logs présents' || echo 'ℹ️ Pas encore de logs')"