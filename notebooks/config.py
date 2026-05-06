"""
GDELT Graph Demo - Configuration File

This file contains all configuration variables for the GDELT analysis notebooks.
Update the values below to match your GCP project settings.

Execution Order:
1. Run 01_gdelt_data_prep.ipynb first (prepares data and creates tables)
2. Run 02_gdelt_graph_create.ipynb second (creates the property graph)
"""

# ============================================================================
# GCP PROJECT SETTINGS
# ============================================================================
# IMPORTANT: Set your GCP project ID below (or export GDELT_GRAPH_DEMO_GCP_PROJECT
# for CI/automation). We intentionally do not read GOOGLE_CLOUD_PROJECT here: it is
# commonly exported globally and would override this file with the wrong project.
import os

GCP_PROJECT_ID = os.environ.get("GDELT_GRAPH_DEMO_GCP_PROJECT", "graph-demo-3")
PROJECT_REGION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", "gdelt")

# ============================================================================
# BIGQUERY SETTINGS
# ============================================================================
# Tables to process from GDELT public dataset
BIGQUERY_TABLES = [
    "gkg_partitioned",
    "events_partitioned",
    "eventmentions_partitioned"
]

# ============================================================================
# GDELT PUBLIC DATASET SETTINGS
# ============================================================================
GDELT_PROJECT_ID = "gdelt-bq"
GDELT_DATASET = "gdeltv2"
GDELT_REGION = "us"

# ============================================================================
# STORAGE SETTINGS
# ============================================================================
# Google Cloud Storage bucket (optional, for data exports)
GCS_BUCKET = "gdelt_graph"  # Set to your bucket name if needed

# ============================================================================
# DATE CONFIGURATION
# ============================================================================
# Date configuration (format: YYYY-MM-DD for timestamp, YYYYMMDD for SQLDATE)
QUERY_DATE = "2025-01-27"  # Update this to query different dates
QUERY_DATE_SQLDATE = "20250127"  # Same date in SQLDATE format

# ============================================================================
# HELPER FUNCTION
# ============================================================================
def validate_config():
    """Validate that required configuration is set"""
    if GCP_PROJECT_ID == "graph-demo-471710":
        print("⚠️  WARNING: You're using the default project ID.")
        print("   Please update GCP_PROJECT_ID in config.py with your actual project ID.")
        return False
    return True

def print_config():
    """Print current configuration settings"""
    print("=" * 70)
    print("GDELT Graph Demo - Configuration")
    print("=" * 70)
    print(f"GCP Project ID:      {GCP_PROJECT_ID}")
    print(f"Project Region:      {PROJECT_REGION}")
    print(f"BigQuery Dataset:    {BIGQUERY_DATASET}")
    print(f"BigQuery Tables:     {', '.join(BIGQUERY_TABLES)}")
    print(f"GDELT Source:        {GDELT_PROJECT_ID}.{GDELT_DATASET}")
    print(f"GDELT Region:        {GDELT_REGION}")
    print(f"GCS Bucket:          {GCS_BUCKET}")
    print(f"Query Date:          {QUERY_DATE}")
    print(f"Query Date (SQL):    {QUERY_DATE_SQLDATE}")
    print("=" * 70)
