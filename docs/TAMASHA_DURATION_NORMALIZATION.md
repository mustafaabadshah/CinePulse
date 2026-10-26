# Tamasha Catalog Explorer: Media Duration Normalization Architecture & Policy

---

## 1. Executive Summary

During production catalog inspection of the Tamasha OTT discovery platform (`data/episodes_prod.csv` and SQLite database `data/researchradar.db`), two primary anomalies were identified regarding video durations:
1. Videos displaying very short durations (such as `00:00:32` and `00:00:39`) for content suspected of being full television episodes.
2. Videos displaying raw integer numbers (such as `1538` or `3269`) directly in the user interface.

This document details the investigative findings, mathematical root causes, conversion policy, database and search index remediation, frontend formatting architecture, and end-to-end verification.

---

## 2. Root Cause Analysis: The Reality of `00:00:32` and `00:00:39`

### 2.1 The Investigation
An exhaustive SQL query and CSV row trace was conducted for all episodes with durations under 60 seconds:

```sql
SELECT id, title, program_id, duration, duration_seconds 
FROM episodes 
WHERE duration_seconds < 60 OR duration LIKE '00:00:%';
```

The exact matching records:
- **Episode `102536`**: *Muhabbat Khel Tamasha | Teaser 3 | TV One Drama* (`duration = "00:00:39"`, `duration_seconds = 39`)
- **Episode `102537`**: *Muhabbat Khel Tamasha | Teaser 2 | TV One Drama* (`duration = "00:00:39"`, `duration_seconds = 39`)
- **Episode `103413`**: *Fashion Pakistan Week | Teaser 2 | TV One Fashion* (`duration = "00:00:32"`, `duration_seconds = 32`)
- **Episode `225711`**: *Rap Icon Pakistan | EP 02 | Promo* (`duration = "00:00:39"`, `duration_seconds = 39`)

### 2.2 Findings
1. **Genuine Short Promotional Media**:
   These media assets are **authentic 32-second and 39-second promotional teasers and trailers**, explicitly named *"Teaser 2"*, *"Teaser 3"*, and *"Promo"*.
   In fact, in `prod_enrichment.csv`, the parent program for IDs `102536`, `102537`, and `103413` is Program ID `248`, whose title is literally **`Teasers`**!
2. **Additional Legitimate Short Content**:
   The catalog contains Quranic surah recitations (e.g. *Surah Al-Ikhlas* `00:00:21`, *Surah Al-Falaq* `00:00:33`, *Surah Al-Fatihah* `00:00:54`) and cricket highlights/wickets (e.g. `00:00:47`), which are also authentic short-form clips.
3. **Core Defect**:
   The database and CSV parser had computed `duration_seconds` accurately (32 and 39 seconds). However, the React frontend displayed the raw clock string `00:00:39` with full hour-padding, creating the visual impression that hours or minutes had been accidentally truncated from a long drama episode. Furthermore, there was no badge distinguishing full-length episodes from short teasers and clips.

---

## 3. The 16 Raw Integer Seconds Records

### 3.1 Identification
While 6,467 episodes in `episodes_prod.csv` were formatted as `HH:MM:SS` (e.g. `00:39:30`), exactly 16 episodes contained raw numbers in seconds stored as text strings in the CSV:

| Episode ID | Episode Title | Raw CSV `duration` | True Elapsed Time | Stored `duration_seconds` | Stored `duration` (Before) | Repaired `duration` (After) |
|---|---|---|---|---|---|---|
| `38006` | *Wabaal - Ep 16 - 17 Dec 2022 - HUM TV* | `"1538"` | 25m 38s | 1538 | `"1538"` | `"25:38"` |
| `38008` | *Wabaal - Ep 17 - 18 Dec 2022 - HUM TV* | `"1743"` | 29m 03s | 1743 | `"1743"` | `"29:03"` |
| `38010` | *Wabaal - Ep 18 - 24 Dec 2022 - HUM TV* | `"1678"` | 27m 58s | 1678 | `"1678"` | `"27:58"` |
| `38012` | *Wabaal - Ep 19 - 25 Dec 2022 - HUM TV* | `"1859"` | 30m 59s | 1859 | `"1859"` | `"30:59"` |
| `38014` | *Wabaal - Ep 20 - 31 Dec 2022 - HUM TV* | `"1907"` | 31m 47s | 1907 | `"1907"` | `"31:47"` |
| `38016` | *Wabaal - Ep 21 - 01 Jan 2023 - HUM TV* | `"1941"` | 32m 21s | 1941 | `"1941"` | `"32:21"` |
| `38018` | *Wabaal - Ep 22 - 07 Jan 2023 - HUM TV* | `"1780"` | 29m 40s | 1780 | `"1780"` | `"29:40"` |
| `38020` | *Wabaal - Ep 23 - 08 Jan 2023 - HUM TV* | `"1916"` | 31m 56s | 1916 | `"1916"` | `"31:56"` |
| `38022` | *Wabaal - Ep 24 - 14 Jan 2023 - HUM TV* | `"1957"` | 32m 37s | 1957 | `"1957"` | `"32:37"` |
| `38024` | *Wabaal - Ep 25 - 15 Jan 2023 - HUM TV* | `"1906"` | 31m 46s | 1906 | `"1906"` | `"31:46"` |
| `38026` | *Wabaal - Ep 26 - 21 Jan 2023 - HUM TV* | `"1945"` | 32m 25s | 1945 | `"1945"` | `"32:25"` |
| `38028` | *Wabaal - Ep 27 - 22 Jan 2023 - HUM TV* | `"1903"` | 31m 43s | 1903 | `"1903"` | `"31:43"` |
| `38030` | *Wabaal - Ep 28 - 28 Jan 2023 - HUM TV* | `"1852"` | 30m 52s | 1852 | `"1852"` | `"30:52"` |
| `38032` | *Wabaal - Ep 29 - 29 Jan 2023 - HUM TV* | `"1894"` | 31m 34s | 1894 | `"1894"` | `"31:34"` |
| `38034` | *Wabaal - Ep 30 - 04 Feb 2023 - HUM TV* | `"1897"` | 31m 37s | 1897 | `"1897"` | `"31:37"` |
| `38036` | *Wabaal - Ep 31 - 05 Feb 2023 - HUM TV* | `"1905"` | 31m 45s | 1905 | `"1905"` | `"31:45"` |

### 3.2 Root Cause
In `episodes_prod.csv`, episodes 16 through 31 of *Wabaal* originated from a CMS feed export that recorded video runtimes directly in total seconds rather than formatted timestamps. When imported, the database preserved `"1538"` in the `duration` column. The parser computed `duration_seconds = 1538`, but because the frontend displayed `item.duration`, the screen printed `"1538"`.

---

## 4. Normalization & Remediation Policy

### 4.1 Strict Safety Principles
1. **Source CSVs are Immutable**: Under no circumstance are `data/episodes_prod.csv` or `data/prod_enrichment.csv` modified. All corrections are executed within the canonical database and search index.
2. **Never Guess or Artificially Multiply**: Authentic teasers and short clips (e.g. 39 seconds) must NEVER be multiplied by 60 or converted into 39 minutes. They remain 39 seconds, clearly labeled with a `Short Clip` badge.
3. **Dual Storage Standard**:
   - `duration_seconds` (Integer): The authoritative mathematical representation for sorting, filtering, and duration range queries.
   - `duration` (String): A clean, human-readable clock representation (`MM:SS` or `HH:MM:SS`).

### 4.2 Mathematical Conversion Rules
For any duration in total seconds $S$:
- If $S \ge 3600$:
  $$H = \lfloor S / 3600 \rfloor, \quad M = \lfloor (S \pmod{3600}) / 60 \rfloor, \quad S_{rem} = S \pmod{60}$$
  Clock format: `H:MM:SS` (e.g., $4779 \to \text{"1:19:39"}$)
- If $60 \le S < 3600$:
  $$M = \lfloor S / 60 \rfloor, \quad S_{rem} = S \pmod{60}$$
  Clock format: `MM:SS` (e.g., $1538 \to \text{"25:38"}$)
- If $0 \le S < 60$:
  Clock format: `0:SS` (e.g., $39 \to \text{"0:39"}$)

### 4.3 Database & Index Repair Execution
The Python script [`scripts/repair-media-durations.py`](file:///E:/MM%20Office/ResearchRadar/scripts/repair-media-durations.py) was implemented with full dry-run safety:
- **Dry-Run Output**: `artifacts/data_quality/duration_repair_dry_run.json`
- **Applied Output**: `artifacts/data_quality/duration_repair_applied.json`
- **Actions Performed**:
  - Identified all 16 pure-integer records.
  - Converted `duration` to standardized `MM:SS` clock strings while verifying that `duration_seconds` remained exact.
  - Synchronized updated documents into Meilisearch index `episodes`.
  - Preserved all 64 null/empty duration records safely without generating corrupt values.

---

## 5. Frontend Duration Architecture

### 5.1 Format Utility (`frontend/src/utils/formatDuration.ts`)
The frontend duration logic is encapsulated into a pure, fully tested utility:

```typescript
export function formatDuration(seconds?: number, rawString?: string): string {
  if (seconds !== undefined && seconds !== null && !isNaN(seconds) && seconds >= 0) {
    const s = Math.floor(seconds);
    const hrs = Math.floor(s / 3600);
    const mins = Math.floor((s % 3600) / 60);
    const secs = s % 60;
    const pad = (n: number) => n.toString().padStart(2, "0");

    if (hrs > 0) return `${hrs}:${pad(mins)}:${pad(secs)}`;
    if (mins > 0) return `${mins}:${pad(secs)}`;
    return `0:${pad(secs)}`;
  }
  // Safe fallback to raw string or Unknown
  ...
}

export function isTeaserOrClip(seconds?: number): boolean {
  return seconds !== undefined && seconds !== null && seconds > 0 && seconds < 60;
}
```

### 5.2 Unit Test Verification
The formatter is accompanied by 14 exhaustive unit tests in `frontend/src/test/formatDuration.test.ts`:
- 32-second teaser: `formatDuration(32) === "0:32"` (clip flag `true`)
- 39-second teaser: `formatDuration(39) === "0:39"` (clip flag `true`)
- 1538-second episode: `formatDuration(1538) === "25:38"`
- 3269-second episode: `formatDuration(3269) === "54:29"`
- 4779-second feature: `formatDuration(4779) === "1:19:39"`
- Exact hour boundaries: `formatDuration(3600) === "1:00:00"`
- Null, undefined, and zero handling: all safe, no exceptions.
- **Test Result**: 14/14 tests PASSED.

---

## 6. Audit Before vs. After Summary

| Metric | Before Normalization | After Normalization | Resolution |
|---|---|---|---|
| Total Episodes | 6,547 | 6,547 | Exact match |
| Standard `HH:MM:SS` / `MM:SS` | 6,467 | 6,483 | +16 converted |
| Raw Integer Seconds Strings | 16 | 0 | 100% resolved |
| Null / Empty Durations | 64 | 64 | Safely preserved |
| `00:00:32` & `00:00:39` Display | Displayed as full raw clock | Displayed as `0:32` / `0:39` with `Short Clip` badge | User confusion eliminated |
| Meilisearch Consistency | 6,547 documents | 6,547 documents | Synchronized |
