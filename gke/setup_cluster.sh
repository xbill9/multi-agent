#!/bin/bash
set -e

PROJECT_ID=$(gcloud config get-value project)
REGION=${GOOGLE_CLOUD_LOCATION:-us-central1}
CLUSTER_NAME="multi-agent-cluster"

echo "Using Project: $PROJECT_ID"
echo "Using Region: $REGION"

# Enable necessary APIs
echo "Enabling Container API..."
gcloud services enable container.googleapis.com

# Check if cluster exists
if gcloud container clusters describe $CLUSTER_NAME --region $REGION --project $PROJECT_ID > /dev/null 2>&1; then
  echo "Cluster $CLUSTER_NAME already exists."
else
  echo "Creating GKE Autopilot cluster $CLUSTER_NAME..."
  gcloud container clusters create-auto $CLUSTER_NAME \
    --region $REGION \
    --project $PROJECT_ID
fi

# Get credentials
echo "Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION --project $PROJECT_ID
