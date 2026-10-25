# Project status and portable memory

## Phase

2026-10-25: the original bilingual Streamlit MVP is verified. A separate
React/Vite frontend and loopback-only Python results API have now been built
and browser-checked as the newly preferred UI; the Streamlit app remains intact.

## Confirmed decisions

- Challenge 4 only, for Rhinopithecus bieti.
- React/Vite frontend in `fronten-2/`, with Streamlit retained for legacy use.
- Python model pipeline and Plotly maps shared across both interfaces.
- Chinese-first interface with an English toggle, selected by the user.
- Self-contained `habitat-2050` root with the complete original data folder.
- A standard-library local API bound to `127.0.0.1` is approved to serve the
  React interface. No FastAPI, public service, mandatory QGIS, Docker, or
  external AI API.
- Aim for a tightly scoped 50-minute prototype once implementation begins.
  Dependency installation and environment issues can affect feasibility.
- One random forest and one supplied future scenario initially.
- User requested setup first and app implementation afterward.
- Rules and skills must travel with the root rather than rely on chat memory.
- Optional Ollama habitat Q&A remains an open, deferred decision. The user
  asked to preserve the possibility, not implement it. Keep result/UI
  boundaries modular; no LLM code, dependencies, downloads, or calls now.
  The core dashboard must work independently of any future assistant.

## Judging priorities

| Group | Weight | Criteria supplied by the user |
| --- | --- | --- |
| ByteDance experts | 30% | Technical implementation and AI; collaborative innovation and track expertise |
| University judges | 40% | Completeness and refinement; presentation and track expertise |
| Live audience | 30% | Hands-on experience and visuals; emotional impact and track experience |

Weights are not feature scores. Protect time for testing, clarity, and demo
reliability. Full official submission rules and the detailed challenge brief
have not been supplied.

## Proposed implementation timebox

1. Minutes 0-10: check environment, load data, audit and deduplicate.
2. Minutes 10-22: sample background, fit model, evaluate, predict both periods.
3. Minutes 22-37: current/future/change maps and summaries.
4. Minutes 37-45: improve layout, attribution, limitations, and explanation.
5. Minutes 45-50: test controls, verify launch, and rehearse.

This is a planning estimate, not a promise or recorded execution time.
Defer a chatbot, second model, quiz, animations, and extensive spatial
validation. Without spatial validation, report model evaluation as preliminary.

## Next action

The new frontend is verified locally. Next rehearse both the desired startup
path and demo flows, consider optimizing the deferred Plotly bundle, and
review official submission packaging requirements. Recreate an isolated
Python 3.11 lockfile environment before reporting locked-runtime model results.

## Frontend decision and progress

- The user explicitly chose React + Vite, the separate folder name
  `fronten-2`, and a local API integration; the Streamlit UI is to be kept
  alongside it, not removed.
- Added bilingual React UI, interactive Plotly maps, threshold sensitivity,
  cell inspector, model evidence/audit, download control, and local API.
- The Python API reuses the existing pipeline and serves dashboard data and
  evidence ZIP exports. It binds to loopback only; no model behavior or raw
  files changed.
- Node.js/npm dependencies are pinned in `fronten-2/package-lock.json`;
  `npm ci` succeeds. Node.js 22.11.0 is available. Plotly's full offline
  heatmap bundle is deferred-loaded so it does not block the initial
  dashboard. The production build passes TypeScript checks.
- API and legacy/model tests: `python -B scripts/run_checks.py` passed **30
  tests**. These cover dashboard data contracts, loopback health, invalid
  threshold errors, and ZIP export.
- Live browser check passed at desktop and 390px viewport widths: React UI
  rendered the Plotly heatmap with no browser console errors or UI exceptions;
  English/Chinese switch, all four map tabs, grid selection, and threshold
  sensitivity worked. The dashboard had no horizontal overflow at 390px.
- The frontend's export endpoint returned a valid ZIP signature with HTTP 200;
  the bundle itself and error handling are also covered by API tests.
- The deferred full Plotly bundle is about 4.74 MB (about 1.45 MB gzip) for
  offline heatmap support; it is loaded only when the map enters the viewport.
  This remains a performance tradeoff.
- Dependency install and frontend build use the machine's Node 22.11.0;
  project does not target a Node version below 20.

## GitHub publication

- The user requested publication to `thecrack243/Habitat-2050`.
- The local workspace was not a Git checkout. The target is a public, empty
  GitHub repository with default branch `main`. GitHub SSH access rejected
  the available key; a cached Git Credential Manager login is available for
  the repository owner, so publication uses the same repository over HTTPS.
- Publish the project and its bundled Challenge 4 sources. Exclude Python and
  Node environments, build output, credentials, and caches according to the
  repository ignore rules.

## Latest verification

Checked 2026-10-25 using the available Python 3.13.9 runtime and its installed
dependencies (Streamlit 1.51.0, pandas 2.3.3, NumPy 2.4.6, scikit-learn 1.7.2,
Plotly 6.3.0):

- `python -B scripts/run_checks.py`: **PASS**, all 25 tests.
- Started Streamlit on `127.0.0.1:8517`; HTTP probe returned **200** and HTML.
- Opened the running app in a browser: bilingual dashboard rendered with two
  Plotly charts and no visible Streamlit exception. App tests also exercised
  both languages, all map views, grid selection, threshold changes, and
  display toggles.
- This runtime's displayed held-out ROC-AUC was **0.837**; the displayed
  current/future suitable areas were **18,414/17,672 km2** at threshold 0.50.
  These differ from the documented locked-runtime baseline because this
  interpreter has different Streamlit and scikit-learn versions. They are
  environment-specific observations, not a replacement baseline.
- The temporary local server was stopped after the smoke test. No dependency
  installation, source-data edits, or model-export regeneration was performed.

## Initial setup evidence (historical)

The following records the earlier setup-only inspection, before the MVP was
implemented and validated; later verification above supersedes its statements
that runtime checks had not yet been performed.

- Python 3.11.9 is available on the setup machine.
- Streamlit and pytest were not installed in that interpreter at inspection.
  No dependencies were installed during setup.
- Installed TRAE code recognizes `.trae/rules/*.md`, `alwaysApply: true`,
  and `AGENTS.md`; the project skill path follows the installed skill-creator
  instructions. UI activation has not been directly tested. Open this folder
  as the workspace root; AGENTS.md remains readable guidance in other tools.
- Data inspection found 34 distinct matched occurrence cells; see the dataset
  notes for exclusions and provenance discrepancies.
- All five copied source files matched the original package by SHA-256.
  The portable manifest is `docs/source_manifest.json`.
- All 10 standard-library scaffold checks passed from the project root,
  from a different working directory, and from a relocated temporary copy.
  They cover paths, hashes, data schema/ranges, scenario alignment, grid
  geometry, occurrence audit, package metadata, skill structure/references,
  the always-on rule, and reference-AUC feature separation.
- Model evaluation, dependency installation, app startup, browser interactions,
  and visual quality have not been tested because the app is not built.

## Latest decision update

2026-10-25: documented the deferred Ollama option consistently in README,
AGENTS, the TRAE rule, the project skill, and architecture. No runtime code,
dependencies, or data changed. No Ollama availability or model was tested.

## Update discipline

After every meaningful work session, record what is implemented, checks run,
limitations, and next action here. Change decisions in AGENTS.md, the TRAE
rule, skill, and README together. Never mark planned functions as completed
just because directories or dependencies exist.
