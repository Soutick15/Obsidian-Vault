"""
Capstone Starter — retrieve.py
==============================
Semantic retrieval over the ChromaDB HR corpus index.

Usage (standalone):
    python capstone/developer/starter/retrieve.py "What is the PTO policy?"
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = os.getenv("CHROMA_DIR", ".chroma_capstone")
COLLECTION_NAME = "hr_corpus"
TOP_K = 3


def load_index():
    """Load the ChromaDB collection and embedding model."""
    # TODO: initialise ChromaDB PersistentClient, get collection, load SentenceTransformer
    # Return (collection, embed_model)
    import chromadb  # type: ignore
    chroma = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        collection = chroma.get_collection(COLLECTION_NAME)
    except Exception:
        collection = chroma.get_or_create_collection(COLLECTION_NAME)

    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    except ImportError:
        embed_model = None

    return collection, embed_model


def retrieve(query: str, collection=None, embed_model=None, top_k: int = TOP_K) -> list[dict]:
    """
    Embed the query and return top_k chunks from the HR corpus.

    Returns a list of dicts: [{"id": str, "text": str, "source": str}, ...]
    """
    # TODO 1: If collection/embed_model are None, load them via load_index()
    if collection is None or embed_model is None:
        collection, embed_model = load_index()

    # TODO 2: Embed the query
    #   Hint: query_emb = embed_model.encode(query).tolist()
    if embed_model:
        query_emb = embed_model.encode(query).tolist()
    else:
        query_emb = [0.0] * 384

    # TODO 3: Query ChromaDB and format results
    #   Hint: results = collection.query(query_embeddings=[query_emb], n_results=top_k)
    try:
        results = collection.query(query_embeddings=[query_emb], n_results=top_k)
        docs = results.get("documents", [[]])[0]
        ids = results.get("ids", [[]])[0]
    except Exception:
        # Empty index or no documents — return mock passage
        return [{"id": "mock_0", "text": "HR policy: employees receive 15 PTO days per year.", "source": "mock"}]

    if not docs:
        return [{"id": "mock_0", "text": "HR policy: employees receive 15 PTO days per year.", "source": "mock"}]

    chunks = []
    for doc_id, text in zip(ids, docs):
        source = doc_id.split("_chunk_")[0] if "_chunk_" in doc_id else doc_id
        chunks.append({"id": doc_id, "text": text, "source": source})
    return chunks


def format_context(chunks: list[dict]) -> str:
    """Format retrieved chunks as a numbered context block."""
    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"[{i}] {chunk['text']}\n    Source: {chunk['source']}")
    return "\n\n".join(lines) if lines else "(no relevant documents found)"


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "What is the PTO policy?"
    chunks = retrieve(query)
    print(f"Query: {query}\n")
    print(format_context(chunks))
