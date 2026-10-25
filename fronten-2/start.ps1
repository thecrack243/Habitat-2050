$ErrorActionPreference = "Stop"
$env:PYTHONDONTWRITEBYTECODE = "1"
python -B (Join-Path $PSScriptRoot "dev.py")
exit $LASTEXITCODE
