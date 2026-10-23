# ResearchRadar — Start All Local Development Services
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "          Starting ResearchRadar Development Stack       " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 1. Start Meilisearch if not running
$meiliRunning = $false
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:7700/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($res.status -eq "available") { $meiliRunning = $true }
} catch {}

if (!$meiliRunning) {
    Write-Host "[1/4] Starting local Meilisearch engine..." -ForegroundColor Yellow
    $startMeili = Join-Path $scriptDir "start-meilisearch.ps1"
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoExit -File `"$startMeili`""
    Start-Sleep -Seconds 3
} else {
    Write-Host "[1/4] Meilisearch is already running on http://127.0.0.1:7700" -ForegroundColor Green
}

# 2. Database Migrations
Write-Host "[2/4] Running database migrations..." -ForegroundColor Yellow
$env:PYTHONPATH = "backend"
& (Join-Path $rootDir "backend\.venv\Scripts\alembic.exe") upgrade head

# 3. Start FastAPI Backend in background job
Write-Host "[3/4] Launching FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoExit -Command `"cd '$rootDir'; `$env:PYTHONPATH='backend'; .\backend\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload`""

# 4. Start Vite Frontend
Write-Host "[4/4] Launching Vite Frontend on http://localhost:5173..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoExit -Command `"cd '$rootDir\frontend'; npm run dev`""

Write-Host "`nAll services launched successfully!" -ForegroundColor Green
Write-Host "• Frontend:   http://localhost:5173" -ForegroundColor White
Write-Host "• API Docs:   http://127.0.0.1:8000/api/docs" -ForegroundColor White
Write-Host "• Search Engine: http://127.0.0.1:7700" -ForegroundColor White
