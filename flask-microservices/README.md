# Flask Microservices on Kubernetes

A scalable, microservices-based chat application deployed on Kubernetes.

## 🏗️ Architecture

The application has been decomposed from a monolith into 5 microservices:

1.  **Frontend**: UI (HTML/JS) serving the SPA.
2.  **API Gateway**: Entry point, routes requests to backend services.
3.  **Auth Service**: Handles registration, login, and JWT issuance.
4.  **User Service**: Manages user profiles.
5.  **Chat Service**: Handles real-time messaging (WebSocket) and rooms.

> See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed diagrams (Before vs. After) and design decisions.

## 🚀 Deployment

### Prerequisites
*   Docker
*   Kubernetes Cluster (e.g., `kind`)
*   `kubectl`

### Podman Users
If you are using Podman instead of Docker:
1.  Run the dedicated deployment script:
    ```bash
    ./deploy-podman.sh
    ```
    This script handles the `KIND_EXPERIMENTAL_PROVIDER=podman` setup and builds images using `podman`.

### Quick Start (Docker/Kind)

1.  **Create Cluster**:
    ```bash
    kind create cluster --name flask-chat --config kind/kind-config.yaml
    ```

2.  **Build & Load Images**:
    ```bash
    ./build-all.sh
    # This script builds all docker images and loads them into the kind cluster
    ```

3.  **Deploy to K8s**:
    ```bash
    kubectl apply -f k8s/
    ```

4.  **Verify**:
    ```bash
    kubectl get pods
    ```

5.  **Access**:
    *   **Frontend**: `http://localhost:30080`
    *   **API**: `http://localhost:30000`

## 📂 Deliverables

*   **Architecture Document**: [ARCHITECTURE.md](ARCHITECTURE.md)
*   **Kubernetes Manifests**: [k8s/](k8s/) directory
*   **Source Code**: [GitHub Repo](#) (This directory)
*   **Screenshots**: See `screenshots/` directory (or generate via `python3 visualize.py`)

## 🧪 Testing

Test the deployment by accessing the frontend or checking service health:

```bash
curl http://localhost:30000/health
```
