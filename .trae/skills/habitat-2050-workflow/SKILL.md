---
name: habitat-2050-workflow
description: Build and validate the Habitat 2050 React/Vite frontend and Python model, or maintain its legacy Streamlit app. Use for Challenge 4 data cleaning, suitability modeling, maps, or demo work. Do not use for other challenges.
---

# Habitat 2050 workflow

## Load project context

Find the project root three directory levels above this skill directory.
Read root `AGENTS.md`, `docs/project_status.md`, `docs/architecture.md`, and
`docs/dataset_and_evaluation.md`. Treat paths below as root-relative.
Check the requested phase before editing. Setup does not authorize app
implementation. Inspect actual files and keep unrelated work intact.

Use React + Vite in `fronten-2` for the preferred UI, Plotly for interactive
maps, and pandas/NumPy/scikit-learn for Python modeling. The original
Streamlit app remains a preserved legacy frontend. A standard-library Python
API bound only to `127.0.0.1` is approved to deliver model results and evidence
exports to React. Do not add FastAPI, a cloud service, required QGIS, Docker,
LLM services, or a database. Keep human communication in English and all
user-facing copy available in Chinese and English, with Chinese as default.
Install `requirements.lock.txt` for the Python model and
`fronten-2/package-lock.json` for the frontend. Run `python -B
scripts/run_checks.py` for backend + legacy checks and `npm run build` in
`fronten-2` for frontend type-checking and production build. Run
`python -B scripts/export_results.py` to regenerate measured evidence.

## Establish the data contract

Use `src/habitat2050/paths.py` to locate the bundled dataset.
Run `python -B scripts/verify_scaffold.py` before altering the scaffold.
Read the bundled source notes. Preserve original files and their hashes.

At implementation time:

1. Audit coordinates, missing years, duplicate records, and unmatched cells.
   Keep an exclusion table with reason codes. Do not synthesize missing values
   for occurrence locations or silently snap out-of-area locations inward.
2. Match occurrence coordinates numerically to grid centers with an explicit
   tolerance well below half a cell. Deduplicate matched grid IDs before
   making any train/validation split.
3. Check current/future grid IDs, coordinates, numeric ranges, and static
   attributes. Join by grid ID and calculate geometry from coordinates.
   The documented north-to-south order disagrees with the actual CSV.
4. Keep `truth_auc.csv` out of training and tuning. Its range is a diagnostic
   reference, not held-out truth labels or an accuracy requirement.

## Model the minimum viable result

Use the five named environmental variables in the dataset documentation.
Use a fixed seed, initially 42, and record sample counts, selected background
cells, split IDs, parameters, dependency versions, and threshold policy.

Sample background from non-occurrence cells; explicitly distinguish it from
verified absence. Partition by grid ID and assert no overlap. Fit learned
preprocessing only on training data. Start with one random forest.

Measure ROC-AUC only when both classes exist in validation. Report validation
sample counts and split method. Mark non-spatial validation as preliminary;
spatial autocorrelation can inflate it. Do not keep changing the split to
improve a score. Assess background-sample sensitivity when time allows.

Predict present and future with the same fitted model and feature order.
Do not interpret classifier outputs as calibrated occupancy probabilities.
Record extrapolation outside the training environmental range.

## Present the result

Create current, 2050, and change views with comparable scales. Use Plotly
and coordinate-derived cell positions with readable tooltips. Make the
essential visualization work without downloading basemaps or fonts. Cache
deterministic data/model work so UI controls do not unintentionally retrain.

Derive change metrics from the actual predictions and a documented common
threshold. Use area-correct calculations for km2. Avoid unsupported corridor
or protection recommendations. Do not fabricate intermediate time steps.

Always identify SSP2-4.5, MPI-ESM1-2-HR, 2041-2060 and static vegetation.
State that the current climate baseline is 1970-2000, not observations of
today's climate. Include sources, uncertainty, and educational-use limits.
Keep Chinese and English UI copy in sync. Do not require a chatbot.

## Preserve the optional Ollama extension

Treat habitat Q&A with Ollama as deferred pending the user's decision.
Keep model results and source context separate from presentation so a future
assistant can consume them without changing the prediction pipeline.
Read the optional-extension boundary in `docs/architecture.md`.
Do not implement adapters, chat UI, prompts, dependencies, model downloads,
or service calls now.

If later approved, keep it optional and disabled by default. Ground answers
in supplied sources and computed results; never let the LLM calculate or
overwrite suitability. Require source references, explicit uncertainty,
bounded requests, and graceful unavailability handling. Verify that the full
dashboard works with Ollama disabled or unreachable.

## Verify and hand over

Test exclusions, matching, deduplication, split disjointness, feature order,
scenario alignment, prediction ranges, threshold categories, and map
orientation. Test the app startup and controls once an app exists. Distinguish
scaffold tests, model validation, and browser checks in reports.

Check portability from a different working directory and a copied root.
Preserve the entire source dataset and local instructions in the handoff;
exclude environments, credentials, caches, and temporary outputs.

Update `docs/project_status.md` after work. Synchronize changed decisions
across the README, AGENTS, TRAE rule, and this skill. Report measured evidence,
remaining gaps, and the next action without claiming unfinished features work.
