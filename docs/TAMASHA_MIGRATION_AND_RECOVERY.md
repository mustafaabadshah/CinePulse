# Tamasha OTT Platform — Database Migration & Disaster Recovery Manual

## 1. Executive Summary

As part of the Tamasha OTT Discovery Platform transition, the obsolete academic research schema was safely replaced with a dedicated, high-performance media catalog schema.

A verified pre-migration backup was created and validated prior to executing any destructive DDL. The schema migration was managed via Alembic (`c8e19f3b7d12`), dropping five academic tables and preserving all 634 programs and 6,547 video episodes.

---

## 2. Pre-Migration Verified Backup

The canonical backup was created using SQLite's online backup API to ensure write-consistency:

- **Backup File Path**: `backups/20261026_094627/researchradar_pre_academic_cleanup.db`
- **File Size**: `11,599,872 bytes` (11.06 MB)
- **Timestamp**: `2026-10-26T09:46:27 UTC`
- **SHA-256 Checksum**: `8e6fff44e60548630659d12cd775f93c0899d37e33b6d8fadff1a993b304add4`
- **SQLite Integrity Status**: `PRAGMA integrity_check -> ok`
- **Pre-Clean Table Counts**:
  - `programs`: 634
  - `episodes`: 6,547
  - `import_jobs`: 8
  - `institutions`: 12
  - `researchers`: 42
  - `publications`: 85
  - `source_records`: 139
  - `search_analytics_events`: 27

---

## 3. Migration Execution (`c8e19f3b7d12`)

### Migration Identification
- **Revision ID**: `c8e19f3b7d12`
- **Revises**: `b7f03d9e4a11` (add media tables)
- **File**: `migrations/versions/c8e19f3b7d12_drop_academic_tables_finalize_media_schema.py`

### Safety Measures Executed
1. **Disposable Database Dry Run**: Applied first to `data/test_disposable_migration.db`.
2. **Dependency-Safe Drop Order**:
   - `search_analytics_events` (foreign keys to search records)
   - `source_records` (provenance records)
   - `publications` (linked to researchers and institutions)
   - `researchers` (linked to institutions)
   - `institutions` (top-level academic root)
3. **Foreign Key Protection**: SQLite `PRAGMA foreign_keys = OFF` during table dropping to avoid lock escalations, followed by `PRAGMA foreign_keys = ON` and `PRAGMA foreign_key_check`.

---

## 4. Post-Migration Verification

After running `alembic upgrade head` on the canonical database `data/researchradar.db`:

```sql
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
```
**Active Tables (Strictly 4):**
1. `alembic_version` (revision: `c8e19f3b7d12`)
2. `episodes` (6,547 rows)
3. `import_jobs` (8 rows)
4. `programs` (634 rows)

**Integrity Check:**
```sql
PRAGMA integrity_check;
-- Output: ok

PRAGMA foreign_key_check;
-- Output: 0 violations
```

---

## 5. Step-by-Step Restoration Procedure

In the event of database corruption or an operational emergency, follow this exact procedure:

### Step 5.1: Stop Running Application Services
Terminate the FastAPI backend and any background workers:
```powershell
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*ResearchRadar*" } | Stop-Process -Force
```

### Step 5.2: Verify Backup Integrity
Verify the SHA-256 hash before restoring:
```powershell
$ExpectedHash = "8e6fff44e60548630659d12cd775f93c0899d37e33b6d8fadff1a993b304add4"
$ActualHash = (Get-FileHash "backups\20261026_094627\researchradar_pre_academic_cleanup.db" -Algorithm SHA256).Hash.ToLower()
if ($ActualHash -ne $ExpectedHash) {
    Write-Error "Backup hash mismatch! Expected: $ExpectedHash, Got: $ActualHash"
} else {
    Write-Host "Backup verified. SHA-256 match!"
}
```

### Step 5.3: Restore the Database File
```powershell
# Copy the verified backup to active database location
Copy-Item "backups\20261026_094627\researchradar_pre_academic_cleanup.db" "data\researchradar.db" -Force
```

### Step 5.4: Apply the Alembic Migration
```powershell
.\backend\.venv\Scripts\alembic.exe upgrade head
```

### Step 5.5: Re-Synchronize Meilisearch
Trigger a fresh index rebuild via the admin API:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/admin/reindex" -Method Post -Headers @{ "X-Admin-API-Key" = "rr_admin_secret_dev_key_change_me" }
```
Verify that `episodes` has 6,547 documents and `programs` has 634 documents.
