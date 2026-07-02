"""
Day 9 Lab — Starter: Operable Ingestion & Index Pipeline
=========================================================
Track: DevOps | No API key required.

Fill in every section marked  TODO  to complete the lab.
Run with:
    python starter.py

Expected final output:
    HEALTH — docs: 12, chunks: <N>, store_size_kb: <X>   (same after re-run)
    Incremental re-index: 1 document changed, 11 unchanged
    Backup written → chroma_backup_<timestamp>.tar.gz
    HEALTH (post-restore) — docs: 12, chunks: <N>, store_size_kb: <X>
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
from chromadb import Collection
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# HR corpus lives 3 levels above labs/devops/day-09/  →  data/hr-corpus/
CORPUS_DIR = Path(__file__).resolve().parents[3] / "data" / "hr-corpus"
STORE_DIR = Path(__file__).parent / ".chroma_day09"
COLLECTION_NAME = "hr_corpus"

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Embedding function — deterministic hash-based, no model download, no API key.
# Produces unit vectors from SHA-256 digests for ops pipeline exercises.
# Replace with sentence-transformers for real semantic retrieval.
# ---------------------------------------------------------------------------
EMBEDDING_DIM = 64


class DeterministicHashEmbedding(EmbeddingFunction):
    """Zero-dependency local embedding: SHA-256 digest → unit float vector."""

    def __init__(self) -> None:
        pass  # required by Chroma's EmbeddingFunction contract

    def __call__(self, input: Documents) -> Embeddings:
        results: Embeddings = []
        for text in input:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            raw = list(digest) * (EMBEDDING_DIM // len(digest) + 1)
            floats = [float(b - 128) for b in raw[:EMBEDDING_DIM]]
            norm = sum(x * x for x in floats) ** 0.5 or 1.0
            results.append([x / norm for x in floats])
        return results


DEFAULT_EF = DeterministicHashEmbedding()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def chunk_id(source: str, chunk_index: int) -> str:
    """
    TODO 1 — Return a deterministic 16-character hex string.

    Requirements:
    - Input key: f"{source}::{chunk_index}"
    - Hash with SHA-256
    - Return the first 16 hex characters of the digest

    This stable ID makes upsert idempotent: re-inserting the same chunk
    overwrites it in place rather than creating a duplicate.

    Example:
        chunk_id("leave-and-pto-policy.md", 0) → "3f8a..." (16 chars)
    """
    # TODO 1 — implement here
    raise NotImplementedError("TODO 1: implement chunk_id")


def load_corpus(corpus_dir: Path) -> list[dict]:
    """
    Load all .md files from corpus_dir (excluding README.md).
    Returns a list of dicts: {path, name, text, content_hash}
    """
    docs = []
    for p in sorted(corpus_dir.glob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        text = p.read_text(encoding="utf-8")
        content_hash = hashlib.md5(text.encode()).hexdigest()
        docs.append({"path": p, "name": p.name, "text": text, "content_hash": content_hash})
    return docs


def split_into_chunks(text: str, chunk_size: int = 300) -> list[str]:
    """
    Split text into non-overlapping chunks of ~chunk_size characters,
    breaking on whitespace where possible.
    """
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # try to break on a whitespace boundary
            ws = text.rfind(" ", start, end)
            if ws > start:
                end = ws
        chunks.append(text[start:end].strip())
        start = end
    return [c for c in chunks if c]


# ---------------------------------------------------------------------------
# Core pipeline functions
# ---------------------------------------------------------------------------

def ingest(collection: Collection, corpus_dir: Path) -> int:
    """
    TODO 2 — Ingest all documents from corpus_dir into collection.

    Requirements:
    1. Load all .md files (use load_corpus and split_into_chunks).
    2. For each chunk build:
         - id:        chunk_id(doc["name"], chunk_index)
         - document:  the chunk text
         - metadata:  {"source": doc["name"],
                        "chunk_index": chunk_index,
                        "content_hash": doc["content_hash"],
                        "indexed_at": <ISO-8601 UTC string>}
    3. Upsert in batches (use collection.upsert).
    4. Return the total number of chunks upserted.

    Because chunk IDs are deterministic and you use upsert (not add),
    re-running this function must produce the same collection state.
    """
    # TODO 2 — implement here
    raise NotImplementedError("TODO 2: implement ingest")


def incremental_reindex(collection: Collection, corpus_dir: Path) -> dict[str, int]:
    """
    TODO 3 — Re-index only documents whose content has changed.

    Algorithm:
    1. Load all docs from corpus_dir.
    2. For each doc, retrieve the stored content_hash from the collection
       by fetching metadata where source == doc["name"] (limit=1 is enough).
       Use: collection.get(where={"source": doc["name"]}, limit=1, include=["metadatas"])
    3. If the stored hash differs from the current file hash (or no record
       exists), call ingest for that document only.
    4. Track and log how many documents were re-indexed vs. unchanged.
    5. Return {"changed": N, "unchanged": M}.

    Tip: you can reuse ingest() but pass a single-element list instead of
    the full corpus — or call collection.upsert directly for just that doc.
    """
    # TODO 3 — implement here
    raise NotImplementedError("TODO 3: implement incremental_reindex")


def backup(store_dir: Path) -> Path:
    """
    TODO 4a — Create a timestamped tarball backup of store_dir.

    Requirements:
    - Filename: chroma_backup_<YYYYMMDD_HHMMSS>.tar.gz  (in store_dir.parent)
    - Use tarfile.open in "w:gz" mode
    - Return the Path to the created tarball

    Note: In production you would quiesce writes first. For this lab,
    the ingestion pipeline is not running concurrently so a direct copy is safe.
    """
    # TODO 4a — implement here
    raise NotImplementedError("TODO 4a: implement backup")


def restore(backup_path: Path, store_dir: Path) -> None:
    """
    TODO 4b — Restore a Chroma store from a backup tarball.

    Requirements:
    1. Delete store_dir if it exists (shutil.rmtree).
    2. Extract the tarball into store_dir.parent using tarfile.open "r:gz".
    3. Log the restore completion.
    """
    # TODO 4b — implement here
    raise NotImplementedError("TODO 4b: implement restore")


# ---------------------------------------------------------------------------
# TODO 5 — Health metrics
# ---------------------------------------------------------------------------
# Implement health_metrics(collection, store_dir, label="") that prints:
#   - doc_count  : number of unique source documents in the collection
#                  (count distinct values of the "source" metadata key)
#   - chunk_count: total number of vectors/chunks (collection.count())
#   - store_size_kb: total on-disk size of store_dir in KiB
#                    (sum f.stat().st_size for f in store_dir.rglob("*") if f.is_file())
# Log with: log.info("%s — docs: %d, chunks: %d, store_size_kb: %d",
#                    prefix, doc_count, count, size_kb)
# where prefix = f"HEALTH ({label})" if label else "HEALTH"

def health_metrics(collection: Collection, store_dir: Path, label: str = "") -> None:
    """Print key health metrics for the collection."""
    # TODO 5 — implement here
    raise NotImplementedError("TODO 5: implement health_metrics")


# ---------------------------------------------------------------------------
# Chroma client factory
# ---------------------------------------------------------------------------

def get_collection(store_dir: Path) -> tuple[Any, Collection]:
    """Return a (client, collection) pair for the persistent store."""
    client = chromadb.PersistentClient(path=str(store_dir))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=DEFAULT_EF,
    )
    return client, collection


# ---------------------------------------------------------------------------
# Main exercise flow
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("=== Day 9 Lab — Ingestion Pipeline ===")
    log.info("Corpus: %s", CORPUS_DIR)
    log.info("Store:  %s", STORE_DIR)

    # Clean slate for demo purposes
    if STORE_DIR.exists():
        shutil.rmtree(STORE_DIR)

    # ---- Step 1: First ingestion ----
    log.info("--- Step 1: Initial ingestion ---")
    _, collection = get_collection(STORE_DIR)
    n = ingest(collection, CORPUS_DIR)
    log.info("Ingested %d chunks (first run)", n)
    health_metrics(collection, STORE_DIR, "after first ingest")

    # ---- Step 2: Idempotency check ----
    log.info("--- Step 2: Idempotency check (re-run ingestion) ---")
    _, collection = get_collection(STORE_DIR)
    n2 = ingest(collection, CORPUS_DIR)
    log.info("Re-ingested %d chunks (should equal %d)", n2, n)
    health_metrics(collection, STORE_DIR, "after second ingest")
    assert n2 == n, f"Idempotency FAILED: first={n}, second={n2}"
    log.info("Idempotency check PASSED ✓")

    # ---- Step 3: Incremental re-index ----
    log.info("--- Step 3: Incremental re-index ---")
    # Simulate a document change by appending a newline
    target = CORPUS_DIR / "leave-and-pto-policy.md"
    original_text = target.read_text(encoding="utf-8")
    target.write_text(original_text + "\n<!-- simulated update -->", encoding="utf-8")

    try:
        _, collection = get_collection(STORE_DIR)
        result = incremental_reindex(collection, CORPUS_DIR)
        log.info("Incremental result: %s", result)
        assert result.get("changed") == 1, f"Expected 1 changed doc, got {result}"
        assert result.get("unchanged") == 11, f"Expected 11 unchanged, got {result}"
        log.info("Incremental re-index check PASSED ✓")
        health_metrics(collection, STORE_DIR, "after incremental")
    finally:
        # Restore original file
        target.write_text(original_text, encoding="utf-8")

    # ---- Step 4: Backup ----
    log.info("--- Step 4: Backup ---")
    backup_path = backup(STORE_DIR)
    log.info("Backup written → %s", backup_path.name)
    assert backup_path.exists(), "Backup file not found"

    # ---- Step 5: Restore ----
    log.info("--- Step 5: Wipe store and restore from backup ---")
    shutil.rmtree(STORE_DIR)
    restore(backup_path, STORE_DIR)
    _, collection = get_collection(STORE_DIR)
    health_metrics(collection, STORE_DIR, "post-restore")
    restored_count = collection.count()
    assert restored_count == n, f"Restore FAILED: expected {n} chunks, got {restored_count}"
    log.info("Backup/restore check PASSED ✓")

    log.info("=== All checks passed. Lab complete. ===")


if __name__ == "__main__":
    main()
