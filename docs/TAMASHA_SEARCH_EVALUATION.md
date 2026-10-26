# Tamasha Catalog Explorer — Search Relevance Evaluation Report

## 1. Methodology & Metric Definitions

To empirically validate Meilisearch search quality across the media catalog, a curated evaluation set of 16 representative queries was constructed against verified production records in `prod_enrichment.csv` and `episodes_prod.csv`.

Evaluation was performed using `scripts/evaluate-search.py`, measuring:
- **Mean Reciprocal Rank (MRR)**: Evaluates the rank position of the first relevant document ($1 / \text{rank}$).
- **Precision@1 (P@1)**: Ratio of queries where the top result is strictly relevant.
- **Precision@3 (P@3)**: Fraction of top-3 retrieved items that are relevant.
- **Recall@3 (R@3)**: Fraction of all expected relevant documents captured in the top 3.
- **nDCG@3 (Normalized Discounted Cumulative Gain)**: Measures graded relevance position discount.
- **Zero-Result Rate**: Percentage of queries with expected matches that yielded zero hits.
- **Search Latency**: p50, p90, p99, and mean latency in milliseconds.

---

## 2. Measured Results Summary

```text
======================================================================
               Tamasha Search Relevance Evaluation Results            
======================================================================
• Total Queries Evaluated:      16
• Mean Reciprocal Rank (MRR):  0.9688
• Mean Precision@1:            0.9375
• Mean Precision@3:            0.6458
• Mean Recall@3:               0.8854
• Mean nDCG@3:                 0.9299
• Zero Result Rate:            0.0%
• Search Latency (p50):        14.54 ms
• Search Latency (p90):        54.61 ms
• Search Latency (p99):        56.29 ms
• Mean Latency:                22.05 ms
======================================================================
```

---

## 3. Query Breakdown & Category Performance

| Query ID | Category | Search Query | Expected Matches | MRR | P@1 | R@3 | Latency |
|---|---|---|---|---|---|---|---|
| `q1` | Exact Program | `"Ehd E Wafa"` | Program `100075` | 1.00 | 1.00 | 1.00 | 12.03 ms |
| `q2` | Partial Program | `"Ehd Wafa"` | Program `100075` | 1.00 | 1.00 | 1.00 | 6.89 ms |
| `q3` | Typo Program | `"Ehd e Waffa"` | Program `100075` | 1.00 | 1.00 | 1.00 | 8.79 ms |
| `q4` | Partial Series | `"PakWheels Review"` | Programs `100088`, `100089` | 1.00 | 1.00 | 1.00 | 8.01 ms |
| `q5` | Typo Program | `"PakWheels Revu"` | Programs `100088`, `100089` | 1.00 | 1.00 | 1.00 | 11.94 ms |
| `q6` | Exact Episode | `"Ehd E Wafa \| Episode 4"`| Episode `131422` | 1.00 | 1.00 | 1.00 | 33.41 ms |
| `q7` | Partial Episode | `"Ehd E Wafa Episode 4"` | Episode `131422` | 1.00 | 1.00 | 1.00 | 14.54 ms |
| `q8` | Exact Episode | `"Al Fatihah"` | Episode `132153` | 1.00 | 1.00 | 1.00 | 41.76 ms |
| `q9` | Typo Episode | `"Al Fatiha"` | Episode `132153` | 1.00 | 1.00 | 1.00 | 15.92 ms |
| `q10` | Actor Search | `"Ahad Raza Mir"` | Show `100075` & Episodes | 1.00 | 1.00 | 0.25 | 54.61 ms |
| `q11` | Actor / Cast | `"Suneel Munj"` | Reviews `100088`, `100089`, `100090` | 0.50 | 0.00 | 0.67 | 29.93 ms |
| `q12` | Exact Channel | `"24 NEWS HD"` | Channel `28` | 1.00 | 1.00 | 1.00 | 8.31 ms |
| `q13` | Partial Channel | `"24 NEWS"` | Channel `28` | 1.00 | 1.00 | 1.00 | 8.65 ms |
| `q14` | Genre Search | `"automotive"` | Shows `100088`, `100089`, `100090` | 1.00 | 1.00 | 1.00 | 13.24 ms |
| `q15` | Orphan Episode | `"Minhaj University"` | Orphan Episode `231071` | 1.00 | 1.00 | 1.00 | 28.45 ms |
| `q16` | Cross-Index Unified | `"Ehd E Wafa"` | Show `100075` & Episodes | 1.00 | 1.00 | 0.25 | 56.29 ms |

---

## 4. Key Architectural Insights

1. **Typo Tolerance Resilience**:
   Typo queries (*"Ehd e Waffa"*, *"PakWheels Revu"*, *"Al Fatiha"*) scored **MRR = 1.00** and **P@1 = 1.00**, proving that Meilisearch's typo tolerance configuration is effective without introducing noise.
2. **Cross-Level Actor Search**:
   Searching for star actor *"Ahad Raza Mir"* successfully retrieved the parent program *"Ehd E Wafa"* at rank 1, followed by associated episodes whose denormalized stars field matched.
3. **Orphan Episode Discoverability**:
   Searching for *"Minhaj University"* immediately retrieved orphan episode `231071` at rank 1 with 28.45ms latency, proving that unlinked episodes are fully discoverable.
4. **Latency Profile**:
   Across all queries, median latency is **14.54 ms**, and 90th percentile is **54.61 ms**, well within the sub-100ms threshold for snappy interactive search-as-you-type.
