"""
Day 2 Lab — Attention from Scratch (SOLUTION)
==============================================
Implements scaled dot-product attention step by step using only NumPy.

Run:
    python labs/common/day-02/solution.py

Dependencies:
    pip install numpy>=1.24.0

No API key required.  No network access required.
"""

import numpy as np

# ─── reproducibility ──────────────────────────────────────────────────────────
np.random.seed(42)

# ─── toy setup ────────────────────────────────────────────────────────────────
TOKENS = ["The", "cat", "sat", "quietly"]
n = len(TOKENS)   # sequence length
d_model = 8       # embedding dimension
d_k = 4           # key/query dimension
d_v = 4           # value dimension

# Simulated token embeddings  shape: (n, d_model)
X = np.random.randn(n, d_model)

# Simulated learned projection matrices
W_Q = np.random.randn(d_model, d_k)
W_K = np.random.randn(d_model, d_k)
W_V = np.random.randn(d_model, d_v)

print("=== Day 2: Scaled Dot-Product Attention from Scratch ===\n")
print(f"Tokens : {TOKENS}")
print(f"d_model: {d_model}   |  d_k: {d_k}   |  d_v: {d_v}\n")


# ─── helper ───────────────────────────────────────────────────────────────────

def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """Numerically stable softmax."""
    x_shifted = x - x.max(axis=axis, keepdims=True)  # stability: subtract max
    exp_x = np.exp(x_shifted)
    return exp_x / exp_x.sum(axis=axis, keepdims=True)


def scaled_dot_product_attention(
    Q: np.ndarray,
    K: np.ndarray,
    V: np.ndarray,
    mask: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Scaled dot-product attention.

    Args:
        Q: Query matrix  (seq_len, d_k)
        K: Key matrix    (seq_len, d_k)
        V: Value matrix  (seq_len, d_v)
        mask: Boolean mask (seq_len, seq_len).  True = keep, False = mask out.

    Returns:
        output:  (seq_len, d_v) — context-aware token representations
        weights: (seq_len, seq_len) — attention weight matrix
    """
    d_k = Q.shape[-1]

    # Step 1: raw scores — how relevant is each key to each query?
    scores = Q @ K.T                          # (n, n)

    # Step 2: scale to keep variance ~1 regardless of d_k
    scores = scores / np.sqrt(d_k)

    # Step 3: optional causal mask (decoder mode)
    if mask is not None:
        scores = np.where(mask, scores, -1e9)

    # Step 4: softmax → attention weights (each row sums to 1)
    weights = softmax(scores, axis=-1)        # (n, n)

    # Step 5: weighted blend of value vectors
    output = weights @ V                      # (n, d_v)

    return output, weights


def print_weight_matrix(
    weights: np.ndarray,
    tokens: list[str],
    title: str,
) -> None:
    """Pretty-print an (n, n) attention weight matrix with token labels."""
    print(f"--- {title} ---")
    print(f"shape: {weights.shape}")
    col_width = max(len(t) for t in tokens) + 2
    header = " " * (col_width + 2) + "  ".join(f"{t:>{col_width}}" for t in tokens)
    print(header)
    for i, token in enumerate(tokens):
        row = "  ".join(f"{weights[i, j]:{col_width}.4f}" for j in range(len(tokens)))
        print(f"{token:<{col_width}} [ {row} ]")
    # Verify rows sum to 1
    row_sums = weights.sum(axis=-1)
    assert np.allclose(row_sums, 1.0), f"Row sums not 1: {row_sums}"
    print(f"(row sums: all ≈ 1.0 ✓)\n")


# ─── PART 1: Bidirectional attention (encoder style) ─────────────────────────

# Project embeddings into Q, K, V
Q = X @ W_Q   # (4, 4)
K = X @ W_K   # (4, 4)
V = X @ W_V   # (4, 4)

# Compute attention (no mask — every token sees every other)
output_bi, weights_bi = scaled_dot_product_attention(Q, K, V)

print_weight_matrix(weights_bi, TOKENS, "Bidirectional attention weights (encoder style)")

print("--- Context-aware output vectors (bidirectional) ---")
print(f"shape: {output_bi.shape}")
print(np.round(output_bi, 4))
print()

# What this shows: each row tells you how token i distributed attention across
# all tokens.  High values = "token i paid a lot of attention to that column token."


# ─── PART 2: Causal masked attention (decoder style) ─────────────────────────

# Lower-triangular mask: position i can only see positions j <= i
causal_mask = np.tril(np.ones((n, n), dtype=bool))
# causal_mask[i][j] = True  iff j <= i  (allowed to attend)

output_causal, weights_causal = scaled_dot_product_attention(Q, K, V, mask=causal_mask)

print("=== Causal (decoder-style) masked attention ===")
print_weight_matrix(weights_causal, TOKENS, "Causal attention weights (future tokens blocked)")

print("--- Context-aware output vectors (causal) ---")
print(f"shape: {output_causal.shape}")
print(np.round(output_causal, 4))
print()

# What this shows:
#   - "The" (row 0) can only attend to itself → weight[0][0] = 1.0
#   - "cat" (row 1) attends to "The" and "cat"
#   - "quietly" (row 3) attends to all four tokens
# This is exactly how GPT/Claude-style models generate text left-to-right.


# ─── PART 3: Interpretation ──────────────────────────────────────────────────

print("=== Interpretation ===")
print("For each token (row), which other token does it attend to most?\n")
for i, token in enumerate(TOKENS):
    top_j = int(np.argmax(weights_bi[i]))
    print(
        f"  {token!r:10} attends most to {TOKENS[top_j]!r:10} "
        f"(weight: {weights_bi[i, top_j]:.4f})"
    )

print()
print("Note: weights are determined by LEARNED W_Q / W_K matrices.")
print("In this demo they are random — in a real model they encode grammar, semantics, etc.")
print()
print("=== Lab complete. See curriculum/Day-02-transformers-attention.md for theory. ===")
