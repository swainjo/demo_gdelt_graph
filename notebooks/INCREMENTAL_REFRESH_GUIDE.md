# GDELT Incremental Refresh - Complete Implementation

This directory contains a complete solution for automatically refreshing GDELT data every 15 minutes.

## What's Included

### 1. Jupyter Notebook
**File**: `03_gdelt_incremental_refresh.ipynb`

Interactive notebook for manual execution and testing:
- Initial 24-hour data backfill
- Incremental 15-minute updates with deduplication
- Cross-region data transfer (US → US-CENTRAL1)
- State tracking via metadata table
- Comprehensive error handling

**Use this for**:
- Testing the refresh logic locally
- One-time data loads
- Development and debugging

### 2. Cloud Function (Production Deployment)
**Directory**: `cloud_function/`

Production-ready automated deployment:
- `main.py` - Cloud Function code
- `config.py` - Configuration
- `requirements.txt` - Dependencies
- `deploy.sh` - Automated deployment script
- `README.md` - Complete documentation

**Use this for**:
- Production automated scheduling
- 24/7 monitoring and logging
- Scalable cloud execution

## Quick Start

### Option A: Manual Execution (Notebook)

```bash
# Open the notebook
jupyter notebook 03_gdelt_incremental_refresh.ipynb

# Or run from command line
jupyter nbconvert --execute --to notebook --inplace 03_gdelt_incremental_refresh.ipynb
```

### Option B: Automated Cloud Deployment (Recommended)

```bash
# 1. Update configuration
cd cloud_function
nano config.py  # Set your GCP_PROJECT_ID

# 2. Deploy everything
./deploy.sh

# 3. Test immediately
gcloud scheduler jobs run gdelt-refresh-scheduler --location=us-central1

# 4. Monitor
gcloud functions logs read gdelt-incremental-refresh --region=us-central1 --gen2
```

## How It Works

### Initial Load (First Run)
```
1. No sync metadata exists
2. Query last 24 hours of GDELT data
3. Transfer from US region to US-CENTRAL1
4. Load into destination tables
5. Record sync timestamp
```

### Incremental Updates (Every 15 Minutes)
```
1. Read last sync timestamp from metadata
2. Query data from (last_sync - 2min) to now
3. Transfer to staging tables
4. MERGE into destination (dedup by unique keys)
5. Clean up staging tables
6. Update sync timestamp
```

### Cross-Region Transfer
```
GDELT (US) → Temp Table (US) → Staging (US-CENTRAL1) → MERGE → Destination (US-CENTRAL1)
```

## Table-Specific Configuration

Each GDELT table has unique keys for deduplication:

| Table | Unique Key(s) | Timestamp Column |
|-------|---------------|------------------|
| `gkg_partitioned` | `GKGRECORDID` | `DATE` |
| `events_partitioned` | `GLOBALEVENTID` | `DATEADDED` |
| `eventmentions_partitioned` | `GLOBALEVENTID` + `MentionIdentifier` + `MentionTimeDate` | `MentionTimeDate` |

## Monitoring

### Check Sync Status
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

### View Function Logs (Cloud Deployment)
```bash
gcloud functions logs read gdelt-incremental-refresh \
  --region=us-central1 \
  --gen2 \
  --limit=50
```

### Pause/Resume Scheduler
```bash
# Pause
gcloud scheduler jobs pause gdelt-refresh-scheduler --location=us-central1

# Resume
gcloud scheduler jobs resume gdelt-refresh-scheduler --location=us-central1
```

## Architecture

### Notebook Architecture
```
Jupyter Notebook
    ↓
BigQuery Client
    ↓
[Query GDELT] → [Stage US] → [Copy US-CENTRAL1] → [MERGE] → [Destination]
    ↓
Update Metadata
```

### Cloud Function Architecture
```
Cloud Scheduler (every 15 min)
    ↓
HTTP Trigger
    ↓
Cloud Function (Python)
    ↓
BigQuery API
    ↓
[Query GDELT] → [Stage US] → [Copy US-CENTRAL1] → [MERGE] → [Destination]
    ↓
Cloud Logging + Metadata Update
```

## Edge Cases Handled

1. **NULL Unique Keys**: Filtered before MERGE
2. **NULL Timestamps**: Excluded from queries
3. **Late Arrivals**: 2-minute overlap window
4. **Zero New Data**: Updates timestamp, skips MERGE
5. **First Load**: Uses COPY instead of MERGE
6. **Duplicate Data**: MERGE automatically deduplicates
7. **Cross-Region Limits**: Staged through temp tables
8. **BigQuery MERGE Syntax**: Uses explicit column lists

## Cost Estimation

### Notebook Execution (Manual)
- **BigQuery**: Query processing + storage (~$10-50/month)
- **No compute costs** (runs locally)

### Cloud Function Deployment (Automated)
- **Cloud Function**: ~$5-10/month (96 executions/day × 5-10 min each)
- **Cloud Scheduler**: ~$0.30/month (2,880 invocations/month)
- **BigQuery**: Query processing + storage (~$10-50/month)
- **Total**: ~$15-60/month

## Troubleshooting

### Notebook Issues
```python
# Check if datasets exist
from google.cloud import bigquery
client = bigquery.Client(project="your-project")
datasets = list(client.list_datasets())
print([d.dataset_id for d in datasets])

# Check metadata table
query = "SELECT * FROM `your-project.gdelt._sync_metadata` ORDER BY last_sync_time DESC LIMIT 5"
df = client.query(query).to_dataframe()
print(df)
```

### Cloud Function Issues
```bash
# View detailed logs
gcloud functions logs read gdelt-incremental-refresh \
  --region=us-central1 \
  --gen2 \
  --format="table(timestamp,severity,textPayload)"

# Check function status
gcloud functions describe gdelt-incremental-refresh \
  --region=us-central1 \
  --gen2

# Test function manually
curl -X POST $(gcloud functions describe gdelt-incremental-refresh \
  --region=us-central1 --gen2 --format="value(serviceConfig.uri)")
```

### Permission Issues
```bash
# Grant BigQuery permissions to service account
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.admin"
```

## Files Overview

```
notebooks/
├── 03_gdelt_incremental_refresh.ipynb  # Interactive notebook
├── cloud_function/                      # Production deployment
│   ├── main.py                         # Cloud Function code
│   ├── config.py                       # Configuration
│   ├── requirements.txt                # Python dependencies
│   ├── deploy.sh                       # Deployment script
│   └── README.md                       # Detailed docs
├── config.py                           # Shared configuration
└── INCREMENTAL_REFRESH_GUIDE.md        # This file
```

## Next Steps

1. **Test locally** with the notebook to verify your setup
2. **Deploy to cloud** using `cloud_function/deploy.sh`
3. **Monitor** the sync metadata table to ensure updates are working
4. **Set up alerts** in Cloud Monitoring for failures
5. **Optimize** the schedule if needed (change from 15 min to different interval)

## Support

For issues:
1. Check the logs (notebook output or Cloud Function logs)
2. Verify configuration in `config.py`
3. Review `cloud_function/README.md` for troubleshooting
4. Check BigQuery job history for query errors
5. Ensure all APIs are enabled in GCP

## References

- [BigQuery MERGE documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax#merge_statement)
- [Cloud Functions documentation](https://cloud.google.com/functions/docs)
- [Cloud Scheduler documentation](https://cloud.google.com/scheduler/docs)
- [GDELT dataset documentation](https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/)
