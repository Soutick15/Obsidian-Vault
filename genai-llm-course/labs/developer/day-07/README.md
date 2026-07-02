# Day 7 Lab — End-to-End RAG over the HR Corpus

**Track:** Developer | **Day:** 7 | **Estimated time:** 75 min

---

## Goal

Build a complete Retrieval-Augmented Generation pipeline over Acme Corp's HR document corpus:

1. **Load** — read all Markdown files from `data/hr-corpus/`
2. **Chunk** — split documents into fixed-size chunks with overlap
3. **Embed** — encode chunks locally with `sentence-transformers` (no API key needed)
4. **Store** — persist in a Chroma vector collection
5. **Retrieve** — embed a question and fetch the top-k most relevant chunks
6. **Augment** — build a grounded prompt injecting retrieved context + source metadata
7. **Generate** — produce a cited answer (Claude / OpenAI if key is set, else deterministic mock)

The lab runs **fully offline with no API key** via the mock generator.

---

## Setup

```bash
# From the repo root
pip install -r labs/developer/day-07/requirements.txt
```

---

## Running

### Offline (mock generator — no key required)

```bash
python labs/developer/day-07/solution.py
```

### With Claude (Anthropic key)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python labs/developer/day-07/solution.py
```

### With OpenAI

```bash
export OPENAI_API_KEY="sk-..."
python labs/developer/day-07/solution.py
```

### Custom question

```bash
python labs/developer/day-07/solution.py --question "What is the home office setup stipend?"
```

---

## Example Questions (from corpus README)

These questions are all answerable from the corpus:

1. `"How many PTO days do new employees get in their first two years?"`
2. `"What is the parental leave policy for a non-birth parent?"`
3. `"How much does Acme Corp match on 401(k) contributions?"`
4. `"What are the password and MFA requirements for company accounts?"`

---

## Starter vs Solution

| File | Purpose |
|---|---|
| `starter.py` | Skeleton with `# TODO` markers — fill in the blanks |
| `solution.py` | Complete working implementation |

Work through `starter.py` first. Run `solution.py` if you get stuck.

---

## Expected Output (mock path)

```
=== RAG System: Acme Corp HR Assistant ===
Generator: MOCK (no API key detected)
Corpus: /path/to/data/hr-corpus  (12 documents)

[INGESTION]
Loaded 12 documents
Split into 87 chunks (size=400, overlap=80)
Embedded 87 chunks with all-MiniLM-L6-v2
Stored in Chroma collection: hr_rag_day07

[QUERY]
Question: How many PTO days do new employees get in their first two years?

[RETRIEVED CHUNKS]
  #1 (score=0.87) leave-and-pto-policy.md
  #2 (score=0.81) leave-and-pto-policy.md
  #3 (score=0.74) employee-handbook-overview.md

[ANSWER]
Based on the provided HR documents:

New employees at Acme Corp receive 15 days (120 hours) of PTO in their first two years of employment. ...

Sources: leave-and-pto-policy.md, employee-handbook-overview.md
```

---

## Key Parameters to Experiment With

| Parameter | Default | Effect |
|---|---|---|
| `CHUNK_SIZE` | 400 | Larger = more context per chunk, less precise retrieval |
| `CHUNK_OVERLAP` | 80 | Higher = better boundary coverage, more storage |
| `TOP_K` | 4 | More chunks = higher recall, more context tokens |
| Embedding model | `all-MiniLM-L6-v2` | Swap for `all-mpnet-base-v2` for higher quality |
