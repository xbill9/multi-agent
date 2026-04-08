#!/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}"

if [ -f ".env" ]; then
  source .env
fi

if [[ "${GOOGLE_CLOUD_PROJECT}" == "" ]]; then
  GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project -q)
fi
if [[ "${GOOGLE_CLOUD_PROJECT}" == "" ]]; then
  echo "ERROR: Run 'gcloud config set project' command to set active project, or set GOOGLE_CLOUD_PROJECT environment variable."
  exit 1
fi

REGION="${GOOGLE_CLOUD_LOCATION}"
if [[ "${REGION}" == "global" ]]; then
  echo "GOOGLE_CLOUD_LOCATION is set to 'global'. Getting a default location for Cloud Run."
  REGION=""
fi

if [[ "${REGION}" == "" ]]; then
  REGION=$(gcloud config get-value compute/region -q)
  if [[ "${REGION}" == "" ]]; then
    REGION="us-central1"
    echo "WARNING: Cannot get a configured compute region. Defaulting to ${REGION}."
  fi
fi
echo "Using project ${GOOGLE_CLOUD_PROJECT}."
echo "Using compute region ${REGION}."

build_images() {
  echo "Building all images using Cloud Build..."
  gcloud builds submit --project "${GOOGLE_CLOUD_PROJECT}" --config cloudbuild.yaml .
}

deploy_researcher() {
  echo "Deploying researcher..."
  IMAGE_NAME="gcr.io/${GOOGLE_CLOUD_PROJECT}/researcher"
  gcloud run deploy researcher \
    --image "${IMAGE_NAME}" \
    --project $GOOGLE_CLOUD_PROJECT \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT}" \
    --set-env-vars GOOGLE_GENAI_USE_VERTEXAI="false" \
    --set-env-vars GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
    --set-env-vars GENAI_MODEL="${GENAI_MODEL}"
}

deploy_content_builder() {
  echo "Deploying content-builder..."
  IMAGE_NAME="gcr.io/${GOOGLE_CLOUD_PROJECT}/content-builder"
  gcloud run deploy content-builder \
    --image "${IMAGE_NAME}" \
    --project $GOOGLE_CLOUD_PROJECT \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT}" \
    --set-env-vars GOOGLE_GENAI_USE_VERTEXAI="false" \
    --set-env-vars GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
    --set-env-vars GENAI_MODEL="${GENAI_MODEL}"
}

deploy_judge() {
  echo "Deploying judge..."
  IMAGE_NAME="gcr.io/${GOOGLE_CLOUD_PROJECT}/judge"
  gcloud run deploy judge \
    --image "${IMAGE_NAME}" \
    --project $GOOGLE_CLOUD_PROJECT \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT}" \
    --set-env-vars GOOGLE_GENAI_USE_VERTEXAI="false" \
    --set-env-vars GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
    --set-env-vars GENAI_MODEL="${GENAI_MODEL}"
}

deploy_orchestrator() {
  echo "Deploying orchestrator..."
  RESEARCHER_URL=$(gcloud run services describe researcher --region $REGION --format='value(status.url)' --project $GOOGLE_CLOUD_PROJECT)
  CONTENT_BUILDER_URL=$(gcloud run services describe content-builder --region $REGION --format='value(status.url)' --project $GOOGLE_CLOUD_PROJECT)
  JUDGE_URL=$(gcloud run services describe judge --region $REGION --format='value(status.url)' --project $GOOGLE_CLOUD_PROJECT)

  IMAGE_NAME="gcr.io/${GOOGLE_CLOUD_PROJECT}/orchestrator"
  gcloud run deploy orchestrator \
    --image "${IMAGE_NAME}" \
    --project $GOOGLE_CLOUD_PROJECT \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars RESEARCHER_AGENT_CARD_URL=$RESEARCHER_URL/a2a/researcher/.well-known/agent-card.json \
    --set-env-vars JUDGE_AGENT_CARD_URL=$JUDGE_URL/a2a/judge/.well-known/agent-card.json \
    --set-env-vars CONTENT_BUILDER_AGENT_CARD_URL=$CONTENT_BUILDER_URL/a2a/content_builder/.well-known/agent-card.json \
    --set-env-vars GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT}" \
    --set-env-vars GOOGLE_GENAI_USE_VERTEXAI="false" \
    --set-env-vars GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
    --set-env-vars GENAI_MODEL="${GENAI_MODEL}"
}

deploy_course_creator() {
  echo "Deploying course-creator..."
  ORCHESTRATOR_URL=$(gcloud run services describe orchestrator --region $REGION --format='value(status.url)' --project $GOOGLE_CLOUD_PROJECT)
  
  IMAGE_NAME="gcr.io/${GOOGLE_CLOUD_PROJECT}/course-creator"
  gcloud run deploy course-creator \
    --image "${IMAGE_NAME}" \
    --project $GOOGLE_CLOUD_PROJECT \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars AGENT_SERVER_URL=$ORCHESTRATOR_URL \
    --set-env-vars AGENT_NAME=orchestrator \
    --set-env-vars GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT}"
}

SERVICE=$1

if [[ "${SERVICE}" == "researcher" ]]; then
  deploy_researcher
elif [[ "${SERVICE}" == "content-builder" ]]; then
  deploy_content_builder
elif [[ "${SERVICE}" == "judge" ]]; then
  deploy_judge
elif [[ "${SERVICE}" == "orchestrator" ]]; then
  deploy_orchestrator
elif [[ "${SERVICE}" == "course-creator" ]]; then
  deploy_course_creator
elif [[ "${SERVICE}" == "" ]]; then
  build_images
  deploy_researcher
  deploy_content_builder
  deploy_judge
  deploy_orchestrator
  deploy_course_creator
else
  echo "ERROR: Unknown service '${SERVICE}'"
  exit 1
fi
