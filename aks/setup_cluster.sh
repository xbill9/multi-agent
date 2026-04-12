#!/bin/bash
# aks/setup_cluster.sh - Set up an Azure Kubernetes Service (AKS) cluster

# Exit on error
set -e

# Default configurations
AZ_LOCATION=${AZ_LOCATION:-"westus2"}
AZ_RESOURCE_GROUP=${AZ_RESOURCE_GROUP:-"adk-rg-aks"}
HOSTNAME_ID=$(hostname | tr -cd '[:alnum:]' | tr '[:upper:]' '[:lower:]' | cut -c1-10)
AZ_ACR_NAME=${AZ_ACR_NAME:-"adkacr${HOSTNAME_ID}v2"}
AZ_AKS_CLUSTER_NAME=${AZ_AKS_CLUSTER_NAME:-"adk-aks-${HOSTNAME_ID}"}

echo "=== Azure AKS Cluster Setup ==="
echo "Azure Location: $AZ_LOCATION"
echo "Resource Group: $AZ_RESOURCE_GROUP"
echo "ACR Name:       $AZ_ACR_NAME"
echo "AKS Cluster:    $AZ_AKS_CLUSTER_NAME"
echo "==============================="

# 1. Create Resource Group
echo "Ensuring Resource Group $AZ_RESOURCE_GROUP exists in $AZ_LOCATION..."
az group create --name "$AZ_RESOURCE_GROUP" --location "$AZ_LOCATION"

# 2. Create ACR
echo "Checking if ACR $AZ_ACR_NAME exists..."
if ! az acr show --name "$AZ_ACR_NAME" --resource-group "$AZ_RESOURCE_GROUP" > /dev/null 2>&1; then
    echo "Creating ACR $AZ_ACR_NAME..."
    az acr create --name "$AZ_ACR_NAME" --resource-group "$AZ_RESOURCE_GROUP" --sku Basic
else
    echo "ACR $AZ_ACR_NAME already exists."
fi

# 3. Create AKS Cluster
echo "Checking if AKS Cluster $AZ_AKS_CLUSTER_NAME exists..."
if ! az aks show --name "$AZ_AKS_CLUSTER_NAME" --resource-group "$AZ_RESOURCE_GROUP" > /dev/null 2>&1; then
    echo "Creating AKS Cluster $AZ_AKS_CLUSTER_NAME (this may take several minutes)..."
    az aks create \
        --resource-group "$AZ_RESOURCE_GROUP" \
        --name "$AZ_AKS_CLUSTER_NAME" \
        --node-count 1 \
        --generate-ssh-keys \
        --attach-acr "$AZ_ACR_NAME" \
        --location "$AZ_LOCATION"
else
    echo "AKS Cluster $AZ_AKS_CLUSTER_NAME already exists."
fi

# 4. Get AKS Credentials
echo "Updating kubeconfig for AKS Cluster $AZ_AKS_CLUSTER_NAME..."
az aks get-credentials --resource-group "$AZ_RESOURCE_GROUP" --name "$AZ_AKS_CLUSTER_NAME" --overwrite-existing

echo "AKS Setup Complete!"
