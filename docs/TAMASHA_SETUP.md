# Tamasha Catalog Explorer — Setup & Operations Guide (Windows PowerShell)

## 1. System Requirements

Designed and optimized for Windows 10/11 environments with lightweight resource constraints (tested on Intel Core i5/i7, 8 GB RAM, integrated graphics):
- **Python**: 3.11 or 3.12 64-bit
- **Node.js**: v18+ or v20+ with npm
- **Meilisearch**: v1.12.0 standalone Windows executable (`bin/meilisearch.exe`)
- **Shell**: Windows PowerShell 5.1 or PowerShell Core 7+

---

## 2. Directory Structure

```text
E:\MM Office\ResearchRadar\
├── backend\                 # FastAPI backend application
│   ├── app\                 # Models, routes, search, normalization
│   └── tests\               # Pytest suite
├── frontend\                # React 18 + Vite + TypeScript application
│   ├── src\                 # Components, pages, design system
│   └── dist\                # Compiled production bundle
├── data\                    # Canonical storage
│   ├── prod_enrichment.csv  # 634 programs/channels
│   ├── episodes_prod.csv    # 6,547 video episodes
│   └── researchradar.db     # SQLite canonical application database
├── bin\                     # Local binaries (meilisearch.exe)
├── backups\                 # Verified disaster recovery backups
├── migrations\              # Alembic schema migration chain
└── scripts\                 # Operational automation scripts
```

---

## 3. Environment Configuration

Copy `.env.example` to `.env` in the project root:
```powershell
Copy-Item ".env.example" ".env"
```

Default local development values:
```ini
ENVIRONMENT=development
DATABASE_URL=sqlite:///./data/researchradar.db
MEILI_HTTP_ADDR=http://127.0.0.1:7700
MEILI_MASTER_KEY=rr_master_secret_dev_key_change_me
ADMIN_API_KEY=rr_admin_secret_dev_key_change_me
LOG_LEVEL=INFO
```

---

## 4. Starting Application Services

Open three separate Windows PowerShell terminal tabs:

### Terminal 1: Start Meilisearch
```powershell
cd "E:\MM Office\ResearchRadar"
powershell -ExecutionPolicy Bypass -File .\scripts\start-meilisearch.ps1
```
*Verification:* Navigate to `http://127.0.0.1:7700/health`. Should return `{"status":"available"}`.

### Terminal 2: Start FastAPI Backend
```powershell
cd "E:\MM Office\ResearchRadar"
.\backend\.venv\Scripts\Activate.ps1
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
*Verification:* Navigate to `http://127.0.0.1:8000/api/health`.

### Terminal 3: Start React Frontend
```powershell
cd "E:\MM Office\ResearchRadar\frontend"
npm run dev
```
*Verification:* Open `http://127.0.0.1:5173/` in your browser.

---

## 5. Data Pipeline & Ingestion Commands

### 5.1 Dry Run Import (Safe Validation, Zero Writes)
Validates headers, UTF-8 BOM, formats, and parent resolution without modifying database or search index:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/admin/import?dry_run=true&source_type=csv" `
  -Method Post `
  -Headers @{ "X-Admin-API-Key" = "rr_admin_secret_dev_key_change_me" }
```

### 5.2 Production Ingestion & Search Synchronization
Performs idempotent upserts into SQLite and updates Meilisearch:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/admin/import?dry_run=false&source_type=csv" `
  -Method Post `
  -Headers @{ "X-Admin-API-Key" = "rr_admin_secret_dev_key_change_me" }
```

### 5.3 Rebuild Search Indexes from Canonical Database
Purges and re-indexes all programs and episodes directly from SQLite:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/admin/reindex" `
  -Method Post `
  -Headers @{ "X-Admin-API-Key" = "rr_admin_secret_dev_key_change_me" }
```

### 5.4 Check Index Consistency
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/admin/index-status" `
  -Method Get `
  -Headers @{ "X-Admin-API-Key" = "rr_admin_secret_dev_key_change_me" }
```

---

## 6. Running Tests & Evaluations

### Backend Test Suite
```powershell
cd "E:\MM Office\ResearchRadar"
.\backend\.venv\Scripts\pytest.exe -v
```

### Frontend Tests & Production Build
```powershell
cd "E:\MM Office\ResearchRadar\frontend"
npm test -- --run
npm run build
```

### Search Relevance Evaluation
```powershell
cd "E:\MM Office\ResearchRadar"
.\backend\.venv\Scripts\python.exe scripts\evaluate-search.py
```
Outputs MRR, Precision@1, Precision@3, Recall@3, nDCG@3, and latency percentiles.
