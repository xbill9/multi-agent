#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
cd "$PROJECT_ROOT"

if [ -f ".env" ]; then
  source .env
fi

PROJECT_ID=$(gcloud config get-value project)
REGION=${GOOGLE_CLOUD_LOCATION:-us-central1}

if [[ "$PROJECT_ID" == "" ]]; then
  echo "ERROR: Google Cloud Project not set."
  exit 1
fi

echo "Deploying to GKE in project $PROJECT_ID, region $REGION..."

# 1. Build images
echo "Building images..."
gcloud builds submit --config cloudbuild.yaml .

# 2. Setup cluster
echo "Ensuring GKE cluster is ready..."
./gke/setup_cluster.sh

# 3. Create Secrets
if [[ "$GOOGLE_API_KEY" == "" ]]; then
  echo "WARNING: GOOGLE_API_KEY not found in environment or .env file."
  echo "The agents might fail to call Gemini if not authenticated via other means."
fi

echo "Creating/Updating Kubernetes secrets..."
kubectl create secret generic multi-agent-secrets \
    --from-literal=GOOGLE_API_KEY="$GOOGLE_API_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

# 4. Deploy Manifests
echo "Applying Kubernetes manifests..."
sed "s/PROJECT_ID/$PROJECT_ID/g" gke/manifests.yaml | kubectl apply -f -

echo "Deployment to GKE initiated."
echo "You can check the status with: make status-gke"
echo "Once the external IP is ready, you can run the E2E test with: make test-e2e-gke"
