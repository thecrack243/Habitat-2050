param(
    [string]$Python = "",
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$env:PYTHONDONTWRITEBYTECODE = "1"
if (-not $Python) {
    $localPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    $Python = if (Test-Path -LiteralPath $localPython) { $localPython } else { "python" }
}

& $Python -B -m streamlit run (Join-Path $PSScriptRoot "app.py") `
    --server.address 127.0.0.1 --server.port $Port --server.headless true `
    --browser.gatherUsageStats false --theme.base light `
    --theme.primaryColor "#2d6a4f" --theme.backgroundColor "#f7f8f3" `
    --theme.secondaryBackgroundColor "#eef2e9" --theme.textColor "#234739"
exit $LASTEXITCODE
