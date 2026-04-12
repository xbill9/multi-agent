#!/bin/bash
# aks/deploy-aks.sh - Deploy Multi-Agent System to Azure Kubernetes Service (AKS)

# Exit on error
set -e

# Default configurations
AZ_LOCATION=${AZ_LOCATION:-"westus2"}
AZ_RESOURCE_GROUP=${AZ_RESOURCE_GROUP:-"adk-rg-aks"}
HOSTNAME_ID=$(hostname | tr -cd '[:alnum:]' | tr '[:upper:]' '[:lower:]' | cut -c1-10)
AZ_ACR_NAME=${AZ_ACR_NAME:-"adkacr${HOSTNAME_ID}v2"}
AZ_AKS_CLUSTER_NAME=${AZ_AKS_CLUSTER_NAME:-"adk-aks-${HOSTNAME_ID}"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}

# Credentials and Project Info
PROJECT_ID=$(cat ~/project_id.txt 2>/dev/null || echo "unknown-project")
GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION:-"us-central1"}
GEMINI_API_KEY=$(cat ${HOME}/gemini.key 2>/dev/null || echo "")

# Derived Azure variables
ACR_LOGIN_SERVER="${AZ_ACR_NAME}.azurecr.io"

echo "=== Azure AKS Deployment ==="
echo "Azure Location: $AZ_LOCATION"
echo "Resource Group: $AZ_RESOURCE_GROUP"
echo "ACR Name:       $AZ_ACR_NAME"
echo "AKS Cluster:    $AZ_AKS_CLUSTER_NAME"
echo "============================="

# 1. Ensure Cluster and ACR are set up
./aks/setup_cluster.sh

# 2. Authenticate with ACR
echo "Logging in to Azure Container Registry..."
az acr login --name "$AZ_ACR_NAME"

# 3. Build and Push Docker Images
build_and_push() {
    local name=$1
    local dockerfile=$2
    local tag="${ACR_LOGIN_SERVER}/${name}:${IMAGE_TAG}"
    
    echo "Building $name..."
    docker build -t "$tag" -f "$dockerfile" .
    
    echo "Pushing $name..."
    docker push "$tag"
}

build_and_push "researcher" "agents/researcher/Dockerfile"
build_and_push "judge" "agents/judge/Dockerfile"
build_and_push "content-builder" "agents/content_builder/Dockerfile"
build_and_push "orchestrator" "agents/orchestrator/Dockerfile"
build_and_push "course-creator" "app/Dockerfile"

# 4. Create Secrets in Kubernetes
echo "Creating/Updating adk-secrets in Kubernetes..."
kubectl create secret generic adk-secrets \
    --from-literal=GOOGLE_API_KEY="$GEMINI_API_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

# 5. Deploy to AKS
echo "Deploying to Azure AKS..."
# Use sed to replace variables in manifests.yaml
sed -e "s|\${ACR_LOGIN_SERVER}|$ACR_LOGIN_SERVER|g" \
    -e "s|\${IMAGE_TAG}|$IMAGE_TAG|g" \
    -e "s|\${PROJECT_ID}|$PROJECT_ID|g" \
    aks/manifests.yaml | kubectl apply -f -

echo "Waiting for deployments to complete..."
kubectl rollout status deployment/researcher
kubectl rollout status deployment/judge
kubectl rollout status deployment/content-builder
kubectl rollout status deployment/orchestrator
kubectl rollout status deployment/course-creator

echo "Deployment complete!"
echo "Course Creator External IP (may take a moment to appear):"
kubectl get svc course-creator -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
echo ""
