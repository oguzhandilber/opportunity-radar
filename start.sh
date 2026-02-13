#!/bin/bash

# Opportunity Radar - Quick Start Script

set -e

echo "🚀 Starting Opportunity Radar..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys before continuing."
    exit 1
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    exit 1
fi

# Build and start
echo "🔨 Building containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "✅ Opportunity Radar is running!"
echo ""
echo "📊 Frontend: http://localhost:3000"
echo "🔌 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f"
