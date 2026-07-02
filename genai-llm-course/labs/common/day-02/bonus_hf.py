"""
Day 2 Bonus — HuggingFace Real Attention
=========================================
Loads distilgpt2 with output_attentions=True, runs a short sentence through it,
and prints the attention weight matrix for head 0 of layer 0.

Requires (install separately — NOT in requirements.txt):
    pip install torch>=2.0.0 transformers>=4.40.0
"""

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
except ImportError:
    print(
        "Bonus dependencies not installed.\n"
        "Run:  pip install torch>=2.0.0 transformers>=4.40.0\n"
        "Then re-run this script."
    )
    raise SystemExit(0)

import numpy as np


def main() -> None:
    sentence = "The cat sat on the mat"
    model_name = "distilgpt2"

    print(f"=== Day 2 Bonus: Real Attention from {model_name} ===\n")
    print(f"Sentence : {sentence!r}")

    print(f"Loading tokeniser and model ({model_name}) …")
    tokeniser = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, output_attentions=True)
    model.eval()

    inputs = tokeniser(sentence, return_tensors="pt")
    tokens = tokeniser.convert_ids_to_tokens(inputs["input_ids"][0])
    print(f"Tokens   : {tokens}\n")

    with torch.no_grad():
        outputs = model(**inputs)

    # outputs.attentions: tuple of tensors, one per layer
    # Each tensor shape: (batch, heads, seq_len, seq_len)
    layer_0_attn = outputs.attentions[0]          # shape: (1, n_heads, n, n)
    head_0 = layer_0_attn[0, 0].numpy()           # shape: (n, n)

    n = len(tokens)
    col_width = max(len(t) for t in tokens) + 2

    print("--- Attention weights: layer 0, head 0 (rows attend to columns) ---")
    header = " " * col_width + "".join(t.rjust(col_width) for t in tokens)
    print(header)

    for i, tok in enumerate(tokens):
        row_vals = "".join(f"{head_0[i, j]:.4f}".rjust(col_width) for j in range(n))
        print(f"{tok.rjust(col_width - 1)} {row_vals}")

    print("\nRow sums (should all be ≈ 1.0):")
    for i, tok in enumerate(tokens):
        print(f"  {tok:<12s} {head_0[i].sum():.6f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
