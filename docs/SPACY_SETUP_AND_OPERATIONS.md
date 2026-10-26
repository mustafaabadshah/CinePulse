# CinePulse — spaCy NLP Setup & Operations Guide

## 1. Prerequisites & Installation

The CinePulse NLP layer runs within the backend Python virtual environment (`Python 3.12+`).

### 1.1. Install spaCy & Small English Model
From the `backend` directory:
```powershell
.\.venv\Scripts\Activate.ps1
pip install spacy==3.8.16
python -m spacy download en_core_web_sm
```

Verify installation:
```powershell
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('spaCy ready:', nlp.meta['name'], nlp.meta['version'])"
```

---

## 2. Configuration Settings

The NLP subsystem is configured via environment variables in `backend/.env` or system environment:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `CINEPULSE_NLP_ENABLED` | `True` | Master kill-switch to enable/disable NLP processing |
| `CINEPULSE_SPACY_MODEL` | `en_core_web_sm` | Model package to load |
| `CINEPULSE_NLP_MAX_QUERY_LEN` | `200` | Max character length allowed for NLP parsing |
| `CINEPULSE_NLP_CONFIDENCE_THRESHOLD` | `0.75` | Minimum confidence score to apply inferred entity filters |

---

## 3. Telemetry & Inspection Endpoints

### 3.1. Readiness & Pattern Status
```http
GET /api/nlp/status
```
Example Response:
```json
{
  "is_available": true,
  "model_name": "en_core_web_sm",
  "spacy_version": "3.8.16",
  "patterns_loaded": 1320,
  "pipeline_components": [
    "tok2vec",
    "tagger",
    "parser",
    "attribute_ruler",
    "entity_ruler",
    "ner"
  ],
  "last_initialized_at": "2026-10-26T13:18:02.364403+00:00",
  "device": "cpu"
}
```

### 3.2. Query Parsing Debug Sandbox
```http
POST /api/nlp/parse
Content-Type: application/json

{
  "q": "i want to watch funny movie"
}
```
Example Response:
```json
{
  "original_query": "i want to watch funny movie",
  "normalized_query": "i want to watch funny movie",
  "recognized_entities": [
    {
      "text": "funny",
      "label": "GENRE",
      "start_char": 16,
      "end_char": 21,
      "confidence": 1.0,
      "source": "spacy_catalog",
      "canonical_name": "Comedy"
    },
    {
      "text": "movie",
      "label": "CONTENT_TYPE",
      "start_char": 22,
      "end_char": 27,
      "confidence": 1.0,
      "source": "spacy_catalog",
      "canonical_name": "movie"
    }
  ],
  "matched_genre": "Comedy",
  "matched_content_type": "movie",
  "remaining_query": "",
  "inferred_filters": {
    "genre_list": "comedy",
    "content_type": "movie"
  },
  "is_nlp_assisted": true
}
```

---

## 4. Verification & Testing

### 4.1. Run NLP Pytest Suite
```powershell
.\.venv\Scripts\pytest.exe tests/test_nlp_normalization.py tests/test_nlp_query_parser.py tests/test_nlp_service.py -v
```

### 4.2. Run Evaluation Benchmark Suite
```powershell
python ..\scripts\evaluate-nlp-search.py
```

---

## 5. Troubleshooting & Operational Recovery

### Issue: spaCy model fails to download or load
- **Behavior**: System logs warning `Could not load spaCy model 'en_core_web_sm'. Falling back to spacy.blank('en').`
- **Mitigation**: The system transparently falls back to `spacy.blank('en')` with the catalog `EntityRuler`. Catalog exact matching and episode regex continue to operate normally with zero downtime.

### Issue: Assisted query produces zero hits
- **Behavior**: System automatically invokes `_execute_search_passes` with unassisted baseline query.
- **Log message**: `Assisted search produced 0 hits for '<query>'. Falling back to baseline search.`
- **Result**: No content is lost.
