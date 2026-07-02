# Day 1 Lab — Tokenisation & Embedding Similarity

## Objective

Practice the two most fundamental LLM primitives:

1. **Tokenisation** — use `tiktoken` to count tokens and observe that token count ≠ word count.
2. **Semantic embeddings** — use `sentence-transformers` (local, no API key) to embed sentences and compute a cosine-similarity matrix, confirming that semantically related sentences score higher.

## Setup

```bash
# From this directory
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

No API keys required. All computation runs locally.

## Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Pinned dependencies (tiktoken, sentence-transformers, numpy) |
| `starter.py` | Skeleton with TODOs — start here |
| `solution.py` | Complete working solution — run to verify expected output |

## Run the solution

```bash
python solution.py
```

## Expected output (approximate)

```
=== Part A: Tokenisation ===
Encoding: cl100k_base

Text: "Hello, world!"
  Words : 2
  Tokens: 4
  Token IDs: [9906, 11, 1917, 0]

Text: "Tokenisation is surprisingly nuanced."
  Words : 4
  Tokens: 7
  Token IDs: [3...

Text: "GPT-4 uses cl100k_base tokenisation."
  Words : 5
  Tokens: 9

Text: "日本語のテキスト (Japanese text) costs more tokens per character."
  Words : 9
  Tokens: 24

Text: "def calculate_embedding_similarity(vec_a, vec_b):"
  Words : 1
  Tokens: 11

Ratio summary:
  Avg tokens/word across all samples: ~1.8
  Rule of thumb: 1 token ≈ 0.75 words (so ratio ≈ 1.33)
  Non-English & code inflate the ratio above the English baseline.

=== Part B: Embedding Similarity ===
Model: all-MiniLM-L6-v2  (384-dimensional vectors, runs locally)

Sentences:
  [0] "A cat is sleeping on the sofa."
  [1] "The kitten napped on the couch."
  [2] "Dogs love to play fetch in the park."
  [3] "Financial markets surged on positive earnings."
  [4] "Puppies enjoy chasing balls outdoors."

Cosine Similarity Matrix (rounded to 2 dp):
         [0]   [1]   [2]   [3]   [4]
  [0]   1.00  0.87  0.38  0.06  0.33
  [1]   0.87  1.00  0.36  0.05  0.30
  [2]   0.38  0.36  1.00  0.07  0.83
  [3]   0.06  0.05  0.07  1.00  0.09
  [4]   0.33  0.30  0.83  0.09  1.00

Key observations:
  Highest similarity: [0] vs [1] = 0.87  ("cat/sofa" ≈ "kitten/couch")
  Dogs/puppies pair : [2] vs [4] = 0.83  (same topic)
  Finance vs pets  : [3] vs [0] = 0.06  (unrelated domains)
```

*(Exact values depend on model version; the pattern — related sentences score higher — should hold.)*

## What to explore next

- Add your own sentences to the list and re-run.
- Change the encoding in Part A to `gpt2` and compare token counts.
- Try a very long document and observe how quickly you approach context limits.
