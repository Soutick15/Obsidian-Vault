"""
Day 8 Lab — Advanced RAG: Hybrid Search + Cross-Encoder Re-ranking
=================================================================
COMPLETE SOLUTION.  No API key required — all models run locally.

Run from repo root:
    python labs/developer/day-08/solution.py
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Corpus path
# ---------------------------------------------------------------------------
CORPUS_DIR = Path(__file__).resolve().parents[3] / "data" / "hr-corpus"

# ---------------------------------------------------------------------------
# Evaluation set  (query -> expected source filename stem)
# ---------------------------------------------------------------------------
EVAL_SET = [
    ("How many PTO days do new employees get in their first two years?", "leave-and-pto-policy"),
    ("What is the parental leave policy for a non-birth parent?", "leave-and-pto-policy"),
    ("How much does Acme Corp match on 401k contributions?", "benefits-and-insurance"),
    ("What is the home office setup stipend for new remote employees?", "remote-work-policy"),
    ("How does the employee referral bonus work and how much is it?", "recruitment-and-hiring-process"),
    ("What are the password and MFA requirements for company accounts?", "it-and-security-policy"),
    ("When do merit increases take effect?", "performance-review-process"),
]

RRF_K = 60


# ---------------------------------------------------------------------------
# 1. Load and chunk
# ---------------------------------------------------------------------------

def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Sliding-window character chunking that respects paragraph boundaries where possible."""
    # Split on double newlines to get paragraphs first
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            # If a single paragraph exceeds chunk_size, split it by character
            if len(para) > chunk_size:
                for start in range(0, len(para), chunk_size - overlap):
                    chunks.append(para[start : start + chunk_size])
            else:
                current = para
    if current:
        chunks.append(current)
    return [c for c in chunks if c.strip()]


def load_and_chunk(chunk_size: int = 400, overlap: int = 80) -> list[dict]:
    """Load all HR corpus *.md files (excluding README) and chunk them."""
    all_chunks: list[dict] = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        if path.stem.lower() == "readme":
            continue
        text = path.read_text(encoding="utf-8")
        pieces = _chunk_text(text, chunk_size, overlap)
        for i, piece in enumerate(pieces):
            all_chunks.append(
                {
                    "text": piece,
                    "source": path.stem,
                    "chunk_id": f"{path.stem}__{i}",
                }
            )
    return all_chunks


# ---------------------------------------------------------------------------
# 2. Chroma dense index
# ---------------------------------------------------------------------------

def build_chroma_index(chunks: list[dict]):
    """Embed all chunks and load into an in-memory Chroma collection."""
    import chromadb
    from sentence_transformers import SentenceTransformer

    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [c["text"] for c in chunks]
    embeddings = embed_model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

    client = chromadb.Client()
    # Drop existing collection if re-running
    try:
        client.delete_collection("hr_day08")
    except Exception:
        pass
    collection = client.create_collection("hr_day08", metadata={"hnsw:space": "cosine"})

    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=[{"source": c["source"], "chunk_id": c["chunk_id"]} for c in chunks],
    )
    return collection, embed_model


# ---------------------------------------------------------------------------
# 3. BM25 index
# ---------------------------------------------------------------------------

def _tokenise(text: str) -> list[str]:
    """Lowercase + split on non-alphanumeric characters."""
    return re.findall(r"[a-z0-9]+", text.lower())


def build_bm25_index(chunks: list[dict]):
    """Build a BM25Okapi index over all chunks."""
    from rank_bm25 import BM25Okapi

    tokenised = [_tokenise(c["text"]) for c in chunks]
    bm25 = BM25Okapi(tokenised)
    return bm25, tokenised


# ---------------------------------------------------------------------------
# 4. Dense retrieval
# ---------------------------------------------------------------------------

def dense_retrieve(query: str, collection, embed_model, n: int = 20) -> list[dict]:
    """Retrieve top-n chunks by dense cosine similarity."""
    q_emb = embed_model.encode([query], convert_to_numpy=True)
    results = collection.query(
        query_embeddings=q_emb.tolist(),
        n_results=min(n, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    candidates: list[dict] = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        candidates.append(
            {
                "text": doc,
                "source": meta["source"],
                "chunk_id": meta["chunk_id"],
            }
        )
    return candidates


# ---------------------------------------------------------------------------
# 5. BM25 retrieval
# ---------------------------------------------------------------------------

def bm25_retrieve(query: str, bm25, chunks: list[dict], n: int = 20) -> list[dict]:
    """Retrieve top-n chunks by BM25 score."""
    tokens = _tokenise(query)
    scores = bm25.get_scores(tokens)
    ranked_indices = np.argsort(scores)[::-1][:n]
    return [chunks[i] for i in ranked_indices]


# ---------------------------------------------------------------------------
# 6. Hybrid RRF
# ---------------------------------------------------------------------------

def hybrid_rrf(
    query: str,
    collection,
    embed_model,
    bm25,
    chunks: list[dict],
    n: int = 20,
) -> list[dict]:
    """Fuse dense and BM25 rankings via Reciprocal Rank Fusion."""
    dense_results = dense_retrieve(query, collection, embed_model, n=n)
    bm25_results = bm25_retrieve(query, bm25, chunks, n=n)

    rrf_scores: dict[str, float] = {}
    chunk_by_id: dict[str, dict] = {}

    for rank, chunk in enumerate(dense_results, start=1):
        cid = chunk["chunk_id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (RRF_K + rank)
        chunk_by_id[cid] = chunk

    for rank, chunk in enumerate(bm25_results, start=1):
        cid = chunk["chunk_id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (RRF_K + rank)
        chunk_by_id[cid] = chunk

    sorted_ids = sorted(rrf_scores, key=lambda cid: rrf_scores[cid], reverse=True)
    return [chunk_by_id[cid] for cid in sorted_ids[:n]]


# ---------------------------------------------------------------------------
# 7. Cross-encoder re-ranking
# ---------------------------------------------------------------------------

def load_cross_encoder():
    """Load the MS MARCO cross-encoder (downloads once, cached locally)."""
    from sentence_transformers import CrossEncoder
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank(query: str, candidates: list[dict], cross_encoder, top_k: int = 5) -> list[dict]:
    """Score (query, chunk) pairs with the cross-encoder; return top_k."""
    if not candidates:
        return []
    pairs = [(query, c["text"]) for c in candidates]
    scores = cross_encoder.predict(pairs)
    ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
    return [c for _, c in ranked[:top_k]]


# ---------------------------------------------------------------------------
# 8. Evaluation
# ---------------------------------------------------------------------------

def _hit_at_k(results: list[dict], expected_source: str, k: int) -> bool:
    return any(c["source"] == expected_source for c in results[:k])


def evaluate(collection, embed_model, bm25, chunks, cross_encoder):
    """Run Hit@1/3/5 comparison: naive dense vs. hybrid+rerank."""
    ks = [1, 3, 5]
    naive_hits = {k: 0 for k in ks}
    hybrid_hits = {k: 0 for k in ks}

    print(f"\n{'Query':<55} {'Expected Source':<35} Naive/Hybrid")
    print("-" * 105)

    for query, expected in EVAL_SET:
        naive_top5 = dense_retrieve(query, collection, embed_model, n=5)
        hybrid_top20 = hybrid_rrf(query, collection, embed_model, bm25, chunks, n=20)
        reranked_top5 = rerank(query, hybrid_top20, cross_encoder, top_k=5)

        naive_src = [c["source"] for c in naive_top5[:3]]
        hybrid_src = [c["source"] for c in reranked_top5[:3]]

        for k in ks:
            if _hit_at_k(naive_top5, expected, k):
                naive_hits[k] += 1
            if _hit_at_k(reranked_top5, expected, k):
                hybrid_hits[k] += 1

        # Short display
        q_short = query[:52] + "..." if len(query) > 55 else query
        naive_hit3 = "HIT" if _hit_at_k(naive_top5, expected, 3) else "miss"
        hybrid_hit3 = "HIT" if _hit_at_k(reranked_top5, expected, 3) else "miss"
        print(f"  {q_short:<55} {expected:<35} {naive_hit3} / {hybrid_hit3}")

    n = len(EVAL_SET)
    print()
    print("=" * 60)
    print(f"{'Metric':<15} {'Naive Dense':>15} {'Hybrid+Rerank':>15}")
    print("-" * 45)
    for k in ks:
        naive_pct = naive_hits[k] / n
        hybrid_pct = hybrid_hits[k] / n
        delta = hybrid_pct - naive_pct
        arrow = "+" if delta > 0 else ("=" if delta == 0 else "-")
        print(
            f"  Hit@{k}        "
            f"  {naive_hits[k]}/{n} ({naive_pct:.0%})   "
            f"  {hybrid_hits[k]}/{n} ({hybrid_pct:.0%})  {arrow}{abs(delta):.0%}"
        )
    print("=" * 60)
    print("\nNote: Hybrid+Rerank should match or exceed Naive on all Hit@k metrics.")
    print("(Small corpus: differences may be modest, but the pipeline is correct.)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Loading HR corpus from: {CORPUS_DIR}")
    if not CORPUS_DIR.exists():
        raise FileNotFoundError(
            f"HR corpus not found at {CORPUS_DIR}. "
            "Run from repo root or check CORPUS_DIR path."
        )

    chunks = load_and_chunk()
    n_docs = len(set(c["source"] for c in chunks))
    print(f"Loaded {n_docs} documents | {len(chunks)} chunks")

    print("\nBuilding Chroma index (dense)...")
    collection, embed_model = build_chroma_index(chunks)

    print("Building BM25 index (sparse)...")
    bm25, _ = build_bm25_index(chunks)

    print("Loading cross-encoder: cross-encoder/ms-marco-MiniLM-L-6-v2")
    cross_encoder = load_cross_encoder()

    print(f"\n=== Retrieval Evaluation — {len(EVAL_SET)} labeled queries ===")
    evaluate(collection, embed_model, bm25, chunks, cross_encoder)


if __name__ == "__main__":
    main()
