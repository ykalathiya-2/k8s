#!/bin/bash

# Build all Docker images for microservices

echo "🐳 Building Docker images for microservices..."
echo ""

# Build Auth Service
echo "📦 Building auth-service..."
cd auth-service
docker build -t auth-service:latest .
cd ..

# Build User Service
echo "📦 Building user-service..."
cd user-service
docker build -t user-service:latest .
cd ..

# Build Chat Service
echo "📦 Building chat-service..."
cd chat-service
docker build -t chat-service:latest .
cd ..

# Build API Gateway
echo "📦 Building api-gateway..."
cd api-gateway
docker build -t api-gateway:latest .
cd ..

# Build Frontend
echo "📦 Building frontend..."
cd frontend
docker build -t frontend:latest .
cd ..

echo ""
echo "✅ All images built successfully!"
echo ""
echo "Images created:"
echo "  - auth-service:latest"
echo "  - user-service:latest"
echo "  - chat-service:latest"
echo "  - api-gateway:latest"
echo "  - frontend:latest"
