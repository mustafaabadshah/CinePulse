# Tamasha OTT Platform — Search Architecture & Index Design

## 1. Overview & Search Philosophy

Tamasha Catalog Explorer uses **Meilisearch v1.12.0** as a dedicated, low-latency, typo-tolerant derived search index. The canonical source-of-truth remains the relational SQLite database (`data/researchradar.db`), enabling complete index rebuilds at any time without needing to reread raw CSV files.

The architecture decouples the media catalog into two primary indexes:
1. `programs`: Show and broadcast channel catalog entities.
2. `episodes`: Video episode items with parent show and cast denormalization.

A unified backend gateway (`GET /api/search`) mediates all client search interactions, ensuring security, filter validation via server-side allowlists, and transparent cross-index result composition.

---

## 2. Meilisearch Index Specifications

### 2.1 Index: `programs`
- **Primary Key**: `id`
- **Document Count**: 634
- **Entity Scope**: Long-form TV shows, drama serials, automotive review series, and 24/7 live broadcast channels (`type: "program" | "channel"`).

#### Searchable Attributes (Deliberate Order of Precedence)
1. `name`: Primary title of the program or channel (e.g., *"Ehd E Wafa"*, *"24 NEWS HD"*).
2. `info_staring`: Star cast and actors (e.g., *"Ahad Raza Mir, Osman Khalid Butt"*, *"Suneel Munj"*).
3. `info_genre`: Primary program genre categorization (e.g., *"romance, comedy"*, *"automotive"*).
4. `channel_name`: Broadcast network or brand (e.g., *"TV One"*, *"Tamasha Dramas"*).
5. `info_meta_keywords`: Program discovery keywords and tags.
6. `info_content_type`: Content format (e.g., *"vod"*, *"channel"*).

#### Filterable Attributes
- `type`: Slices shows (`"program"`) vs live broadcast streams (`"channel"`).
- `info_language`: Spoken language (`"urdu"`, `"punjabi"`, `"english"`).
- `info_genre`: Program genres for faceted search.
- `channel_name`: Broadcast network name.
- `info_content_type`: Format type.

#### Sortable Attributes
- `name`: Alphabetical ordering.

---

### 2.2 Index: `episodes`
- **Primary Key**: `id`
- **Document Count**: 6,547
- **Entity Scope**: Individual video content, drama episodes, news bulletins, and short-form video clips.

#### Searchable Attributes (Deliberate Order of Precedence)
1. `title`: Episode title (e.g., *"Ehd E Wafa | Episode 4"*).
2. `program_name`: Denormalized parent show title for cross-level discovery.
3. `stars`: Denormalized starring cast from parent program.
4. `genre`: Episode genre tags (e.g., *"Pakistani Dramas"*, *"Kids"*).
5. `description`: Long-form synopsis and plot summary.
6. `channel_name`: Network or channel name.
7. `meta_keywords`: Keywords from parent program.

#### Denormalization Strategy
When an episode has a valid parent relationship (`program_id` references a known `programs.id`), the indexing pipeline denormalizes:
- `program_name`
- `program_slug`
- `program_type`
- `channel_name`
- `language`
- `stars`
- `stars_list`
- `meta_keywords`

*Orphan Episodes Preservation:* For 247 episodes whose parent ID is missing from `prod_enrichment.csv`, all native episode attributes are indexed, while parent fields remain empty. Orphan episodes are fully searchable by title, description, and genre without referential integrity loss.

#### Filterable Attributes
- `is_free`: Content access tier (`true` for Free, `false` for Premium/Pro).
- `content_tier`: Quality/access tier (`"free"`, `"pro"`).
- `genre`: Multi-valued episode genres.
- `language`: Audio language.
- `channel_name`: Network name.
- `region`: Licensed broadcast regions (e.g., `"PK"`, `"WW"`).
- `is_vertical`: Video aspect ratio (`"mini"` for vertical shorts).
- `program_id`: Exact parent show filter.

#### Sortable Attributes
- `views`: Numerical view counts (integer, up to millions).
- `duration_seconds`: Consistent runtime in seconds.
- `title`: Lexicographical episode title.

---

## 3. Typo Tolerance & Ranking Configuration

Meilisearch's native ranking rules are configured to balance title precision with forgiving typo tolerance:

```json
{
  "rankingRules": [
    "words",
    "typo",
    "proximity",
    "attribute",
    "sort",
    "exactness"
  ],
  "typoTolerance": {
    "enabled": true,
    "minWordSizeForTypos": {
      "oneTypo": 4,
      "twoTypos": 8
    }
  }
}
```

- Words >= 4 characters tolerate 1 typographical error (e.g., *"Ehd e Waffa"* -> *"Ehd E Wafa"*, *"Al Fatiha"* -> *"Al Fatihah"*).
- Words >= 8 characters tolerate 2 typographical errors.
- Exactness and proximity preserve exact multi-word phrases (e.g. *"24 NEWS HD"*).

---

## 4. Unified Search API (`GET /api/search`)

### Query Parameters
- `q`: Search string (optional; empty queries return top-ranked catalog items).
- `type`: Target scope — `"all"`, `"programs"`, `"channels"`, `"episodes"`. Default is `"all"`.
- `limit`: Number of results (default: 12, max: 100).
- `offset`: Offset for pagination.
- `sort`: Validated sort expression (e.g., `"views:desc"`, `"duration_seconds:asc"`).
- `is_free`: Boolean access filter.
- `content_tier`: String tier filter.
- `genre`: Genre filter.
- `channel_name`: Channel/network filter.
- `region`: Distribution region.
- `is_vertical`: Video orientation filter.

### Cross-Index Composition Policy (`type: "all"`)
When `type=all`:
1. Queries both `programs` and `episodes` concurrently in Meilisearch.
2. Allocates results: top program matches + top episode matches.
3. If query explicitly matches a program title or show, the program is elevated to rank 1, followed by associated episodes.
4. Aggregates facet distributions transparently across both entities.
5. Emits normalized `SearchResultItem` records preserving entity metadata, duration, views, badges, and highlighted snippets.
