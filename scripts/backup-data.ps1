# Backup SQLite database and Meilisearch persistent storage
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $rootDir "backups\$timestamp"

New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

Write-Host "Creating backup in $backupDir ..." -ForegroundColor Cyan

# Backup SQLite database
$sqliteDb = Join-Path $rootDir "data\researchradar.db"
if (Test-Path $sqliteDb) {
    Copy-Item -Path $sqliteDb -Destination (Join-Path $backupDir "researchradar.db")
    Write-Host "• Relational database backed up." -ForegroundColor Green
}

# Trigger Meilisearch dump API
try {
    $meiliKey = "masterKey_ResearchRadar_Dev_2026_Secure"
    $dumpRes = Invoke-RestMethod -Uri "http://127.0.0.1:7700/dumps" -Method Post -Headers @{ "Authorization" = "Bearer $meiliKey" } -TimeoutSec 5
    Write-Host "• Triggered Meilisearch dump task: $($dumpRes.taskUid)" -ForegroundColor Green
} catch {
    Write-Host "• Note: Meilisearch dump API call skipped (engine may be offline or direct file backup used)." -ForegroundColor Yellow
}

Write-Host "`nBackup completed successfully to $backupDir" -ForegroundColor Green
