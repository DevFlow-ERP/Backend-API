#!/bin/bash
# DevFlow ERP Backend - Production Deployment Script

set -e

echo "========================================="
echo "DevFlow ERP - Production Deployment"
echo "========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file with production settings"
    exit 1
fi

# Verify critical environment variables
source .env

if [ "$ENVIRONMENT" != "production" ]; then
    echo "Error: ENVIRONMENT is not set to 'production'"
    exit 1
fi

if [ "$SECRET_KEY" == "your-secret-key-here-change-this-in-production-min-32-chars" ]; then
    echo "Error: SECRET_KEY is still using default value!"
    echo "Please generate a secure secret key"
    exit 1
fi

echo "✓ Environment configuration validated"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running!"
    exit 1
fi

echo "✓ Docker is running"

# Build production image
echo ""
echo "Building production Docker image..."
docker build -f Dockerfile.prod -t devflow-erp-backend:latest .

echo "✓ Production image built"

# Stop existing containers
echo ""
echo "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Start services
echo ""
echo "Starting production services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check backend health
echo ""
echo "Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ Backend is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Error: Backend failed to start"
        echo "Check logs with: docker-compose -f docker-compose.prod.yml logs backend"
        exit 1
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

echo ""
echo "========================================="
echo "✓ Production deployment successful!"
echo "========================================="
echo ""
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/api/docs"
echo ""
echo "To view logs: docker-compose -f docker-compose.prod.yml logs -f backend"
echo "To stop: docker-compose -f docker-compose.prod.yml down"
echo ""
