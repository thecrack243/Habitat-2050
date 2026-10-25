# Habitat 2050 · React frontend

This separate React + Vite app is the preferred interface; the root
Streamlit app remains available as a preserved legacy frontend. A
standard-library Python service in `api/` serves results from the existing
model pipeline. Python continues to own validation, modeling, predictions,
change areas, and exports.

The API binds to `127.0.0.1:8765` only. Vite proxies browser `/api` requests
locally. Plotly is bundled locally, including offline heatmap and scatter
renderers. No basemap tiles, remote fonts, credentials, cloud APIs, or Ollama
service are used.

## Start development app (Windows PowerShell)

From the project root, install Python dependencies into the project `.venv`
as described in the main README. Then:

```powershell
Push-Location .\fronten-2
npm.cmd ci
Pop-Location
.\.venv\Scripts\python.exe -B .\fronten-2\dev.py
```

Open `http://127.0.0.1:5174`. Press Ctrl+C to stop the frontend and local
model API. `start.ps1` is an alternative when the Python dependencies are
available on `PATH`.

## Verify and build

```powershell
python -B scripts/run_checks.py
Push-Location .\fronten-2
npm.cmd run build
Pop-Location
```

The frontend build performs a strict TypeScript check. `npm run dev` can also
start only the Vite process, but the Python API must already be running for
model results and exports.

The API exposes `/api/health`, `/api/dashboard`, and `POST /api/export`.
Threshold requests are validated; API errors are logged and returned with
appropriate HTTP error statuses. This is a local development service, not a
public hosting or production-deployment setup.
