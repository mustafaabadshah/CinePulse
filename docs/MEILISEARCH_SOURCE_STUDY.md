# Meilisearch Source Code Architectural Study & Contribution Blueprint

## 1. Overview & Repository Topology
This study examines the official open-source **Meilisearch** repository (`meilisearch/meilisearch`).
The repository is structured as a high-performance Rust multi-crate workspace. The core subsystems, verified entry points, data flows, and contribution paths are documented below based on verified paths in the active repository tree.

```
meilisearch/
├── Cargo.toml                  # Cargo workspace manifest
├── crates/
│   ├── meilisearch/            # Binary entry point, HTTP server, Actix Web routing
│   │   ├── src/main.rs         # CLI entry point, argument parsing, telemetry setup
│   │   ├── src/routes/         # HTTP request handlers (indexes, documents, search, tasks, keys)
│   │   ├── src/middleware.rs   # Authentication, payload size limiting, error formatting
│   │   └── src/analytics/      # Anonymous usage statistics
│   ├── routes/                 # Modular HTTP routes definition
│   ├── index-scheduler/        # Asynchronous task queue, concurrency control & index lifecycle
│   │   ├── src/lib.rs          # IndexScheduler struct and public interface
│   │   ├── src/scheduler.rs    # Batch processing and scheduling loop
│   │   ├── src/task.rs         # Task enum, status transitions (Enqueued, Processing, Succeeded, Failed)
│   │   └── src/index_mapper.rs # Maps index UIDs to underlying milli index instances
│   ├── milli/                  # The core search engine library (embedded & standalone)
│   │   ├── src/index.rs        # Index struct wrapping LMDB database handles
│   │   ├── src/search/         # Query execution, ranking rules, facet filtering, typo tolerance
│   │   ├── src/update/         # Document addition, deletion, settings updates, inverted index construction
│   │   ├── src/criterion.rs    # Ranking criteria definitions (words, typo, proximity, exactness)
│   │   └── src/heed_codec/     # Zero-copy binary serializers for LMDB (heed)
│   ├── file-store/             # Raw payload and dump temporary storage management
│   ├── meilisearch-auth/       # Master key validation, API keys storage and permission scopes
│   └── meilisearch-types/      # Shared domain types, error codes, and serialization models
├── external-crates/            # In-tree dependencies including Charabia tokenization
└── workloads/ & benchmarks/    # Performance regression suites and Criterion benchmarks
```

---

## 2. Deep Dive: The 8 Subsystems

### Subsystem 1: HTTP API & Request Handling
1. **Responsibility:**
   Accepts incoming HTTP requests, handles TLS/network sockets, validates API key permissions, deserializes JSON/CSV payloads into internal types, and returns standard JSON responses with proper HTTP status codes.
2. **Important Files & Entry Points:**
   - `crates/meilisearch/src/main.rs`: CLI initialization, daemon startup, signal handling.
   - `crates/meilisearch/src/routes/`: Route definitions (`search.rs`, `indexes/mod.rs`, `documents.rs`, `tasks.rs`).
   - `crates/meilisearch/src/middleware.rs`: Master key and search API key verification.
3. **Request Flow:**
   A `POST /indexes/{uid}/search` request reaches `Actix-Web` -> enters authentication middleware in `meilisearch-auth` -> passes to `routes/search.rs` -> extracts query and parameters into a `SearchQuery` struct -> delegates to `IndexScheduler.search()` -> invokes `milli::Index::search()` -> returns results as JSON.
4. **Demonstrating Tests:**
   - `crates/meilisearch/tests/search/mod.rs`: Integration tests covering queries, filters, and highlighting.
   - `crates/meilisearch/tests/auth/mod.rs`: Verification of key permissions and tenant tokens.
5. **Hands-on Experiment:**
   Run `cargo test -p meilisearch --test search` with `RUST_LOG=trace` to observe request parsing and duration logging.
6. **Beginner Contribution:**
   Clarify error messages in `crates/meilisearch/src/error.rs` when user-provided JSON payloads exceed body limits.

---

### Subsystem 2: Index Management & Scheduler (`index-scheduler`)
1. **Responsibility:**
   Acts as the brain of Meilisearch. Maintains an ACID-compliant task queue, batches multiple incoming document additions or settings mutations, coordinates concurrency between writes and reads, and creates or drops indexes.
2. **Important Files & Entry Points:**
   - `crates/index-scheduler/src/lib.rs`: The central `IndexScheduler` engine.
   - `crates/index-scheduler/src/scheduler.rs`: Batch scheduler logic combining compatible pending tasks.
   - `crates/index-scheduler/src/task.rs`: Task status states (`Enqueued`, `Processing`, `Succeeded`, `Failed`, `Canceled`).
3. **Data Flow:**
   When documents are submitted via HTTP, a new `Task` is enqueued into the scheduler's internal database -> scheduler worker wakes up -> aggregates consecutive document additions into a single batch -> acquires write lock on the target `milli::Index` -> commits batch to disk -> updates task status to `Succeeded`.
4. **Demonstrating Tests:**
   - `crates/index-scheduler/tests/`: Tests task cancellation, batching of multiple updates, and crash recovery.
5. **Hands-on Experiment:**
   Enqueue 5 small document update batches simultaneously; observe that the scheduler automatically auto-batches them into 1 update transaction for optimal LMDB throughput.
6. **Beginner Contribution:**
   Add descriptive doc-comments explaining `IndexScheduler::register` and task priority queues.

---

### Subsystem 3: The `milli` Search and Indexing Engine
1. **Responsibility:**
   The heart of Meilisearch. An embedded search library written in Rust that builds inverted indexes, calculates Roaring Bitmaps for term postings, evaluates boolean filters, and scores matching candidates.
2. **Important Files & Entry Points:**
   - `crates/milli/src/index.rs`: Main `Index` struct with LMDB database descriptors.
   - `crates/milli/src/search/mod.rs`: Search pipeline coordinating candidate matching.
   - `crates/milli/src/update/index_documents/mod.rs`: Pipeline converting raw JSON documents into inverted indexes.
3. **Data Flow:**
   Documents are tokenized by Charabia -> word IDs and position maps are stored in LMDB -> word-pair proximity bitmaps are created -> during search, candidate roaring bitmaps for each query term are intersected.
4. **Demonstrating Tests:**
   - `crates/milli/src/search/facet/tests.rs`: Tests facet distribution calculation.
   - `crates/milli/src/update/index_documents/tests.rs`: Tests index updates and rollbacks.
5. **Hands-on Experiment:**
   Write a small Rust test script utilizing `milli` as a standalone embedded library without the HTTP layer.
6. **Beginner Contribution:**
   Improve error documentation for custom ranking rules syntax validation.

---

### Subsystem 4: `Charabia` Multilingual Tokenization
1. **Responsibility:**
   Splits arbitrary text into tokens, normalizes unicode (NFKC), converts characters to lowercase, strips accents, segments languages without whitespace (Chinese, Japanese, Thai), and applies language-specific stemmers.
2. **Important Files & Entry Points:**
   - `external-crates/charabia/charabia/src/tokenizer.rs`: Tokenizer abstraction and iterator.
   - `external-crates/charabia/charabia/src/segmenter/`: Language segmenters.
   - `external-crates/charabia/charabia/src/normalizer/`: Unicode and diacritic normalizers.
3. **Data Flow:**
   Raw text string enters `charabia::tokenize()` -> language detector identifies script -> segmenter splits into lemma tokens -> normalizer strips accents and normalizes case -> emits stream of `Token` structs to `milli`.
4. **Demonstrating Tests:**
   - `charabia/tests/`: Extensive multilingual test vectors covering Latin, Cyrillic, CJK, and Arabic scripts.
5. **Hands-on Experiment:**
   Test Charabia with non-English characters (e.g. German umlauts `ä -> a` or French `é -> e`) to verify typo tolerance alignment.
6. **Beginner Contribution:**
   Add new test cases for scientific and technical abbreviations (e.g. `p99`, `k-NN`, `4D-Gaussians`).

---

### Subsystem 5: Task Processing & Updates
1. **Responsibility:**
   Manages asynchronous operations. Since indexing in Meilisearch is non-blocking, every document addition, index deletion, or settings modification returns an asynchronous task UID.
2. **Important Files & Entry Points:**
   - `crates/index-scheduler/src/task.rs`
   - `crates/meilisearch/src/routes/tasks.rs`
3. **Data Flow:**
   Client issues `POST /indexes/{uid}/documents` -> server returns `{"taskUid": 12, "status": "enqueued"}` -> client polls `GET /tasks/12` -> server queries scheduler's task database and returns details including duration, error, and matched records count.
4. **Demonstrating Tests:**
   - `crates/meilisearch/tests/tasks/mod.rs`: Task status polling and filter expressions (`statuses=succeeded`).
5. **Hands-on Experiment:**
   Submit an invalid document schema and inspect the detailed error payload returned by `GET /tasks/{uid}`.
6. **Beginner Contribution:**
   Add documentation examples for filtering tasks by date or index UID.

---

### Subsystem 6: Persistence & Storage (`heed` & LMDB)
1. **Responsibility:**
   Provides ACID transactional persistence using LMDB (Lightning Memory-Mapped Database) through the typed Rust wrapper `heed`. Enables zero-copy reads via memory-mapped files (`data.ms`).
2. **Important Files & Entry Points:**
   - `crates/milli/src/heed_codec/`: Zero-copy serializers/deserializers for roaring bitmaps and string keys.
   - `crates/file-store/`: Large payload streaming and temporary file management.
3. **Data Flow:**
   All index data, inverted lists, and task histories are stored directly in LMDB B+ trees on disk. Because LMDB is memory-mapped, reads bypass kernel-to-user space copy overhead.
4. **Demonstrating Tests:**
   - `crates/milli/src/heed_codec/`: Unit tests verifying bit-level roundtrip serialization.
5. **Hands-on Experiment:**
   Inspect the size of `data.ms` after inserting 10,000 documents; verify that restarting the process takes <10ms due to mmap caching.
6. **Beginner Contribution:**
   Document disk space best practices and memory-map size limits for resource-constrained systems.

---

### Subsystem 7: Ranking Rules & Relevancy Engine
1. **Responsibility:**
   Determines the exact ordering of search results using a deterministic Bucket Sort algorithm based on 6 default ranking rules:
   1. `Words`: Matches containing more query terms rank higher.
   2. `Typo`: Matches with fewer spelling mistakes rank higher.
   3. `Proximity`: Terms closer together in the document text rank higher.
   4. `Attribute`: Matches in prioritized attributes (e.g. `title` before `abstract`) rank higher.
   5. `Sort`: User-defined custom sort attributes (e.g. `publication_year:desc`).
   6. `Exactness`: Exact word matches rank higher than prefix or partial matches.
2. **Important Files & Entry Points:**
   - `crates/milli/src/criterion.rs`: Criterion trait implementation.
   - `crates/milli/src/search/ranking_rules/`: Implementation of `words.rs`, `typo.rs`, `proximity.rs`, `attribute.rs`, `exactness.rs`.
3. **Data Flow:**
   Candidates matching query terms are grouped into buckets by rule 1 (`words`) -> ties within the same bucket are evaluated by rule 2 (`typo`) -> remaining ties evaluated by rule 3 (`proximity`), cascading until top-k documents are fully sorted.
4. **Demonstrating Tests:**
   - `crates/milli/src/search/ranking_rules/tests.rs`: Tests ranking order permutations.
5. **Hands-on Experiment:**
   Modify index ranking rules in ResearchRadar to place `sort` before `typo` and observe how year sorting changes result order.
6. **Beginner Contribution:**
   Create an interactive visual diagram in `docs/` illustrating how bucket sort resolves ties.

---

### Subsystem 8: Tests & Benchmarks
1. **Responsibility:**
   Ensures engine correctness, zero memory leaks, and detects performance regressions.
2. **Important Files & Entry Points:**
   - `crates/milli/tests/`: Low-level unit and property tests.
   - `crates/meilisearch/tests/`: High-level end-to-end HTTP integration tests.
   - `BENCHMARKS.md` & `workloads/`: Benchmark datasets (e.g. Hitting Songs, Hacker News, Movies) run with Criterion.
3. **Demonstrating Tests:**
   - `cargo test --workspace` executes the complete integration test suite.
4. **Hands-on Experiment:**
   Run a micro-benchmark using `cargo bench -p milli`.
5. **Beginner Contribution:**
   Add edge-case tests for unicode punctuation and hyphenated author names in search queries.

---

## 3. Upstream Contribution Plan

### Step-by-Step Workflow for Contributing to Meilisearch
1. **Fork & Clone:**
   ```bash
   git clone https://github.com/<your-username>/meilisearch.git
   cd meilisearch
   ```
2. **Set up Rust Toolchain:**
   Meilisearch uses a pinned Rust toolchain specified in `rust-toolchain.toml`:
   ```bash
   rustup show
   ```
3. **Build & Test Workspace:**
   ```bash
   cargo build
   cargo test -p meilisearch --test search
   ```
4. **Identify Good First Issues:**
   Search GitHub issues labeled `good first issue` or `documentation`:
   - [Good First Issues on GitHub](https://github.com/meilisearch/meilisearch/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
5. **Implement Fix with Regression Test:**
   Always add an integration test in `crates/meilisearch/tests/` demonstrating the bug before fixing it.
6. **Run Formatters & Linters:**
   ```bash
   cargo fmt --check
   cargo clippy --workspace --all-targets -- -D warnings
   ```
7. **Submit Pull Request:**
   Submit PR with a clear summary linking the issue, describing changes, and confirming that CI passes.
