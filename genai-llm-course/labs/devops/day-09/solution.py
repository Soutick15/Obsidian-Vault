"""
Day 9 Lab — Solution: Operable Ingestion & Index Pipeline
==========================================================
Track: DevOps | No API key required.

Run with:
    python solution.py

Demonstrates:
  (a) Idempotent ingestion — re-run never duplicates chunks
  (b) Incremental re-index — only changed documents are re-embedded
  (c) Backup + restore — tarball snapshot of the Chroma persistence dir
  (d) Index health metrics — doc count, chunk count, on-disk size
"""

from __future__ import annotations

import hashlib
import logging
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
from chromadb import Collection
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CORPUS_DIR = Path(__file__).resolve().parents[3] / "data" / "hr-corpus"
STORE_DIR = Path(__file__).parent / ".chroma_day09"
COLLECTION_NAME = "hr_corpus"

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Embedding function — deterministic hash-based, no model download, no API key.
#
# Each text is hashed with SHA-256; the 32-byte digest is mapped to a unit
# vector of dimension DIM. This is purely for the ops pipeline exercises
# (idempotency, backup/restore, health metrics). It does NOT produce
# semantically meaningful embeddings — replace with sentence-transformers
# or an API embedding model before using in a real retrieval system.
# ---------------------------------------------------------------------------
EMBEDDING_DIM = 64  # small for fast local operation


class DeterministicHashEmbedding(EmbeddingFunction):
    """Zero-dependency local embedding: SHA-256 digest → unit float vector."""

    def __init__(self) -> None:
        pass  # required by Chroma's EmbeddingFunction contract

    def __call__(self, input: Documents) -> Embeddings:
        results: Embeddings = []
        for text in input:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            # Repeat digest to fill EMBEDDING_DIM floats (each byte → float)
            raw = list(digest) * (EMBEDDING_DIM // len(digest) + 1)
            floats = [float(b - 128) for b in raw[:EMBEDDING_DIM]]
            # Normalise to unit vector
            norm = sum(x * x for x in floats) ** 0.5 or 1.0
            results.append([x / norm for x in floats])
        return results


DEFAULT_EF = DeterministicHashEmbedding()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def chunk_id(source: str, chunk_index: int) -> str:
    """
    Deterministic 16-character hex ID derived from source path + chunk index.
    Using sha256 ensures collision resistance across all corpus documents.
    """
    key = f"{source}::{chunk_index}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def load_corpus(corpus_dir: Path) -> list[dict]:
    """
    Load all .md files from corpus_dir (excluding README.md).
    Returns list of dicts: {path, name, text, content_hash}
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
    breaking on whitespace where possible to avoid mid-word splits.
    """
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            ws = text.rfind(" ", start, end)
            if ws > start:
                end = ws
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end
    return chunks


# ---------------------------------------------------------------------------
# Core pipeline functions
# ---------------------------------------------------------------------------

def ingest(collection: Collection, corpus_dir: Path) -> int:
    """
    Ingest all documents from corpus_dir into collection via upsert.

    Idempotency mechanism: each chunk receives a deterministic ID from
    chunk_id(source_filename, chunk_index). Upsert overwrites an existing
    record rather than creating a duplicate, so re-running is safe.

    Returns the total number of chunks upserted.
    """
    docs = load_corpus(corpus_dir)
    now = datetime.now(timezone.utc).isoformat()
    total = 0

    for doc in docs:
        chunks = split_into_chunks(doc["text"])
        ids = [chunk_id(doc["name"], i) for i in range(len(chunks))]
        metadatas = [
            {
                "source": doc["name"],
                "chunk_index": i,
                "content_hash": doc["content_hash"],
                "indexed_at": now,
            }
            for i in range(len(chunks))
        ]
        collection.upsert(
            ids=ids,
            documents=chunks,
            metadatas=metadatas,
        )
        total += len(chunks)

    return total


def _ingest_single_doc(collection: Collection, doc: dict) -> int:
    """Helper: ingest a single document dict into collection. Returns chunk count."""
    now = datetime.now(timezone.utc).isoformat()
    chunks = split_into_chunks(doc["text"])
    ids = [chunk_id(doc["name"], i) for i in range(len(chunks))]
    metadatas = [
        {
            "source": doc["name"],
            "chunk_index": i,
            "content_hash": doc["content_hash"],
            "indexed_at": now,
        }
        for i in range(len(chunks))
    ]
    collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)


def incremental_reindex(collection: Collection, corpus_dir: Path) -> dict[str, int]:
    """
    Re-index only documents whose content hash has changed since last ingest.

    Algorithm:
    1. Load current file hashes from disk.
    2. For each document, fetch the stored content_hash from collection metadata.
    3. If hash differs (or document not yet indexed), re-embed and upsert.
    4. Return {"changed": N, "unchanged": M}.
    """
    docs = load_corpus(corpus_dir)
    changed = 0
    unchanged = 0

    for doc in docs:
        # Fetch one record for this source to get its stored hash
        results = collection.get(
            where={"source": doc["name"]},
            limit=1,
            include=["metadatas"],
        )
        stored_hash: str | None = None
        if results["metadatas"]:
            stored_hash = results["metadatas"][0].get("content_hash")

        if stored_hash != doc["content_hash"]:
            log.info("  Re-indexing changed document: %s", doc["name"])
            _ingest_single_doc(collection, doc)
            changed += 1
        else:
            unchanged += 1

    log.info(
        "Incremental re-index complete: %d changed, %d unchanged",
        changed,
        unchanged,
    )
    return {"changed": changed, "unchanged": unchanged}


def backup(store_dir: Path) -> Path:
    """
    Create a timestamped gzip-compressed tarball of the Chroma persistence dir.

    The backup is written to store_dir.parent so it is not nested inside
    the store directory itself.

    Returns the Path of the created tarball.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = store_dir.parent / f"chroma_backup_{timestamp}.tar.gz"

    with tarfile.open(backup_path, "w:gz") as tar:
        # arcname=store_dir.name preserves the directory structure inside the tarball
        tar.add(store_dir, arcname=store_dir.name)

    log.info("Backup written → %s (%.1f KB)", backup_path.name, backup_path.stat().st_size / 1024)
    return backup_path


def restore(backup_path: Path, store_dir: Path) -> None:
    """
    Restore a Chroma store from a backup tarball.

    Steps:
    1. Remove existing store directory (if any).
    2. Extract the tarball into store_dir.parent so the store directory
       is recreated in the correct location.
    """
    if store_dir.exists():
        log.info("Removing existing store at %s", store_dir)
        shutil.rmtree(store_dir)

    log.info("Restoring from %s...", backup_path.name)
    with tarfile.open(backup_path, "r:gz") as tar:
        tar.extractall(path=store_dir.parent, filter="data")

    log.info("Restore complete → %s", store_dir)


# ---------------------------------------------------------------------------
# Health metrics
# ---------------------------------------------------------------------------

def health_metrics(collection: Collection, store_dir: Path, label: str = "") -> None:
    """Print key health metrics for the index."""
    chunk_count = collection.count()

    # Unique source documents from metadata
    results = collection.get(include=["metadatas"])
    sources = (
        {m.get("source") for m in results["metadatas"]}
        if results["metadatas"]
        else set()
    )
    doc_count = len(sources)

    # On-disk size of the persistence directory
    total_bytes = (
        sum(f.stat().st_size for f in store_dir.rglob("*") if f.is_file())
        if store_dir.exists()
        else 0
    )
    size_kb = total_bytes // 1024

    prefix = f"HEALTH ({label})" if label else "HEALTH"
    log.info(
        "%s — docs: %d, chunks: %d, store_size_kb: %d",
        prefix,
        doc_count,
        chunk_count,
        size_kb,
    )


# ---------------------------------------------------------------------------
# Chroma client factory
# ---------------------------------------------------------------------------

def get_collection(store_dir: Path) -> tuple[Any, Collection]:
    """Return a (client, collection) pair backed by a persistent store."""
    client = chromadb.PersistentClient(path=str(store_dir))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=DEFAULT_EF,
    )
    return client, collection


# ---------------------------------------------------------------------------
# Main demonstration
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("=== Day 9 Lab — Operable Ingestion & Index Pipeline ===")
    log.info("Corpus: %s", CORPUS_DIR)
    log.info("Store:  %s", STORE_DIR)

    if not CORPUS_DIR.exists():
        raise FileNotFoundError(f"HR corpus not found at {CORPUS_DIR}")

    # Start from a clean slate for repeatable demo
    if STORE_DIR.exists():
        shutil.rmtree(STORE_DIR)

    # =========================================================
    # Step 1 — Initial ingestion
    # =========================================================
    log.info("--- Step 1: Initial ingestion ---")
    _, collection = get_collection(STORE_DIR)
    n = ingest(collection, CORPUS_DIR)
    log.info("Ingested %d chunks (first run)", n)
    health_metrics(collection, STORE_DIR, "after first ingest")

    # =========================================================
    # Step 2 — Idempotency check
    # =========================================================
    log.info("--- Step 2: Idempotency check (re-run ingestion) ---")
    # Re-open a fresh client to avoid any in-memory caching effects
    _, collection = get_collection(STORE_DIR)
    n2 = ingest(collection, CORPUS_DIR)
    log.info("Re-ingested %d chunks (should equal %d)", n2, n)
    health_metrics(collection, STORE_DIR, "after second ingest")

    if n2 == n:
        log.info("Idempotency check PASSED ✓  (chunk count unchanged)")
    else:
        log.error("Idempotency FAILED: first=%d, second=%d", n, n2)
        raise AssertionError(f"Idempotency failed: {n} vs {n2}")

    # =========================================================
    # Step 3 — Incremental re-index
    # =========================================================
    log.info("--- Step 3: Incremental re-index ---")
    target = CORPUS_DIR / "leave-and-pto-policy.md"
    original_text = target.read_text(encoding="utf-8")
    # Simulate an edit to exactly one document
    target.write_text(original_text + "\n<!-- simulated update -->", encoding="utf-8")

    try:
        _, collection = get_collection(STORE_DIR)
        result = incremental_reindex(collection, CORPUS_DIR)
        health_metrics(collection, STORE_DIR, "after incremental")

        assert result.get("changed") == 1, f"Expected 1 changed doc, got {result}"
        assert result.get("unchanged") == 11, f"Expected 11 unchanged, got {result}"
        log.info("Incremental re-index check PASSED ✓")
    finally:
        # Always restore the original file so the corpus is not permanently modified
        target.write_text(original_text, encoding="utf-8")

    # =========================================================
    # Step 4 — Backup
    # =========================================================
    log.info("--- Step 4: Backup ---")
    backup_path = backup(STORE_DIR)
    assert backup_path.exists(), "Backup file missing"

    # =========================================================
    # Step 5 — Restore
    # =========================================================
    log.info("--- Step 5: Wipe store and restore ---")
    shutil.rmtree(STORE_DIR)
    log.info("Store wiped. Restoring...")
    restore(backup_path, STORE_DIR)

    _, collection = get_collection(STORE_DIR)
    health_metrics(collection, STORE_DIR, "post-restore")
    restored_count = collection.count()

    if restored_count == n:
        log.info("Backup/restore check PASSED ✓  (%d chunks restored)", restored_count)
    else:
        log.error("Restore FAILED: expected %d chunks, got %d", n, restored_count)
        raise AssertionError(f"Restore failed: expected {n} chunks, got {restored_count}")

    log.info("=== All checks passed. Day 9 lab complete. ===")


if __name__ == "__main__":
    main()
