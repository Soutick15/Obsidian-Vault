"""
Day 2 Lab — Attention from Scratch (STARTER)
=============================================
Goal: implement scaled dot-product attention step by step using NumPy.

Instructions:
  - Find every comment that starts with  # TODO  and fill in the code.
  - Run with:  python labs/common/day-02/starter.py
  - Compare your output against labs/common/day-02/README.md (Expected Output section).
  - If you get stuck, check solution.py — but try first!
"""

import numpy as np

# ─── reproducibility ──────────────────────────────────────────────────────────
np.random.seed(42)

# ─── toy setup ────────────────────────────────────────────────────────────────
TOKENS = ["The", "cat", "sat", "quietly"]
n = len(TOKENS)   # sequence length: 4
d_model = 8       # embedding dimension
d_k = 4           # key/query projection dimension
d_v = 4           # value projection dimension

# Simulate token embeddings (in a real model these come from an embedding table)
X = np.random.randn(n, d_model)  # shape: (4, 8)

# Learned projection weight matrices (in a real model these are trained)
W_Q = np.random.randn(d_model, d_k)   # (8, 4)
W_K = np.random.randn(d_model, d_k)   # (8, 4)
W_V = np.random.randn(d_model, d_v)   # (8, 4)

print("=== Day 2: Scaled Dot-Product Attention from Scratch ===\n")
print(f"Tokens : {TOKENS}")
print(f"d_model: {d_model}   |  d_k: {d_k}   |  d_v: {d_v}\n")


# ─── STEP 1: Compute Q, K, V projections ─────────────────────────────────────
# TODO: project X through W_Q, W_K, W_V to get Q, K, V
#       shapes should be (n, d_k), (n, d_k), (n, d_v) respectively
Q = None  # TODO
K = None  # TODO
V = None  # TODO


# ─── STEP 2: Raw attention scores ────────────────────────────────────────────
# TODO: compute scores = Q · Kᵀ
#       shape should be (n, n)
#       scores[i][j] = "how much does token i want to attend to token j?"
scores = None  # TODO

print("--- Raw attention scores (Q · Kᵀ) ---")
print(f"shape: {scores.shape}")
print(np.round(scores, 3), "\n")


# ─── STEP 3: Scale ────────────────────────────────────────────────────────────
# TODO: divide scores by sqrt(d_k) to keep gradients healthy
scores_scaled = None  # TODO


# ─── STEP 4: Softmax → attention weights ──────────────────────────────────────
def softmax(x, axis=-1):
    """Numerically stable softmax along the given axis."""
    # TODO: implement softmax
    # Hint: subtract the max along `axis` first for numerical stability,
    #       then exponentiate, then divide by the sum.
    pass  # TODO


weights = softmax(scores_scaled, axis=-1)  # shape: (n, n)

print("--- Attention weights after softmax (each row sums to 1) ---")
print(f"shape: {weights.shape}")
# Pretty-print with token labels
header = "         " + "  ".join(f"{t:>7}" for t in TOKENS)
print(header)
for i, token in enumerate(TOKENS):
    row = "  ".join(f"{weights[i, j]:7.4f}" for j in range(n))
    print(f"{token:<8} [ {row} ]")
print()

# Sanity check: each row should sum to 1.0
assert np.allclose(weights.sum(axis=-1), 1.0), "Rows must sum to 1!"


# ─── STEP 5: Weighted sum of values ──────────────────────────────────────────
# TODO: compute output = weights · V
#       shape should be (n, d_v)
output = None  # TODO

print("--- Context-aware output vectors ---")
print(f"shape: {output.shape}")
print(np.round(output, 3), "\n")


# ─── BONUS STEP: Causal (decoder) mask ───────────────────────────────────────
print("=== Causal (decoder-style) masked attention ===")

# TODO: create a causal mask — a boolean matrix where mask[i][j] = True
#       means position j is ALLOWED for position i to attend to.
#       In other words: only the lower triangle (including diagonal) is True.
# Hint: look up np.tril or np.triu

mask = None  # TODO  shape: (n, n), dtype bool

# TODO: apply the mask — set scores_scaled to -1e9 (approx. -inf) where mask is False
scores_masked = scores_scaled.copy()
# TODO: scores_masked[...] = -1e9  (fill in the condition)

weights_causal = softmax(scores_masked, axis=-1)

print("--- Masked attention weights (future tokens zeroed) ---")
header = "         " + "  ".join(f"{t:>7}" for t in TOKENS)
print(header)
for i, token in enumerate(TOKENS):
    row = "  ".join(f"{weights_causal[i, j]:7.4f}" for j in range(n))
    print(f"{token:<8} [ {row} ]")

print("\nDone! Compare your output with the expected output in README.md.")
print("Then open solution.py to check your implementation.")
