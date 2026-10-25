# Habitat 2050

Challenge 4: climate-related habitat suitability for the Yunnan snub-nosed
monkey (Rhinopithecus bieti).

## Current status

**Two local frontends; React/Vite is the preferred interface.** The React app
in `fronten-2/` uses the existing Python model through a loopback-only API.
The original bilingual Streamlit app is preserved unchanged as a legacy
frontend. Both default to Chinese; Ollama remains unimplemented.

This folder is the independent project and submission root. Open this folder
itself in TRAE. It contains the complete, unchanged Challenge 4 source package.
No file from the parent workspace is needed.

The React frontend includes four interactive Plotly grid views, a cell
inspector, threshold sensitivity, bilingual copy, model evidence, data audit,
and a downloadable results bundle. Its Python API binds to `127.0.0.1`;
modeling, data files, and area calculations remain in the existing Python
pipeline. No credentials or online basemap/font service is required.

The original Streamlit app remains available via `.\start.ps1`. This
development layout is not a verified official submission template.

## Decisions

- Preferred frontend: React + Vite in `fronten-2/`; Plotly grid maps.
- Legacy frontend: existing Streamlit `app.py`, preserved without replacement.
- Python: existing validation/model pipeline, exposed through a local,
  standard-library API that only binds to `127.0.0.1`.
- Interface: Chinese-first with a complete English toggle.
- Modeling: Python, pandas, NumPy, scikit-learn; one random forest first.
- No FastAPI, cloud backend, Docker, database, required QGIS, or external AI service.
- Optional future extension: an Ollama habitat Q&A assistant. Decision deferred;
  nothing is installed or implemented for it. The core app must work without it.
- First build target: one dashboard, current/future/change maps, basic held-out
  evaluation, understandable limitations, and a reliable short demonstration.
- The 50-minute target is a scope constraint, not a tested delivery guarantee.

## Structure

```text
habitat-2050/
  app.py
  start.ps1
  requirements.lock.txt
  AGENTS.md
  .streamlit/config.toml
  .trae/rules/project_rules.md
  .trae/skills/habitat-2050-workflow/SKILL.md
  pyproject.toml
  src/habitat2050/       Data, modeling, maps, exports, and local styling
  tests/                Scaffold, scientific, and Streamlit interaction checks
  scripts/              Verification and evidence export entry points
  fronten-2/            React/Vite UI, Plotly maps, local Python API, and launcher
  data/processed/       Reserved for derived tables; raw data stays unchanged
  artifacts/            Default-threshold evidence ZIP and evaluation JSON
  docs/                 Architecture, dataset, evaluation, project status
  demo/                 Demonstration outline
  题四_栖息地2050_气候变化下的物种适生区预测/
    【发放给参赛队伍】物种适生区数据包/
      occurrence_records.csv
      env_factors.csv
      env_scenario_2050.csv
      truth_auc.csv
      数据来源与合规说明.txt
```

## Verify now

Python 3.11+ is required. From this folder in PowerShell:

```powershell
py -3.11 -B scripts/verify_scaffold.py
```

This needs only the Python standard library. It checks scaffold contracts and
the bundled data; it does not train or evaluate a model.

## Install and run the preferred React frontend

From this project folder in Windows PowerShell, use Python 3.11:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
```

Node.js 20+ and npm are required for the React frontend. Install the pinned
frontend dependencies once, then start the frontend and local Python API
together:

```powershell
Push-Location .\fronten-2
npm.cmd ci
Pop-Location
.\.venv\Scripts\python.exe -B .\fronten-2\dev.py
```

Open `http://127.0.0.1:5174`. Press Ctrl+C in the launcher terminal to stop
both processes. The API listens only on `127.0.0.1:8765`; Vite proxies `/api`
requests locally. The initial data/model calculation takes a few seconds.
Alternatively, run `.\fronten-2\start.ps1` when the Python dependencies are
already available on PATH.

The legacy Streamlit app is still available from the project root with
`.\start.ps1` at `http://127.0.0.1:8501`. Neither frontend requires a
credential or `.env` file. Do not change system execution policy to launch it.
The tested Python lockfile was produced with Python 3.11.9. Different
scikit-learn versions can change forecast outputs even with the same seed.

## Test and export

```powershell
.\.venv\Scripts\python.exe -B scripts/run_checks.py
.\.venv\Scripts\python.exe -B scripts/export_results.py
Push-Location .\fronten-2
npm.cmd run build
Pop-Location
```

The Python suite covers the model, scaffold, legacy Streamlit app, and the
React frontend API. The frontend build performs a strict TypeScript check and
produces static assets in `fronten-2/dist/`. `export_results.py` writes the
default-threshold evidence ZIP and evaluation JSON to `artifacts/`; both
frontends can also request an evidence bundle at the selected threshold. The
model is rebuilt deterministically from bundled inputs, never an untrusted
pickle.

## Measured baseline

With the locked runtime, seed 42, and threshold 0.50:

- 34 unique presence cells and 102 sampled background cells.
- 102 training cells; 34 validation cells (8 presence, 26 background).
- Held-out ROC-AUC: **0.8173**. This is preliminary non-spatial validation.
- Current suitable area: **26,721 km2**; 2050: **24,820 km2**.
- Net change: **-1,901 km2 (-7.1%)**, sensitive to the chosen threshold.

These are model outputs, not observed habitat loss. The full measured result
and limitations are in `artifacts/evaluation.json`.

## Continue here

Read `AGENTS.md`, `docs/project_status.md`, and the local skill before editing.
Keep rules and status up to date when decisions change. Human reports can be
exported to DOCX later; these Markdown files are portable repository guidance.

Retain `.trae`, `src`, documentation, tests, and the full dataset folder when
sharing this root. Do not ship virtual environments, secrets, or caches.
Review official competition packaging requirements when they become available.

## Scientific boundary

Outputs will be relative habitat suitability, not confirmed presence or
calibrated occupancy probabilities. The supplied future is SSP2-4.5,
MPI-ESM1-2-HR, 2041-2060, with vegetation held fixed. This is an educational
competition demonstration, not a conservation or land-use decision tool.
Preserve the bundled source and licensing notes.
