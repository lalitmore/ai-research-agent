#!/bin/bash
# deploy.sh — Full GCP deploy for AI Research Agent
# Usage: ./deploy.sh YOUR_PROJECT_ID YOUR_REGION
# Example: ./deploy.sh my-project-123 us-central1

set -e  # exit on error

PROJECT_ID=${1:-"YOUR_PROJECT_ID"}
REGION=${2:-"us-central1"}
SERVICE_NAME="research-agent"
BUCKET_NAME="${PROJECT_ID}-research-artifacts"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying AI Research Agent to GCP"
echo "   Project: $PROJECT_ID | Region: $REGION"

# 1. Set project
gcloud config set project $PROJECT_ID

# 2. Enable required APIs
echo "⚙️  Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com

# 3. Create GCS bucket
echo "🪣 Creating Cloud Storage bucket..."
gsutil mb -p $PROJECT_ID -l $REGION gs://$BUCKET_NAME 2>/dev/null || echo "Bucket already exists"

# 4. Store Anthropic API key in Secret Manager
echo "🔐 Storing secrets..."
echo -n "Enter your Anthropic API key: "
read -s ANTHROPIC_KEY
echo
printf "%s" "$ANTHROPIC_KEY" | gcloud secrets create anthropic-api-key \
  --data-file=- --project=$PROJECT_ID 2>/dev/null || \
  printf "%s" "$ANTHROPIC_KEY" | gcloud secrets versions add anthropic-api-key \
  --data-file=- --project=$PROJECT_ID

# 5. Create service account
echo "👤 Creating service account..."
SA_NAME="research-agent-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts create $SA_NAME \
  --display-name="Research Agent Service Account" \
  --project=$PROJECT_ID 2>/dev/null || echo "Service account already exists"

# Grant roles
for ROLE in \
  "roles/storage.objectAdmin" \
  "roles/bigquery.dataEditor" \
  "roles/bigquery.jobUser" \
  "roles/secretmanager.secretAccessor"; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE" --quiet
done

# 6. Set up BigQuery
echo "📊 Setting up BigQuery..."
export GCP_PROJECT_ID=$PROJECT_ID
python3.11 setup_bigquery.py

# 7. Build and push Docker image
echo "🐳 Building and pushing Docker image..."
gcloud builds submit --tag $IMAGE .

# 8. Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE \
  --platform managed \
  --region $REGION \
  --service-account $SA_EMAIL \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCS_BUCKET_NAME=${BUCKET_NAME}" \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 120

echo ""
echo "✅ Deploy complete!"
gcloud run services describe $SERVICE_NAME --region $REGION --format "value(status.url)"
