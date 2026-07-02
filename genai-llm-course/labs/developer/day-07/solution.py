"""
Day 7 Solution — End-to-End RAG over the Acme Corp HR Corpus
=============================================================
Complete working implementation. Runs fully offline via the mock generator.

Usage:
    python labs/developer/day-07/solution.py                   # mock (no key)
    ANTHROPIC_API_KEY=sk-... python labs/developer/day-07/solution.py
    OPENAI_API_KEY=sk-...    python labs/developer/day-07/solution.py
    python labs/developer/day-07/solution.py --question "How do I request PTO?"
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ── Resolve corpus path from any working directory ──────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[3]
CORPUS_DIR = REPO_ROOT / "data" / "hr-corpus"

# ── Chunking / retrieval parameters ─────────────────────────────────────────
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80
TOP_K = 4
COLLECTION_NAME = "hr_rag_day07"
EMBED_MODEL = "all-MiniLM-L6-v2"

# ── Example questions (from corpus README) ───────────────────────────────────
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
    """Read all .md files from corpus_dir, excluding README.md."""
    documents = []
    for filepath in sorted(corpus_dir.glob("*.md")):
        if filepath.name.lower() == "readme.md":
            continue
        text = filepath.read_text(encoding="utf-8")
        documents.append({"source": filepath.name, "text": text})
    return documents


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
    Returns list of {"id", "source", "text", "chunk_index"} dicts.
    """
    chunks = []
    step = max(1, chunk_size - overlap)

    for doc in documents:
        source = doc["source"]
        text = doc["text"]
        chunk_index = 0
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:  # skip empty windows at end of very short docs
                chunks.append(
                    {
                        "id": f"{source}_chunk_{chunk_index}",
                        "source": source,
                        "text": chunk_text,
                        "chunk_index": chunk_index,
                    }
                )
                chunk_index += 1

            if end == len(text):
                break
            start += step

    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 + 4 — EMBED & STORE
# ─────────────────────────────────────────────────────────────────────────────


def build_index(chunks: List[Dict[str, Any]], collection_name: str):
    """
    Embed all chunks with sentence-transformers and store in Chroma.
    Returns (collection, embed_model).
    """
    import chromadb
    from sentence_transformers import SentenceTransformer

    # In-memory Chroma client (no persistence needed for this lab)
    client = chromadb.Client()

    # Create or reset collection
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    # Embed all chunks
    embed_model = SentenceTransformer(EMBED_MODEL)
    texts = [c["text"] for c in chunks]
    embeddings = embed_model.encode(texts, show_progress_bar=False)

    # Store in Chroma
    collection.add(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=[
            {"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks
        ],
    )

    return collection, embed_model


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — RETRIEVE
# ─────────────────────────────────────────────────────────────────────────────


def retrieve(
    question: str,
    collection,
    embed_model,
    top_k: int = TOP_K,
) -> List[Dict[str, Any]]:
    """
    Embed the question and query Chroma for the top-k most relevant chunks.
    Returns list of {"text", "source", "chunk_index", "score"} dicts.
    """
    query_vec = embed_model.encode([question])[0].tolist()

    results = collection.query(
        query_embeddings=[query_vec],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # Chroma cosine distance is 1 - similarity; convert back to similarity
        score = max(0.0, 1.0 - dist)
        retrieved.append(
            {
                "text": doc,
                "source": meta["source"],
                "chunk_index": meta["chunk_index"],
                "score": round(score, 3),
            }
        )

    return retrieved


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — AUGMENT
# ─────────────────────────────────────────────────────────────────────────────


def build_prompt(question: str, retrieved: List[Dict[str, Any]]) -> str:
    """Build the grounded, citation-eliciting prompt."""
    system = (
        "You are Acme Corp's internal HR assistant.\n"
        "Answer ONLY using the context provided below.\n"
        "If the context does not contain enough information to answer, respond with exactly:\n"
        '"I don\'t know based on the available documents."\n'
        "At the end of your answer, always list the source document(s) you used on a line "
        "beginning with 'Sources:'.\n"
    )

    context_blocks = []
    for i, chunk in enumerate(retrieved, 1):
        context_blocks.append(
            f"[Context {i}]\n{chunk['text']}\nSource: {chunk['source']}"
        )
    context_section = "\n\n".join(context_blocks)

    prompt = (
        f"{system}\n"
        f"---\n"
        f"CONTEXT:\n\n{context_section}\n\n"
        f"---\n"
        f"QUESTION: {question}\n\n"
        f"ANSWER:"
    )
    return prompt


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — GENERATE
# ─────────────────────────────────────────────────────────────────────────────


def _sentences(text: str, max_sentences: int = 3) -> str:
    """Return up to max_sentences from text."""
    # Split on period/exclamation/question followed by whitespace or end
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    # Filter out very short fragments (likely headers or bullets)
    sentences = [s for s in sentences if len(s) > 20]
    return " ".join(sentences[:max_sentences])


def mock_generate(prompt: str, retrieved: List[Dict[str, Any]]) -> str:
    """
    Deterministic mock generator: composes an answer from retrieved chunk excerpts.
    Produces a sensible, cited response without any API call.
    """
    if not retrieved:
        return "I don't know based on the available documents."

    parts = []
    seen_sources = []
    for chunk in retrieved:
        excerpt = _sentences(chunk["text"], max_sentences=3)
        if excerpt:
            parts.append(excerpt)
        if chunk["source"] not in seen_sources:
            seen_sources.append(chunk["source"])

    body = "\n\n".join(parts)
    sources_line = "Sources: " + ", ".join(seen_sources)

    return f"Based on the provided HR documents:\n\n{body}\n\n{sources_line}"


def generate(prompt: str, retrieved: List[Dict[str, Any]]) -> Tuple[str, str]:
    """
    Route to the appropriate generator based on available API keys.
    Returns (answer, generator_name).
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if anthropic_key:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip(), "Claude claude-haiku-4-5"
        except Exception as e:
            print(
                f"[WARNING] Claude call failed ({e}); falling back to mock.",
                file=sys.stderr,
            )

    if openai_key:
        try:
            import openai

            client = openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
            )
            return response.choices[0].message.content.strip(), "OpenAI gpt-5-mini"
        except Exception as e:
            print(
                f"[WARNING] OpenAI call failed ({e}); falling back to mock.",
                file=sys.stderr,
            )

    return mock_generate(prompt, retrieved), "MOCK (no API key detected)"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Day 7 RAG — Acme Corp HR Assistant")
    parser.add_argument(
        "--question", "-q", default=None, help="Single question to answer"
    )
    args = parser.parse_args()

    # Verify corpus directory exists
    if not CORPUS_DIR.is_dir():
        sys.exit(
            f"[ERROR] Corpus directory not found: {CORPUS_DIR}\n"
            "Run from the repo root or adjust REPO_ROOT in solution.py."
        )

    # Detect generator (for display)
    if os.getenv("ANTHROPIC_API_KEY", "").strip():
        generator_label = "Claude claude-haiku-4-5"
    elif os.getenv("OPENAI_API_KEY", "").strip():
        generator_label = "OpenAI gpt-5-mini"
    else:
        generator_label = "MOCK (no API key detected)"

    print("=== RAG System: Acme Corp HR Assistant ===")
    print(f"Generator: {generator_label}")
    print(f"Corpus: {CORPUS_DIR}")

    # ── INGESTION ────────────────────────────────────────────────────────────
    print("\n[INGESTION]")

    docs = load_documents(CORPUS_DIR)
    print(f"Loaded {len(docs)} documents")

    chunks = chunk_documents(docs, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    print(
        f"Split into {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})"
    )

    print(f"Embedding {len(chunks)} chunks with {EMBED_MODEL} ...")
    collection, embed_model = build_index(chunks, COLLECTION_NAME)
    print(f"Stored in Chroma collection: {COLLECTION_NAME}")

    # ── QUERIES ───────────────────────────────────────────────────────────────
    questions = [args.question] if args.question else EXAMPLE_QUESTIONS

    for question in questions:
        print(f"\n{'─' * 62}")
        print(f"[QUERY]\nQuestion: {question}")

        retrieved = retrieve(question, collection, embed_model, top_k=TOP_K)

        print("\n[RETRIEVED CHUNKS]")
        for i, r in enumerate(retrieved, 1):
            print(f"  #{i} (score={r['score']:.3f}) {r['source']}")

        prompt = build_prompt(question, retrieved)
        answer, used_generator = generate(prompt, retrieved)

        print(f"\n[ANSWER] (via {used_generator})")
        print(answer)

    print(f"\n{'─' * 62}")
    print("Done.")


if __name__ == "__main__":
    main()
