#!/bin/bash

# Setup script for License SKU Microservice

set -e

echo "🚀 Setting up License SKU Microservice..."

# Prefer a supported Python version for native dependencies
PYTHON_BIN=""
if command -v python3.12 &> /dev/null; then
    PYTHON_BIN="python3.12"
elif command -v python3.13 &> /dev/null; then
    PYTHON_BIN="python3.13"
elif command -v python3.14 &> /dev/null; then
    echo "❌ Python 3.14 is installed, but this project dependencies do not build reliably on 3.14."
    echo "   Install Python 3.12 first (recommended): brew install python@3.12"
    exit 1
elif command -v python3 &> /dev/null; then
    PYTHON_BIN="python3"
else
    echo "❌ Python 3 is not installed. Please install Python 3.12 or 3.13."
    exit 1
fi

echo "✅ Python found: $($PYTHON_BIN --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    "$PYTHON_BIN" -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "🔄 Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Copy environment file if not exists
if [ ! -f ".env" ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
else
    echo "✅ .env file already exists"
fi

# Check for Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker found: $(docker --version)"
    
    # Check for docker-compose
    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose found: $(docker-compose --version)"
        echo ""
        echo "To start the service with Docker Compose:"
        echo "  docker-compose up -d"
    fi
else
    echo "⚠️  Docker not found. You can still run locally or install Docker."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Start PostgreSQL and Redis (Docker or locally)"
echo "3. Run the application:"
echo "   source venv/bin/activate"
echo "   python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Or use Docker Compose:"
echo "  docker-compose up -d"
echo ""
echo "Then visit http://localhost:8000/docs for API documentation"
