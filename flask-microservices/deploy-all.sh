#!/bin/bash

# Complete deployment script for kind cluster

echo "🚀 Flask Chat Microservices - Complete Deployment"
echo "=================================================="
echo ""

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "❌ kind is not installed. Please install kind first:"
    echo "   https://kind.sigs.k8s.io/docs/user/quick-start/"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Create kind cluster if it doesn't exist
if ! kind get clusters | grep -q "flask-chat"; then
    echo "📦 Creating kind cluster..."
    kind create cluster --name flask-chat --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30000
    hostPort: 30000
    protocol: TCP
  - containerPort: 30080
    hostPort: 30080
    protocol: TCP
EOF
    echo "✅ Kind cluster created"
else
    echo "✅ Kind cluster 'flask-chat' already exists"
fi

# Switch context
kubectl cluster-info --context kind-flask-chat

echo ""
echo "🐳 Building Docker images..."
./build-all.sh

echo ""
echo "📦 Loading images into kind cluster..."
kind load docker-image auth-service:latest --name flask-chat
kind load docker-image user-service:latest --name flask-chat
kind load docker-image chat-service:latest --name flask-chat
kind load docker-image api-gateway:latest --name flask-chat
kind load docker-image frontend:latest --name flask-chat

echo ""
echo "🚀 Deploying to Kubernetes..."
./deploy-k8s.sh

echo ""
echo "=================================================="
echo "✅ Deployment Complete!"
echo "=================================================="
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:30080"
echo "   API Gateway: http://localhost:30000/health"
echo ""
echo "📝 Default credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "🔍 Useful commands:"
echo "   kubectl get pods        - View all pods"
echo "   kubectl get services    - View all services"
echo "   kubectl logs <pod>      - View pod logs"
echo "   kind delete cluster --name flask-chat  - Delete cluster"
