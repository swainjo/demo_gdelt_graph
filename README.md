# GCP GDELT Graph Analytics Demo

This repository contains a demonstration of Google Cloud analytics on the public **GDELT** (Global Database of Events, Language, and Tone) dataset. It showcases how to stage data into BigQuery, build a **Property Graph**, perform **incremental refreshes**, and profile results.

> [!IMPORTANT]
> This is a **demo** project designed for clarity, reproducibility, and a readable narrative. It is not intended for production use.

## 🚀 Features

- **Data Preparation**: Load and transform public GDELT data in BigQuery.
- **Property Graphs**: Create and query nodes and edges using BigQuery Property Graphs.
- **Incremental Refresh**: Demonstrate metadata-tracked incremental loads and cross-region copies.
- **Data Profiling**: Inspect and profile loaded data using Dataplex.
- **Automation**: Deploy the refresh pipeline as a Cloud Function with Cloud Scheduler.

## 📁 Repository Layout

| Path | Role |
| :--- | :--- |
| `notebooks/` | Core demo notebooks and configurations |
| `notebooks/01_gdelt_data_prep.ipynb` | Step 1: Data prep and stored procedures |
| `notebooks/02_gdelt_graph_create.ipynb` | Step 2: BigQuery Property Graph |
| `notebooks/03_gdelt_incremental_refresh.ipynb` | Step 3: Incremental loads |
| `notebooks/04_gdelt_data_profiling.ipynb` | Step 4: Data profiling |
| `requirements.txt` | Repository-wide Python dependencies |
| `AGENT_REFERENCE.md` | Detailed rules and guidelines for agents |

## 🛠️ Quick Start

### 1. Setup Environment

Clone the repository and install the dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\\Scripts\\activate`
pip install -r requirements.txt
```

### 2. Configure Google Cloud Project

Set the environment variable for your target GCP project:

```bash
export GDELT_GRAPH_DEMO_GCP_PROJECT="your-project-id"
```

*Alternatively, you can edit `notebooks/config.py` directly.*

### 3. Authenticate

Authenticate with Google Cloud:

```bash
gcloud auth application-default login
```

### 4. Run the Demo

Open Jupyter and run the notebooks in the `notebooks/` directory in sequential order:

1. `01_gdelt_data_prep.ipynb`
2. `02_gdelt_graph_create.ipynb`
3. `03_gdelt_incremental_refresh.ipynb` (Optional)
4. `04_gdelt_data_profiling.ipynb` (Optional)

## 📖 Further Reading

- Check [notebooks/README.md](./notebooks/README.md) for detailed notebook instructions and troubleshooting.
- See [ARCHITECTURE.md](./notebooks/ARCHITECTURE.md) for details on the incremental refresh design.
- Read [AGENT_REFERENCE.md](./AGENT_REFERENCE.md) for repository conventions and rules.
