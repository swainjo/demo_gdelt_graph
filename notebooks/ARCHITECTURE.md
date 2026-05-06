# GDELT Incremental Refresh Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Cloud Scheduler (Every 15 min)               │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Cloud Function (Python)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Get last sync time from metadata                      │  │
│  │ 2. Determine mode (initial: 24h / incremental: 15m)     │  │
│  │ 3. Process each GDELT table (gkg, events, eventmentions) │  │
│  │ 4. Call sp_update_person_table(since_timestamp)          │  │
│  │ 5. Call sp_update_person_cooccurrence_table(since)       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Flow Per Table                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐    Query with      ┌──────────────┐
│   GDELT      │    time filter     │  Temp Table  │
│  (US Region) │  ─────────────────> │  (US Region) │
│ gdelt-bq     │    SELECT * WHERE   │ gdelt_us     │
└──────────────┘    timestamp...     └──────┬───────┘
                                            │
                                            │ Copy Table
                                            │ (Cross-region)
                                            ▼
                    ┌─────────────────────────────────┐
                    │    Staging Table                │
                    │    (US-CENTRAL1)                │
                    │    gdelt.staging_{table}        │
                    └────────┬────────────────────────┘
                             │
                             │ MERGE
                             │ (Dedup by unique keys)
                             ▼
                    ┌─────────────────────────────────┐
                    │    Destination Table            │
                    │    (US-CENTRAL1)                │
                    │    gdelt.{table_name}           │
                    └────────┬────────────────────────┘
                             │
                             │ Record sync
                             ▼
                    ┌─────────────────────────────────┐
                    │    Metadata Table               │
                    │    gdelt._sync_metadata         │
                    │    (tracks last_sync_time)      │
                    └─────────────────────────────────┘
```

## Data Flow Details

### Step 1: Query GDELT Source
```sql
SELECT *
FROM `gdelt-bq.gdeltv2.{table_name}`
WHERE {timestamp_col} >= {start_time}
  AND {timestamp_col} <= {current_time}
  AND {timestamp_col} IS NOT NULL
```

**Output**: Temp table in US region (`gdelt_us.staging_{table_name}`)

### Step 2: Cross-Region Copy
```
Copy Table Job:
  Source: gdelt_us.staging_{table_name} (US)
  Destination: gdelt.staging_{table_name} (US-CENTRAL1)
  Mode: WRITE_TRUNCATE
```

### Step 3: MERGE Deduplication
```sql
MERGE `gdelt.{table_name}` AS target
USING (
  SELECT * FROM `gdelt.staging_{table_name}`
  WHERE {unique_keys} IS NOT NULL
) AS source
ON {unique_key_match_condition}
WHEN NOT MATCHED THEN
  INSERT (col1, col2, ..., colN)
  VALUES (source.col1, source.col2, ..., source.colN)
```

**Deduplication Keys**:
- `gkg_partitioned`: `GKGRECORDID`
- `events_partitioned`: `GLOBALEVENTID`
- `eventmentions_partitioned`: `GLOBALEVENTID` + `MentionIdentifier` + `MentionTimeDate`

### Step 4: Cleanup & Metadata Update
```
1. DELETE temp table (gdelt_us.staging_{table_name})
2. DELETE staging table (gdelt.staging_{table_name})
3. INSERT INTO gdelt._sync_metadata (
     table_name, last_sync_time, rows_processed, sync_mode
   )
```

### Step 5: Person Table Updates (after all three tables)
```
CALL gdelt.sp_update_person_table(since_timestamp)
CALL gdelt.sp_update_person_cooccurrence_table(since_timestamp)
```

Both are BigQuery stored procedures that accept a single `TIMESTAMP` parameter:
- `NULL` → full rebuild (TRUNCATE + INSERT from all gkg_partitioned rows); used by `01_gdelt_data_prep.ipynb`
- non-NULL → incremental update using only GKG rows added since that timestamp; used by the Cloud Function and `03_gdelt_incremental_refresh.ipynb`

**sp_update_person_table**: MERGE — inserts new persons, updates `last_seen_date` and `total_mentions` for existing ones.

**sp_update_person_cooccurrence_table**: DELETE + INSERT (not MERGE) to merge ARRAY columns, avoiding BigQuery's
*"Correlated Subquery is unsupported in UPDATE clause"* restriction.
Incremental steps:
1. Compute new pairs into a temp table (`_new_cooccurrence`)
2. Build merged rows for already-existing pairs (`_merged_cooccurrence`): count accumulation + ARRAY_CONCAT of article_ids/themes/locations
3. DELETE old rows for those pairs
4. INSERT merged rows back
5. INSERT genuinely new pairs

## Execution Modes

### Initial Load (First Run)
```
┌─────────────────────────────────────────────────────────┐
│ No metadata exists                                      │
│ ↓                                                       │
│ Query: last 24 hours                                   │
│ ↓                                                       │
│ Transfer: US → US-CENTRAL1                             │
│ ↓                                                       │
│ Load: COPY to destination (no MERGE needed)           │
│ ↓                                                       │
│ Record: sync_mode = 'initial'                         │
└─────────────────────────────────────────────────────────┘
```

### Incremental Update (Every 15 Minutes)
```
┌─────────────────────────────────────────────────────────┐
│ Read metadata: last_sync_time                          │
│ ↓                                                       │
│ Query: (last_sync - 2min) to now                      │
│ ↓                                                       │
│ Transfer: US → US-CENTRAL1                             │
│ ↓                                                       │
│ MERGE: Insert only new rows (dedup by unique keys)    │
│ ↓                                                       │
│ Record: sync_mode = 'incremental'                     │
│ ↓ (after all three tables)                             │
│ CALL sp_update_person_table(last_gkg_sync)            │
│ ↓                                                       │
│ CALL sp_update_person_cooccurrence_table(last_gkg_sync)│
└─────────────────────────────────────────────────────────┘
```

## Timing Diagram

```
Time:   0min          15min         30min         45min         60min
        │             │             │             │             │
Run 1:  ├─────────────┤ (Initial: Load last 24h)
        │             │
        │             ├─────────────┤ (Incremental: 13-17min data)
        │             │             │
        │             │             ├─────────────┤ (Incremental: 28-32min data)
        │             │             │             │
        │             │             │             ├─────────────┤ (Incremental: 43-47min data)
        │             │             │             │             │
        
Notes:
- 2-minute overlap ensures late arrivals are captured
- Each run processes ~15 minutes of new data
- Duplicates are automatically handled by MERGE
```

## Error Handling

```
┌─────────────────────────────────────────────────────────┐
│ Function Start                                          │
└────────┬────────────────────────────────────────────────┘
         │
         ├─ Error: Metadata table doesn't exist
         │  → Create table automatically
         │  → Continue with initial load
         │
         ├─ Error: No new data in time range
         │  → Update sync time
         │  → Return success (rows_added: 0)
         │
         ├─ Error: Destination table doesn't exist
         │  → Use COPY instead of MERGE
         │  → Continue normally
         │
         ├─ Error: Query timeout
         │  → Log error
         │  → Return failure
         │  → Retry on next schedule (15 min)
         │
         └─ Success
            → Log metrics
            → Update metadata
            → Return summary
```

## Monitoring Points

```
┌────────────────────────────────────────────────────────┐
│ Monitoring & Observability                             │
├────────────────────────────────────────────────────────┤
│                                                        │
│ 1. Cloud Function Metrics:                            │
│    • Execution count (should be ~96/day)              │
│    • Execution time (typical: 5-10 min)               │
│    • Error rate (should be < 1%)                      │
│    • Memory usage (allocated: 2GB)                    │
│                                                        │
│ 2. BigQuery Metrics:                                  │
│    • Query bytes processed                            │
│    • Slot time consumed                               │
│    • MERGE rows affected                              │
│    • Storage size growth                              │
│                                                        │
│ 3. Sync Metadata Table:                               │
│    • last_sync_time (should be recent)                │
│    • rows_processed (trend over time)                 │
│    • sync_mode (initial vs incremental)               │
│    • gaps in timestamps (missed runs)                 │
│                                                        │
│ 4. Cloud Scheduler:                                   │
│    • Job state (should be ENABLED)                    │
│    • Last run time                                    │
│    • Success/failure status                           │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Performance Characteristics

### Typical Execution Time
```
Initial Load (24h data):    ~5-10 minutes per table
Incremental (15min data):   ~1-3 minutes per table
Total (3 tables):           ~3-9 minutes incremental
                            ~15-30 minutes initial
```

### Data Volume Estimates
```
Typical 15-minute window:
- gkg_partitioned:          ~10,000-50,000 rows
- events_partitioned:       ~5,000-20,000 rows
- eventmentions_partitioned: ~15,000-60,000 rows

Total per day:              ~4-10 million rows
Storage growth:             ~1-5 GB/day
Query processing:           ~10-50 GB scanned/day
```

### Cost Breakdown
```
Cloud Function:
  • Invocations: 96/day × 30 days = 2,880/month
  • Compute time: 96 × 5 min = 480 min/day = ~240 GB-sec/day
  • Cost: ~$5-10/month

Cloud Scheduler:
  • Jobs: 1 × $0.10/month = $0.10/month
  • Invocations: Free (first 3 included)
  • Cost: ~$0.10/month

BigQuery:
  • Query: ~300 GB processed/day × $5/TB = ~$0.50/day = ~$15/month
  • Storage: ~50 GB × $0.02/GB = ~$1/month
  • Cost: ~$16/month

Total: ~$21-26/month
```
