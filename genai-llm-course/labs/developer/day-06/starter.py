"""
Day 6 Lab — Embeddings & Vector Search (starter)
=================================================
Fill in each TODO block. Run with:
    python labs/developer/day-06/starter.py
from the repo root.

No API key required — all embedding is local.
"""

from pathlib import Path
import re

# ---------------------------------------------------------------------------
# TODO 1 — Locate the HR corpus directory
# ---------------------------------------------------------------------------
# Use pathlib to resolve the path robustly regardless of where Python is invoked.
# The corpus lives at <repo-root>/data/hr-corpus/
# Hint: __file__ is this script; go up 3 parents to reach the repo root.

CORPUS_DIR = None  # TODO: replace with Path(__file__).resolve().parents[...] / "data" / "hr-corpus"
CHROMA_DIR = Path(__file__).resolve().parent / ".chroma_db"

# ---------------------------------------------------------------------------
# TODO 2 — Load and chunk the corpus
# ---------------------------------------------------------------------------
# Write a function that:
#   1. Iterates over all *.md files in CORPUS_DIR (skip README.md)
#   2. Reads each file's text
#   3. Splits on double-newlines (\n\n) to get paragraph chunks
#   4. Filters out chunks that are too short (< 40 characters)
#   5. Returns a list of dicts:  {"text": str, "source": filename, "id": str}

def load_chunks(corpus_dir: Path) -> list[dict]:
    """Load all .md files and split into paragraph chunks with metadata."""
    chunks = []

    # TODO: iterate corpus_dir.glob("*.md"), skip "README.md"
    # for each file:
    #   text = path.read_text(encoding="utf-8")
    #   paragraphs = re.split(r"\n\n+", text)
    #   for each paragraph that is long enough, append a dict:
    #       {"text": para.strip(), "source": path.name, "id": f"{path.stem}-{idx}"}

    return chunks


# ---------------------------------------------------------------------------
# TODO 3 — Load the embedding model
# ---------------------------------------------------------------------------
# Use sentence_transformers.SentenceTransformer to load "all-MiniLM-L6-v2".
# This downloads ~22 MB on first run and caches locally.

def load_model():
    """Return a loaded SentenceTransformer model."""
    # TODO: from sentence_transformers import SentenceTransformer
    #       return SentenceTransformer("all-MiniLM-L6-v2")
    raise NotImplementedError("TODO 3: load the embedding model")


# ---------------------------------------------------------------------------
# TODO 4 — Create or reuse a persistent Chroma collection
# ---------------------------------------------------------------------------
# Use chromadb.PersistentClient to open/create a DB at CHROMA_DIR.
# Collection name: "hr-corpus-day06"
# Distance metric: cosine  (pass metadata={"hnsw:space": "cosine"})

def get_collection(chroma_dir: Path):
    """Return a Chroma collection, creating it if needed."""
    # TODO: import chromadb
    #       client = chromadb.PersistentClient(path=str(chroma_dir))
    #       return client.get_or_create_collection(
    #           name="hr-corpus-day06",
    #           metadata={"hnsw:space": "cosine"},
    #       )
    raise NotImplementedError("TODO 4: create the Chroma collection")


# ---------------------------------------------------------------------------
# TODO 5 — Embed chunks and upsert into Chroma
# ---------------------------------------------------------------------------
# Only do this if the collection is empty (collection.count() == 0),
# so re-running the script reuses the persisted index.
#
# Steps:
#   1. Extract texts, ids, and metadatas from the chunks list.
#   2. Embed all texts in one call: model.encode(texts, show_progress_bar=True)
#      — returns a numpy array of shape (n, 384).
#   3. Convert embeddings to list-of-lists (Chroma expects plain Python lists).
#   4. Call collection.upsert(ids=ids, embeddings=embs, documents=texts, metadatas=metas)

def ingest(collection, model, chunks: list[dict]) -> None:
    """Embed chunks and upsert into the Chroma collection (skips if already populated)."""
    if collection.count() > 0:
        print(f"  Collection already has {collection.count()} vectors — skipping ingestion.")
        return

    # TODO: extract ids, texts, metadatas from chunks
    # TODO: embed with model.encode(...)
    # TODO: upsert into collection
    raise NotImplementedError("TODO 5: embed and upsert chunks")


# ---------------------------------------------------------------------------
# TODO 6 — Query the collection and print top-k results
# ---------------------------------------------------------------------------
# Steps:
#   1. Embed the query string with model.encode([query]).tolist()
#   2. Call collection.query(query_embeddings=..., n_results=top_k)
#   3. Chroma returns distances (lower = more similar with cosine space).
#      Convert to similarity = 1 - distance for display.
#   4. Print each result: similarity score, source filename, text snippet.

def semantic_search(collection, model, query: str, top_k: int = 3) -> None:
    """Embed query, search collection, print top-k results."""
    print(f"\n=== Query: \"{query}\" ===")

    # TODO: embed the query
    # TODO: call collection.query(...)
    # TODO: loop over results and print
    raise NotImplementedError("TODO 6: query and print results")


# ---------------------------------------------------------------------------
# TODO 7 — Metadata filter example
# ---------------------------------------------------------------------------
# Repeat a query but restrict results to a single source file using
# the `where` parameter:
#   collection.query(..., where={"source": "leave-and-pto-policy.md"})

def filtered_search(collection, model, query: str, source_file: str, top_k: int = 3) -> None:
    """Same as semantic_search but filtered to a specific source document."""
    print(f"\n=== Filtered query (source={source_file}): \"{query}\" ===")

    # TODO: add where={"source": source_file} to the collection.query() call
    raise NotImplementedError("TODO 7: add metadata filter")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("[1/3] Loading HR corpus ...")
    chunks = load_chunks(CORPUS_DIR)
    if not chunks:
        raise RuntimeError(f"No chunks loaded. Check CORPUS_DIR: {CORPUS_DIR}")
    print(f"  Loaded {len(set(c['source'] for c in chunks))} documents, {len(chunks)} chunks total")

    print("\n[2/3] Setting up Chroma collection and embedding model ...")
    model = load_model()
    collection = get_collection(CHROMA_DIR)
    ingest(collection, model, chunks)
    print(f"  Collection '{collection.name}' ready ({collection.count()} vectors)")

    print("\n[3/3] Running semantic queries ...")

    queries = [
        "What is the parental leave policy?",
        "How does the 401(k) match work?",
        "What are the stages of the hiring process?",
        "What are the password and MFA requirements?",
        "When do merit increases take effect?",
    ]

    for q in queries:
        semantic_search(collection, model, q, top_k=3)

    # Metadata filter demo
    filtered_search(
        collection, model,
        query="sick days and personal leave",
        source_file="leave-and-pto-policy.md",
        top_k=3,
    )

    print(f"\nDone. Chroma DB persisted at {CHROMA_DIR}")


if __name__ == "__main__":
    main()
