# ResearchRadar: Windows PowerShell CSV Import & Search Operations Manual

This runbook provides complete, tested PowerShell instructions for ingesting, synchronizing, managing, and searching the ResearchRadar media catalog (`prod_enrichment.csv` and `episodes_prod.csv`) using the canonical SQLite database and Meilisearch engine.

---

## 1. Prerequisites & Assumptions

- **Operating System:** Windows 10/11 with PowerShell 5.1+ or PowerShell Core 7+.
- **Repository Directory:** `E:\MM Office\ResearchRadar`
- **Python Environment:** Python 3.12+ located in `backend\.venv`
- **Node.js Environment:** Node 18+ and npm installed
- **Meilisearch Binary:** Standalone binary at `bin\meilisearch.exe` (or Docker running `docker-compose.yml`)
- **Default Service Ports:**
  - FastAPI Backend: `http://127.0.0.1:8000`
  - React (Vite) Frontend: `http://127.0.0.1:5173`
  - Meilisearch Engine: `http://127.0.0.1:7700`
- **Admin API Key:** Default development key is `rr_admin_secret_dev_key_change_me` (set in `.env` / headers as `X-Admin-API-Key`).

---

## 2. Checking Service Health

### Check Meilisearch Health
```powershell
# Query Meilisearch HTTP health endpoint
Invoke-RestMethod -Uri "http://127.0.0.1:7700/health"
# Output should return: @{status=available}
```

### Check Backend Health
```powershell
# Query FastAPI backend composite health endpoint
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health"
# Output returns status of database, meilisearch, and overall system health
```

---

## 3. Environment Configuration

Copy `.env.example` to `.env` if not already present:
```powershell
Copy-Item .env.example .env
```

Key configuration variables in `.env`:
```ini
DATABASE_URL=sqlite:///./data/researchradar.db
MEILI_HTTP_ADDR=http://127.0.0.1:7700
MEILI_MASTER_KEY=masterKey_ResearchRadar_Dev_2026_Secure
ADMIN_API_KEY=rr_admin_secret_dev_key_change_me
CSV_DATA_DIR=data
CSV_ENRICHMENT_FILE=prod_enrichment.csv
CSV_EPISODES_FILE=episodes_prod.csv
```

---

## 4. Source File Validation (No DB Mutation)

Inspect both production CSV files without modifying any data:
```powershell
$headers = @{ "X-Admin-API-Key" = "rr_admin_secret_dev_key_change_me" }
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/admin/source-files" -Headers $headers
$response | ConvertTo-Json -Depth 4
```

Expected output:
- `prod_enrichment.csv`: `exists = true`, `row_count = 634`, encoding detected as `utf-8-sig`.
- `episodes_prod.csv`: `exists = true`, `row_count = 6547`, encoding detected as `utf-8-sig`.

---

## 5. Dry-Run Import Execution

Simulate ingestion against the real CSV files without making any changes to the database or Meilisearch:
```powershell
$headers = @{ "X-Admin-API-Key" = "rr_admin_secret_dev_key_change_me" }
$dryRun = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/admin/import?dry_run=true" -Headers $headers
$dryRun | ConvertTo-Json -Depth 4
```

Verify in response:
- `dry_run: true`
- `status: "dry_run_completed"`
- `records_processed: 7181`
- `records_created: 7181` (projected)

---

## 6. Backing Up the Canonical Database

Always create a verified backup before running real production migrations or imports:
```powershell
# Run the built-in backup script
powershell.exe -ExecutionPolicy Bypass -File .\scripts\backup-data.ps1
```
Backups are saved to `backups\YYYYMMDD_HHMMSS\` with sha256 checksums.

To manually copy SQLite database:
```powershell
Copy-Item "data\researchradar.db" "data\researchradar_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
```

---

## 7. First Production Database Import & Synchronization

Run the transactional import into the canonical database and index into Meilisearch:
```powershell
$headers = @{ "X-Admin-API-Key" = "rr_admin_secret_dev_key_change_me" }
$importResult = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/admin/import?dry_run=false" -Headers $headers
$importResult | ConvertTo-Json -Depth 4
```

### Idempotency Check
Run the exact same command a second time:
```powershell
$repeat = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/admin/import?dry_run=false" -Headers $headers
$repeat | ConvertTo-Json -Depth 4
```
Expected: `records_created: 0`, `records_updated: 0`, all records marked `unchanged`.

---

## 8. Monitoring Meilisearch Tasks & Status

### Check Index Status & Consistency
```powershell
$headers = @{ "X-Admin-API-Key" = "rr_admin_secret_dev_key_change_me" }
$status = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/admin/index-status" -Headers $headers
$status.indexes | ConvertTo-Json -Depth 3
```
Expected:
- `episodes.database_count == 6547` and `episodes.indexed_count == 6547` (`is_consistent: true`)
- `programs.database_count == 634` and `programs.indexed_count == 634` (`is_consistent: true`)

### Query Meilisearch Task Queue Directly
```powershell
$meiliHeaders = @{ "Authorization" = "Bearer masterKey_ResearchRadar_Dev_2026_Secure" }
$tasks = Invoke-RestMethod -Uri "http://127.0.0.1:7700/tasks?limit=5" -Headers $meiliHeaders
$tasks.results | Select-Object uid, indexUid, status, type, duration
```

---

## 9. Starting Frontend and Backend Services

### Option A: Run Services Manually in Separate PowerShell Terminals

**Terminal 1 — Meilisearch Engine:**
```powershell
cd "E:\MM Office\ResearchRadar"
.\bin\meilisearch.exe --db-path data\meili_data --master-key masterKey_ResearchRadar_Dev_2026_Secure --http-addr 127.0.0.1:7700
```

**Terminal 2 — FastAPI Backend:**
```powershell
cd "E:\MM Office\ResearchRadar\backend"
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 3 — React Frontend:**
```powershell
cd "E:\MM Office\ResearchRadar\frontend"
npm run dev
```

### Option B: Start Services via Background Helper Scripts
```powershell
cd "E:\MM Office\ResearchRadar"
.\scripts\start-meilisearch.ps1
.\scripts\start-backend.ps1
.\scripts\start-frontend.ps1
```

---

## 10. Testing Search with Actual Data

### Search API Examples via PowerShell
```powershell
# 1. Search for drama serials across all indexes
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/search?q=tamasha&type=all" | Select-Object total_hits, processing_time_ms

# 2. Search episodes filtered by free content
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/search?q=honda&type=episodes&filter=is_free=true"

# 3. Typo tolerance search ("tamsha" -> matches "Tamasha")
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/search?q=tamsha&type=programs"

# 4. Fetch specific episode detail with program relation
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/episodes/102537"

# 5. Fetch specific program detail with child episodes
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/programs/100075"
```

---

## 11. Rebuilding Indexes from Database

If Meilisearch data is ever cleared or recreated, rebuild directly from SQLite without touching CSV files:
```powershell
$headers = @{ "X-Admin-API-Key" = "rr_admin_secret_dev_key_change_me" }
$rebuild = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/admin/reindex" -Headers $headers
$rebuild | ConvertTo-Json -Depth 3
```

---

## 12. Running Tests & Linters

### Run Backend Pytest Suite
```powershell
cd "E:\MM Office\ResearchRadar\backend"
.\.venv\Scripts\pytest.exe -v
```

### Run Frontend Typecheck & Production Build
```powershell
cd "E:\MM Office\ResearchRadar\frontend"
npm run build
```

### Run Search Relevance Benchmark Suite
```powershell
cd "E:\MM Office\ResearchRadar\backend"
.\.venv\Scripts\python.exe ..\scripts\evaluate-search.py
```

---

## 13. Stopping and Restarting Services

To find and terminate running background services:
```powershell
# Find process IDs listening on ports 7700, 8000, 5173
Get-NetTCPConnection -LocalPort 7700, 8000, 5173 -ErrorAction SilentlyContinue | Select-Object LocalPort, OwningProcess -Unique

# Terminate process by PID (e.g., 1234)
Stop-Process -Id <PID> -Force
```

To stop all Meilisearch and Python processes safely:
```powershell
Get-Process meilisearch -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## 14. Common Errors and Troubleshooting

| Symptom | Root Cause | Solution |
| :--- | :--- | :--- |
| `Cannot connect to Meilisearch at 127.0.0.1:7700` | Process not running or wrong port | Verify `bin\meilisearch.exe` is started with `--http-addr 127.0.0.1:7700`. |
| `Invalid API Key (401 / 403)` | Master key mismatch | Verify `MEILI_MASTER_KEY` matches between `.env` and Meilisearch command arguments. |
| `Missing required field (id, name, or slug)` | CSV row has empty mandatory identifier | Normal behavior. Malformed rows are safely rejected and logged in `invalid_samples`. |
| `Orphan episode warning in import report` | Episode references `program_id` not in enrichment CSV | The system safely saves the episode, preserves `raw_program_id`, and sets `program_id` to NULL. |
| `Unused import error TS6133 during npm build` | Stale or unused icon import in React | Remove unused imports from component and rerun `npm run build`. |
| `database locked error` | Concurrent writes in SQLite during rapid batch test | Transactions use retry backoff; avoid running simultaneous destructive re-imports in parallel. |
