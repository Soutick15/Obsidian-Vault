"""
Capstone Starter — ingest.py
============================
Chunk and embed the HR corpus into ChromaDB.
Runs in mock mode (no API key) using sentence-transformers for embeddings.

Usage:
    python capstone/developer/starter/ingest.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

CORPUS_DIR = Path(os.getenv("CORPUS_DIR", "data/hr-corpus"))
CHROMA_DIR = os.getenv("CHROMA_DIR", ".chroma_capstone")
COLLECTION_NAME = "hr_corpus"
CHUNK_SIZE = 400       # characters per chunk
CHUNK_OVERLAP = 80


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character-level chunks."""
    # TODO: implement sliding-window chunking
    # Hint: step = size - overlap; yield text[i:i+size] for i in range(0, len(text), step)
    chunks = []
    step = size - overlap
    for i in range(0, len(text), step):
        chunk = text[i: i + size]
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def load_corpus(corpus_dir: Path) -> dict[str, str]:
    """Load all .txt and .md files from the corpus directory."""
    # TODO: walk corpus_dir, read each file, return {filename: content}
    docs: dict[str, str] = {}
    if not corpus_dir.exists():
        print(f"[warn] Corpus dir not found: {corpus_dir} — using empty corpus")
        return docs
    for path in corpus_dir.glob("**/*"):
        if path.suffix in (".txt", ".md") and path.is_file():
            docs[path.stem] = path.read_text(encoding="utf-8", errors="ignore")
    return docs


def build_index(corpus_dir: Path = CORPUS_DIR, chroma_dir: str = CHROMA_DIR) -> tuple:
    """
    Embed all corpus chunks and store in ChromaDB.

    Returns (collection, embed_model) for immediate use after ingestion.
    """
    # TODO 1: Import and initialise the sentence-transformers embedding model
    #   Hint: from sentence_transformers import SentenceTransformer
    #         model = SentenceTransformer("all-MiniLM-L6-v2")
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    except ImportError:
        embed_model = None
        print("[warn] sentence-transformers not installed — embeddings will be empty vectors")

    # TODO 2: Initialise a persistent ChromaDB client and get/create the collection
    #   Hint: import chromadb; client = chromadb.PersistentClient(path=chroma_dir)
    import chromadb  # type: ignore
    chroma = chromadb.PersistentClient(path=chroma_dir)
    collection = chroma.get_or_create_collection(COLLECTION_NAME)

    docs = load_corpus(corpus_dir)
    if not docs:
        print("[ingest] No documents found — index will be empty")
        return collection, embed_model

    all_ids, all_docs, all_embeddings = [], [], []
    for doc_name, content in docs.items():
        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_name}_chunk_{i}"
            emb = embed_model.encode(chunk).tolist() if embed_model else [0.0] * 384
            all_ids.append(chunk_id)
            all_docs.append(chunk)
            all_embeddings.append(emb)

    if all_ids:
        # TODO 3: upsert chunks into the collection
        collection.upsert(ids=all_ids, documents=all_docs, embeddings=all_embeddings)
        print(f"[ingest] Indexed {len(all_ids)} chunks from {len(docs)} documents.")
    return collection, embed_model


if __name__ == "__main__":
    build_index()
    print("[ingest] Done.")
