#!/bin/bash

# Configuration - UPDATE THESE VALUES
PROJECT_ID="your-project-id"
SERVICE_ACCOUNT_EMAIL="gramedia-app@your-project-id.iam.gserviceaccount.com"
BUCKET_NAME="gramedia-display"  # Update when bucket is created
SPREADSHEET_ID="1IBAPr6UMH1EwBY5WzKiwMEcGZQdcWzF5_3eTJl4U9MU"  # Fixed Gramedia spreadsheet
CREDENTIALS_FILE="path/to/your/credentials.json"  # UPDATE THIS

# Set project
gcloud config set project $PROJECT_ID

# Enable Secret Manager API (if not already enabled)
echo "Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

# Create secrets
echo "Creating secrets in Secret Manager..."

# 1. Google credentials secret
echo "📁 Creating gramedia-google-credentials secret..."
gcloud secrets create gramedia-google-credentials \
    --data-file=$CREDENTIALS_FILE \
    --replication-policy="automatic"

# 2. GCS bucket name secret
echo "🪣 Creating gramedia-gcs-bucket secret..."
echo -n $BUCKET_NAME | gcloud secrets create gramedia-gcs-bucket \
    --data-file=- \
    --replication-policy="automatic"

# 3. Spreadsheet ID secret (not needed as it's hardcoded, but keeping for consistency)
echo "📊 Creating gramedia-spreadsheet-id secret..."
echo -n $SPREADSHEET_ID | gcloud secrets create gramedia-spreadsheet-id \
    --data-file=- \
    --replication-policy="automatic"

# Grant your service account access to the secrets
echo "🔐 Granting service account access to secrets..."

gcloud secrets add-iam-policy-binding gramedia-google-credentials \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding gramedia-gcs-bucket \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding gramedia-spreadsheet-id \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

echo "✅ Secret Manager setup complete!"
echo ""
echo "📋 Summary:"
echo "   • gramedia-google-credentials: Service account credentials"
echo "   • gramedia-gcs-bucket: $BUCKET_NAME"
echo "   • gramedia-spreadsheet-id: $SPREADSHEET_ID"
echo ""
echo "🚀 Your service account ($SERVICE_ACCOUNT_EMAIL) now has access to all secrets."
echo ""
echo "Next steps:"
echo "1. Make sure your service account has the necessary IAM roles:"
echo "   - Storage Object Admin (for bucket access)"
echo "   - Secret Manager Secret Accessor (already granted)"
echo "2. Share the Google Spreadsheet with: $SERVICE_ACCOUNT_EMAIL"
echo "   Spreadsheet URL: https://docs.google.com/spreadsheets/d/$SPREADSHEET_ID/edit"
echo "3. Deploy your app to Cloud Run using deploy-gramedia.sh"