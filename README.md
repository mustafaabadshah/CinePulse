# CinePulse 🎬
> **Production-Grade OTT Media Discovery & Search Engine**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Meilisearch](https://img.shields.io/badge/Meilisearch-v1.12.0-FF5C5C.svg?logo=meilisearch&logoColor=white)](https://www.meilisearch.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![Tests](https://img.shields.io/badge/Tests-55%20Passed%20(100%25)-success.svg)](#testing--verification)

**CinePulse** is a production-grade OTT video streaming catalog explorer and sub-50ms media discovery platform. Built to showcase modern search relevance engineering, automated catalog normalization, and cinematic dark-mode streaming UI, CinePulse indexes real-world television dramas, news bulletins, comedy series, and live broadcast channels.

---

## 🏛️ System Architecture

```text
                                  +---------------------------------------+
                                  |         React 18 + Vite (SPA)         |
                                  |  - Cinematic Charcoal & Red Theme     |
                                  |  - Debounced Search-as-you-type (280ms|
                                  |  - S3 WebP Thumbnail CDN Resolver     |
                                  |  - Chronological Sequence Badges      |
                                  +-------------------+-------------------+
                                                      | HTTP / JSON Proxy (:5173 -> :8000)
                                                      v
                                  +---------------------------------------+
                                  |       FastAPI Backend (Py 3.12)       |
                                  |  - Safe Allowlisted Query Extraction  |
                                  |  - Chronological Sequence Sorter      |
                                  |  - Data Normalization Engine          |
                                  |  - Administrative Artwork Curator     |
                                  +---------+-------------------+---------+
                                            |                   |
                                            v                   v
            +------------------------------------+  +-------------------------------------+
            |        Relational Storage          |  |         Meilisearch Engine          |
            |  - SQLite Canonical Store          |  |  - 'programs' Index (634 docs)      |
            |  - SQLAlchemy 2.0 & Alembic        |  |  - 'episodes' Index (6,547 docs)    |
            |  - Dual Duration Storage (sec+str) |  |  - Sortable: episode_number, views  |
            |  - `media_artwork` Audit Registry  |  |  - Facets: genre, channel, is_free  |
            +------------------------------------+  +-------------------------------------+
```

---

## ✨ Key Technical Highlights

### 1. Instant Faceted Search & Ranking (Meilisearch v1.12)
- **Sub-50ms Latency**: Real-time search-as-you-type querying across 634 shows and 6,547 video episodes.
- **Faceted Filtration**: Filter concurrently by **Category / Type** (Shows, Channels, Episodes), **Genre**, **Broadcaster Network**, and **Content Tier** (Free AVOD vs. Pro Subscription).
- **Typo Tolerance & Highlights**: Matching query substrings are extracted with formatted highlight snippets.

### 2. Chronological Episode Sequencing & Binge Recommendation
- **Canonical `episode_number` Extraction**: Employs an extraction engine parsing multi-format title patterns (`Episode 25`, `Ep 03`, `S01E02`, `Part 1`).
- **Sequential Program Exploration**: TV shows default to narrative order (`EP 1`, `EP 2`, `EP 3`), with an instant toggle for "Most Viewed".
- **Intelligent Sibling Recommendations**: When watching Episode 5, next recommendations automatically queue Episodes 6, 7, and 8.

### 3. Media Data Quality & Duration Normalization
- **Dual Runtime Architecture**: Stores mathematical `duration_seconds` for sorting alongside standardized clock representations (`MM:SS` or `HH:MM:SS`).
- **Short Clip Clarification**: Identifies genuine 30-second promotional trailers and recitations, rendering visual `Short Clip` badges to eliminate viewer confusion.
- **Source Immutability**: All repairs occur safely within the canonical database and search index while preserving source CSV datasets unmodified.

### 4. Amazon S3 CDN Resolution & Resilient Fallbacks
- **Relative Path Translation**: Resolves 6,292 relative image paths to active Amazon S3 WebP endpoints (`https://tamasha-app-images.s3.amazonaws.com/jazzlive/uploads/episodes/...`).
- **Program Artwork Inheritance**: Shows without standalone posters dynamically inherit primary child episode imagery (providing 79.2% instant coverage).
- **Zero Layout Shift (CLS)**: Strictly reserves 16:9 (episodes) and 3:4 (posters) aspect ratios with loading skeleton shimmers and designed SVG fallback cards.

---

## 📊 Catalog Metrics

| Dimension | Count / Metric | Description |
|---|---|---|
| **Programs & Channels** | `634` | Full-length television drama series, morning talk shows, and live TV channels |
| **Video Episodes** | `6,547` | Serialized television episodes, news bulletins, and short clips |
| **S3 WebP Thumbnails** | `6,292` (96.1%) | Hosted on Amazon S3 CDN |
| **Sequenced Episodes** | `2,343` | Extracted and populated with numerical sequence numbers |
| **Live Broadcast Networks** | `50+` | Channels including Hum News, 24 News HD, City 42, and TV One |

---

## 🚀 Quickstart Guide

### Prerequisites
- **Windows 10/11**, **macOS**, or **Linux**
- **Python 3.12+**
- **Node.js 20+** and **npm 10+**
- PowerShell (on Windows) or Bash

---

### Step 1: Clone Repository & Setup
```bash
git clone https://github.com/mustafaabadshah/CinePulse.git
cd CinePulse
```

### Step 2: Start Meilisearch
Download or run the local Meilisearch binary:
```powershell
# Windows PowerShell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\start-meilisearch.ps1

# Linux / macOS
./bin/meilisearch --master-key "masterKey123" --http-addr "127.0.0.1:7700"
```

### Step 3: Start the FastAPI Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 4: Start the React Frontend
```bash
cd frontend
npm install
npm run dev
```

Visit **`http://127.0.0.1:5173/`** in your browser.

---

## 🧪 Testing & Verification

The project includes unit and integration test coverage across the entire stack:

```bash
# Run Backend Pytest Suite (29 tests)
cd backend
pytest -v

# Run Frontend Vitest Suite (26 tests)
cd frontend
npm test -- --run

# Run Production Frontend Typecheck & Build
npm run build
```

**Results:**
- **Pytest**: `29 passed in 8.07s` (100%)
- **Vitest**: `26 passed in 3.67s` (100%)
- **TypeScript**: `0 errors, Vite bundle built cleanly`

---

## 📂 Repository Structure

```text
CinePulse/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI routers (search, programs, episodes, admin)
│   │   ├── core/                # Database engine, config, and security
│   │   ├── models/              # SQLAlchemy models (Program, Episode, MediaArtwork, ImportJob)
│   │   ├── search/              # Meilisearch client, indexes, and search service
│   │   └── services/            # Normalizer, CSV importer, and indexing pipeline
│   └── tests/                   # Pytest test suite (29 tests)
├── frontend/
│   ├── src/
│   │   ├── components/          # MediaImage, SearchCard, FilterSidebar, Pagination
│   │   ├── pages/               # HomePage, SearchResultsPage, ProgramDetailPage, EpisodeDetailPage
│   │   ├── utils/               # formatDuration, duration parsers
│   │   └── test/                # Vitest unit test suites (26 tests)
├── data/
│   ├── prod_enrichment.csv      # Source metadata for 634 shows & channels
│   ├── episodes_prod.csv        # Source metadata for 6,547 video episodes
│   └── researchradar.db         # Canonical SQLite database
├── docs/                        # Complete technical specifications & data audits
└── scripts/                     # Auditing, duration repair, and sequence extraction CLI scripts
```

---

## 📜 Documentation

- [`docs/TAMASHA_DURATION_NORMALIZATION.md`](docs/TAMASHA_DURATION_NORMALIZATION.md): Duration root cause analysis, conversion tables, and audit logs.
- [`docs/TAMASHA_ARTWORK_STRATEGY.md`](docs/TAMASHA_ARTWORK_STRATEGY.md): S3 CDN discovery, program inheritance, and fallback designs.
- [`docs/TAMASHA_MEDIA_DATA_QUALITY_AUDIT.md`](docs/TAMASHA_MEDIA_DATA_QUALITY_AUDIT.md): End-to-end data quality audit and sequence repair metrics.
- [`docs/CSV_DATA_DICTIONARY.md`](docs/CSV_DATA_DICTIONARY.md): Column-by-column schema specifications for all production datasets.

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
