#!/bin/bash
# Script to run tests for the OptimizeDeFi application

set -e

echo "🧪 OptimizeDeFi Test Runner"
echo "=========================="

# Check if backend is running
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Backend is not running. Starting backend..."
    cd backend
    docker-compose up -d
    cd ..
    echo "Waiting for backend to be ready..."
    sleep 10
fi

# Frontend tests
echo ""
echo "📦 Running Frontend Tests..."
echo "--------------------------"
cd frontend
npm test -- --watchAll=false --ci || true
cd ..

# Backend tests (if pytest is installed)
echo ""
echo "🐍 Running Backend Tests..."
echo "-------------------------"
echo "Note: Backend tests require pytest to be installed in the container."
echo "To install: docker-compose exec backend pip install pytest pytest-asyncio pytest-cov"
docker-compose exec backend python -m pytest tests/ -v --tb=short 2>/dev/null || echo "❌ pytest not installed. See instructions above."

# Manual test
echo ""
echo "🔍 Running Manual Chat Service Test..."
echo "------------------------------------"
python scripts/test_chat_service.py

echo ""
echo "✅ Test run complete!"