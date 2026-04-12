#!/bin/bash

# Only exit on error if the script is being executed, not sourced.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  set -euo pipefail
fi

# --- Function for error handling ---
handle_error() {
  echo "Error: $1" >&2
  if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    return 1
  else
    exit 1
  fi
}

# Source environment variables
source ./set_env.sh

# --- Part 1: Configuration ---
REGION="${REGION:-us-central1}"
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [[ -z "$PROJECT_ID" || "$PROJECT_ID" == "(unset)" ]]; then
    handle_error "No project ID set. Run 'gcloud config set project [PROJECT_ID]'." || return 1
fi

ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
if [[ -z "$ACCOUNT" ]]; then
    handle_error "No active gcloud account found. Run 'gcloud auth login'." || return 1
fi

echo "--- Setting up GKE MCP for project: $PROJECT_ID ---"

echo "Enabling Services..."
gcloud services enable \
    container.googleapis.com \
    compute.googleapis.com \
    apikeys.googleapis.com

echo "Enabling GKE MCP server..."
gcloud beta services mcp enable container.googleapis.com

echo "Assigning IAM roles for GKE MCP..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="user:$ACCOUNT" \
    --role="roles/mcp.toolUser" --quiet

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="user:$ACCOUNT" \
    --role="roles/container.clusterViewer" --quiet

# Add IAM roles for default Compute Engine service account
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
DEFAULT_SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

echo "Assigning IAM roles for default service account: $DEFAULT_SA"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$DEFAULT_SA" \
    --role="roles/mcp.toolUser" --quiet

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$DEFAULT_SA" \
    --role="roles/container.clusterViewer" --quiet

echo "Checking for existing API Key for GKE MCP..."
KEY_NAME=$(gcloud services api-keys list --filter='displayName="GKE MCP Key"' --format="value(name)" --limit=1)

if [[ -z "$KEY_NAME" ]]; then
    echo "Creating API Key for GKE MCP..."
    gcloud services api-keys create --display-name="GKE MCP Key" || echo "API Key creation failed."
    
    # Wait for the key to be available (max 30 seconds)
    echo "Waiting for API Key to be ready..."
    for i in {1..10}; do
        KEY_NAME=$(gcloud services api-keys list --filter='displayName="GKE MCP Key"' --format="value(name)" --limit=1)
        if [[ -n "$KEY_NAME" ]]; then
            break
        fi
        sleep 3
    done
else
    echo "Using existing API Key: $KEY_NAME"
fi

if [[ -z "$KEY_NAME" ]]; then
    handle_error "Failed to retrieve or create GKE MCP API Key." || return 1
fi

echo "Restricting API Key to GKE API..."
gcloud services api-keys update "$KEY_NAME" --api-target=service=container.googleapis.com --quiet

echo "Retrieving API Key string..."
GKE_MCP=$(gcloud services api-keys get-key-string "$KEY_NAME" --format="value(keyString)")

# Generate and export GKE_TOKEN
echo "Generating GKE_TOKEN (Access Token)..."
GKE_TOKEN=$(gcloud auth print-access-token)
export GKE_TOKEN

if [[ -n "$GKE_MCP" ]]; then
    export GKE_MCP
    echo "GKE MCP API Key retrieved."

    echo "Configuring .gemini/settings.json for GKE MCP..."
    mkdir -p .gemini
    if [[ ! -f ".gemini/settings.json" ]]; then
        echo "{}" > .gemini/settings.json
    fi

    if command -v jq >/dev/null 2>&1; then
        jq '.mcpServers["mcp_gke"] = {"httpUrl": "https://container.googleapis.com/mcp", "headers": {"Authorization": "Bearer $GKE_TOKEN"}}' .gemini/settings.json > .gemini/settings.json.tmp && mv .gemini/settings.json.tmp .gemini/settings.json
    else
        echo "Warning: jq not found. Please manually update .gemini/settings.json with:"
        echo "{\"mcpServers\": {\"mcp_gke\": {\"httpUrl\": \"https://container.googleapis.com/mcp\", \"headers\": {\"Authorization\": \"Bearer \$GKE_TOKEN\"}}}}"
    fi

    echo "--- GKE MCP Configuration Summary ---"
    echo "GKE MCP URL: https://container.googleapis.com/mcp"
    echo "Authorization: Bearer \$GKE_TOKEN"
    echo "X-Goog-Api-Key (GKE_MCP): [HIDDEN]"
    echo "IAM Roles assigned: roles/mcp.toolUser, roles/container.clusterViewer"
    echo ""
else
    handle_error "Failed to retrieve GKE MCP API Key string." || return 1
fi

# Environment checks
echo "--- Environment Checks ---"
if [[ -n "${CLOUD_SHELL:-}" ]]; then
    echo "Running in Google Cloud Shell."
elif curl -s -m 2 -i metadata.google.internal | grep -q "Metadata-Flavor: Google"; then
    echo "Running on a Google Cloud VM."
else
    echo "Not running in Google Cloud VM or Shell. Checking ADC..."
    if ! gcloud auth application-default print-access-token >/dev/null 2>&1; then
        echo "Setting ADC Credentials..."
        gcloud auth application-default login
    fi
fi

echo "--- GKE MCP Setup complete ---"
