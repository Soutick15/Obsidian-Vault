# Day 8 Lab — Advanced RAG: Hybrid Search + Cross-Encoder Re-ranking

**Track:** Developer | **Prerequisite:** Day 7 (Basic RAG with Chroma)

---

## What You'll Build

An improved RAG retrieval pipeline over the Acme Corp HR corpus that:

1. **Naive baseline** — dense-only retrieval using `sentence-transformers` + Chroma (same as Day 7)
2. **Hybrid retrieval** — fuse BM25 (rank_bm25) + dense scores via Reciprocal Rank Fusion (RRF)
3. **Cross-encoder re-ranking** — re-sort the hybrid top-N with `ms-marco-MiniLM-L-6-v2`
4. **Evaluation** — compute Hit@1, Hit@3, Hit@5 for naive vs. hybrid+rerank on a labeled eval set

No API key required. No generation step. All local.

---

## Setup

From the repo root:

```bash
pip install -r labs/developer/day-08/requirements.txt
```

---

## Files

| File | Purpose |
|---|---|
| `README.md` | This file |
| `requirements.txt` | Python dependencies |
| `starter.py` | Skeleton with TODO markers — your starting point |
| `solution.py` | Complete reference implementation |

---

## Running

```bash
# Attempt the lab yourself:
python labs/developer/day-08/starter.py

# Check against the full solution:
python labs/developer/day-08/solution.py
```

Run from the **repo root** so relative paths resolve correctly.

---

## Expected Output (solution.py)

```
Loading HR corpus from: .../data/hr-corpus
Loaded 12 documents | 47 chunks

Building Chroma index (dense)...
Building BM25 index (sparse)...
Loading cross-encoder: cross-encoder/ms-marco-MiniLM-L-6-v2

=== Retrieval Evaluation — 7 labeled queries ===

Query: "How many PTO days do new employees get?"
  Naive  top-3 docs: ['leave-and-pto-policy', ...]
  Hybrid top-3 docs: ['leave-and-pto-policy', ...]
  Expected: leave-and-pto-policy

...

=== Hit@k Summary ===
              Naive   Hybrid+Rerank
Hit@1:         X/7      X/7
Hit@3:         X/7      X/7
Hit@5:         X/7      X/7
```

(Exact numbers depend on the chunking and local model but Hybrid+Rerank should equal or beat Naive on every k.)

---

## Lab Tasks (starter.py TODOs)

1. **TODO 1** — Load and chunk the HR corpus documents
2. **TODO 2** — Build a Chroma collection with dense embeddings
3. **TODO 3** — Build a BM25 index from the same chunks
4. **TODO 4** — Implement `dense_retrieve(query, k)` using Chroma
5. **TODO 5** — Implement `bm25_retrieve(query, k)` using rank_bm25
6. **TODO 6** — Implement `hybrid_rrf(query, n)` fusing both retrievers via RRF
7. **TODO 7** — Load the cross-encoder and implement `rerank(query, candidates, top_k)`
8. **TODO 8** — Evaluate naive vs. hybrid+rerank using Hit@k on the labeled eval set

---

## Key Concepts Practised

- Reciprocal Rank Fusion (RRF)
- Bi-encoder vs. cross-encoder retrieval
- Hit@k evaluation without a generation step
- Two-stage retrieve-then-rerank pipeline
