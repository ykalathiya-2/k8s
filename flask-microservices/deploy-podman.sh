#!/bin/bash

# Deployment script for Podman users
set -e

echo "🚀 Flask Chat Microservices - Podman Deployment"
echo "=================================================="

# Ensure KIND_EXPERIMENTAL_PROVIDER is set
export KIND_EXPERIMENTAL_PROVIDER=podman

# Check kind cluster
if ! kind get clusters | grep -q "flask-chat"; then
    echo "❌ Cluster 'flask-chat' not found. Please create it first."
    exit 1
fi

echo "🐳 Building images with Podman..."

# Build function
build_image() {
    service=$1
    echo "📦 Building $service..."
    cd $service
    podman build -t $service:latest .
    cd ..
}

build_image "auth-service"
build_image "user-service"
build_image "chat-service"
build_image "api-gateway"
build_image "frontend"

echo ""
echo "📦 Loading images into kind cluster..."
# kind load docker-image works with podman when provider is set
kind load docker-image auth-service:latest --name flask-chat
kind load docker-image user-service:latest --name flask-chat
kind load docker-image chat-service:latest --name flask-chat
kind load docker-image api-gateway:latest --name flask-chat
kind load docker-image frontend:latest --name flask-chat

echo ""
echo "🚀 Deploying to Kubernetes..."
kubectl apply -f k8s/

echo ""
echo "✅ Deployment Complete!"
echo "🌐 Access: http://localhost:30080"
