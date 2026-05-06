#!/bin/bash

# Deployment script for GDELT Incremental Refresh Cloud Function
# This script deploys the Cloud Function and sets up Cloud Scheduler

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
# Single source: notebooks/config.py (also used by Jupyter). Copied into this folder for gcloud --source=.
cp -f "$SCRIPT_DIR/../config.py" "$SCRIPT_DIR/config.py"

# Configuration
FUNCTION_NAME="gdelt-incremental-refresh"
REGION="us-central1"
RUNTIME="python312"
ENTRY_POINT="gdelt_refresh"
MEMORY="2048MB"
TIMEOUT="540s"  # 9 minutes (Cloud Functions max is 9min for HTTP)
SCHEDULER_JOB_NAME="gdelt-refresh-scheduler"
SCHEDULE="*/15 * * * *"  # Every 15 minutes

echo "================================================"
echo "GDELT Incremental Refresh - Cloud Deployment"
echo "================================================"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No GCP project configured"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Function Name: $FUNCTION_NAME"
echo "   Region: $REGION"
echo "   Schedule: Every 15 minutes"
echo ""

# Confirm deployment
read -p "Deploy to project '$PROJECT_ID'? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo ""
echo "🚀 Step 1: Deploying Cloud Function..."
echo "----------------------------------------"

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
INVOKER_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=$RUNTIME \
    --region=$REGION \
    --source=. \
    --entry-point=$ENTRY_POINT \
    --trigger-http \
    --no-allow-unauthenticated \
    --memory=$MEMORY \
    --timeout=$TIMEOUT \
    --set-env-vars=GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GDELT_GRAPH_DEMO_GCP_PROJECT=$PROJECT_ID

if [ $? -eq 0 ]; then
    echo "✅ Cloud Function deployed successfully"
else
    echo "❌ Cloud Function deployment failed"
    exit 1
fi

# Grant the scheduler service account permission to invoke the (now private) function.
# Gen2 functions are Cloud Run services under the hood, so the role lives on Cloud Run.
gcloud run services add-iam-policy-binding "$FUNCTION_NAME" \
    --region="$REGION" \
    --member="serviceAccount:${INVOKER_SA}" \
    --role="roles/run.invoker" >/dev/null

# Get the function URL
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --gen2 --format="value(serviceConfig.uri)")
echo ""
echo "📍 Function URL: $FUNCTION_URL (auth required)"

echo ""
echo "⏰ Step 2: Setting up Cloud Scheduler..."
echo "----------------------------------------"

# Check if scheduler job already exists
if gcloud scheduler jobs describe $SCHEDULER_JOB_NAME --location=$REGION &>/dev/null; then
    echo "⚠️  Scheduler job already exists. Updating..."

    gcloud scheduler jobs update http $SCHEDULER_JOB_NAME \
        --location=$REGION \
        --schedule="$SCHEDULE" \
        --uri="$FUNCTION_URL" \
        --http-method=POST \
        --oidc-service-account-email="$INVOKER_SA" \
        --oidc-token-audience="$FUNCTION_URL" \
        --time-zone="UTC"
else
    echo "📝 Creating new scheduler job..."

    gcloud scheduler jobs create http $SCHEDULER_JOB_NAME \
        --location=$REGION \
        --schedule="$SCHEDULE" \
        --uri="$FUNCTION_URL" \
        --http-method=POST \
        --oidc-service-account-email="$INVOKER_SA" \
        --oidc-token-audience="$FUNCTION_URL" \
        --time-zone="UTC"
fi

if [ $? -eq 0 ]; then
    echo "✅ Cloud Scheduler configured successfully"
else
    echo "❌ Cloud Scheduler configuration failed"
    exit 1
fi

echo ""
echo "================================================"
echo "✅ Deployment Complete!"
echo "================================================"
echo ""
echo "📊 Summary:"
echo "   • Cloud Function: $FUNCTION_NAME"
echo "   • Region: $REGION"
echo "   • URL: $FUNCTION_URL"
echo "   • Schedule: Every 15 minutes"
echo ""
echo "🔧 Next Steps:"
echo ""
echo "1. Test the function manually (auth token required):"
echo "   curl -X POST -H \"Authorization: Bearer \$(gcloud auth print-identity-token)\" $FUNCTION_URL"
echo ""
echo "2. View function logs:"
echo "   gcloud functions logs read $FUNCTION_NAME --region=$REGION --gen2 --limit=50"
echo ""
echo "3. View scheduled jobs:"
echo "   gcloud scheduler jobs list --location=$REGION"
echo ""
echo "4. Trigger scheduler manually (don't wait 15 min):"
echo "   gcloud scheduler jobs run $SCHEDULER_JOB_NAME --location=$REGION"
echo ""
echo "5. Pause scheduler (if needed):"
echo "   gcloud scheduler jobs pause $SCHEDULER_JOB_NAME --location=$REGION"
echo ""
echo "6. Resume scheduler (if paused):"
echo "   gcloud scheduler jobs resume $SCHEDULER_JOB_NAME --location=$REGION"
echo ""
echo "📈 Monitor your data refresh in BigQuery:"
echo "   SELECT * FROM \`$PROJECT_ID.gdelt._sync_metadata\`"
echo "   ORDER BY last_sync_time DESC LIMIT 10;"
echo ""
