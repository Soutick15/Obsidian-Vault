# Day 9 Lab — Operable Ingestion & Index Pipeline

**Track:** DevOps | **Estimated time:** 60–70 minutes
**Prerequisites:** Python 3.11+, `pip install -r requirements.txt`
**API key required:** None — fully local

---

## What you will build

An operable ingestion pipeline for the 12-document Acme HR corpus into a local Chroma vector store with four production-ready properties:

| Capability | What it means |
|---|---|
| **Idempotent ingestion** | Re-running the pipeline never duplicates chunks |
| **Incremental re-index** | Only changed documents are re-embedded on subsequent runs |
| **Backup + restore** | The Chroma store can be snapshotted and restored from a tarball |
| **Index health metrics** | Pipeline prints doc count, chunk count, and on-disk size |

---

## Setup

```bash
# from repo root
cd labs/devops/day-09
pip install -r requirements.txt
```

No `.env` file needed — no API key is used. The lab uses Chroma's built-in embedding function so no external model download is required.

---

## Running the lab

```bash
# Run the solution (complete implementation)
python solution.py

# Run your own work from starter.py
python starter.py
```

Expected output (abridged):

```
[INFO] Ingesting HR corpus (first run)...
[INFO] Ingested 12 documents → N chunks
[INFO] HEALTH — docs: 12, chunks: N, store_size_kb: X

[INFO] Re-running ingestion (idempotency check)...
[INFO] HEALTH — docs: 12, chunks: N, store_size_kb: X   ← same chunk count

[INFO] Simulating document change (leave-and-pto-policy.md)...
[INFO] Incremental re-index: 1 document changed, 11 unchanged
[INFO] HEALTH — docs: 12, chunks: N, store_size_kb: X

[INFO] Performing backup...
[INFO] Backup written → chroma_backup_<timestamp>.tar.gz

[INFO] Wiping store and restoring from backup...
[INFO] Restore complete.
[INFO] HEALTH (post-restore) — docs: 12, chunks: N, store_size_kb: X
```

---

## File structure

```
labs/devops/day-09/
├── README.md           ← this file
├── requirements.txt    ← pip dependencies
├── starter.py          ← skeleton with TODO markers (your work)
└── solution.py         ← complete reference implementation
```

The pipeline stores its Chroma data in `.chroma_day09/` (relative to where you run the script) and backup tarballs in the same directory. Both are excluded from source control via `.gitignore`.

---

## Tasks

Work through `starter.py` filling in the four TODO sections:

1. **`chunk_id(source, chunk_index)`** — Return a deterministic 16-character hex ID from `sha256(source + "::" + chunk_index)`.
2. **`ingest(collection, corpus_dir)`** — Load each `.md` file, split into ~300-char chunks, build metadata (including `content_hash` and `indexed_at`), and `upsert` with stable IDs.
3. **`incremental_reindex(collection, corpus_dir)`** — Compare current file hash to stored `content_hash` in metadata; re-embed only changed documents; report how many were re-indexed.
4. **`backup(store_dir)`** and **`restore(backup_path, store_dir)`** — Tar/untar the Chroma persistence directory.

The `health_metrics(collection, store_dir)` function is provided for you — use it after each step to observe the state of the index.

---

## Key concepts practised

- Deterministic chunk IDs for idempotent upsert
- Content-hash-based change detection
- Chroma `PersistentClient` and `EmbeddingFunction` API
- File-level backup and restore of an embedded vector store
- Index health metrics as an operational observable

---

## Stretch goals (optional, no starter scaffolding)

- Add an `indexed_at` freshness check that prints a warning for any document older than N hours.
- Expose the health metrics as a Prometheus-format text file (`/metrics` endpoint) using `http.server`.
- Implement orphan detection: if a document is deleted from the corpus, remove its chunks from the collection.
