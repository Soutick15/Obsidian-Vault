# Day 2 Lab — Attention from Scratch

## Objective

Make self-attention concrete by implementing the three core steps of
scaled dot-product attention in NumPy on toy embedding vectors: compare
(`Q · Kᵀ`), scale + turn into weights (`softmax(scores / √d_k)`), and blend
(`weights · V`).

This is the same three-step pattern from the Day 2 Worked Example — see
`curriculum/common/Day-02-transformers-attention.md`, Section 3, "The real
version (what the lab uses)".

The `softmax` helper and the Q/K/V projections are already provided in
`starter.py`. You only need to fill in the four required TODOs:

1. `scores = Q @ K.T`
2. `scores_scaled = scores / sqrt(d_k)`
3. `weights = softmax(scores_scaled)`
4. `output = weights @ V`

An Optional / Bonus section (causal masking) is at the end of `starter.py` —
it is not required to finish the lab.

No API key required. No network access required. Only NumPy.

## Setup

```bash
# From the repo root (or this directory):
pip install -r labs/common/day-02/requirements.txt
```

## Running the Lab

**Starter (fill in the TODOs):**
```bash
python labs/common/day-02/starter.py
```

**Reference solution:**
```bash
python labs/common/day-02/solution.py
```

## Expected Output

The lab seeds NumPy's random generator (`np.random.seed(42)`), so the numbers
below are deterministic — your output should match this exactly once the
required TODOs are filled in correctly.

```
=== Day 2: Scaled Dot-Product Attention from Scratch ===

Tokens : ['The', 'cat', 'sat', 'quietly']
d_model: 8   |  d_k: 4   |  d_v: 4

--- Bidirectional attention weights (encoder style) ---
shape: (4, 4)
                 The        cat        sat    quietly
The       [    0.1125     0.0038     0.4562     0.4276 ]
cat       [    0.0248     0.6162     0.0000     0.3590 ]
sat       [    0.0000     0.1477     0.8514     0.0009 ]
quietly   [    0.9936     0.0002     0.0000     0.0062 ]
(row sums: all ≈ 1.0 ✓)

--- Context-aware output vectors (bidirectional) ---
shape: (4, 4)
[[-0.2656  1.247  -1.7113 -0.2598]
 [-1.3262  2.649  -4.7311  0.2527]
 [-1.782   0.4248  0.9401  0.8662]
 [ 2.3123  0.2939 -0.4525 -2.8146]]
```

> Note: `starter.py` prints the raw scores and weights/output separately
> (without the "bidirectional" framing used above) — the numbers themselves
> are identical, since both scripts compute the same thing on the same seed.
> `solution.py` additionally labels this as "Part 1: Bidirectional attention".

## Bonus: Causal Masking

If you complete the optional causal-mask section at the bottom of
`starter.py` (or run `solution.py`, which includes it), you'll see:

```
=== Causal (decoder-style) masked attention ===
--- Causal attention weights (future tokens blocked) ---
shape: (4, 4)
                 The        cat        sat    quietly
The       [    1.0000     0.0000     0.0000     0.0000 ]
cat       [    0.0386     0.9614     0.0000     0.0000 ]
sat       [    0.0000     0.1478     0.8521     0.0000 ]
quietly   [    0.9936     0.0002     0.0000     0.0062 ]
(row sums: all ≈ 1.0 ✓)

--- Context-aware output vectors (causal) ---
shape: (4, 4)
[[ 2.3242  0.2779 -0.4182 -2.828 ]
 [-2.3766  2.5733 -4.116   0.83  ]
 [-1.784   0.4227  0.9462  0.8676]
 [ 2.3123  0.2939 -0.4525 -2.8146]]
```

Notice the upper-right triangle is all zeros — each word is blocked from
attending to words that come after it, exactly what makes decoder-only
generation (GPT, Claude) work one token at a time.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'numpy'` | Dependencies not installed, or installed into the wrong environment | Run `pip install -r labs/common/day-02/requirements.txt` (activate your virtual environment first, if you're using one) |
| `command not found: python` | Some systems only have `python3` on PATH | Use `python3` instead of `python` |
| `FileNotFoundError` / `can't open file 'starter.py'` | Running the command from the wrong directory | `cd labs/common/day-02` and run `python starter.py`, or use the full path `python labs/common/day-02/starter.py` from the repo root |
| Your numbers don't match this README at all (not just unfilled) | A TODO was filled in with the wrong operation, or `np.random.seed(42)` was edited/removed | Diff your TODOs against `solution.py`; the seed line must stay exactly as given |
| `AttributeError: 'NoneType' object has no attribute 'shape'` | A TODO above the failing line hasn't been filled in yet | Fill in TODOs in order, top to bottom — later steps depend on earlier ones |

## Bonus: HuggingFace Real Attention

After completing the main lab, try `bonus_hf.py`.

**The bonus requires additional dependencies NOT included in `requirements.txt`.**
Install them separately before running:

```bash
pip install torch>=2.0.0 transformers>=4.40.0
python labs/common/day-02/bonus_hf.py
```

This loads `distilgpt2`, runs a sentence through it with `output_attentions=True`,
and prints the attention weight matrix for head 0 of layer 0.
If torch or transformers are not installed, the script prints a friendly message and exits.
