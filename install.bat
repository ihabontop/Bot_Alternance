@echo off
echo 🚀 Installation du Bot Discord - Monitoring d'Alternances
echo =========================================================

echo.
echo 📦 Vérification de Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python n'est pas installé ou pas dans le PATH
    echo Téléchargez Python depuis https://python.org
    pause
    exit /b 1
)

echo ✅ Python trouvé

echo.
echo 📦 Installation des dépendances...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Erreur lors de l'installation des dépendances
    pause
    exit /b 1
)

echo ✅ Dépendances installées

echo.
echo 📁 Création des dossiers...
mkdir logs 2>nul
mkdir data 2>nul
echo ✅ Dossiers créés

echo.
echo 📋 Configuration...
if not exist .env (
    echo ⚠️  Fichier .env manquant
    echo Copiez .env.example vers .env et configurez vos paramètres
    copy .env.example .env >nul
    echo ✅ Fichier .env créé depuis l'exemple
) else (
    echo ✅ Fichier .env trouvé
)

echo.
echo 🎉 Installation terminée!
echo.
echo 📝 Prochaines étapes:
echo 1. Configurez votre fichier .env avec vos tokens Discord et PostgreSQL
echo 2. Configurez votre base de données PostgreSQL
echo 3. Lancez: python scripts/setup_database.py
echo 4. Testez les scrapers: python scripts/test_scrapers.py --all
echo 5. Lancez le bot: python run.py
echo.

pause