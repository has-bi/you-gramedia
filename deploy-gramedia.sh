#!/bin/bash

# Configuration
PROJECT_ID="your-project-id"
SERVICE_NAME="gramedia-display"
REGION="asia-southeast1"  # Singapore region
SERVICE_ACCOUNT="gramedia-app@${PROJECT_ID}.iam.gserviceaccount.com"

# Set project
gcloud config set project $PROJECT_ID

echo "🔧 Ensuring proper IAM roles for service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/storage.objectAdmin" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

echo "🐳 Building and pushing container..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --region $REGION \
    --platform managed \
    --service-account $SERVICE_ACCOUNT \
    --allow-unauthenticated \
    --max-instances 10 \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --port 8080 \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID

echo "✅ Deployment complete!"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
echo ""
echo "🌐 Your Gramedia Display Competition app is live at: $SERVICE_URL"
echo ""
echo "📋 Final checklist:"
echo "✅ Secrets configured in Secret Manager"
echo "✅ Service account has proper permissions"
echo "✅ App deployed to Cloud Run"
echo ""
echo "⚠️  Don't forget to:"
echo "1. Share the Google Spreadsheet (ID: 1IBAPr6UMH1EwBY5WzKiwMEcGZQdcWzF5_3eTJl4U9MU) with: $SERVICE_ACCOUNT"
echo "2. Give the service account 'Editor' permissions on the spreadsheet"
echo "3. Create the GCS bucket for image storage when ready"