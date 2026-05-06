# Agent reference (canonical)

Single source of truth for humans and coding agents working on this repository. Stub files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) point here; **open this file** when your tool only ingests a short stub.

## Purpose

This repo is a **demo** of Google Cloud analytics on the public **GDELT** dataset: Jupyter notebooks stage data into BigQuery, build a **Property Graph**, walk **incremental refresh**, and profile results; `notebooks/cloud_function/` shows the same refresh **on a schedule**.

**Not production.** Optimize for clarity, reproducibility, and a readable narrative — not hardening, scale, or cost tuning unless asked. Agents should preserve data-facing behavior, keep config centralized, and avoid silent cross-project mistakes on GCP.

### Demo flow (order matters)

| Step | File | What it shows |
|------|------|----------------|
| 1 | `notebooks/01_gdelt_data_prep.ipynb` | Dataset/table creation, load from public GDELT, stored procedures (full rebuild) |
| 2 | `notebooks/02_gdelt_graph_create.ipynb` | BigQuery Property Graph (nodes + edges) and queries |
| 3 | `notebooks/03_gdelt_incremental_refresh.ipynb` | Cross-region copy (US → `us-central1`), MERGE dedup, metadata-tracked incremental loads |
| 4 | `notebooks/04_gdelt_data_profiling.ipynb` | Inspect / profile loaded data |
| 5 | `notebooks/cloud_function/` | Deploy step 3 as a Cloud Function + Cloud Scheduler |

See also `notebooks/INCREMENTAL_REFRESH_GUIDE.md` for the refresh story.

## Do this / avoid this

| Good | Avoid |
|------|--------|
| Read `notebooks/config.py` and match project/dataset/region before running or editing queries | Assuming `GOOGLE_CLOUD_PROJECT` or notebook defaults are the intended target project |
| Small, task-scoped diffs; match existing notebook and Python style | Drive-by refactors, deleting unrelated comments, or broad rewrites |
| Run notebooks in documented order when touching the pipeline | Skipping `01` before changing schema expectations in `02` / `03` |
| Use env vars documented in `config.py` for automation (`GDELT_GRAPH_DEMO_GCP_PROJECT`, etc.) | Hardcoding new project IDs in multiple places |
| For deploy paths, follow `notebooks/cloud_function/README.md` | Deploying from ad-hoc copies of `config.py` that drift from `notebooks/config.py` |

## Repository layout

| Path | Role |
|------|------|
| `requirements.txt` | Notebook / local Python dependencies (repo root) |
| `notebooks/config.py` | **Central config**: GCP project, region, BigQuery dataset, table list, dates |
| `notebooks/01_*.ipynb` … `04_*.ipynb` | Ordered pipelines (prep → graph → incremental / profiling as applicable) |
| `notebooks/ARCHITECTURE.md` | Incremental refresh and data-flow detail |
| `notebooks/README.md` | Notebook quick start and troubleshooting |
| `notebooks/INCREMENTAL_REFRESH_GUIDE.md` | Refresh pipeline walkthrough |
| `notebooks/cloud_function/` | Cloud Function source, `deploy.sh`, function-specific `requirements.txt` |
| `notebooks/AGENTS.md` | Stub → this file (Conductor pointer lives here for some setups) |
| `notebooks/conductor/` | Conductor extension tracks, plans, product docs (if using Conductor) |
| `notebooks/.agents/skills/` | Conductor-related skills |

## Numbered working rules

1. **Confirm target GCP context** before running cells or shell that touch BigQuery (see [Quick gcloud / config check](#quick-gcloud--config-check)).
2. **Preserve the demo narrative.** Do not refactor notebooks into helper modules; cells are the lesson. Each cell should show one concept where practical.
3. **Be explicit.** Prefer inlined SQL, API calls, and IAM steps over helpers that hide GCP behavior — unless the user asks for abstraction.
4. **Do not over-engineer.** Avoid retry loops, heavy defensive error handling, or production patterns unless the demo is explicitly teaching them.
5. **Prefer `notebooks/config.py`** (or its documented env overrides) as the single source for project ID, region, and dataset.
6. **Respect execution order** (demo table above); downstream notebooks assume upstream tables and procedures exist.
7. **Keep Cloud Function config in sync**: deployment copies `notebooks/config.py` into `cloud_function/` via `deploy.sh` — edit the shared parent config so keys stay aligned.
8. **Cross-region behavior** (GDELT public data in `US` multi-region, destination in `us-central1`) is intentional; do not “simplify” without reading `notebooks/ARCHITECTURE.md`.
9. **Incremental refresh** semantics (MERGE keys, metadata, person-table procedures) live in `ARCHITECTURE.md`; align changes with that design.
10. **Respect placeholders.** If `validate_config()` warns about a default project ID, do not replace it with a real production ID in committed code unless the user requests that.
11. **Large or risky changes**: outline the approach and get confirmation before editing broadly (repo convention).

### Stored-procedure contract

`gdelt.sp_update_person_table` and `gdelt.sp_update_person_cooccurrence_table` each take one **TIMESTAMP** argument:

- **`NULL`** → full rebuild (used by `01_gdelt_data_prep.ipynb`).
- **Non-null** → incremental since that timestamp (used by `03_gdelt_incremental_refresh.ipynb` and the Cloud Function).

Preserve this signature if you touch those procedures or their callers.

## Conventions

- **Python**: Match surrounding notebook/script style; avoid unnecessary abstractions in one-off cells.
- **Config**: `GCP_PROJECT_ID` defaults come from `GDELT_GRAPH_DEMO_GCP_PROJECT` when set; the code intentionally does **not** use `GOOGLE_CLOUD_PROJECT` for this demo’s project ID (see comments in `notebooks/config.py`).
- **Secrets**: No credentials in repo; use `gcloud auth application-default login` or workspace secrets as appropriate.
- **Docs**: Do not add new top-level guides or notebooks unless the task asks for it. Do not rename numbered notebooks — the prefix order is the demo script.
- **Git**: Do not commit `.env`, service-account keys, or real secrets. Use the branch the session specifies when one is given; do not open a PR unless asked.

## When making changes

- Touch only files and lines needed for the request.
- Do not remove or rewrite unrelated comments or “tidy” adjacent code.
- If you change schema, refresh logic, or deploy steps, cross-check `notebooks/ARCHITECTURE.md` and `notebooks/cloud_function/README.md`.
- After logical edits to config or deploy, verify with the [quick checks](#quick-gcloud--config-check) where applicable.

## Authentication and GCP access

- **Local / notebooks**: Users authenticate with Google as described in `01_gdelt_data_prep.ipynb` and `notebooks/README.md` (typical: Application Default Credentials after `gcloud auth application-default login`).
- **Cloud Function HTTP trigger** (from `notebooks/cloud_function/README.md`): invoke with a Google-signed identity token, e.g. `Authorization: Bearer $(gcloud auth print-identity-token)`; Scheduler uses its own OIDC token.
- **Permissions**: Deployer and runtime service accounts need BigQuery roles as listed in `notebooks/cloud_function/README.md`.

## Claude Code (web) and branches

If you use **Claude Code on the web** or another environment that does not share your local git state by default, **create or attach a branch / worktree** for the session so changes do not land on the wrong default branch and can be reviewed like normal git work. Prefer a named feature branch when the workflow expects review or CI.

## Conductor: plans and file resolution

If the user mentions a **plan** and uses the Conductor extension in the session, they likely mean `notebooks/conductor/tracks.md` or a track plan under `notebooks/conductor/tracks/<track_id>/plan.md`.

**Resolve docs by index:**

1. **Project context**: read `notebooks/conductor/index.md` and follow matching links (paths relative to that file’s directory).
2. **Track context**: from the tracks registry in `notebooks/conductor/tracks.md`, open the track folder, then `index.md` inside it.
3. If unregistered or missing links, fall back to:
   - Product: `notebooks/conductor/product.md`
   - Workflow: `notebooks/conductor/workflow.md`
   - Track spec: `notebooks/conductor/tracks/<track_id>/spec.md`
   - Track plan: `notebooks/conductor/tracks/<track_id>/plan.md`
4. **Verify** the file exists on disk after resolving.

Relevant skills live under `notebooks/.agents/skills/` (conductor-*). Do not modify conductor files unless explicitly requested.

## Quick local setup

```bash
pip install -r requirements.txt
export GDELT_GRAPH_DEMO_GCP_PROJECT=your-project-id   # preferred for this repo; see notebooks/config.py
gcloud auth application-default login
jupyter notebook notebooks/
```

`.env sample` is a template for local secrets (for example API keys). Real `.env` is gitignored.

## Quick gcloud / config check

Run from the repo root (or any directory; these commands are global):

```bash
gcloud config get-value project
gcloud auth list --filter=status:ACTIVE --format="value(account)"
```

In Python (from repo root, with venv if you use one):

```bash
python -c "import sys; sys.path.insert(0, 'notebooks'); import config; config.print_config()"
```

Confirm **project**, **region**, and **dataset** match the environment you intend before destructive BigQuery operations or deploys. Override project safely with:

```bash
export GDELT_GRAPH_DEMO_GCP_PROJECT="your-project-id"
```

---

*Stub entrypoints: [AGENTS.md](./AGENTS.md), [CLAUDE.md](./CLAUDE.md), [GEMINI.md](./GEMINI.md).*
