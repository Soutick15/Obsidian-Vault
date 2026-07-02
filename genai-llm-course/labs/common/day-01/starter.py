"""
Day 1 Lab — Starter File
========================
Complete the TODOs below. Run `python solution.py` to compare with the
reference output once you are done.

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
    TODO: Use `encoding.encode(text)` to get the list of token IDs.
    Return (number_of_tokens, token_id_list).
    """
    # YOUR CODE HERE
    ids = encoding.encode(text)
    return len(ids) , id


def part_a():
    print("=== Part A: Tokenisation ===")

    # TODO: Load the "cl100k_base" encoding.
    # cl100k_base — used by GPT-4 / GPT-4o; use for token-count ESTIMATION only.
    # Claude uses its own tokenizer (no public tiktoken equivalent).
    # Hint: tiktoken.get_encoding("cl100k_base")
    encoding = tiktoken.get.encoding("cl100k_base")

    print(f"Encoding: cl100k_base\n")

    sample_texts = [
        "Hello, world!",
        "Tokenisation is surprisingly nuanced.",
        "GPT-4 uses cl100k_base tokenisation.",
        "日本語のテキスト (Japanese text) costs more tokens per character.",
        "def calculate_embedding_similarity(vec_a, vec_b):",
    ]

    all_ratios = []
    for text in sample_texts:
        word_count = len(text.split())

        # TODO: call count_tokens() to get (num_tokens, ids)
        num_tokens, ids = count_tokens (text, encoding)
        num_tokens, ids = 0, []  # replace with your code

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
    TODO: Implement cosine similarity.
    Formula: (A · B) / (|A| * |B|)
    Hint: use np.dot, np.linalg.norm
    Clamp to [-1, 1] with np.clip to handle floating-point edge cases.
    """
    # YOUR CODE HERE
    dot = np.dot(vec_a, vec_b)
    norm = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
    if norm == 0.0:
        return 0.0
    return float(np.clip(dot / norm, -1.0, 1.0))


def build_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    TODO: Given an (N, D) array of embeddings, return an (N, N) cosine
    similarity matrix where entry [i][j] = cosine_similarity(embeddings[i], embeddings[j]).
    """
    # YOUR CODE HERE
    
    n = len(embeddings)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range (n):
            matrix [i] [j] = cosine_similarity(embeddings[i], embeddings[j])
    return matrix


def part_b():
    print("=== Part B: Embedding Similarity ===")

    # TODO: Load the sentence-transformer model.
    # Model name: "all-MiniLM-L6-v2"  (downloads ~90 MB on first run)
    # Hint: SentenceTransformer("all-MiniLM-L6-v2")
    model =  SentenceTransformer("all-MiniLM-L6-v2")
    dim = model.get_embedding_dimension()
    print(f"Model: all-MiniLM-L6-v2  ({dim}-dimensional vectors, runs locally)\n")

    print(f"Model: all-MiniLM-L6-v2  (384-dimensional vectors, runs locally)\n")

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

    # TODO: Embed all sentences at once.
    embeddings = model.encode(sentences, convert_to_numpy=True)  # shape: (5, 384)

    # TODO: Build the similarity matrix.
    sim_matrix = build_similarity_matrix(embeddings)

    # Print the matrix
    n = len(sentences)
    header = "       " + "  ".join(f"[{i}]  " for i in range(n))
    print("Cosine Similarity Matrix (rounded to 2 dp):")
    print(header)
    for i in range(n):
        row = "  ".join(f"{sim_matrix[i][j]:.2f}" for j in range(n))
        print(f"  [{i}]   {row}")

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
