#!/bin/bash
# Start Opportunity Radar Full Stack

echo "🚀 Starting Opportunity Radar..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start all services
echo "📦 Starting PostgreSQL, Backend, and Frontend..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Initialize database
echo "🗄️ Initializing database..."
cd backend
python -c "
import asyncio
from app.database import init_db
try:
    asyncio.run(init_db())
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'⚠️ Database initialization warning: {e}')
    print('This is normal if database already exists.')
"
cd ..

# Start backend
echo "🔧 Starting backend..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend
echo "⏳ Waiting for backend to start..."
sleep 3

# Start frontend
echo "🎨 Starting frontend..."
cd frontend
npm run dev -- --port 5175 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Opportunity Radar is starting up!"
echo ""
echo "📊 Dashboard: http://localhost:5175"
echo "📚 API Docs:  http://localhost:8000/docs"
echo "🗄️  Database: localhost:5432"
echo ""
echo "📝 Logs:"
echo "  Backend:  tail -f backend/app.log"
echo "  Frontend: tail -f frontend/npm.log"
echo ""
echo "🛑 To stop:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  docker-compose down"

# Keep script running
wait
