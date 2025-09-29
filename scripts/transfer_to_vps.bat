@echo off
REM Script de transfert vers VPS Debian 13

echo 📤 Transfert du projet vers VPS Debian 13
echo ==========================================

REM Variables à configurer
set VPS_IP=45.158.77.193
set VPS_USER=alternance_user
set SSH_KEY_PATH=C:\chemin\vers\votre\cle\ssh

echo.
echo ⚠️  CONFIGURATION REQUISE:
echo    - Modifiez les variables VPS_IP, VPS_USER et SSH_KEY_PATH dans ce script
echo    - Assurez-vous d'avoir une clé SSH configurée
echo    - Le VPS doit être accessible via SSH
echo.

REM Vérifier si les variables sont configurées
if "%VPS_IP%"=="VOTRE_IP_VPS" (
    echo ❌ Veuillez configurer VPS_IP dans le script
    pause
    exit /b 1
)

if "%VPS_USER%"=="votre_utilisateur" (
    echo ❌ Veuillez configurer VPS_USER dans le script
    pause
    exit /b 1
)

echo 🔍 Test de connexion SSH...
ssh -i "%SSH_KEY_PATH%" %VPS_USER%@%VPS_IP% "echo 'Connexion SSH OK'"

if %errorlevel% neq 0 (
    echo ❌ Erreur de connexion SSH
    echo Vérifiez:
    echo   - L'IP du VPS: %VPS_IP%
    echo   - L'utilisateur: %VPS_USER%
    echo   - La clé SSH: %SSH_KEY_PATH%
    pause
    exit /b 1
)

echo ✅ Connexion SSH établie

echo.
echo 📦 Création de l'archive du projet...

REM Créer un tar.gz du projet (exclure les dossiers non nécessaires)
tar --exclude=".git" --exclude="__pycache__" --exclude="*.pyc" --exclude="venv" --exclude="logs/*" --exclude="data/*" -czf bot_alternance.tar.gz *

if %errorlevel% neq 0 (
    echo ❌ Erreur lors de la création de l'archive
    pause
    exit /b 1
)

echo ✅ Archive créée: bot_alternance.tar.gz

echo.
echo 📤 Transfert vers le VPS...

REM Transférer l'archive
scp -i "%SSH_KEY_PATH%" bot_alternance.tar.gz %VPS_USER%@%VPS_IP%:~/

if %errorlevel% neq 0 (
    echo ❌ Erreur lors du transfert
    pause
    exit /b 1
)

echo ✅ Archive transférée

echo.
echo 📋 Extraction et préparation sur le VPS...

REM Commandes à exécuter sur le VPS
ssh -i "%SSH_KEY_PATH%" %VPS_USER%@%VPS_IP% << 'ENDSSH'
echo "🗂️  Extraction du projet..."

# Créer le répertoire s'il n'existe pas
mkdir -p ~/Bot_Alternance

# Sauvegarder l'ancien répertoire si il existe
if [ -d ~/Bot_Alternance_old ]; then
    rm -rf ~/Bot_Alternance_old
fi

if [ -d ~/Bot_Alternance ] && [ "$(ls -A ~/Bot_Alternance)" ]; then
    echo "📦 Sauvegarde de l'ancienne version..."
    mv ~/Bot_Alternance ~/Bot_Alternance_old
    mkdir -p ~/Bot_Alternance
fi

# Extraire la nouvelle version
tar -xzf ~/bot_alternance.tar.gz -C ~/Bot_Alternance/

# Supprimer l'archive
rm ~/bot_alternance.tar.gz

echo "✅ Projet extrait dans ~/Bot_Alternance/"

# Si ancienne version existe, copier la config
if [ -f ~/Bot_Alternance_old/.env ]; then
    echo "📋 Récupération de l'ancienne configuration..."
    cp ~/Bot_Alternance_old/.env ~/Bot_Alternance/.env
    echo "✅ Configuration récupérée"
fi

echo "✅ Préparation terminée"
ENDSSH

if %errorlevel% neq 0 (
    echo ❌ Erreur lors de l'extraction sur le VPS
    pause
    exit /b 1
)

REM Nettoyer l'archive locale
del bot_alternance.tar.gz

echo.
echo 🎉 Transfert terminé avec succès!
echo.
echo 📋 Prochaines étapes sur le VPS:
echo 1. Connectez-vous: ssh -i "%SSH_KEY_PATH%" %VPS_USER%@%VPS_IP%
echo 2. Allez dans le dossier: cd ~/Bot_Alternance
echo 3. Exécutez le script de déploiement: chmod +x scripts/deploy_vps.sh && ./scripts/deploy_vps.sh
echo 4. Configurez le fichier .env avec vos tokens
echo 5. Démarrez le bot: ./manage.sh start
echo.

pause