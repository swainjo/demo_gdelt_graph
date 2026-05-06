# GDELT Graph Demo Notebooks

This directory contains Jupyter notebooks for analyzing GDELT (Global Database of Events, Language, and Tone) data using BigQuery Property Graphs.

## 📋 Quick Start

### 1. Configure Your Project

Edit `config.py` and update the following:

```python
GCP_PROJECT_ID = "your-project-id"  # Replace with your GCP project ID
```

You can instead set the environment variable **`GDELT_GRAPH_DEMO_GCP_PROJECT`** (see `config.py`). The notebooks do **not** read the project ID from `GOOGLE_CLOUD_PROJECT`.

### 2. Install Dependencies

Dependencies for the notebooks live in the repository root (`../requirements.txt` relative to this folder). From the repo root:

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Cloud Function:** `cloud_function/requirements.txt` is only for deploying the incremental refresh function to GCP (Cloud Functions installs it at deploy time). You do **not** need it to run these notebooks.

**Kernel:** Notebooks use the generic `python3` kernel. Select the interpreter from your activated virtualenv (with `ipykernel` installed, as above) in VS Code, Cursor, or JupyterLab.

### 3. Run Notebooks in Order

**Core pipeline** (run in order):

| Order | Notebook | Description |
|-------|----------|-------------|
| 1️⃣ | `01_gdelt_data_prep.ipynb` | Prepares GDELT data and creates BigQuery tables |
| 2️⃣ | `02_gdelt_graph_create.ipynb` | Creates the BigQuery Property Graph |

**Optional** (after the core pipeline, as needed):

| Notebook | Description |
|----------|-------------|
| `03_gdelt_incremental_refresh.ipynb` | Incremental merges from public GDELT; updates person tables via stored procedures from notebook 01 |
| `04_gdelt_data_profiling.ipynb` | Dataplex profiling and AI-generated table/column descriptions |

⚠️ **Important**: Run **01** then **02** for the main demo. Notebook **03** requires **01** (tables and procedures); **04** needs populated tables (typically after **01**, and after **02** if you want graph-related tables described).

Teardown helpers live in **`clean_up/`** — see the numbered “Full reset order” section in each cleanup notebook.

## 📁 Files

- **`config.py`** - Centralized configuration file for all notebooks
- **`../requirements.txt`** (repo root) - Python dependencies for notebooks (includes `google-cloud-dataplex` for notebook 04)
- **`01_gdelt_data_prep.ipynb`** - Data preparation notebook
- **`02_gdelt_graph_create.ipynb`** - Graph creation notebook
- **`03_gdelt_incremental_refresh.ipynb`** - Incremental refresh (and optional in-notebook Cloud Function scaffolding)
- **`04_gdelt_data_profiling.ipynb`** - Dataplex profiling and documentation API
- **`cloud_function/`** - Deployable incremental refresh function (`deploy.sh` copies `config.py` before upload)
- **`clean_up/`** - Notebooks to drop graphs, incremental artifacts, Dataplex scans, or full datasets

## ⚙️ Configuration Options

All configuration is managed in `config.py`:

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Your GCP project ID | `graph-demo-3` (or value of `GDELT_GRAPH_DEMO_GCP_PROJECT`) |
| `PROJECT_REGION` | GCP region for operations | `us-central1` |
| `BIGQUERY_DATASET` | BigQuery dataset name | `gdelt` |
| `BIGQUERY_TABLES` | Tables to process | `[gkg_partitioned, events_partitioned, eventmentions_partitioned]` |
| `QUERY_DATE` | Date for data queries | `2025-01-27` |
| `GCS_BUCKET` | Cloud Storage bucket | `gdelt_graph` |

## 🔍 What Each Notebook Does

### 01_gdelt_data_prep.ipynb
- Sets up GCP authentication
- Connects to GDELT public BigQuery dataset
- Prepares and transforms GDELT data
- Creates required tables for graph analysis
- Extracts entities (persons, organizations, locations, events)
- Builds relationship tables

### 02_gdelt_graph_create.ipynb
- Connects to your BigQuery project
- Creates a Property Graph from prepared tables
- Defines nodes (Person, Organization, Location, Event, Article)
- Defines edges (CO_OCCURS_WITH, AFFILIATED_WITH, LOCATED_AT)
- Runs sample graph queries

### 03_gdelt_incremental_refresh.ipynb
- Incrementally merges new rows into the partitioned GDELT tables (US → US-CENTRAL1)
- Maintains `_sync_metadata` and calls person-table stored procedures defined in notebook 01
- Optional: cells to scaffold/deploy a Cloud Function (production deploy typically uses `cloud_function/deploy.sh`)

### 04_gdelt_data_profiling.ipynb
- Runs Dataplex data profile scans per table
- Uses the Dataplex Data Documentation API (Gemini-backed) and applies descriptions in BigQuery
- Requires the Dataplex API enabled and dependencies from the repo root `requirements.txt`

## 🛠️ Troubleshooting

### "Project ID not configured"
Update `GCP_PROJECT_ID` in `config.py` with your actual project ID, or set **`GDELT_GRAPH_DEMO_GCP_PROJECT`**.

### "Authentication failed"
Run the authentication cell in `01_gdelt_data_prep.ipynb` to authenticate with GCP.

### "Table not found"
Ensure you've run `01_gdelt_data_prep.ipynb` completely before running `02_gdelt_graph_create.ipynb`.

### Dataplex / `dataplex_v1` import errors (notebook 04)
Install from the repo root with `pip install -r requirements.txt` and enable the Dataplex API on your project.

## 📖 Additional Resources

- [GDELT Project](https://www.gdeltproject.org/)
- [BigQuery Property Graphs](https://cloud.google.com/bigquery/docs/graph-analytics)
- [Google Cloud BigQuery](https://cloud.google.com/bigquery/docs)
