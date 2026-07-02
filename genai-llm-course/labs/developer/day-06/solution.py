"""
Day 6 Lab — Embeddings & Vector Search (solution)
==================================================
Complete reference implementation.

Run from the repo root:
    python labs/developer/day-06/solution.py

No API key required. All computation is local.
Requires:  chromadb  sentence-transformers  numpy
"""

from pathlib import Path
import re

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Resolve repo root by going 3 levels up from this file:
#   labs/developer/day-06/solution.py  ->  repo root
CORPUS_DIR: Path = Path(__file__).resolve().parents[3] / "data" / "hr-corpus"
CHROMA_DIR: Path = Path(__file__).resolve().parent / ".chroma_db"
COLLECTION_NAME = "hr-corpus-day06"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"


# ---------------------------------------------------------------------------
# Step 1 — Load and chunk the corpus
# ---------------------------------------------------------------------------

def load_chunks(corpus_dir: Path) -> list[dict]:
    """
    Read every .md file in corpus_dir (excluding README.md),
    split on blank lines into paragraph chunks,
    and return a list of dicts with keys: text, source, id.
    """
    if not corpus_dir.exists():
        raise FileNotFoundError(
            f"HR corpus not found at: {corpus_dir}\n"
            "Make sure you are running from the repo root:\n"
            "    python labs/developer/day-06/solution.py"
        )

    chunks: list[dict] = []
    md_files = sorted(p for p in corpus_dir.glob("*.md") if p.name != "README.md")

    for path in md_files:
        text = path.read_text(encoding="utf-8")
        paragraphs = re.split(r"\n\n+", text)
        idx = 0
        for para in paragraphs:
            para = para.strip()
            # Skip very short snippets (headings, blank separators)
            if len(para) < 40:
                continue
            chunks.append({
                "text": para,
                "source": path.name,
                "id": f"{path.stem}-{idx}",
            })
            idx += 1

    return chunks


# ---------------------------------------------------------------------------
# Step 2 — Load the embedding model
# ---------------------------------------------------------------------------

def load_model():
    """Load all-MiniLM-L6-v2 from sentence-transformers (cached after first download)."""
    from sentence_transformers import SentenceTransformer  # type: ignore
    return SentenceTransformer(EMBED_MODEL_NAME)


# ---------------------------------------------------------------------------
# Step 3 — Create or reuse a persistent Chroma collection
# ---------------------------------------------------------------------------

def get_collection(chroma_dir: Path):
    """
    Open a persistent Chroma DB at chroma_dir and return the collection.
    Creates the collection if it does not exist.
    Uses cosine distance so that 1 - distance = cosine similarity.
    """
    import chromadb  # type: ignore

    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


# ---------------------------------------------------------------------------
# Step 4 — Embed and upsert (only if collection is empty)
# ---------------------------------------------------------------------------

def ingest(collection, model, chunks: list[dict]) -> None:
    """
    Embed all chunks and upsert into Chroma.
    Skips ingestion if the collection already has data (idempotent).
    """
    if collection.count() > 0:
        print(f"  Collection already has {collection.count()} vectors — skipping ingestion.")
        return

    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    metadatas = [{"source": c["source"]} for c in chunks]

    print(f"  Embedding {len(texts)} chunks with {EMBED_MODEL_NAME} ...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)
    # Chroma requires plain Python lists, not numpy arrays
    embeddings_list = embeddings.tolist()

    collection.upsert(
        ids=ids,
        embeddings=embeddings_list,
        documents=texts,
        metadatas=metadatas,
    )
    print(f"  Upserted {len(ids)} vectors into '{COLLECTION_NAME}'.")


# ---------------------------------------------------------------------------
# Step 5 — Semantic search helper
# ---------------------------------------------------------------------------

def semantic_search(
    collection,
    model,
    query: str,
    top_k: int = 3,
    where: dict | None = None,
) -> None:
    """
    Embed query, retrieve top_k nearest chunks from Chroma, and print results.

    Chroma uses distance (lower = more similar) when hnsw:space is 'cosine'.
    We display similarity = 1 - distance for intuitive reading.
    """
    query_embedding = model.encode([query]).tolist()

    kwargs: dict = dict(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        similarity = 1.0 - dist  # cosine distance -> cosine similarity
        snippet = doc[:120].replace("\n", " ")
        print(f"  [{similarity:.2f}] {meta['source']:<40} | {snippet}...")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"[1/3] Loading HR corpus from {CORPUS_DIR} ...")
    chunks = load_chunks(CORPUS_DIR)
    doc_count = len(set(c["source"] for c in chunks))
    print(f"  Loaded {doc_count} documents, {len(chunks)} chunks total")

    print(f"\n[2/3] Embedding chunks and storing in Chroma ...")
    model = load_model()
    collection = get_collection(CHROMA_DIR)
    ingest(collection, model, chunks)
    print(
        f"  Collection '{collection.name}' ready "
        f"({collection.count()} vectors, {EMBED_MODEL_NAME} — 384 dimensions)"
    )

    print("\n[3/3] Running semantic queries ...")

    # Core semantic queries covering different HR topics
    queries = [
        "What is the parental leave policy?",
        "How does the 401(k) match work?",
        "What are the stages of the hiring process?",
        "What are the password and MFA requirements?",
        "When do merit increases take effect?",
    ]

    for q in queries:
        print(f"\n=== Query: \"{q}\" ===")
        semantic_search(collection, model, q, top_k=3)

    # Metadata filter demo: restrict to a single source document
    filter_query = "sick days and personal leave"
    filter_source = "leave-and-pto-policy.md"
    print(f"\n=== Filtered query (source={filter_source}): \"{filter_query}\" ===")
    print(f"  Filtering to source: {filter_source}")
    semantic_search(
        collection,
        model,
        filter_query,
        top_k=3,
        where={"source": filter_source},
    )

    print(f"\nDone. Chroma DB persisted at {CHROMA_DIR}")


if __name__ == "__main__":
    main()
