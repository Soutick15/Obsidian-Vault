# Day 6 Lab — Embeddings & Vector Search

## Objective

Build a local semantic search engine over the Acme Corp HR corpus using:

- **`sentence-transformers`** (`all-MiniLM-L6-v2`, runs entirely on your machine — no API key)
- **Chroma** as the persistent vector database
- **NumPy** for utility calculations

You will ingest 12 HR markdown documents, embed them at the paragraph level, store them in Chroma, and run semantic queries that retrieve the most relevant passages with similarity scores.

No API key required. All computation is local.

---

## Files

| File | Purpose |
|---|---|
| `README.md` | This file |
| `requirements.txt` | Python dependencies |
| `starter.py` | Skeleton with `TODO` comments — work through these |
| `solution.py` | Complete reference implementation — run to verify expected output |

---

## Setup

```bash
# From the repo root — create a virtual environment for this lab
python -m venv labs/developer/day-06/.venv
source labs/developer/day-06/.venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r labs/developer/day-06/requirements.txt
```

> **Note:** First run downloads the `all-MiniLM-L6-v2` model (~22 MB) from Hugging Face.
> Subsequent runs use the cached copy. No network calls at inference time.

---

## Run the solution

```bash
# From the repo root
python labs/developer/day-06/solution.py
```

---

## Expected output (approximate)

```
[1/3] Loading HR corpus from data/hr-corpus/ ...
  Loaded 12 documents, 147 chunks total

[2/3] Embedding chunks and storing in Chroma ...
  Collection 'hr-corpus-day06' ready (147 vectors, 384 dimensions)

[3/3] Running semantic queries ...

=== Query 1: "What is the parental leave policy?" ===
  [0.88] leave-and-pto-policy.md  | Acme Corp provides 16 weeks of fully paid parental leave ...
  [0.81] leave-and-pto-policy.md  | Secondary caregivers (non-birth parents, adoptive parents) ...
  [0.72] benefits-and-insurance.md | The Employee Assistance Program (EAP) also supports ...

=== Query 2: "How does the 401(k) match work?" ===
  [0.92] benefits-and-insurance.md | Acme Corp matches 100% of employee contributions up to 4% ...
  ...

=== Query 5 (metadata filter — leave-and-pto-policy.md only): "sick days" ===
  Filtering to source: leave-and-pto-policy.md
  [0.84] leave-and-pto-policy.md  | Employees accrue 10 days of sick leave per calendar year ...
  ...

Done. Chroma DB persisted at labs/developer/day-06/.chroma_db/
```

*(Exact similarity scores depend on model version; the ranking pattern should match.)*

---

## Tasks (starter.py TODOs)

1. **TODO 1** — Locate the HR corpus directory using `pathlib`.
2. **TODO 2** — Load each `.md` file and split into paragraph chunks; attach `source` metadata.
3. **TODO 3** — Load `all-MiniLM-L6-v2` from `sentence_transformers`.
4. **TODO 4** — Create or retrieve a persistent Chroma collection.
5. **TODO 5** — Embed all chunks and `upsert` them into Chroma with IDs and metadata.
6. **TODO 6** — Embed a query string and call `collection.query()` for top-k results; print scores.
7. **TODO 7** — Add a metadata `where` filter to restrict results to one source document.

---

## Concepts practiced

- Paragraph-level chunking and its effect on retrieval precision
- Local embedding with `sentence-transformers` (no API calls)
- Chroma collection lifecycle: create / persist / reuse
- Cosine similarity scores in Chroma's distance notation (lower = more similar)
- Metadata filtering with `where` clauses

---

## Extension challenges

- Add chunk overlap (repeat the last sentence of chunk N as the first sentence of chunk N+1) and compare retrieval quality.
- Run all 10 example questions from `data/hr-corpus/README.md` and evaluate whether the correct source document is in top-3.
- Swap the embedding model to `all-mpnet-base-v2` (768 dims) and compare scores.
- Implement a simple re-ranker: retrieve top-20 by cosine, then re-rank by BM25 keyword score.
