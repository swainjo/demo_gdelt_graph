"""GDELT Incremental Refresh Cloud Function."""
import functions_framework
from google.cloud import bigquery
from datetime import datetime, timedelta
import logging
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TABLE_METADATA = {
    "gkg_partitioned": {"unique_key": ["GKGRECORDID"], "timestamp_col": "DATE"},
    "events_partitioned": {"unique_key": ["GLOBALEVENTID"], "timestamp_col": "DATEADDED"},
    "eventmentions_partitioned": {"unique_key": ["GLOBALEVENTID", "MentionIdentifier", "MentionTimeDate"], "timestamp_col": "MentionTimeDate"},
}

def ensure_datasets(client):
    dataset_ref = client.dataset(config.BIGQUERY_DATASET)
    try:
        client.get_dataset(dataset_ref)
    except:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US-CENTRAL1"
        client.create_dataset(dataset, timeout=30, exists_ok=True)
    us_dataset_name = f"{config.BIGQUERY_DATASET}_us"
    us_dataset_ref = bigquery.DatasetReference(config.GCP_PROJECT_ID, us_dataset_name)
    try:
        client.get_dataset(us_dataset_ref)
    except:
        us_dataset = bigquery.Dataset(us_dataset_ref)
        us_dataset.location = "US"
        client.create_dataset(us_dataset, timeout=30, exists_ok=True)

def get_last_sync_time(client, table_name):
    metadata_table = f"{config.GCP_PROJECT_ID}.{config.BIGQUERY_DATASET}._sync_metadata"
    try:
        query = f"SELECT last_sync_time FROM `{metadata_table}` WHERE table_name = '{table_name}' ORDER BY last_sync_time DESC LIMIT 1"
        result = client.query(query, location="US-CENTRAL1").result()
        rows = list(result)
        return rows[0].last_sync_time if rows else None
    except Exception as e:
        if "notFound" in str(e) or "404" in str(e):
            create_query = f"""CREATE TABLE IF NOT EXISTS `{metadata_table}` (
                table_name STRING NOT NULL, last_sync_time TIMESTAMP NOT NULL,
                rows_processed INT64, sync_mode STRING, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP())"""
            client.query(create_query, location="US-CENTRAL1").result()
            return None
        return None

def update_sync_time(client, table_name, sync_time, rows_processed, sync_mode):
    metadata_table = f"{config.GCP_PROJECT_ID}.{config.BIGQUERY_DATASET}._sync_metadata"
    merge_query = f"""MERGE `{metadata_table}` AS target USING (
        SELECT '{table_name}' as table_name, TIMESTAMP('{sync_time.strftime('%Y-%m-%d %H:%M:%S')}') as last_sync_time,
        {rows_processed} as rows_processed, '{sync_mode}' as sync_mode, CURRENT_TIMESTAMP() as created_at
    ) AS source ON target.table_name = source.table_name 
       AND TIMESTAMP_DIFF(target.last_sync_time, source.last_sync_time, SECOND) BETWEEN -60 AND 60
    WHEN NOT MATCHED THEN INSERT (table_name, last_sync_time, rows_processed, sync_mode, created_at)
        VALUES (source.table_name, source.last_sync_time, source.rows_processed, source.sync_mode, source.created_at)"""
    try:
        client.query(merge_query, location="US-CENTRAL1").result()
    except Exception as e:
        logger.warning(f"Error updating metadata: {e}")

def build_time_filter(timestamp_col, start_time, end_time):
    start_int = int(start_time.strftime('%Y%m%d%H%M%S'))
    end_int = int(end_time.strftime('%Y%m%d%H%M%S'))
    return f"{timestamp_col} >= {start_int} AND {timestamp_col} <= {end_int}"

def incremental_refresh_table(client, table_name):
    logger.info(f"Processing {table_name}")
    try:
        metadata = TABLE_METADATA[table_name]
        unique_keys = metadata["unique_key"]
        timestamp_col = metadata["timestamp_col"]
        last_sync = get_last_sync_time(client, table_name)
        current_time = datetime.utcnow()
        if last_sync is None:
            sync_mode = "initial"
            start_time = current_time - timedelta(hours=24)
        else:
            sync_mode = "incremental"
            start_time = last_sync - timedelta(minutes=2)
        time_filter = build_time_filter(timestamp_col, start_time, current_time)
        us_dataset_name = f"{config.BIGQUERY_DATASET}_us"
        temp_table_ref = client.dataset(us_dataset_name).table(f"staging_{table_name}")
        gdelt_table = f"{config.GDELT_PROJECT_ID}.{config.GDELT_DATASET}.{table_name}"
        job_config = bigquery.QueryJobConfig()
        job_config.destination = temp_table_ref
        job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
        job_config.create_disposition = bigquery.CreateDisposition.CREATE_IF_NEEDED
        partition_start = start_time.strftime('%Y-%m-%d')
        partition_end = current_time.strftime('%Y-%m-%d')
        query = f"""
        SELECT *
        FROM `{gdelt_table}`
        WHERE _PARTITIONDATE BETWEEN '{partition_start}' AND '{partition_end}'
          AND {time_filter}
          AND {timestamp_col} IS NOT NULL
        """
        client.query(query, job_config=job_config, location="US").result()
        temp_table = client.get_table(temp_table_ref)
        temp_rows = temp_table.num_rows
        if temp_rows == 0:
            update_sync_time(client, table_name, current_time, 0, sync_mode)
            return {"status": "success", "mode": sync_mode, "rows_processed": 0, "rows_added": 0}
        staging_table_ref = client.dataset(config.BIGQUERY_DATASET).table(f"staging_{table_name}")
        copy_job_config = bigquery.CopyJobConfig()
        copy_job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
        copy_job_config.create_disposition = bigquery.CreateDisposition.CREATE_IF_NEEDED
        client.copy_table(temp_table_ref, staging_table_ref, job_config=copy_job_config, location="US").result()
        dest_table = f"{config.GCP_PROJECT_ID}.{config.BIGQUERY_DATASET}.{table_name}"
        staging_table = f"{config.GCP_PROJECT_ID}.{config.BIGQUERY_DATASET}.staging_{table_name}"
        join_conditions = " AND ".join([f"COALESCE(CAST(target.{key} AS STRING), 'NULL') = COALESCE(CAST(source.{key} AS STRING), 'NULL')" for key in unique_keys])
        try:
            client.get_table(dest_table)
            table_exists = True
        except:
            table_exists = False
        if table_exists:
            staging_table_obj = client.get_table(staging_table_ref)
            columns = [field.name for field in staging_table_obj.schema]
            columns_list = ", ".join(columns)
            source_columns_list = ", ".join([f"source.{col}" for col in columns])
            null_filters = " AND ".join([f"{key} IS NOT NULL" for key in unique_keys])
            merge_query = f"""MERGE `{dest_table}` AS target USING (
                SELECT * FROM `{staging_table}` WHERE {null_filters}) AS source
                ON {join_conditions} WHEN NOT MATCHED THEN INSERT ({columns_list}) VALUES ({source_columns_list})"""
            merge_job = client.query(merge_query, location="US-CENTRAL1")
            merge_job.result()
            rows_added = merge_job.num_dml_affected_rows if merge_job.num_dml_affected_rows else 0
        else:
            client.copy_table(staging_table_ref, dest_table, location="US-CENTRAL1").result()
            rows_added = temp_rows
        try:
            client.delete_table(temp_table_ref)
            client.delete_table(staging_table_ref)
        except:
            pass
        update_sync_time(client, table_name, current_time, rows_added, sync_mode)
        logger.info(f"Completed {table_name}: {rows_added} rows")
        return {"status": "success", "mode": sync_mode, "rows_processed": temp_rows, "rows_added": rows_added}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "failed", "error": str(e)}

def update_person_tables(client):
    """Call stored procedures to update person and person_cooccurrence tables."""
    since = get_last_sync_time(client, "gkg_partitioned")
    if since is not None:
        since_param = f"TIMESTAMP('{since.strftime('%Y-%m-%d %H:%M:%S')}')"
    else:
        since_param = "NULL"

    person_result = {"status": "success"}
    cooccurrence_result = {"status": "success"}

    try:
        logger.info("Updating person table")
        client.query(
            f"CALL `{config.GCP_PROJECT_ID}.{config.BIGQUERY_DATASET}.sp_update_person_table`({since_param})",
            location="US-CENTRAL1"
        ).result()
        logger.info("Person table updated")
    except Exception as e:
        logger.error(f"Error updating person table: {e}")
        person_result = {"status": "failed", "error": str(e)}

    try:
        logger.info("Updating person_cooccurrence table")
        client.query(
            f"CALL `{config.GCP_PROJECT_ID}.{config.BIGQUERY_DATASET}.sp_update_person_cooccurrence_table`({since_param})",
            location="US-CENTRAL1"
        ).result()
        logger.info("Person cooccurrence table updated")
    except Exception as e:
        logger.error(f"Error updating person_cooccurrence table: {e}")
        cooccurrence_result = {"status": "failed", "error": str(e)}

    return {"person": person_result, "person_cooccurrence": cooccurrence_result}

@functions_framework.http
def gdelt_refresh(request):
    try:
        logger.info("Starting refresh")
        client = bigquery.Client(project=config.GCP_PROJECT_ID)
        ensure_datasets(client)
        results = {}
        for table_name in config.BIGQUERY_TABLES:
            if table_name in TABLE_METADATA:
                results[table_name] = incremental_refresh_table(client, table_name)
        success_count = sum(1 for r in results.values() if r.get("status") == "success")
        total_rows = sum(r.get("rows_added", 0) for r in results.values())
        logger.info(f"Complete: {success_count} tables, {total_rows} rows")
        person_results = update_person_tables(client)
        return {"status": "completed", "timestamp": datetime.utcnow().isoformat(),
                "summary": {"successful": success_count, "total_rows_added": total_rows},
                "details": results, "person_updates": person_results}, 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}, 500

