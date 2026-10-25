---
alwaysApply: true
---

# Habitat 2050 project rule

Read `AGENTS.md` and `docs/project_status.md` at the start of work. They carry
the project decisions and current phase. Resolve them relative to this
project root, not the parent competition-data workspace.

Use `.trae/skills/habitat-2050-workflow/SKILL.md` for Challenge 4 development,
modeling, maps, evaluation, and demo preparation.

- The preferred UI is the separate React + Vite frontend in `fronten-2`;
  preserve the original Streamlit app unchanged as a legacy frontend. Use
  Python for model computation and Plotly for interactive maps. A standard-
  library Python API bound only to `127.0.0.1` is approved to serve the local
  frontend. Do not add FastAPI, a cloud service, or QGIS without approval.
- App implementation is authorized. Use Chinese-first copy with an English
  toggle; preserve the local MVP scope and keep Ollama deferred.
- Keep the copied Challenge 4 source directory unchanged and bundled.
- Use pathlib and file-relative paths. No parent-workspace dependencies.
- Keep raw data, derived data, model logic, and presentation separate.
- Deduplicate matched grid cells before splits; background is not absence.
- Never train or tune against `truth_auc.csv`; never invent model results.
- Derive map positions from coordinates, not grid ID ordering.
- Label suitability and limitations honestly; protect coarse species locations
  and retain source attribution.
- Use minimal dependencies and meaningful tests. Update project status after
  work. Report checks actually run and unresolved limitations.
- Preserve the MVP scope; do not add Docker, a chatbot, or a database.
- Keep Ollama habitat Q&A as a deferred optional extension, not an approved
  feature. Preserve separation of results and UI; add no LLM code, packages,
  model downloads, or calls now. Core functionality must not depend on Ollama.
- Use the local files as portable memory. Synchronize changes across
  `AGENTS.md`, this rule, the skill, README, architecture, and status.
