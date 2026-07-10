"""
Day 1 Lab — Starter File
========================
The tokenizer and embedding model are already loaded for you below —
no need to fight downloads or setup boilerplate. Your job is to fill in
the three TODOs, which mirror the by-hand walkthrough in Day-01 curriculum
section 3 (Worked Example).

Run `python solution.py` to compare with the reference output once done.

Note: running this file before completing the TODOs will raise an error
partway through — that is expected. Fill in TODOs 1-3 and rerun.

No API key required — everything runs locally.
"""

import numpy as np
import tiktoken
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Part A: Tokenisation with tiktoken
# ---------------------------------------------------------------------------

def count_tokens(text: str, encoding) -> tuple[int, list[int]]:
    """
    TODO 1: Count tokens for a string.
    Use `encoding.encode(text)` to get the list of token IDs, then return
    (number_of_tokens, token_id_list).
    Hint: this is exactly the split you traced by hand in curriculum §3.1
    for "I love tokenization!" — here you do it programmatically instead.
    """
    # YOUR CODE HERE
    pass


def part_a():
    print("=== Part A: Tokenisation ===")

    # o200k_base — used by current OpenAI models (GPT-4o and newer); use for
    # token-count ESTIMATION only. Older models (GPT-3.5-turbo, original GPT-4)
    # used cl100k_base instead. Claude uses its own tokenizer (no public
    # tiktoken equivalent).
    encoding = tiktoken.get_encoding("o200k_base")
    print("Encoding: o200k_base\n")

    sample_texts = [
        "Hello, world!",
        "Tokenisation is surprisingly nuanced.",
        "GPT-4o uses o200k_base tokenisation.",
        "日本語のテキスト (Japanese text) costs more tokens per character.",
        "def calculate_embedding_similarity(vec_a, vec_b):",
    ]

    all_ratios = []
    for text in sample_texts:
        word_count = len(text.split())
        num_tokens, ids = count_tokens(text, encoding)

        ratio = num_tokens / max(word_count, 1)
        all_ratios.append(ratio)

        print(f'Text: "{text}"')
        print(f"  Words : {word_count}")
        print(f"  Tokens: {num_tokens}")
        print(f"  Token IDs: {ids[:8]}{'...' if len(ids) > 8 else ''}")
        print()

    print("Ratio summary:")
    print(f"  Avg tokens/word across all samples: {np.mean(all_ratios):.2f}")
    print("  Rule of thumb: 1 token ≈ 0.75 words (ratio ≈ 1.33) for English.")
    print("  Non-English & code inflate the ratio above the English baseline.\n")


# ---------------------------------------------------------------------------
# Part B: Embeddings & Cosine Similarity
# ---------------------------------------------------------------------------

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    TODO 2: Implement cosine similarity.
    Formula: (A . B) / (|A| * |B|)
    Hint: use np.dot and np.linalg.norm — this is the exact two-line
    calculation verified against the "cat vs kitten vs car" toy example
    in curriculum §3.2/§3.3. Clamp the result to [-1, 1] with np.clip to
    handle floating-point edge cases.
    """
    # YOUR CODE HERE
    pass


def build_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    TODO 3: Given an (N, D) array of embeddings, return an (N, N) cosine
    similarity matrix where entry [i][j] = cosine_similarity(embeddings[i], embeddings[j]).
    Hint: loop i over range(N), loop j over range(N), call cosine_similarity()
    for each pair — same idea as computing cat-vs-kitten and cat-vs-car by
    hand in §3.2, just done N x N times instead of twice.
    """
    # YOUR CODE HERE
    pass


def part_b():
    print("=== Part B: Embedding Similarity ===")

    # Downloads ~90 MB on first run; cached locally afterwards.
    model = SentenceTransformer("all-MiniLM-L6-v2")
    dim = model.get_embedding_dimension()
    print(f"Model: all-MiniLM-L6-v2  ({dim}-dimensional vectors, runs locally)\n")

    sentences = [
        "A cat is sleeping on the sofa.",
        "The kitten napped on the couch.",
        "Dogs love to play fetch in the park.",
        "Financial markets surged on positive earnings.",
        "Puppies enjoy chasing balls outdoors.",
    ]

    print("Sentences:")
    for i, s in enumerate(sentences):
        print(f"  [{i}] \"{s}\"")
    print()

    # Embed all sentences in a single batch call
    embeddings = model.encode(sentences, convert_to_numpy=True)  # shape: (5, 384)

    sim_matrix = build_similarity_matrix(embeddings)

    # Print formatted matrix
    n = len(sentences)
    col_header = "         " + "  ".join(f" [{i}] " for i in range(n))
    print("Cosine Similarity Matrix (rounded to 2 dp):")
    print(col_header)
    for i in range(n):
        row = "  ".join(f"{sim_matrix[i][j]:.2f}" for j in range(n))
        print(f"  [{i}]    {row}")

    print()
    print("Key observations:")

    # Highest off-diagonal similarity
    masked = sim_matrix.copy()
    np.fill_diagonal(masked, -np.inf)
    idx = np.unravel_index(np.argmax(masked), masked.shape)
    i, j = idx
    print(f"  Highest similarity: [{i}] vs [{j}] = {sim_matrix[i][j]:.2f}")
    print(f"    \"{sentences[i]}\"")
    print(f"    \"{sentences[j]}\"")

    # Dogs vs puppies
    dogs_idx, pups_idx = 2, 4
    print(f"\n  Dogs/puppies pair: [{dogs_idx}] vs [{pups_idx}] = {sim_matrix[dogs_idx][pups_idx]:.2f}  (same topic, different words)")

    # Finance vs cats
    finance_idx, cat_idx = 3, 0
    print(f"  Finance vs cats:   [{finance_idx}] vs [{cat_idx}] = {sim_matrix[finance_idx][cat_idx]:.2f}  (unrelated domains)")

    print()
    print("Takeaway: semantically similar sentences cluster near 1.0; unrelated ones drop toward 0.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    part_a()
    part_b()
