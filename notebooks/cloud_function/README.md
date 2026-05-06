# GDELT Incremental Refresh - Cloud Function Deployment

This directory contains everything needed to deploy the GDELT incremental refresh as a Cloud Function triggered by Cloud Scheduler.

## Overview

The Cloud Function runs every 15 minutes to:
1. Check the last sync time from metadata
2. Query new GDELT data (last 24h on first run, or last 15min + 2min overlap on subsequent runs)
3. Transfer data from US region to US-CENTRAL1
4. MERGE new rows into destination tables (deduplicates automatically)
5. Update sync metadata

## Files

- **`main.py`**: Cloud Function code (HTTP trigger)
- **`requirements.txt`**: Python dependencies
- **`deploy.sh`**: Copies `../config.py` into this directory, then deploys
- **`README.md`**: This file

Configuration is shared with the notebooks: edit **`../config.py`** (or set env vars such as `GDELT_GRAPH_DEMO_GCP_PROJECT` and `BIGQUERY_DATASET`). A copy named `config.py` is placed here by `deploy.sh` (and is gitignored) because `gcloud functions deploy --source=.` only uploads this folder.

## Prerequisites

1. **GCP Project** with billing enabled
2. **APIs Enabled**:
   - Cloud Functions API
   - Cloud Scheduler API
   - Cloud Build API
   - BigQuery API
3. **gcloud CLI** installed and authenticated
4. **Permissions** (deployer): Your account needs:
   - `roles/cloudfunctions.developer`
   - `roles/cloudscheduler.admin`
   - `roles/iam.serviceAccountUser`
   - `roles/bigquery.dataEditor` on the target dataset (or `roles/bigquery.admin` only if you need to create/manage datasets)
   - `roles/bigquery.jobUser` at the project level
5. **Runtime service account** (the SA the function runs as) needs the
   minimum set:
   - `roles/bigquery.dataEditor` on the target `gdelt` dataset
   - `roles/bigquery.dataViewer` on `gdelt-bq.gdeltv2` (public — usually granted automatically)
   - `roles/bigquery.jobUser` at the project level
   - `roles/run.invoker` on the deployed function (granted by `deploy.sh` to the Cloud Scheduler SA)

## Quick Start

### 1. Update Configuration

Edit **`notebooks/config.py`** (parent directory: `../config.py` from here), or export:

- `GDELT_GRAPH_DEMO_GCP_PROJECT` — BigQuery project (preferred; avoids mixing with a global `GOOGLE_CLOUD_PROJECT`)
- `BIGQUERY_DATASET`, `GOOGLE_CLOUD_REGION`, etc., as documented in that file

### 2. Deploy

Run the deployment script:
```bash
cd cloud_function
./deploy.sh
```

The script will:
- Copy `../config.py` to `./config.py` for the upload bundle
- Deploy the Cloud Function
- Create a Cloud Scheduler job (runs every 15 minutes)
- Display the function URL and management commands

### 3. Test

The function is deployed with authentication required. Send a signed identity
token with the request:
```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://YOUR-REGION-YOUR-PROJECT.cloudfunctions.net/gdelt-incremental-refresh
```

Or trigger the scheduler manually (it carries its own OIDC token):
```bash
gcloud scheduler jobs run gdelt-refresh-scheduler --location=us-central1
```

## Manual Deployment

If you prefer to deploy manually, copy the shared config first (same as `deploy.sh`):

```bash
cp -f ../config.py ./config.py
```

### Deploy Cloud Function
```bash
gcloud functions deploy gdelt-incremental-refresh \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=gdelt_refresh \
  --trigger-http \
  --no-allow-unauthenticated \
  --memory=2048MB \
  --timeout=540s \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GDELT_GRAPH_DEMO_GCP_PROJECT=YOUR_PROJECT_ID
```

### Grant the scheduler service account permission to invoke the function
```bash
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")
INVOKER_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud run services add-iam-policy-binding gdelt-incremental-refresh \
  --region=us-central1 \
  --member="serviceAccount:${INVOKER_SA}" \
  --role="roles/run.invoker"
```

### Create Cloud Scheduler Job
```bash
# Get the function URL first
FUNCTION_URL=$(gcloud functions describe gdelt-incremental-refresh \
  --region=us-central1 --gen2 --format="value(serviceConfig.uri)")

# Create scheduler job (signs requests with an OIDC token)
gcloud scheduler jobs create http gdelt-refresh-scheduler \
  --location=us-central1 \
  --schedule="*/15 * * * *" \
  --uri="$FUNCTION_URL" \
  --http-method=POST \
  --oidc-service-account-email="$INVOKER_SA" \
  --oidc-token-audience="$FUNCTION_URL" \
  --time-zone="UTC"
```

## Monitoring

### View Function Logs
```bash
gcloud functions logs read gdelt-incremental-refresh \
  --region=us-central1 \
  --gen2 \
  --limit=50
```

### Check Sync Status in BigQuery
```sql
SELECT 
  table_name,
  last_sync_time,
  sync_mode,
  rows_processed,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), last_sync_time, MINUTE) as minutes_since_sync
FROM `your-project.gdelt._sync_metadata`
ORDER BY last_sync_time DESC
LIMIT 10;
```

### View Scheduled Jobs
```bash
gcloud scheduler jobs list --location=us-central1
```

### Check Scheduler Job Status
```bash
gcloud scheduler jobs describe gdelt-refresh-scheduler --location=us-central1
```

## Management Commands

### Pause Scheduler
```bash
gcloud scheduler jobs pause gdelt-refresh-scheduler --location=us-central1
```

### Resume Scheduler
```bash
gcloud scheduler jobs resume gdelt-refresh-scheduler --location=us-central1
```

### Update Schedule
```bash
# Change to every 30 minutes
gcloud scheduler jobs update http gdelt-refresh-scheduler \
  --location=us-central1 \
  --schedule="*/30 * * * *"
```

### Delete Resources
```bash
# Delete scheduler job
gcloud scheduler jobs delete gdelt-refresh-scheduler --location=us-central1

# Delete cloud function
gcloud functions delete gdelt-incremental-refresh --region=us-central1 --gen2
```

## Cost Estimation

**Cloud Function (2nd gen)**:
- Memory: 2GB
- Execution time: ~5-10 minutes per run
- Frequency: 96 runs/day (every 15 minutes)
- Estimated cost: ~$5-10/month

**Cloud Scheduler**:
- Jobs: 1
- Invocations: 2,880/month
- Estimated cost: ~$0.30/month

**BigQuery**:
- Queries: ~288/day
- Data processed: Depends on incremental data volume
- Storage: Depends on data retention
- Estimated cost: Variable, ~$10-50/month

**Total estimated cost**: ~$15-60/month (varies with data volume)

## Troubleshooting

### Function Timeout
If the function times out (9-minute limit):
1. Reduce the number of tables processed
2. Increase memory allocation (up to 32GB for faster processing)
3. Consider splitting into multiple functions

### Permission Errors
Grant the runtime service account least-privilege BigQuery roles:
```bash
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")
SA="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Run jobs at the project level
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="$SA" --role="roles/bigquery.jobUser"

# Read/write the target dataset only (not all datasets in the project)
bq add-iam-policy-binding \
  --member="$SA" --role="roles/bigquery.dataEditor" \
  YOUR_PROJECT_ID:gdelt
```
Avoid `roles/bigquery.admin` on the runtime SA — it grants DDL on every
dataset in the project.

### Scheduler Not Triggering
1. Check if job is paused:
   ```bash
   gcloud scheduler jobs describe gdelt-refresh-scheduler --location=us-central1
   ```
2. Check scheduler logs:
   ```bash
   gcloud logging read "resource.type=cloud_scheduler_job" --limit=50
   ```

### Data Not Updating
1. Check function logs for errors
2. Verify metadata table exists and is being updated
3. Check BigQuery queries in the Cloud Console
4. Ensure source GDELT tables are accessible

## Advanced Configuration

### Environment Variables
You can pass additional configuration via environment variables:
```bash
gcloud functions deploy gdelt-incremental-refresh \
  --set-env-vars=LOG_LEVEL=DEBUG,MAX_RETRIES=3
```

### VPC Connector
For private network access:
```bash
gcloud functions deploy gdelt-incremental-refresh \
  --vpc-connector=YOUR_VPC_CONNECTOR
```

### Service Account
Use a custom service account:
```bash
gcloud functions deploy gdelt-incremental-refresh \
  --service-account=your-service-account@your-project.iam.gserviceaccount.com
```

## Security Best Practices

1. **Authenticated endpoint by default.** `deploy.sh` deploys with
   `--no-allow-unauthenticated` and grants the Cloud Scheduler SA
   `roles/run.invoker`. Don't relax this without a reason.
2. **Use Secret Manager** for any sensitive configuration.
3. **Enable VPC** for private network communication when accessing internal
   resources.
4. **Set up monitoring** alerts for failures (Cloud Logging metric →
   Cloud Monitoring alert on the function's error rate).
5. **Use least-privilege** runtime service accounts —
   `roles/bigquery.dataEditor` + `roles/bigquery.jobUser`, not
   `roles/bigquery.admin`.

## Support

For issues or questions:
1. Check function logs
2. Review BigQuery job history
3. Verify configuration in `notebooks/config.py` (and env vars on the function)
4. Ensure all prerequisites are met
