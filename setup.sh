#!/bin/bash

# ====================================
# Snow Analysis - Setup Script
# ====================================
# This script sets up the Python environment locally
# and starts the PostGIS Docker container

set -e  # Exit on error

echo ""
echo "======================================"
echo "❄️  Snow Analysis - Setup"
echo "======================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker n'est pas démarré!"
    echo "   → Lancez Docker Desktop et réessayez"
    exit 1
fi

echo "✓ Docker est démarré"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Fichier .env non trouvé"
    echo "   → Création depuis .env.example"
    cp .env.example .env
    echo "   ✓ .env créé"
    echo ""
    echo "⚠️  IMPORTANT: Éditez .env avec vos identifiants Copernicus!"
    echo "   → CDSE_USERNAME et CDSE_PASSWORD"
    echo ""
fi

# Start PostGIS container
echo "🐳 Démarrage du conteneur PostGIS..."
docker-compose up -d

echo ""
echo "⏳ Attente que PostGIS soit prêt..."
sleep 5

# Wait for PostGIS to be healthy
until docker-compose exec -T postgis pg_isready -U postgres > /dev/null 2>&1; do
    echo "   En attente de PostGIS..."
    sleep 2
done

echo "✓ PostGIS est prêt!"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✓ $PYTHON_VERSION détecté"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel Python..."
    python3 -m venv venv
    echo "✓ Environnement virtuel créé"
else
    echo "✓ Environnement virtuel déjà existant"
fi

echo ""
echo "📦 Installation des dépendances Python..."

# Activate virtual environment and install dependencies
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
pip install -r scripts/requirements.txt

echo "✓ Dépendances installées"
echo ""

echo "======================================"
echo "✅ Installation terminée!"
echo "======================================"
echo ""
echo "🚀 Prochaines étapes:"
echo ""
echo "1. Configurez vos identifiants dans .env:"
echo "   → CDSE_USERNAME et CDSE_PASSWORD"
echo ""
echo "2. Activez l'environnement virtuel:"
echo "   → source venv/bin/activate"
echo ""
echo "3. Lancez le pipeline ETL:"
echo "   → python scripts/etl_pipeline.py"
echo ""
echo "4. Visualisez dans QGIS:"
echo "   → Connexion: localhost:5432"
echo "   → Base: snowdb"
echo ""
echo "======================================"
echo ""
