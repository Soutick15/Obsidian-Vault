# Day 2 Lab — Attention from Scratch

## Objective

Make self-attention concrete by implementing scaled dot-product attention
in NumPy on toy embedding vectors.  You will:

1. Project token embeddings into Q, K, V using random weight matrices.
2. Compute raw attention scores as Q · Kᵀ.
3. Scale, (optionally) mask, and apply softmax to get attention weights.
4. Compute the weighted output (attention weights · V).
5. Print the attention weight matrix and the output vectors.

No API key required.  No network access required.  Only NumPy.

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

```
=== Day 2: Scaled Dot-Product Attention from Scratch ===

Tokens : ['The', 'cat', 'sat', 'quietly']
d_model: 8   |  d_k: 4   |  d_v: 4

--- Raw attention scores (Q · Kᵀ) ---
shape: (4, 4)
[[ ...  ...  ...  ...]
 [ ...  ...  ...  ...]
 [ ...  ...  ...  ...]
 [ ...  ...  ...  ...]]

--- Attention weights after softmax (each row sums to 1) ---
shape: (4, 4)
         The    cat    sat  quietly
The   [ 0.xx   0.xx   0.xx   0.xx ]
cat   [ 0.xx   0.xx   0.xx   0.xx ]
sat   [ 0.xx   0.xx   0.xx   0.xx ]
quietly[ 0.xx  0.xx   0.xx   0.xx ]

--- Context-aware output vectors ---
shape: (4, 4)
Each row is the weighted blend of V vectors for that token.

=== Causal (decoder-style) masked attention ===
--- Masked attention weights (upper triangle zeroed) ---
         The    cat    sat  quietly
The   [ 1.00   0.00   0.00   0.00 ]
cat   [ 0.xx   0.xx   0.00   0.00 ]
sat   [ 0.xx   0.xx   0.xx   0.00 ]
quietly[ 0.xx  0.xx   0.xx   0.xx ]
```

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
