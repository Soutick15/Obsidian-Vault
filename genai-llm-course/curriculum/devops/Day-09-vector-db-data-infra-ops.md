# Day 9 — Vector DB & Data Infrastructure Operations

**Track:** DevOps | **Position in course:** 9 of 15
**Prerequisites:** Days 1–5 (LLM basics, transformers, decoding, prompting, APIs); Days 6–8 DevOps track (model serving infrastructure, containerisation & orchestration, observability & CI/CD)

---

## 1. Learning Objectives

By the end of Day 9 you will be able to:

1. Explain the architecture and operational tradeoffs of self-hosted vector databases (pgvector, Chroma, Qdrant) versus managed options, and select the right tier for a given workload.
2. Describe HNSW index parameters (`ef_construction`, `M`, `ef_search`) as tunable operational knobs and reason about their effect on memory, build time, and recall.
3. Design an idempotent ingestion pipeline that can be re-run safely on schedule without duplicating or corrupting data.
4. Implement incremental re-indexing — detecting and re-processing only changed documents.
5. Describe a backup-and-restore procedure for a local Chroma collection and explain what makes it operationally viable.
6. Define and collect index health metrics (document count, chunk count, on-disk size) and use them as input to capacity planning.
7. Explain data versioning and schema migration concerns specific to vector stores, and articulate a safe migration strategy.

---

## 2. Concept Reading

### 2.1 The Data/Retrieval Layer as Infrastructure

In a production AI system, the **vector database** is infrastructure — not application code. It stores the embedded representations of all your documents and serves approximate-nearest-neighbour (ANN) search queries under latency SLOs. Like any data store, it requires:

- **Provisioning** — right-sized compute and memory for the index
- **Ingestion pipelines** — reliable, idempotent, observable
- **Backups and restore procedures** — tested, not just written
- **Health monitoring** — metrics that fire alerts before users notice problems
- **Data versioning and migration** — when embedding models change or schema evolves

Most teams build these concerns as an afterthought and pay for it when the index drifts stale, duplicates accumulate on re-runs, or a disk failure triggers a scramble.

---

### 2.2 Vector Database Options and Tradeoffs

There is no single "best" vector database. Operational fit depends on your team's existing stack, scale, and tolerable ops burden.

#### pgvector (PostgreSQL extension)

```
PROS  — Zero new infrastructure if you already run Postgres;
        full SQL joins possible; ACID transactions; mature backup tooling.
CONS  — ANN performance at >1M vectors requires careful index tuning;
        single-node write throughput; no native distributed sharding.
BEST FOR — Teams with strong Postgres experience; <5M vectors; hybrid
           SQL + vector queries (e.g., "search within a tenant's documents").
```

**Key operational parameter:** `lists` in IVFFlat (number of Voronoi cells) or `m`/`ef_construction` in HNSW (pgvector ≥0.5). Set `SET hnsw.ef_search = 100;` per session to tune recall vs. latency.

#### Chroma

```
PROS  — Pure-Python; zero-config local persistent mode; simple HTTP server
        mode; ideal for development and small-scale production.
CONS  — No horizontal scaling; no replication; backup = copy the SQLite file.
BEST FOR — Dev/test; single-node services with <500K vectors; internal tools.
```

Chroma's default embedding function (when no function is specified) uses a built-in model. For no-dep local use you can supply a deterministic custom `EmbeddingFunction`. The persistent store is a directory containing `chroma.sqlite3` plus segment files.

#### Qdrant

```
PROS  — High-performance Rust core; native HNSW; built-in payload filtering;
        distributed mode with sharding; gRPC + REST; snapshot API.
CONS  — New operational surface (separate process/container); less SQL-native.
BEST FOR — Production workloads >1M vectors; low-latency requirements;
           multi-tenant with payload filtering.
```

#### Managed Options (Pinecone, Weaviate Cloud, Vertex AI Vector Search)

Managed services eliminate node-level ops but introduce vendor lock-in and higher per-query cost. They are appropriate when:
- The team has no capacity to operate stateful infrastructure.
- Workloads need global replication or enterprise SLAs.
- Cost modelling favours managed pricing over staffing.

**Key managed tradeoff:** you trade operational control for SLA coverage. Data portability (export/import) must be verified before commitment.

---

### 2.3 HNSW Index Parameters as Operational Knobs

HNSW (Hierarchical Navigable Small World) is the dominant ANN algorithm in modern vector databases. Its parameters are **ops decisions**, not just engineering ones.

| Parameter | What it controls | Ops tradeoff |
|---|---|---|
| `M` (max edges per node) | Graph connectivity | Higher M → better recall, larger index in RAM, longer build |
| `ef_construction` | Build-time search width | Higher → better recall, much slower build; set once at index creation |
| `ef_search` (or `ef`) | Query-time search width | Higher → better recall, higher latency; tunable per query |

**Memory formula (rough):** `index_size_bytes ≈ n_vectors × (vector_dim × 4 + M × 8 × 2)`. A 1M-vector index at 384 dimensions with M=16 takes roughly 4–5 GB RAM.

**Operational rule of thumb:**
- Start with `M=16`, `ef_construction=200` for most workloads.
- Set `ef_search` at query time: 50 for speed-prioritised, 100–200 for recall-prioritised.
- Rebuild the index (not just add vectors) when recall measurements degrade — incremental additions to HNSW over time cause recall decay.

---

### 2.4 Ingestion Pipelines as Ops Concerns

The ingestion pipeline turns raw documents into searchable vector records. In production it must be:

#### Idempotent

Running the pipeline twice must produce the same result as running it once. Without idempotency:
- Scheduled re-runs accumulate duplicates, inflating index size and degrading search quality.
- Failure + retry produces inconsistent state.

**Implementation pattern:** assign each chunk a **deterministic ID** derived from the source document path and chunk index (e.g., `sha256(source_path + chunk_index)`). Chroma's `upsert` with stable IDs is idempotent: inserting an existing ID updates in place.

```python
import hashlib

def chunk_id(source: str, chunk_index: int) -> str:
    key = f"{source}::{chunk_index}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]
```

#### Incremental (detect changed documents only)

Re-embedding every document on each run is expensive and unnecessary. Instead:
1. Store a **content hash** (MD5 or SHA-256) of each source document alongside the metadata.
2. On the next run, compare the current file hash to the stored hash.
3. Re-index only documents whose hash has changed, and delete orphaned chunks for removed documents.

This reduces pipeline runtime from O(corpus_size) to O(changed_docs) — critical when corpus grows to thousands of documents.

#### Data Freshness

Track when each document was last indexed with an `indexed_at` timestamp in chunk metadata. Surface this in your monitoring dashboard. Staleness SLOs ("no document may be >24 hours stale") should trigger alerts, not manual checks.

#### Pipeline Scheduling

- **Scheduled full re-index:** weekly, as a safety net for drift detection.
- **Event-triggered incremental update:** on document change events (file-system watch, GitLab webhook, S3 event notification).
- **Backfill:** one-time re-index when the embedding model changes (unavoidable; plan for it).

---

### 2.5 Backups and Restore

Vector database backups are often neglected because the data is "just derived" — but re-indexing from scratch can take hours and takes the retrieval layer offline. A backup strategy must be:

1. **Consistent** — snapshot a quiesced or read-only state; avoid backing up mid-write.
2. **Tested** — restore drills must happen on a schedule, not just when disaster strikes.
3. **Versioned** — keep N snapshots, not just the latest.

**Chroma backup procedure:**
1. Quiesce writes (briefly stop the ingestion pipeline or use a maintenance window).
2. Copy the entire Chroma persistence directory (contains `chroma.sqlite3` + segment subdirectories).
3. Compress and timestamp: `tar -czf chroma-backup-$(date +%Y%m%d%H%M%S).tar.gz ./chroma_store/`.
4. Store offsite (S3, GCS, NAS).
5. To restore: unpack into the persistence path and restart the Chroma server.

**Qdrant snapshot API** (`POST /collections/{name}/snapshots`) creates a portable `.snapshot` file that can be loaded into any Qdrant instance — more operationally clean than file copy.

**pgvector** inherits standard Postgres backup tooling (`pg_dump`, `pg_basebackup`, continuous WAL archiving). This is a significant advantage for teams already running Postgres.

---

### 2.6 Data Versioning and Migrations

Vector databases have schema — it just lives in embedding space rather than in column definitions.

#### When you must migrate

- **Embedding model upgrade:** the new model's vectors are not comparable to the old model's vectors. You cannot mix them in the same collection. Full re-index is required.
- **Chunking strategy change:** chunk boundaries change → IDs change → old chunks become orphans.
- **Metadata schema change:** adding new filterable fields requires re-upsert with new metadata.

#### Safe migration pattern

1. Build the new index in a **shadow collection** while the current collection serves traffic.
2. Run both in parallel; route a small percentage of queries to the shadow collection and compare results.
3. Switch traffic to the new collection atomically (update the environment variable / service config).
4. Keep the old collection for a rollback window (48–72 h), then delete.

This blue/green pattern for vector collections eliminates migration-induced downtime.

#### Document lineage in metadata

Always store `source`, `chunk_index`, `content_hash`, `indexed_at`, and `embedding_model` in chunk metadata. Without `embedding_model`, you cannot detect when a collection was built with a stale model version.

---

### 2.7 Monitoring Index Size and Health

A vector database without monitoring is a time bomb. Key metrics to collect and alert on:

| Metric | How to collect | Alert threshold |
|---|---|---|
| Document count | Query collection metadata | Drop > 5% vs. yesterday |
| Chunk count | Count records in collection | Sudden spike (duplicate ingestion) |
| Index size on disk | `os.path.getsize` on store directory | Exceeds capacity budget |
| Ingestion job duration | Instrument the pipeline with `time.perf_counter` | > 2× baseline |
| Ingestion job last success | Write timestamp to a heartbeat file | > configured freshness SLO |
| Query latency (p50/p99) | Time ANN query calls | p99 > 200 ms for typical workloads |

**In Prometheus/Grafana:** expose these as custom gauges from the ingestion pipeline and from a sidecar that periodically queries the collection. This pairs with the observability infrastructure from Day 8.

---

### 2.8 Capacity Planning

Capacity planning for vector databases is deterministic given known inputs.

**Inputs:**
- `N` = number of documents in corpus
- `avg_chunks_per_doc` = average document size / chunk size
- `dim` = embedding dimension (e.g., 384 for all-MiniLM-L6-v2)
- `M` = HNSW M parameter (default 16)

**Approximate memory footprint:**
```
total_vectors = N × avg_chunks_per_doc
index_ram_GB  = total_vectors × (dim × 4 + M × 8 × 2) / 1_073_741_824
```

**Disk footprint:** roughly 2–3× the raw vector data (metadata, SQLite overhead).

**Growth planning:** project 6-month corpus growth and provision for 2× headroom. For Chroma on a single node, the practical limit before latency degrades is roughly 1–5M vectors (hardware dependent). Beyond that, migrate to Qdrant or a managed solution.

---

## 3. Lab

**Lab:** `labs/devops/day-09/`

Build and operate an ingestion pipeline for the HR corpus into a local Chroma store. You will implement idempotent ingestion, incremental re-indexing, backup/restore, and index health metrics — all running locally with no API key.

See `labs/devops/day-09/README.md` for full instructions.

**Learning goals for the lab:**
- Witness idempotency: run the ingestion pipeline twice and confirm chunk count stays constant.
- Witness incrementality: modify one HR document, re-run, and confirm only that document's chunks are re-indexed.
- Perform a backup, wipe the store, restore, and confirm the index is identical.
- Print a health metrics report.

---

## 4. Self-Check Quiz

Answer these before looking anything up. Return here after the lab if any stump you.

**Q1. You re-run the ingestion pipeline on a 12-document corpus and the chunk count doubles. What is the most likely cause, and how do you fix it?**

<details>
<summary>Show answer</summary>

The most likely cause is a non-idempotent pipeline using `add` instead of `upsert`. Each run inserts new records with new (non-deterministic) IDs, so chunks accumulate rather than overwrite. The fix is to assign each chunk a **deterministic ID** (e.g., `sha256(source_path + "::" + chunk_index)`) and switch all insert calls to `upsert`. Re-running will then overwrite existing chunks in place, keeping the count stable.

</details>

**Q2. HNSW's `ef_construction` is set at index creation and `ef_search` can be set at query time. Why would you want to set a higher `ef_search` for a recall-sensitive use case but keep `ef_construction` moderate?**

<details>
<summary>Show answer</summary>

`ef_construction` controls the quality of graph connectivity when vectors are inserted — a higher value produces a better-connected graph but dramatically increases index build time and is fixed at creation. `ef_search` controls how widely the graph is searched at query time and can be tuned per query without rebuilding the index. For recall-sensitive use cases you can raise `ef_search` to trade query latency for better recall without paying the rebuild cost. Keeping `ef_construction` moderate avoids long build times while still producing a usable graph structure.

</details>

**Q3. You upgrade the embedding model from `all-MiniLM-L6-v2` to `bge-large-en-v1.5` (different dimension). Why can you not simply add new vectors to the existing Chroma collection, and what is the correct migration approach?**

<details>
<summary>Show answer</summary>

Chroma collections are created with a fixed vector dimension. `all-MiniLM-L6-v2` produces 384-dimensional vectors while `bge-large-en-v1.5` produces 1024-dimensional vectors — these are geometrically incomparable and cannot coexist in the same collection. The correct approach is the blue/green migration pattern: create a new collection, re-embed the entire corpus with the new model, validate recall on a golden query set, then atomically switch traffic to the new collection. Keep the old collection for a rollback window before deleting it.

</details>

**Q4. Your ingestion pipeline runs nightly. One night it silently fails and no new documents are indexed. What monitoring mechanism would detect this within the next morning, and what would it look like?**

<details>
<summary>Show answer</summary>

A **heartbeat / freshness check**: the pipeline writes a timestamp to a heartbeat file (or a metadata record in the collection) upon successful completion. A monitoring job runs each morning and compares `now - last_success_timestamp` against the configured freshness SLO (e.g., 25 hours). If the gap exceeds the SLO, it fires an alert. The alert would appear as: "Ingestion pipeline last succeeded at 2024-01-14 02:15 UTC — 27 hours ago, exceeding the 25-hour SLO." This catches silent failures that produce no error logs.

</details>

**Q5. A team is deciding between pgvector and Qdrant for a new internal knowledge base with ~200K documents. They already run PostgreSQL for their transactional data. Which would you recommend and why?**

<details>
<summary>Show answer</summary>

**pgvector** is the stronger recommendation here. The team already operates PostgreSQL, so pgvector adds zero new infrastructure: same backup tooling (`pg_dump`, WAL archiving), same access controls, same monitoring dashboards. At ~200K documents (roughly 1–2M vectors), pgvector with HNSW performs well within its comfort zone. The ability to do SQL joins between vector search results and transactional data in a single query is a significant advantage for a knowledge base that likely references relational entities (users, projects, etc.). Qdrant becomes the better choice when the team has no existing PostgreSQL or when the workload grows beyond pgvector's single-node limits.

</details>

**Q6. Describe the "shadow collection" migration pattern in three sentences. What is the rollback procedure?**

<details>
<summary>Show answer</summary>

The shadow collection pattern builds a new index (with new model, chunking, or schema) in a separate collection while the current collection continues serving all production traffic. Once the shadow collection passes validation (recall checks, coverage checks), traffic is switched atomically by updating an environment variable or service config to point at the new collection. The old collection is retained for a rollback window (typically 48–72 hours) before being deleted. Rollback is instant at any point before deletion: revert the environment variable to point back at the original collection name.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1. What makes an ingestion pipeline idempotent, and why is idempotency particularly important for scheduled pipelines?**

<details>
<summary>Show answer</summary>

An ingestion pipeline is idempotent when running it N times produces the same result as running it once — no additional records, no modified records, no deleted records unless the source data changed. The key implementation mechanism is a **deterministic chunk ID** derived from the source document path and chunk position (e.g., `sha256(path + "::" + chunk_index)`). When the pipeline uses `upsert` (rather than `add`) with these stable IDs, re-inserting an existing chunk simply overwrites it in place rather than creating a duplicate.

For scheduled pipelines this matters because: (1) pipelines fail and must retry safely; (2) ops teams often run pipelines manually to debug issues; (3) without idempotency, each re-run inflates the index — 7 nightly runs of a 10K-chunk corpus yields 70K chunks, degrading search quality and consuming unbounded storage.

</details>

---

**Q2. Explain the memory impact of HNSW's `M` parameter. A team reports their Qdrant node runs out of memory after doubling the corpus. What is the first parameter to inspect, and what is the trade-off of reducing it?**

<details>
<summary>Show answer</summary>

Each vector in an HNSW graph maintains up to `M` bidirectional edges, each requiring ~8 bytes. The approximate RAM formula is:

```
index_ram ≈ n_vectors × (vector_dim × 4 + M × 8 × 2)
```

So doubling the corpus approximately doubles RAM. With `M=32` (a common "high recall" default), cutting to `M=16` roughly halves the graph overhead, though RAM savings are partially offset by the fixed per-vector dimension cost.

The trade-off: lower `M` reduces connectivity, which can decrease recall at low `ef_search` values. After reducing `M`, the team must rebuild the index (not just insert more vectors) and validate recall on a held-out query set. The mitigation is to increase `ef_search` slightly to compensate — this costs latency rather than memory, which is often the better trade.

</details>

---

**Q3. A Chroma collection has been accumulating vectors for six months. The embedding model is unchanged, but search quality has degraded over time despite the corpus content being stable. What operational cause should you investigate first?**

<details>
<summary>Show answer</summary>

The most likely cause is **HNSW recall decay from incremental insertions**. HNSW builds its graph at insertion time and never restructures existing edges. As more vectors are inserted incrementally, the graph becomes progressively less balanced — new vectors are well-connected to their contemporaries but poorly connected to older parts of the graph. Effective recall therefore drops below the theoretical `ef_search`-predicted recall.

The investigation: measure recall against a golden query set now vs. six months ago. The fix is a **full index rebuild**: export all vectors, drop and recreate the collection with the same parameters, and re-insert. This is why a periodic scheduled full re-index (even if the corpus hasn't changed) is valuable maintenance — it restores optimal graph structure. Chroma does not expose a native "rebuild index" API, so the rebuild must be done by deleting and recreating the collection.

</details>

---

**Q4. You need to change the chunking strategy for an existing corpus (switch from 512-token fixed-size chunks to semantic sentence-boundary chunks). How do you execute this migration without taking the retrieval layer offline?**

<details>
<summary>Show answer</summary>

Use a **blue/green collection migration**:

1. **Build shadow:** Run the new chunking + ingestion pipeline against a new collection (e.g., `hr_corpus_v2`). The current collection (`hr_corpus_v1`) continues serving all production queries.
2. **Validate shadow:** Run your golden query set against both collections and compare recall, precision, and answer quality. Check that chunk counts and document coverage are correct.
3. **Canary switch:** Update the retrieval service config to read from `hr_corpus_v2` (environment variable / feature flag). No data is deleted yet.
4. **Monitor:** Watch query latency and answer-quality metrics for 24–48 hours.
5. **Cutover:** If stable, mark `hr_corpus_v1` as superseded. Delete it after the rollback window expires.

Rollback at any point before step 5 is instant: revert the env var to point back at `hr_corpus_v1`.

</details>

---

**Q5. A junior DevOps engineer proposes running nightly backups of the Chroma persistence directory while the ingestion pipeline may be actively writing. What is the risk, and how do you address it?**

<details>
<summary>Show answer</summary>

The risk is a **torn backup**: the SQLite WAL file (`chroma.sqlite3-wal`) and the segment files can be in an inconsistent state mid-write, producing a backup that silently corrupts on restore. SQLite is designed to recover from crashes using its WAL, but a filesystem-level copy taken mid-write is not guaranteed to be in a recoverable state.

Mitigation options:
1. **Quiesce the pipeline** before backup: add a maintenance-mode flag that pauses the ingestion job during the backup window. Because nightly ingestion is typically a batch job (not a long-lived write stream), this is usually acceptable.
2. **Use SQLite's online backup API** (`VACUUM INTO` or the `sqlite3` backup API) — this is SQLite-safe and works while the database is open.
3. **Move to Qdrant**, which has a native snapshot API (`POST /collections/{name}/snapshots`) that produces a consistent point-in-time snapshot without quiescing.

The key lesson: "it's just a file copy" is not a valid backup strategy for any database, even an embedded one.

</details>

---

**Q6. A team is choosing between Qdrant and pgvector for a 500K-document knowledge base. Their current stack has no PostgreSQL. They anticipate needing horizontal scaling in 12 months. Walk through the capacity-planning and operational considerations that should drive the decision.**

<details>
<summary>Show answer</summary>

**Capacity planning starting point:**

Use the HNSW RAM formula: `index_ram ≈ n_vectors × (dim × 4 + M × 16)`. For 500K documents, ~5 chunks each = 2.5M vectors at 384 dimensions (a common sentence-transformer size) with M=16:

```
2,500,000 × (384 × 4 + 16 × 16) = 2,500,000 × (1,536 + 256) = ~4.5 GB RAM
```

Add 2× headroom for growth and OS overhead: provision a node with ≥ 10 GB RAM for the index alone.

**Qdrant advantages for this scenario:**
- Native horizontal scaling via distributed collections (sharding + replication) — critical for the 12-month growth horizon.
- Built-in snapshot API for consistent point-in-time backups without quiescing writes.
- Payload (metadata) filtering is implemented efficiently inside the HNSW graph, not as a post-filter.
- No dependency on PostgreSQL operational knowledge if the team does not already run it.

**pgvector advantages (not applicable here since no existing Postgres):**
- Zero new infrastructure if already running PostgreSQL — same backup tooling, same access controls, same monitoring.
- ACID transactions: vector upserts and relational data updates in a single transaction.
- Full SQL joins between vector search results and relational tables.

**Decision:** With no existing PostgreSQL and a scaling requirement on the horizon, **Qdrant is the stronger choice**. The team avoids learning PostgreSQL operational patterns and gets native horizontal scaling. If the team later needs SQL joins between vectors and transactional data, a hybrid approach (Qdrant for vectors, Postgres for relational) is common and well-supported via application-layer joins.

**Operational checklist before production:**
- Configure Qdrant with a persistent volume (not in-memory mode).
- Enable the snapshot API and schedule nightly snapshots to object storage.
- Set `on_disk: true` for vectors if RAM is constrained (trades latency for memory).
- Monitor `/metrics` (Prometheus-compatible) for index size, query latency p95, and shard balance.

</details>

---

## 6. Further Reading

> These are referenced in `resources/reading-list.md`. Review the vector DB and ingestion-ops sections.

- **Chroma Documentation** — Persistent client, `upsert`, custom embedding functions, metadata filtering: [docs.trychroma.com](https://docs.trychroma.com)
- **Qdrant Documentation** — HNSW parameter reference, snapshot API, capacity planning: [qdrant.tech/documentation](https://qdrant.tech/documentation)
- **pgvector README** — IVFFlat vs. HNSW options in Postgres: [github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)
- **"HNSW: Hierarchical Navigable Small World Graphs"** (Malkov & Yashunin, 2018) — Algorithm paper: [arXiv:1603.09320](https://arxiv.org/abs/1603.09320)
- **"Revisiting the Inverted Indices for Billion-Scale Approximate Nearest Neighbors"** — IVF scaling study: [arXiv:1802.02422](https://arxiv.org/abs/1802.02422)

---

## 7. Summary

| Topic | Key takeaway |
|---|---|
| Vector DB selection | Match the database to team skills and scale; pgvector wins for Postgres shops; Qdrant for high-performance production; Chroma for dev/small-scale. |
| HNSW params | `M` and `ef_construction` are set at build time and control memory + recall; `ef_search` is tunable per query. |
| Idempotent ingestion | Deterministic chunk IDs + `upsert` = safe to re-run. |
| Incremental re-index | Hash source files; re-embed only changed docs. |
| Backups | Quiesce writes before copying Chroma; use Qdrant snapshot API; leverage `pg_basebackup` for pgvector. |
| Data versioning | Track `embedding_model` in metadata; use blue/green collection migration for model upgrades. |
| Health metrics | Monitor doc count, chunk count, disk size, ingestion freshness, and query latency. |
| Capacity planning | `index_ram ≈ n_vectors × (dim × 4 + M × 16)` bytes; provision 2× headroom for growth. |

**Coming up — Day 10:** Authentication, authorisation, and multi-tenant isolation in AI services.
