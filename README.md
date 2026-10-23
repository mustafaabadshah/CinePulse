# ResearchRadar 🛰️
> **Production-Grade Academic Research Discovery Platform Powered by Meilisearch**

ResearchRadar is an open-source, full-stack academic discovery platform built to showcase the speed, relevancy, typo tolerance, and faceting capabilities of the **Meilisearch** search engine. It enables researchers, students, and engineers to explore research papers, university professors, research laboratories, and key AI topics (Computer Vision, Machine Learning, Generative AI, NLP, Agentic AI, Medical AI, MLOps, and Trustworthy AI) with sub-50ms query latencies and provenance tracking.

---

## Architecture Overview

```
                                  +---------------------------------------+
                                  |         React 18 + Vite (SPA)         |
                                  |  - Modern Dark Academic Aesthetics    |
                                  |  - Debounced Search-as-you-type       |
                                  |  - Facets, Highlighting & Skeletons   |
                                  +-------------------+-------------------+
                                                      | HTTP / JSON Proxy
                                                      v
                                  +---------------------------------------+
                                  |       FastAPI Backend (Py 3.12)       |
                                  |  - Safe Allowlisted Filter Validation |
                                  |  - Admin API Key Security             |
                                  |  - Search Analytics & Observability   |
                                  |  - Ingestion & Provenance Engine      |
                                  +---------+-------------------+---------+
                                            |                   |
                                            v                   v
            +------------------------------------+  +-------------------------------------+
            |        Relational Storage          |  |         Meilisearch Engine          |
            |  - SQLite (Lightweight Dev Profile)|  |  - 'researchers' Index              |
            |  - PostgreSQL (Docker Prod Profile)|  |  - 'publications' Index             |
            |  - SQLAlchemy 2.0 & Alembic        |  |  - 'institutions' Index             |
            |  - Source Provenance Records       |  |  - Typo Tolerance & Ranking Rules   |
            +------------------------------------+  +-------------------------------------+
```

---

## Technology Stack

- **Search Engine:** Official self-hosted [Meilisearch Community Edition](https://www.meilisearch.com/) (v1.55.0 binary / Docker v1.12) with persistent LMDB storage.
- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic migrations, HTTPX, and Pytest.
- **Frontend:** React 18, TypeScript 5, Vite, Modern CSS Custom Design System (no Tailwind bloat), Lucide Icons, and Vitest with React Testing Library.
- **Relational Databases:** SQLite for lightweight local development (zero RAM overhead); PostgreSQL 16 for Docker Compose multi-service deployment.
- **CI / CD & Tooling:** GitHub Actions workflow, Ruff linter/formatter, and mypy.

---

## Getting Started

### Prerequisites
- Windows 10/11 with PowerShell
- Python 3.12+
- Node.js 20+ and npm 10+
- (Optional for containers) Docker Desktop

### 1. Clone & Configure Environment
```powershell
git clone https://github.com/<your-username>/ResearchRadar.git
cd ResearchRadar
Copy-Item .env.example .env
```

### 2. Quick Local Start (Lightweight Profile — Recommended for 8GB RAM)
Run the automated startup script which starts the Meilisearch engine, applies migrations, launches the FastAPI server, and starts the Vite frontend:
```powershell
.\scripts\start-all.ps1
```

Or run services individually:

**Terminal 1 — Meilisearch Engine:**
```powershell
.\scripts\start-meilisearch.ps1
```

**Terminal 2 — Backend API:**
```powershell
$env:PYTHONPATH="backend"
.\backend\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 3 — Frontend UI:**
```powershell
cd frontend
npm run dev
```

- **Frontend:** [http://localhost:5173](http://localhost:5173)
- **Interactive Swagger API Docs:** [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
- **Meilisearch Engine Health:** [http://127.0.0.1:7700/health](http://127.0.0.1:7700/health)

---

### 3. Docker Compose Full Profile (PostgreSQL + Meilisearch + API + Frontend)
```powershell
docker compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api/health`
- Meilisearch: `http://localhost:7700`

---

## Meilisearch Indexes & Relevancy Rules

Three primary indexes are configured with idempotent initialization and primary keys:

| Index | Primary Key | Searchable Attributes | Filterable Attributes | Sortable Attributes |
|---|---|---|---|---|
| `researchers` | `id` | `full_name`, `research_interests`, `biography`, `institution_name`, `department` | `country`, `institution_name`, `research_interests`, `is_synthetic`, `contact_email_verified` | `full_name`, `country` |
| `publications` | `id` | `title`, `abstract`, `keywords`, `authors`, `venue` | `publication_year`, `venue`, `keywords`, `source_provider`, `is_synthetic`, `primary_institution_id` | `publication_year`, `title` |
| `institutions` | `id` | `name`, `city`, `country` | `country`, `city` | `name`, `country` |

### Ranking Rules Order
All indexes employ Meilisearch's deterministic Bucket Sort algorithm:
1. `words` (matches containing the most query terms)
2. `typo` (matches with fewer typos)
3. `proximity` (matches with search terms closest together)
4. `attribute` (matches in high-priority fields, e.g. `title` before `abstract`)
5. `sort` (matches sorted by custom attributes like `publication_year:desc`)
6. `exactness` (exact matches over prefix matches)

---

## Search Quality & Relevance Evaluation

ResearchRadar includes a reproducible benchmark suite in `scripts/evaluate-search.py` evaluating 13 curated query test cases across exact matches, misspellings, domain topics, and zero-result checks.

To execute the benchmark:
```powershell
$env:PYTHONPATH="backend"
.\backend\.venv\Scripts\python.exe scripts\evaluate-search.py
```

### Measured Benchmark Results
*(Generated from `fixtures/evaluation_report.json`)*

| Metric | Measured Score | Target | Description |
|---|---|---|---|
| **Mean Reciprocal Rank (MRR)** | **0.9231** | > 0.85 | First relevant item returned at rank 1 on almost all queries |
| **Mean Precision@1** | **0.9231** | > 0.85 | Fraction of top retrieved results that are strictly relevant |
| **Mean Precision@3** | **0.8974** | > 0.80 | Precision within top 3 results |
| **Mean Recall@3** | **0.8974** | > 0.80 | Fraction of total known relevant documents captured in top 3 |
| **Mean nDCG@3** | **0.8676** | > 0.80 | Graded relevance ranking quality |
| **Zero-Result Rate** | **7.69%** | < 10% | Zero-results only on deliberate nonsense control strings |
| **Latency p50** | **34.89 ms** | < 100 ms | 50% of search queries resolve in < 35ms |
| **Latency p90** | **109.47 ms** | < 200 ms | 90% of search queries resolve in < 110ms |
| **Latency p99** | **148.68 ms** | < 250 ms | Worst-case latency across complex multi-index union queries |

---

## Automated Testing & Smoke Test

### Run Backend Pytest Suite
```powershell
$env:PYTHONPATH="backend"
.\backend\.venv\Scripts\pytest.exe backend\tests -v
```
*Result: 20 passed in 1.31s (Validation, Normalization, API Endpoints, Auth Security, Importer, and Search).*

### Run Frontend Vitest Suite
```powershell
cd frontend
npm test
```
*Result: 3 test files passed (SearchCard, FilterSidebar, Pagination).*

### Run Automated End-to-End Smoke Test
Verify health, typo tolerance, facets, detail routes, admin security, telemetry, and reindexing:
```powershell
$env:PYTHONPATH="backend"
.\backend\.venv\Scripts\python.exe scripts\smoke-test.py
```
*Result: 7/7 checks PASSED.*

---

## Operational Scripts

- `scripts\start-meilisearch.ps1`: Starts native Meilisearch engine with persistent LMDB data in `meili_data/`.
- `scripts\start-all.ps1`: One-click startup for Meilisearch, database migrations, FastAPI, and Vite.
- `scripts\backup-data.ps1`: Generates timestamped backups of relational data and initiates Meilisearch dumps.
- `scripts\reset-dev-data.ps1`: Clears database, reinitializes Meilisearch indexes, and imports canonical fixture.
- `scripts\openalex_fetch.py`: Optional metadata fetcher querying OpenAlex polite pool for real publications.

---

## Source Code Architectural Study

See [`docs/MEILISEARCH_SOURCE_STUDY.md`](docs/MEILISEARCH_SOURCE_STUDY.md) for a comprehensive study of the upstream Meilisearch engine architecture, including:
1. HTTP API & Actix Web routing (`crates/meilisearch`)
2. Asynchronous Index Scheduler (`crates/index-scheduler`)
3. The `milli` search & indexing engine (`crates/milli`)
4. Multilingual tokenization with `Charabia`
5. Task processing and lifecycle management
6. LMDB zero-copy persistence via `heed`
7. Ranking criteria & Bucket Sort algorithm
8. Upstream contribution guide (forking, building, regression tests, and PR submission).

---

## Implemented vs Planned Features

### ✅ Implemented
- [x] Complete self-hosted Meilisearch engine integration with persistent LMDB storage
- [x] Three synchronized indexes: `researchers`, `publications`, `institutions`
- [x] Idempotent index initialization and settings configuration
- [x] Search-as-you-type with 280ms debouncing, clear query control, and highlighted text matching
- [x] Safe allowlisted filter validation preventing arbitrary query injection
- [x] Multi-index aggregation, facet distribution (Country, Institution, Topics, Years)
- [x] Entity detail pages with verified contact provenance and associated publication links
- [x] Data ingestion pipeline supporting dry-run mode, field normalization, deduplication, and error tracking
- [x] Admin API key authentication and reindexing action with confirmation modal
- [x] Privacy-conscious search analytics telemetry (latencies, top queries, zero-result rates)
- [x] 20 backend unit/integration tests and 4 frontend component tests
- [x] Full Docker Compose setup (Postgres + Meilisearch + FastAPI + Frontend) and lightweight SQLite profile
- [x] Labelled search relevance evaluation suite with MRR, P@k, R@k, nDCG, and measured latencies
- [x] Upstream Meilisearch source study documentation

### 🔮 Planned Optional Enhancements
- [ ] Hybrid semantic search via HuggingFace sentence-transformers embeddings (Meilisearch Vector Search)
- [ ] Export search results to BibTeX format
- [ ] Scheduled daily OpenAlex synchronization cron job
