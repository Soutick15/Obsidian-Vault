# Day 1 Lab — Tokenisation & Embedding Similarity

## Objective

Practice the two calculations walked through by hand in curriculum Day-01 §3 (Worked Example):

1. **Tokenisation** — use `tiktoken` to count tokens and observe that token count ≠ word count.
2. **Semantic embeddings** — use `sentence-transformers` (local, no API key) to embed sentences and compute a cosine-similarity matrix, confirming that semantically related sentences score higher.

If anything below doesn't click, re-read curriculum Day-01 §3 first — the lab is the same two calculations at a larger scale, just done in code instead of by hand.

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
| `starter.py` | Tokenizer and embedding model are already loaded for you; fill in 3 TODOs |
| `solution.py` | Complete working solution — run to verify expected output |

The 3 TODOs in `starter.py` are: (1) count tokens for a string, (2) compute cosine similarity between two embeddings, (3) build the full similarity matrix. Each TODO's docstring points back to the matching part of curriculum §3.

## Run the solution

```bash
python solution.py
```

## Expected output

This is real output from running `solution.py`. Exact numbers depend on the installed model/library versions, so treat this as the pattern to expect (related sentences score highest, unrelated ones score lowest) rather than exact values to match.

```
=== Part A: Tokenisation ===
Encoding: o200k_base

Text: "Hello, world!"
  Words : 2
  Tokens: 4
  Token IDs: [13225, 11, 2375, 0]

Text: "Tokenisation is surprisingly nuanced."
  Words : 4
  Tokens: 6
  Token IDs: [4421, 6993, 382, 50999, 174421, 13]

Text: "GPT-4o uses o200k_base tokenisation."
  Words : 4
  Tokens: 12
  Token IDs: [162016, 12, 19, 78, 8844, 293, 1179, 74]...

Text: "日本語のテキスト (Japanese text) costs more tokens per character."
  Words : 8
  Tokens: 16
  Token IDs: [9048, 40909, 3385, 16056, 18368, 38236, 350, 103871]...

Text: "def calculate_embedding_similarity(vec_a, vec_b):"
  Words : 3
  Tokens: 10
  Token IDs: [1314, 17950, 122618, 198666, 57650, 10852, 11, 10563]...

Ratio summary:
  Avg tokens/word across all samples: 2.37
  Rule of thumb: 1 token ≈ 0.75 words (ratio ≈ 1.33) for English.
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
          [0]    [1]    [2]    [3]    [4]
  [0]    1.00  0.69  -0.01  -0.07  -0.05
  [1]    0.69  1.00  0.09  -0.04  0.10
  [2]    -0.01  0.09  1.00  0.03  0.53
  [3]    -0.07  -0.04  0.03  1.00  0.06
  [4]    -0.05  0.10  0.53  0.06  1.00

Key observations:
  Highest similarity: [0] vs [1] = 0.69
    "A cat is sleeping on the sofa."
    "The kitten napped on the couch."

  Dogs/puppies pair: [2] vs [4] = 0.53  (same topic, different words)
  Finance vs cats:   [3] vs [0] = -0.07  (unrelated domains)

Takeaway: semantically similar sentences cluster near 1.0; unrelated ones drop toward 0.
```

**Reading the matrix:** the diagonal is always 1.00 (a sentence compared with itself). The cat/kitten pair `[0]` vs `[1]` and the dogs/puppies pair `[2]` vs `[4]` are the two highest off-diagonal scores — both pairs describe the same kind of scene in different words. The finance sentence `[3]` scores lowest against every pet sentence, because it is about an unrelated topic. This is the same "arrows pointing the same direction vs. arrows pointing apart" idea from curriculum §2.4/§3.2, just with 384-dimensional vectors instead of the 2-D toy example.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: python` | Use `python3` instead of `python`, or check your Python installation is on PATH. |
| `ModuleNotFoundError` for tiktoken / sentence_transformers / numpy | Your virtual environment isn't active, or dependencies weren't installed. Run `source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows), then `pip install -r requirements.txt` again. |
| First run of `solution.py` hangs or is slow | `sentence-transformers` downloads the `all-MiniLM-L6-v2` model (~90 MB) the first time it runs. This requires an internet connection and only happens once — later runs load the cached copy and start instantly. |
| No internet access / fully offline machine | Ask your instructor for a pre-downloaded model cache, or run this lab on a machine with internet access once to populate the cache (usually `~/.cache/huggingface`), then copy that folder to the offline machine. |
| `pip install` fails with a permissions or "externally managed environment" error | Make sure your virtual environment is active (you should see `(.venv)` in your prompt) before running `pip install`. Never install directly into your system Python. |
| Output numbers don't exactly match this README | Expected — see the note above the output block. The pattern (related sentences score highest, unrelated lowest) is what matters, not the exact decimals. |

## What to explore next

- Add your own sentences to the list and re-run.
- Try a very long document and observe how quickly you approach context limits (curriculum §2.5).
- Compare a sentence against a paraphrase of itself vs. against a sentence on a completely different topic, and predict the similarity score before running the code.
