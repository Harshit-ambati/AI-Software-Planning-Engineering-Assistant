$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create .venv and install backend dependencies first; see README.md.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend\node_modules'))) { throw 'Run npm ci in frontend first.' }
$backend = Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','app.main:app','--app-dir','backend','--host','127.0.0.1','--port','8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru
try {
    Push-Location (Join-Path $projectRoot 'frontend')
    npm run dev
} finally {
    Pop-Location
    if (-not $backend.HasExited) { Stop-Process -Id $backend.Id }
}
