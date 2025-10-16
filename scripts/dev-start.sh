#!/bin/bash
# DevFlow ERP Backend - Development Environment Startup Script

set -e

echo "========================================="
echo "DevFlow ERP - Development Environment"
echo "========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and fill in the values"
    exit 1
fi

echo "✓ Environment file found"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running!"
    echo "Please start Docker and try again"
    exit 1
fi

echo "✓ Docker is running"

# Stop existing containers
echo ""
echo "Stopping existing containers..."
docker-compose down

# Start services
echo ""
echo "Starting services..."
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo ""
echo "Waiting for PostgreSQL to be ready..."
until docker-compose exec -T postgres pg_isready -U devflow > /dev/null 2>&1; do
    echo "  Waiting..."
    sleep 2
done

echo "✓ PostgreSQL is ready"

# Wait for Redis to be ready
echo ""
echo "Waiting for Redis to be ready..."
until docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    echo "  Waiting..."
    sleep 1
done

echo "✓ Redis is ready"

# Run migrations
echo ""
echo "Running database migrations..."
source .venv/bin/activate
alembic upgrade head

# Start backend
echo ""
echo "Starting backend service..."
docker-compose up -d backend

echo ""
echo "========================================="
echo "✓ Development environment is ready!"
echo "========================================="
echo ""
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/api/docs"
echo "PostgreSQL: localhost:5432"
echo "Redis: localhost:6379"
echo ""
echo "To view logs: docker-compose logs -f backend"
echo "To stop: docker-compose down"
echo ""
