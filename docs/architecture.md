# Architecture and interface contracts

## Implemented now

- A source-layout Python package with portable path and feature constants.
- A bundled, unchanged Challenge 4 source folder.
- Standard-library verification, a source SHA-256 manifest, project rules,
  and a reusable local workflow skill.
- Bilingual React + Vite frontend in `fronten-2/`, with interactive Plotly
  grids, evidence views, threshold sensitivity, and ZIP exports.
- A loopback-only standard-library Python API presents outputs from the shared
  pipeline; no second model or data-processing implementation exists.
- The original bilingual Streamlit `app.py` remains as an unchanged legacy UI.
- Scientific invariants, React API contracts, and legacy Streamlit reruns are
  covered by automated tests.

## Application flow

```text
Bundled source CSVs
    -> validation / exclusions / occurrence-to-grid matching
    -> grid deduplication / background selection / disjoint split
    -> fitted random forest / validation results
    -> aligned current and future predictions
    -> 127.0.0.1 Python API / React + Vite / Plotly maps / source notes
```

Modules in `src/habitat2050/`:

| Module | Responsibility |
| --- | --- |
| paths.py | Implemented path and predictor constants |
| data.py | Loading, schema checks, grid alignment, exclusion audit |
| modeling.py | Sampling, fitting, evaluation, predictions, WGS84 cell areas |
| visualization.py | Coordinate-based grid maps, polygons, importance charts |
| exports.py | In-memory ZIP with predictions and full evidence |
| theme.css | Local light-theme styling; no downloaded assets |
| fronten-2/api/ | Loopback-only HTTP endpoints for health, dashboard, and ZIP export |
| fronten-2/src/ | React UI, bilingual copy, Plotly map, and presentation calculations |
| app.py at root | Preserved bilingual legacy Streamlit composition |

The React development server proxies `/api` to the standard-library API.
Both processes are started and stopped together with `fronten-2/dev.py`.
The API binds exclusively to `127.0.0.1:8765`; it provides no public hosting,
authentication, database, or persistence layer. Python remains the only
implementation of the model and area calculation.

## Data boundaries

- Clean occurrences: one row per retained grid_id, with an audit table linking
  raw record_id to retained grid or exclusion reason.
- Environmental data: unique grid_id, lon, lat, and exactly the five configured
  predictors. Join both scenarios on grid_id.
- Predictions: grid_id, lon, lat, suitability_current, suitability_2050,
  delta_suitability, and extrapolation flag. Scores must be finite in [0, 1];
  delta is future minus current.
- Change classes: lost, gained, stable suitable, and stable unsuitable, based
  on a documented common threshold. Do not call these observed habitat changes.
- Evaluation: seed, counts, split method and IDs, background sampling policy,
  parameters, measured metrics, threshold method, and warnings.

Both UIs consume the same computed results. Slider, map, and language
interactions must not cause random resampling or implicit model retraining.
The local API caches results against bundled source hashes. The React app can
recompute threshold summaries from predictions but never recalculates scores.

## Optional future habitat assistant

**Decision deferred. No Ollama integration is approved or implemented.**
Keep the existing separation of modeling, results, and UI; no speculative
adapter code or additional dependency is needed now.

If the user later approves, add a separate explanation component:

```text
Question + selected-cell values + verified results + cited source context
    -> optional local Ollama adapter
    -> grounded explanation in a separate frontend panel
```

The assistant would explain habitat and existing results, not train the model,
calculate suitability, modify data, or execute user instructions as tools.
Keep context small and relevant; no vector database is required initially.
Distinguish sourced facts, computed findings, and unknowns. Include source
references and do not invent ecological causes from feature importance.

Keep the feature disabled by default. When disabled, make no Ollama calls.
When enabled, use a local endpoint, bounded context and timeouts, and display
unavailability without blocking maps or metrics. Do not silently fall back
to a cloud provider. Treat questions and source content as untrusted input.
Do not persist conversations by default.

Choose a model only after checking available hardware and installed models.
Installation, model downloads, configuration, prompts, and chat UI all remain
future work requiring the user's decision. Core app startup and use must
never require Ollama.

## Deployment and paths

Run from the full copied root after installing locked dependencies. A standalone wheel
is not a supported distribution: raw data is intentionally beside the package,
not embedded inside a wheel.

Use pathlib with Unicode paths. Do not depend on the parent folder, personal
home directories, absolute paths, external credentials, or online map tiles.
Essential maps should be coordinate-based grid polygons even without a basemap.
Do not interpolate the two supplied time slices into fictional year forecasts.

Install `requirements.lock.txt` for the tested runtime; editable installation
is optional because entry points add their own file-relative `src` path.
`start.ps1` accepts an explicit interpreter and binds to localhost, setting
the light theme even when launched from another directory.

Cache keys include source SHA-256 hashes and MODEL_VERSION. Bump MODEL_VERSION
when changing training or dependent pipeline logic to invalidate cached results.
One training-only forest is used for evaluation and both projections; it is
not refitted on validation. Default 0.5 is an illustrative cutoff, never a
validation-optimized threshold.

All maps use heatmap cell edges plus scatter centers for selection. Lon/lat
positions determine orientation; no tile server or geographic asset fetch is
needed. GeoJSON exports contain explicit cell polygons.

The React frontend dependencies are locked in `fronten-2/package-lock.json`;
Python dependencies remain in `requirements.lock.txt`. Do not load `.env`
secrets or contact cloud services. The API's health endpoint exists to verify
the local React-to-Python connection; it is not a cloud service or public API.

## Suggested team areas

1. React layout and user journey; the Streamlit app is a preserved legacy UI.
2. Data validation, exclusions, and portable file handling.
3. Background sampling, model training, and evaluation.
4. Plotly maps, legends, tooltips, and change calculations.
5. Integration tests, source notes, presentation, and packaging.

These are suggested ownership boundaries, not assigned people or permission
to create sub-agents. Agree on data contracts before working in parallel.
