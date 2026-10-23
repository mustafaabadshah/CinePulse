# Starts local Meilisearch engine with persistent database storage
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

$binPath = Join-Path $rootDir "bin\meilisearch.exe"
$dbPath = Join-Path $rootDir "meili_data"
$httpAddr = "127.0.0.1:7700"
$masterKey = "masterKey_ResearchRadar_Dev_2026_Secure"

if (!(Test-Path $binPath)) {
    Write-Error "Meilisearch binary not found at $binPath"
    exit 1
}

if (!(Test-Path $dbPath)) {
    New-Item -ItemType Directory -Path $dbPath -Force | Out-Null
}

Write-Host "Starting Meilisearch at http://$httpAddr with db at $dbPath ..."
& $binPath --db-path $dbPath --http-addr $httpAddr --master-key $masterKey --env development
