"""
Acme HR Knowledge Assistant — core RAG service.

Deterministic, lexical retrieval over the shared HR corpus.
No API key required; uses a mock LLM generator by default.
If ANTHROPIC_API_KEY (or OPENAI_API_KEY) is set, a real provider
may be wired in, but the mock is always the default so labs run
with zero credentials.
"""

from __future__ import annotations

import hashlib
import os
import re
import textwrap
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Corpus path — always resolved relative to this file's location so it works
# regardless of working directory.
# ---------------------------------------------------------------------------
_CORPUS_ROOT = Path(__file__).resolve().parents[3] / "data" / "hr-corpus"


# ---------------------------------------------------------------------------
# Lightweight document store
# ---------------------------------------------------------------------------

def _load_corpus(root: Path = _CORPUS_ROOT) -> list[dict[str, Any]]:
    """Load all .md files (skip README.md) from the corpus directory."""
    docs: list[dict[str, Any]] = []
    if not root.exists():
        return docs
    for path in sorted(root.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8")
        # Strip front-matter / markdown headings for cleaner chunking
        docs.append({"source": path.name, "text": text, "path": str(path)})
    return docs


def _chunk(doc: dict[str, Any], max_chars: int = 800) -> list[dict[str, Any]]:
    """Split a document into overlapping chunks of ≤ max_chars."""
    text = doc["text"]
    chunks = []
    # Split on paragraph boundaries first
    paragraphs = re.split(r"\n{2,}", text.strip())
    current = ""
    chunk_idx = 0
    for para in paragraphs:
        if len(current) + len(para) + 2 > max_chars and current:
            chunks.append({
                "source": doc["source"],
                "chunk_id": f"{doc['source']}#{chunk_idx}",
                "text": current.strip(),
            })
            # 25 % overlap — keep last paragraph
            current = para + "\n\n"
            chunk_idx += 1
        else:
            current += para + "\n\n"
    if current.strip():
        chunks.append({
            "source": doc["source"],
            "chunk_id": f"{doc['source']}#{chunk_idx}",
            "text": current.strip(),
        })
    return chunks


# ---------------------------------------------------------------------------
# Retrieval — TF-IDF via scikit-learn (falls back to BM25-lite if unavailable)
# ---------------------------------------------------------------------------

class _Retriever:
    def __init__(self, chunks: list[dict[str, Any]]):
        self._chunks = chunks
        self._texts = [c["text"] for c in chunks]
        self._vectorizer: Any = None
        self._matrix: Any = None
        self._build()

    def _build(self) -> None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                max_df=0.95,
                min_df=1,
            )
            self._matrix = self._vectorizer.fit_transform(self._texts)
        except ImportError:
            # Fallback: simple term-frequency scoring (no sklearn dependency)
            self._vectorizer = None

    def retrieve(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        if self._vectorizer is not None:
            return self._sklearn_retrieve(query, k)
        return self._fallback_retrieve(query, k)

    def _sklearn_retrieve(self, query: str, k: int) -> list[dict[str, Any]]:
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        q_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self._matrix).flatten()
        top_idx = np.argsort(scores)[::-1][:k]
        results = []
        for i in top_idx:
            if scores[i] > 0:
                results.append({**self._chunks[i], "score": float(scores[i])})
        return results

    def _fallback_retrieve(self, query: str, k: int) -> list[dict[str, Any]]:
        """Simple token-overlap scoring — no dependencies."""
        tokens = set(re.findall(r"\w+", query.lower()))
        scored = []
        for chunk in self._chunks:
            doc_tokens = re.findall(r"\w+", chunk["text"].lower())
            doc_freq: dict[str, int] = {}
            for t in doc_tokens:
                doc_freq[t] = doc_freq.get(t, 0) + 1
            score = sum(doc_freq.get(t, 0) for t in tokens)
            if score > 0:
                scored.append({**chunk, "score": float(score)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]


# ---------------------------------------------------------------------------
# Singleton corpus / retriever (loaded once at import time)
# ---------------------------------------------------------------------------

_DOCS = _load_corpus()
_CHUNKS: list[dict[str, Any]] = []
for _doc in _DOCS:
    _CHUNKS.extend(_chunk(_doc))

_RETRIEVER = _Retriever(_CHUNKS) if _CHUNKS else None


# ---------------------------------------------------------------------------
# Mock LLM generator — deterministic, no API key
# ---------------------------------------------------------------------------

_TEMPLATES = [
    (
        "Based on Acme HR policy, {summary} "
        "Please review the source documents for full details."
    ),
    (
        "According to the Acme employee handbook, {summary} "
        "Consult the referenced documents for authoritative guidance."
    ),
    (
        "The Acme HR documentation indicates that {summary} "
        "See the cited sources for complete information."
    ),
]


def _mock_generate(question: str, contexts: list[str]) -> str:
    """
    Produce a deterministic grounded answer from retrieved contexts.
    Selects a template based on a hash of the question for variety.
    Extracts the first meaningful sentence from each context.
    """
    if not contexts:
        return (
            "I don't have specific information about that in the Acme HR "
            "documentation. Please contact HR directly for assistance."
        )

    # Extract first non-empty, non-heading line from each context
    snippets: list[str] = []
    for ctx in contexts:
        for line in ctx.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and len(line) > 20:
                # Trim to ~120 chars
                snippets.append(line[:120])
                break

    summary = " ".join(snippets[:2]) if snippets else contexts[0][:200]
    summary = summary.rstrip(".") + "."

    # Pick template deterministically from question hash
    idx = int(hashlib.md5(question.encode()).hexdigest(), 16) % len(_TEMPLATES)
    template = _TEMPLATES[idx]
    return template.format(summary=summary)


# ---------------------------------------------------------------------------
# Optional real-provider path (only if key present)
# ---------------------------------------------------------------------------

def _real_generate(question: str, contexts: list[str]) -> str | None:
    """
    Attempt to call a real LLM if credentials are available.
    Returns None if no provider is configured — caller falls back to mock.
    """
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    context_block = "\n\n".join(contexts)
    prompt = (
        f"You are an HR assistant for Acme Corp. Answer using only the "
        f"provided context.\n\nContext:\n{context_block}\n\n"
        f"Question: {question}\nAnswer:"
    )

    if anthropic_key:
        try:
            import anthropic  # type: ignore
            client = anthropic.Anthropic(api_key=anthropic_key)
            msg = client.messages.create(
                model=os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception:
            return None

    if openai_key:
        try:
            import openai  # type: ignore
            client = openai.OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
            )
            return resp.choices[0].message.content
        except Exception:
            return None

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def answer(question: str, k: int = 3) -> dict[str, Any]:
    """
    Retrieve the top-k relevant chunks and generate an answer.

    Returns:
        {
            "answer": str,
            "contexts": list[str],   # raw retrieved text snippets
            "sources":  list[str],   # corpus filenames
            "mock": bool,            # True when using the mock generator
        }
    """
    if _RETRIEVER is None:
        return {
            "answer": "HR corpus not found. Check data/hr-corpus/ directory.",
            "contexts": [],
            "sources": [],
            "mock": True,
        }

    hits = _RETRIEVER.retrieve(question, k=k)
    contexts = [h["text"] for h in hits]
    sources = list(dict.fromkeys(h["source"] for h in hits))  # deduplicated, ordered

    real_answer = _real_generate(question, contexts)
    if real_answer is not None:
        return {"answer": real_answer, "contexts": contexts, "sources": sources, "mock": False}

    mock_answer = _mock_generate(question, contexts)
    return {"answer": mock_answer, "contexts": contexts, "sources": sources, "mock": True}


def corpus_info() -> dict[str, Any]:
    """Return basic stats about the loaded corpus (used by /health)."""
    return {
        "documents": len(_DOCS),
        "chunks": len(_CHUNKS),
        "corpus_path": str(_CORPUS_ROOT),
        "corpus_found": _CORPUS_ROOT.exists(),
    }
