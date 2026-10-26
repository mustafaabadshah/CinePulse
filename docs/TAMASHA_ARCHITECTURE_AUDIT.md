# Tamasha Catalog Explorer: Architecture Audit & Migration Plan

## Executive Summary
This document outlines the architectural transformation of ResearchRadar from an academic research prototype into **Tamasha Catalog Explorer / Tamasha Discovery** — a dedicated, cinematic, high-performance OTT media discovery platform powered exclusively by the production media catalog (`prod_enrichment.csv` and `episodes_prod.csv`), canonical relational persistence, and Meilisearch.

---

## 1. Existing Architecture Overview

```
                                      ┌─────────────────────────────────────┐
                                      │        React + TypeScript UI        │
                                      │ (Vite, Tailwind-free Vanilla CSS,   │
                                      │   Cinematic Dark OTT Architecture)  │
                                      └──────────────────┬──────────────────┘
                                                         │ HTTP / JSON
                                                         ▼
                                      ┌─────────────────────────────────────┐
                                      │         FastAPI Backend             │
                                      │ (Uvicorn, Port 8000, Python 3.12)   │
                                      └───────┬─────────────────────┬───────┘
                                              │                     │
                     SQLAlchemy ORM           │                     │ Meilisearch Python SDK
                     (Alembic Migrations)     │                     │ (Port 7700)
                                              ▼                     ▼
                                      ┌───────────────┐     ┌───────────────┐
                                      │ SQLite DB     │     │ Meilisearch   │
                                      │ (Canonical)   │     │ (Search Index)│
                                      └───────────────┘     └───────────────┘
```

- **Frontend:** React 18 with TypeScript and Vite. Uses custom Vanilla CSS design tokens (`src/index.css`), Lucide icons, and React Router DOM v6.
- **Backend:** FastAPI with dependency injection, Pydantic v2 schemas, structured JSON logging, and transactional SQLAlchemy sessions.
- **Canonical Storage:** SQLite database at `data/researchradar.db` (11.6 MB).
- **Search Engine:** Meilisearch v1.10+ at `http://127.0.0.1:7700` with native typo tolerance, faceted filtering, and prefix matching.
- **Data Ingestion:** Reusable streaming CSV ingestion pipeline (`app/services/csv_importer.py` & `app/services/data_normalizer.py`) with UTF-8-sig BOM sniffing, dialect detection, dry-run mode, and idempotent upserts.

---

## 2. Current Database Tables & Dependencies

| Table | Status | Row Count | Purpose & Decision |
| :--- | :--- | :--- | :--- |
| `programs` | **Active / Target** | 634 | Shows, Dramas, Series, Movies & Live Channels. **Retain.** |
| `episodes` | **Active / Target** | 6,547 | Individual video broadcast episodes with view counts & durations. **Retain.** |
| `import_jobs` | **Active / Target** | 8 | Persistent audit log of CSV ingestion runs, dry-run reports, and task IDs. **Retain.** |
| `alembic_version`| **System** | 1 | Tracks migration head (`6662fb76ebf3`). **Retain.** |
| `institutions` | **Obsolete / Academic** | 8 | Academic research institutions. **Remove.** |
| `researchers` | **Obsolete / Academic** | 8 | Academic researcher profiles. **Remove.** |
| `publications` | **Obsolete / Academic** | 8 | Academic research papers/proceedings. **Remove.** |
| `source_records` | **Obsolete / Academic** | 24 | Academic provenance records. **Remove.** |
| `search_analytics_events` | **Obsolete / Academic** | 188 | Academic search logging events. **Remove.** |

---

## 3. Existing Meilisearch Indexes & Settings

- `episodes` (**Retain & Optimize**): 6,548 docs. Searchable: `title`, `program_name`, `stars`, `genre`, `description`, `channel_name`, `meta_keywords`. Filterable: `is_free`, `content_tier`, `genre`, `language`, `channel_name`, `region`, `is_vertical`, `program_id`. Sortable: `views`, `duration_seconds`, `title`.
- `programs` (**Retain & Optimize**): 635 docs. Searchable: `name`, `info_staring`, `info_genre`, `channel_name`, `info_meta_keywords`, `info_content_type`. Filterable: `type`, `info_language`, `info_genre`, `info_content_type`, `channel_name`. Sortable: `name`.
- `institutions` (**Obsolete**): 9 docs. **Delete.**
- `researchers` (**Obsolete**): 8 docs. **Delete.**
- `publications` (**Obsolete**): 8 docs. **Delete.**

---

## 4. Academic Features to Remove

1. **Database Schema:** Drop `source_records`, `search_analytics_events`, `researchers`, `publications`, `institutions` tables via Alembic revision.
2. **Backend Models:** Remove `app/models/institution.py`, `app/models/researcher.py`, `app/models/publication.py`, `app/models/source_record.py`, `app/models/analytics.py`.
3. **Backend API Routes:** Remove `app/api/routes_researchers.py`, `app/api/routes_publications.py`, `app/api/routes_institutions.py`, `app/api/routes_analytics.py`.
4. **Backend Ingestion & Validation:** Remove `app/ingestion/` academic synthetic generators (`academic_importer.py`, `schema_validator.py`).
5. **Frontend Pages & Components:**
   - Remove `ResearcherDetailPage.tsx`, `PublicationDetailPage.tsx`, `InstitutionDetailPage.tsx`.
   - Remove academic navigation links from `Navbar.tsx`.
   - Remove academic filter facets and tabs from `SearchResultsPage.tsx` and `FilterSidebar.tsx`.
6. **Frontend API & Types:** Remove academic types (`Researcher`, `Publication`, `Institution`) from `types/index.ts` and client methods from `api/client.ts`.
7. **Test Suites:** Update tests to assert 100% media-domain behavior, removing academic assertions from `test_api.py`, `test_search.py`, `test_auth.py`, `test_validation.py`.

---

## 5. Media Features to Retain & Improve

1. **Canonical Schema:**
   - `Program`: `id`, `type`, `name`, `slug`, `channel_name`, `info_language`, `info_genre`, `info_meta_keywords`, `info_content_type`, `info_staring`, `source_file`, `imported_at`.
   - `Episode`: `id`, `program_id` (nullable FK), `raw_program_id`, `title`, `slug`, `description`, `duration`, `duration_seconds`, `views`, `is_free`, `is_enable`, `content_tier`, `genre`, `thumbnail`, `region`, `is_vertical`.
2. **Robust Duration & Type Normalizer:** Handles `HH:MM:SS`, `MM:SS`, numeric seconds, and textual formats (`1h 30m`, `45 mins`) safely.
3. **Orphan Episode Policy:** Preserves 247 orphan episodes with `raw_program_id` auditability without breaking referential integrity.
4. **Unified Media Search API (`GET /api/search`):** Supports `type=all`, `programs`, `channels`, `episodes` with highlighting, facets, and pagination.
5. **Cinematic Dark UI Experience:**
   - Top navigation: "Tamasha Catalog Explorer" with Live Shows, Channels, Episodes, Genres, and Admin.
   - Home / Discovery Page: Spotlight featured hero, "Popular by Views" carousel, "Shows & Dramas", "Channels", "Free to Watch".
   - Search Page: Debounced search-as-you-type, media facets, active chips, responsive cards with thumbnails, view counters, duration badges, and direct detail links.
   - Detail Pages: Full media detail with parent show connection and sibling episode carousels.

---

## 6. Migration & Rollback Plan

### Backup Verification:
- **Pre-Clean Backup Created:** `backups/20261026_094627/researchradar_pre_academic_cleanup.db` (11,599,872 bytes).
- **Integrity Check:** Verified `PRAGMA integrity_check` returned `ok`.
- **SHA-256:** `8e6fff44e60548630659d12cd775f93c0899d37e33b6d8fadff1a993b304add4`.

### Reversible Migration Strategy:
1. Create Alembic migration `drop_academic_tables_and_finalize_media_schema.py`.
2. Downgrade method will recreate the academic tables if rollback is ever necessary.
3. Test migration on a copy of the database before applying to live canonical database.
4. Verify table list, row counts of `programs` (634), `episodes` (6,547), and `import_jobs` (8).
5. Delete academic Meilisearch indexes (`institutions`, `researchers`, `publications`).

---

## 7. Risks & Mitigation

| Risk | Mitigation Strategy |
| :--- | :--- |
| Accidental deletion of media records | Verified SQLite backup created and checksummed. Migration explicitly drops ONLY academic tables. |
| Broken frontend imports from academic code | Reference audit across frontend codebase before removing files; verify with `npm run build`. |
| Broken backend tests | Rewrite test suite to be 100% media-focused, testing CSV importer, normalization, Meilisearch indexer, and search API. |
| Inconsistent Meilisearch state | Post-migration `/api/admin/index-status` check verifies 100% count consistency between SQLite and Meilisearch. |

---

## 8. Exact Implementation Sequence

1. **Audit & Backup:** Complete architecture audit and verify pre-migration backup.
2. **Schema Migration:** Apply Alembic migration to drop academic tables; verify `programs` and `episodes` row counts.
3. **Backend Refactor:** Remove obsolete academic models, routes, schemas, and services; update `main.py` and `models/__init__.py`.
4. **Meilisearch Cleanup:** Remove academic indexes from Meilisearch engine; retain `programs` and `episodes`.
5. **Frontend Transformation:**
   - Rebrand application to **Tamasha Catalog Explorer**.
   - Implement Cinematic OTT Home/Discovery page with featured hero, trending carousel, genres, and channels.
   - Refactor Search Results page, Navbar, FilterSidebar, SearchCard, EpisodeDetailPage, ProgramDetailPage, AdminPage.
   - Remove obsolete academic pages, components, hooks, and types.
6. **Automated Testing:** Run backend pytest suite and frontend `npm run build`.
7. **Relevance Benchmark:** Run evaluation suite with media test queries.
8. **Browser Verification:** Verify live end-to-end user workflows in browser.
9. **Documentation & Reporting:** Deliver comprehensive setup and migration runbooks.
