#!/bin/bash

# Deploy all services to Kubernetes

echo "🚀 Deploying Flask Chat Microservices to Kubernetes..."
echo ""

# Apply all Kubernetes manifests
echo "📋 Applying Kubernetes manifests..."
kubectl apply -f k8s/auth-service.yaml
kubectl apply -f k8s/user-service.yaml
kubectl apply -f k8s/chat-service.yaml
kubectl apply -f k8s/api-gateway.yaml
kubectl apply -f k8s/frontend.yaml

echo ""
echo "✅ All services deployed!"
echo ""

# Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/auth-service
kubectl wait --for=condition=available --timeout=300s deployment/user-service
kubectl wait --for=condition=available --timeout=300s deployment/chat-service
kubectl wait --for=condition=available --timeout=300s deployment/api-gateway
kubectl wait --for=condition=available --timeout=300s deployment/frontend

echo ""
echo "🎉 All deployments are ready!"
echo ""

# Show status
echo "📊 Deployment Status:"
kubectl get deployments
echo ""
echo "📊 Pod Status:"
kubectl get pods
echo ""
echo "📊 Service Status:"
kubectl get services
echo ""

# Get access URLs
API_PORT=$(kubectl get svc api-gateway -o jsonpath='{.spec.ports[0].nodePort}')
FRONTEND_PORT=$(kubectl get svc frontend -o jsonpath='{.spec.ports[0].nodePort}')

echo "🌐 Access URLs:"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "  API Gateway: http://localhost:$API_PORT"
echo ""
echo "📝 Default Login: admin / admin123"
