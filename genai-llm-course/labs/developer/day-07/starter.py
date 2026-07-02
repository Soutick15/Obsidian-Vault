"""
Day 7 Starter — End-to-End RAG over the Acme Corp HR Corpus
============================================================
Fill in every # TODO block. Run with:
    python labs/developer/day-07/starter.py

No API key needed — the mock generator runs offline.
Set ANTHROPIC_API_KEY or OPENAI_API_KEY to use a live model.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# ── Resolve corpus path from any working directory ──────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[3]
CORPUS_DIR = REPO_ROOT / "data" / "hr-corpus"

# ── Chunking parameters ─────────────────────────────────────────────────────
CHUNK_SIZE = 400  # characters per chunk
CHUNK_OVERLAP = 80  # overlap between adjacent chunks
TOP_K = 4  # chunks to retrieve per query
COLLECTION_NAME = "hr_rag_day07_starter"
EMBED_MODEL = "all-MiniLM-L6-v2"

# ── Example questions from the corpus README ─────────────────────────────────
EXAMPLE_QUESTIONS = [
    "How many PTO days do new employees get in their first two years?",
    "What is the parental leave policy for a non-birth parent?",
    "How much does Acme Corp match on 401(k) contributions?",
    "What are the password and MFA requirements for company accounts?",
]


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — LOAD
# ─────────────────────────────────────────────────────────────────────────────


def load_documents(corpus_dir: Path) -> List[Dict[str, str]]:
    """
    Read all .md files from corpus_dir, excluding README.md.
    Returns a list of dicts: {"source": filename, "text": file_content}
    """
    # TODO: use Path.glob("*.md") to find all markdown files
    # TODO: skip any file whose name is "README.md"
    # TODO: read each file's text and append {"source": file.name, "text": text}
    # TODO: return the list
    raise NotImplementedError("Implement load_documents()")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — CHUNK
# ─────────────────────────────────────────────────────────────────────────────


def chunk_documents(
    documents: List[Dict[str, str]],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    """
    Split each document into fixed-size character chunks with overlap.
    Returns a list of dicts:
        {"id": str, "source": str, "text": str, "chunk_index": int}

    Hint: slide a window of `chunk_size` characters, stepping by
    (chunk_size - overlap) each time.
    """
    chunks = []
    # TODO: iterate over documents
    # TODO: for each document, slide a window over doc["text"]
    #       start = 0; step = chunk_size - overlap
    # TODO: for each window, build a chunk dict with a unique id
    #       e.g. id = f"{source}_chunk_{i}"
    # TODO: append to chunks
    # TODO: return chunks
    raise NotImplementedError("Implement chunk_documents()")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 + 4 — EMBED & STORE
# ─────────────────────────────────────────────────────────────────────────────


def build_index(chunks: List[Dict[str, Any]], collection_name: str):
    """
    Embed all chunks with sentence-transformers and store in a Chroma collection.
    Returns a tuple (collection, embed_model) — both are needed by retrieve().
    """
    # TODO: import SentenceTransformer from sentence_transformers
    # TODO: import chromadb
    # TODO: create an in-memory Chroma client: chromadb.Client()
    # TODO: get-or-create a collection named collection_name
    # TODO: load the embedding model EMBED_MODEL
    # TODO: encode all chunk["text"] values — model.encode([...])
    # TODO: add to the collection:
    #       collection.add(
    #           ids=[c["id"] for c in chunks],
    #           embeddings=embeddings.tolist(),
    #           documents=[c["text"] for c in chunks],
    #           metadatas=[{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks],
    #       )
    # TODO: return (collection, embed_model) as a tuple — both are needed by retrieve()
    raise NotImplementedError("Implement build_index()")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — RETRIEVE
# ─────────────────────────────────────────────────────────────────────────────


def retrieve(
    question: str, collection, model, top_k: int = TOP_K
) -> List[Dict[str, Any]]:
    """
    Embed the question, query the Chroma collection, and return top-k results.
    Each result dict: {"text": str, "source": str, "score": float}
    """
    # TODO: embed the question using model.encode([question])[0].tolist()
    # TODO: query the collection:
    #       results = collection.query(
    #           query_embeddings=[query_vec],
    #           n_results=top_k,
    #           include=["documents", "metadatas", "distances"],
    #       )
    # TODO: zip documents, metadatas, distances into a list of dicts
    #       score = 1 - distance  (Chroma returns L2 or cosine distance)
    # TODO: return the list
    raise NotImplementedError("Implement retrieve()")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — AUGMENT
# ─────────────────────────────────────────────────────────────────────────────


def build_prompt(question: str, retrieved: List[Dict[str, Any]]) -> str:
    """
    Build the augmented prompt.
    Structure:
        System instruction (grounding + citation + I-don't-know instruction)
        Context block (each chunk with its source)
        Question
    Returns the full prompt string.
    """
    # TODO: write a system instruction that:
    #   - Identifies the assistant as Acme Corp's HR assistant
    #   - Instructs it to answer ONLY from the context below
    #   - Instructs it to say "I don't know based on the available documents."
    #     if the context is insufficient
    #   - Instructs it to cite source filenames at the end of the answer
    # TODO: build a context block by iterating over retrieved chunks
    #   - Include chunk["text"] and "Source: {chunk['source']}" for each
    # TODO: append the question
    # TODO: return the assembled prompt string
    raise NotImplementedError("Implement build_prompt()")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — GENERATE
# ─────────────────────────────────────────────────────────────────────────────


def mock_generate(prompt: str, retrieved: List[Dict[str, Any]]) -> str:
    """
    Deterministic mock generator: composes an answer from retrieved chunks.
    Used when no API key is present.
    """
    # TODO: extract first 2–3 sentences from each retrieved chunk
    # TODO: collect unique source filenames
    # TODO: compose and return a string like:
    #   "Based on the provided HR documents:\n\n{sentences}\n\nSources: {sources}"
    raise NotImplementedError("Implement mock_generate()")


def generate(prompt: str, retrieved: List[Dict[str, Any]]) -> tuple[str, str]:
    """
    Route to the appropriate generator based on available API keys.
    Returns (answer: str, generator_name: str).
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    if anthropic_key:
        # TODO: import anthropic; create client
        # TODO: call client.messages.create(
        #           model="claude-haiku-4-5",
        #           max_tokens=512,
        #           messages=[{"role": "user", "content": prompt}],
        #       )
        # TODO: return (response.content[0].text, "Claude claude-haiku-4-5")
        raise NotImplementedError("Implement Claude generation")

    if openai_key:
        # TODO: import openai; create client
        # TODO: call client.chat.completions.create(
        #           model="gpt-5-mini",
        #           messages=[{"role": "user", "content": prompt}],
        #           max_tokens=512,
        #       )
        # TODO: return (response.choices[0].message.content, "OpenAI gpt-5-mini")
        raise NotImplementedError("Implement OpenAI generation")

    return mock_generate(prompt, retrieved), "MOCK (no API key detected)"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Day 7 RAG starter")
    parser.add_argument("--question", "-q", default=None, help="Question to answer")
    args = parser.parse_args()

    print("=== RAG System: Acme Corp HR Assistant ===")

    # Ingestion
    print("\n[INGESTION]")
    docs = load_documents(CORPUS_DIR)
    print(f"Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(
        f"Split into {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})"
    )

    print(f"Embedding with {EMBED_MODEL} ...")
    collection, embed_model = build_index(chunks, COLLECTION_NAME)
    print(f"Stored in Chroma collection: {COLLECTION_NAME}")

    # Select question
    questions = [args.question] if args.question else EXAMPLE_QUESTIONS

    for question in questions:
        print(f"\n{'─' * 60}")
        print(f"[QUERY]\nQuestion: {question}")

        retrieved = retrieve(question, collection, embed_model)

        print("\n[RETRIEVED CHUNKS]")
        for i, r in enumerate(retrieved, 1):
            print(f"  #{i} (score={r['score']:.2f}) {r['source']}")

        prompt = build_prompt(question, retrieved)
        answer, generator = generate(prompt, retrieved)

        print(f"\n[ANSWER] (via {generator})")
        print(answer)


if __name__ == "__main__":
    main()
