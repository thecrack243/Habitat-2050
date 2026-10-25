# Project instructions

Treat this directory as the entire workspace root. Read this file and
`docs/project_status.md` before acting. For Challenge 4 implementation, modeling,
map work, or validation, also read
`.trae/skills/habitat-2050-workflow/SKILL.md` in full.

## Fixed decisions

1. The user selected a separate React + Vite frontend in `fronten-2` as the
   preferred UI. Keep the original Streamlit app intact as a legacy frontend.
   Use Plotly for interactive maps and Python for all modeling. A standard-
   library Python API bound only to `127.0.0.1` is approved for this local UI;
   do not add a cloud backend, FastAPI, or QGIS without further approval.
2. Keep both apps local, credential-free, and independent of network basemaps.
   Do not add Docker, a database, or a chatbot. The local API only presents
   results from the existing model; it does not change model behavior.
   Keep an optional Ollama habitat assistant possible through separated UI,
   model results, and explanation logic. It is deferred, not approved for
   implementation. Add no LLM code, dependencies, downloads, or service calls
   until the user decides. The dashboard must work fully without it.
3. Build one random-forest model first. Add a second model or spatial evaluation
   only when the core demo works and time allows. Clearly label ordinary
   held-out validation as preliminary without spatial validation.
4. App implementation is authorized as of 2026-10-25. Build and test the
   React/Vite frontend alongside the preserved Streamlit app. Ollama remains
   deferred. Keep the UI Chinese-first with an English toggle.

## Portability and integrity

- Derive paths from files using pathlib, never the process working directory
  or an absolute developer-machine path. Keep all required assets inside here.
- The bundled original Challenge 4 directory is logically read-only. Write
  derived data to `data/processed` and model outputs to `artifacts`.
- Preserve raw file names, Chinese paths, UTF-8 content, and source notes.
  Do not modify other challenge folders.
- Do not invent missing data, labels, citations, scientific conclusions,
  model performance, or test outcomes.
- Do not treat `truth_auc.csv` as labels, training features, or a tuning target.
- Never expose finer species locations than the supplied coarse grid.

## Scientific contract

- Audit missing/out-of-grid coordinates; log exclusions without fabricating
  coordinates. Match numerically with documented tolerance.
- Deduplicate by matched grid ID before splitting. Background cells are not
  confirmed absences. Keep training and validation grid IDs disjoint.
- Use only the five environmental predictors, not IDs, coordinates, source
  types, years, or reference AUC values. Fix and record random seeds.
- Build grid polygons from lon/lat, not row-order assumptions. The source
  notes and actual north/south ordering disagree.
- Join present/future data on grid_id. Only climate changes in this scenario.
- Display relative suitability, not occupancy probability. Explain threshold
  choices. Compute area using geodesic or equal-area methods, never square
  degrees or an assumed identical 81 km2 per cell.
- Do not fabricate intermediate-year or additional-scenario forecasts.
- Educational use only; preserve attribution and uncertainty statements.

## Workflow

Separate data loading, validation, modeling, visualization, and UI. Keep
dependencies minimal. Read existing files before editing; preserve user work.
Test changes, report what actually ran, and update `docs/project_status.md`
with implemented versus planned features and the next action.

Use English for collaboration and repository guidance. Keep all user-facing
app copy available in Chinese and English; default to Chinese.

The judge weights are 30% technical experts, 40% university judges, and 30%
audience. Protect time for completeness, map clarity, testing, and a short
presentation rather than expanding scope.

Team areas in the docs are suggestions, not authorization to spawn agents.
No commits, destructive operations, or external publication without permission.

When a decision changes, update this file, the TRAE rule, the relevant skill,
and project status together. Do not rely on memory outside this folder.
