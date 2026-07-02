"""
Day 8 Lab — Advanced RAG: Hybrid Search + Cross-Encoder Re-ranking
=================================================================
Starter file with TODO markers.  Complete each TODO in order.

Run from repo root:
    python labs/developer/day-08/starter.py

No API key required — all models run locally.
"""

from __future__ import annotations

import re
import math
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Corpus path — resolves regardless of where you cd to
# ---------------------------------------------------------------------------
CORPUS_DIR = Path(__file__).resolve().parents[3] / "data" / "hr-corpus"

# ---------------------------------------------------------------------------
# Evaluation set  (query -> expected source filename stem)
# Built from the HR corpus README example questions
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


# ===========================================================================
# TODO 1 — Load and chunk the HR corpus
# ===========================================================================
# Steps:
#   a) Iterate over all *.md files in CORPUS_DIR (excluding README.md)
#   b) Split each document into chunks of ~300 characters with ~50-char overlap
#      (use a simple character-level sliding window or split on "\n\n")
#   c) Return a list of dicts:  {"text": str, "source": str (filename stem), "chunk_id": str}
#
# Starter hint:
#   for path in sorted(CORPUS_DIR.glob("*.md")):
#       if path.stem.lower() == "readme": continue
#       text = path.read_text(encoding="utf-8")
#       ... split into chunks ...

def load_and_chunk(chunk_size: int = 400, overlap: int = 80) -> list[dict]:
    """Load all HR corpus documents and split into overlapping text chunks."""
    # TODO 1: implement this function
    raise NotImplementedError("TODO 1: implement load_and_chunk()")


# ===========================================================================
# TODO 2 — Build a Chroma collection with dense embeddings
# ===========================================================================
# Steps:
#   a) Import chromadb and sentence_transformers
#   b) Create an in-memory Chroma client and a collection named "hr_day08"
#   c) Embed all chunks with SentenceTransformer("all-MiniLM-L6-v2")
#   d) Add chunks to the collection with ids, embeddings, documents, and metadatas
#   e) Return (collection, embedding_model)

def build_chroma_index(chunks: list[dict]):
    """Return (chroma_collection, embedding_model)."""
    # TODO 2: implement this function
    raise NotImplementedError("TODO 2: implement build_chroma_index()")


# ===========================================================================
# TODO 3 — Build a BM25 index from the same chunks
# ===========================================================================
# Steps:
#   a) Import BM25Okapi from rank_bm25
#   b) Tokenise each chunk's text (lowercase + split on whitespace/punctuation)
#   c) Build and return a BM25Okapi object
#
# Keep a parallel list `bm25_chunks` so you can map BM25 scores back to chunk dicts.

def build_bm25_index(chunks: list[dict]):
    """Return (BM25Okapi, tokenised_corpus_list)."""
    # TODO 3: implement this function
    raise NotImplementedError("TODO 3: implement build_bm25_index()")


# ===========================================================================
# TODO 4 — Dense retrieval using Chroma
# ===========================================================================
# Steps:
#   a) Embed the query with the same SentenceTransformer model
#   b) Query the Chroma collection for n_results candidates
#   c) Return list of chunk dicts in ranked order
#
# Chroma returns results["documents"], results["metadatas"], results["distances"]

def dense_retrieve(query: str, collection, embed_model, n: int = 20) -> list[dict]:
    """Return top-n chunks from the dense (Chroma) index."""
    # TODO 4: implement this function
    raise NotImplementedError("TODO 4: implement dense_retrieve()")


# ===========================================================================
# TODO 5 — BM25 retrieval
# ===========================================================================
# Steps:
#   a) Tokenise the query the same way you tokenised the corpus
#   b) Call bm25.get_scores(tokenised_query) to get a score per chunk
#   c) Sort by descending score; return top-n chunk dicts

def bm25_retrieve(query: str, bm25, chunks: list[dict], n: int = 20) -> list[dict]:
    """Return top-n chunks from the BM25 (sparse) index."""
    # TODO 5: implement this function
    raise NotImplementedError("TODO 5: implement bm25_retrieve()")


# ===========================================================================
# TODO 6 — Hybrid retrieval via Reciprocal Rank Fusion (RRF)
# ===========================================================================
# Steps:
#   a) Call dense_retrieve() and bm25_retrieve() each for top-N candidates
#   b) For each unique chunk_id, compute its RRF score:
#        rrf_score = sum( 1 / (k + rank) ) for each list it appears in
#      where k=60, rank is 1-indexed position in that list
#   c) Sort by descending RRF score; return top-n chunk dicts

RRF_K = 60

def hybrid_rrf(
    query: str,
    collection,
    embed_model,
    bm25,
    chunks: list[dict],
    n: int = 20,
) -> list[dict]:
    """Return top-n chunks fused via Reciprocal Rank Fusion."""
    # TODO 6: implement this function
    raise NotImplementedError("TODO 6: implement hybrid_rrf()")


# ===========================================================================
# TODO 7 — Cross-encoder re-ranking
# ===========================================================================
# Steps:
#   a) from sentence_transformers import CrossEncoder
#   b) Load CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
#   c) Build pairs = [(query, chunk["text"]) for chunk in candidates]
#   d) scores = cross_encoder.predict(pairs)
#   e) Sort candidates by descending score; return top_k

def load_cross_encoder():
    """Load and return the cross-encoder model."""
    # TODO 7a: implement this function
    raise NotImplementedError("TODO 7a: implement load_cross_encoder()")


def rerank(query: str, candidates: list[dict], cross_encoder, top_k: int = 5) -> list[dict]:
    """Re-rank candidates with the cross-encoder; return top_k."""
    # TODO 7b: implement this function
    raise NotImplementedError("TODO 7b: implement rerank()")


# ===========================================================================
# TODO 8 — Evaluation: Hit@k
# ===========================================================================
# Steps:
#   a) For each (query, expected_source) in EVAL_SET:
#        - Run naive_top5  = dense_retrieve(..., n=5)
#        - Run hybrid_top20 = hybrid_rrf(..., n=20)
#        - Run reranked_top5 = rerank(query, hybrid_top20, cross_encoder, top_k=5)
#   b) Check if expected_source appears in the "source" metadata of top-k results
#   c) Count hits at k=1, 3, 5 for both pipelines
#   d) Print a comparison table

def evaluate(collection, embed_model, bm25, chunks, cross_encoder):
    """Run the eval set and print Hit@k comparison."""
    # TODO 8: implement this function
    raise NotImplementedError("TODO 8: implement evaluate()")


# ===========================================================================
# Main
# ===========================================================================

def main():
    print(f"Loading HR corpus from: {CORPUS_DIR}")
    chunks = load_and_chunk()
    print(f"Loaded {len(set(c['source'] for c in chunks))} documents | {len(chunks)} chunks")

    print("\nBuilding Chroma index (dense)...")
    collection, embed_model = build_chroma_index(chunks)

    print("Building BM25 index (sparse)...")
    bm25, _ = build_bm25_index(chunks)

    print("Loading cross-encoder: cross-encoder/ms-marco-MiniLM-L-6-v2")
    cross_encoder = load_cross_encoder()

    print("\n=== Retrieval Evaluation ===")
    evaluate(collection, embed_model, bm25, chunks, cross_encoder)


if __name__ == "__main__":
    main()
