"""
Day 10 Lab — Multi-Agent HR Assistant with Memory  (STARTER)
=============================================================
Work through the TODO markers in order. Run solution.py if you get stuck.

Architecture:
  User ──► Orchestrator ──► PolicyExpert  (RAG over HR corpus)
                        └──► HRCalculator (numeric HR calcs)

Memory layers:
  - Short-term : rolling messages list (current session)
  - Long-term  : ChromaDB collection of past Q&A embeddings

Run with no API key (mock mode):
    python labs/developer/day-10/starter.py

Run with Anthropic key:
    export ANTHROPIC_API_KEY=sk-ant-...
    python labs/developer/day-10/starter.py
"""

from __future__ import annotations

import os
import re
import math
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Optional .env loading
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]
HR_CORPUS = REPO_ROOT / "data" / "hr-corpus"

# ---------------------------------------------------------------------------
# TODO 1 — Provider detection
#
# Read ANTHROPIC_API_KEY and OPENAI_API_KEY from env.
# Set PROVIDER to "anthropic", "openai", or "mock".
# Priority: anthropic > openai > mock
# ---------------------------------------------------------------------------
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_KEY    = os.getenv("OPENAI_API_KEY", "")

PROVIDER = "mock"  # TODO: replace with your detection logic

print(f"[config] Provider: {PROVIDER.upper()}")
print(f"[config] HR corpus: {HR_CORPUS}")

# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------
MAX_TURNS         = 10   # hard limit on orchestrator iterations
MAX_TOKENS_BUDGET = 5000 # cumulative token budget before aborting
HISTORY_COMPACT_AT = 6   # compact history after this many messages

# ---------------------------------------------------------------------------
# TODO 2 — Embedding function
#
# Implement embed_text(text: str) -> list[float]
# Use sentence-transformers model "all-MiniLM-L6-v2" (downloads automatically).
# In mock mode, return a deterministic fake vector (e.g. all zeros, length 384).
#
# Hint:
#   from sentence_transformers import SentenceTransformer
#   _model = SentenceTransformer("all-MiniLM-L6-v2")
#   return _model.encode(text).tolist()
# ---------------------------------------------------------------------------

def embed_text(text: str) -> list[float]:
    """Return a 384-dim embedding for text."""
    # TODO 2: implement
    raise NotImplementedError("TODO 2: implement embed_text")


# ---------------------------------------------------------------------------
# Long-Term Memory (ChromaDB)
# ---------------------------------------------------------------------------

class LongTermMemory:
    """Persists and retrieves Q&A pairs via ChromaDB + sentence-transformers."""

    def __init__(self, collection_name: str = "hr_agent_memory"):
        import chromadb
        self._client = chromadb.Client()  # in-memory; swap for PersistentClient for cross-session
        self._col = self._client.get_or_create_collection(collection_name)

    # TODO 3 — Implement store()
    #
    # Store a Q&A pair:
    #   1. Embed the question text using embed_text().
    #   2. Upsert into self._col with:
    #        ids       = [str(uuid.uuid4())]
    #        embeddings= [embedding]
    #        documents = [question]
    #        metadatas = [{"answer": answer, "agent": agent_name}]
    #
    def store(self, question: str, answer: str, agent_name: str) -> None:
        """Embed and store a Q&A pair."""
        # TODO 3: implement
        raise NotImplementedError("TODO 3: implement LongTermMemory.store")

    # TODO 4 — Implement retrieve()
    #
    # Retrieve the top-k most similar past Q&A pairs for a given query:
    #   1. Embed the query using embed_text().
    #   2. Query self._col:
    #        results = self._col.query(query_embeddings=[embedding], n_results=min(k, count))
    #   3. Return a list of dicts: [{"question": ..., "answer": ..., "agent": ...}, ...]
    #
    def retrieve(self, query: str, k: int = 3) -> list[dict]:
        """Return top-k past Q&A pairs most similar to query."""
        # TODO 4: implement
        raise NotImplementedError("TODO 4: implement LongTermMemory.retrieve")

    @property
    def count(self) -> int:
        return self._col.count()


# ---------------------------------------------------------------------------
# HR Corpus loader (shared by PolicyExpert)
# ---------------------------------------------------------------------------

def load_hr_corpus() -> list[dict]:
    """Load all .md files from the HR corpus. Returns list of {filename, content}."""
    docs = []
    if not HR_CORPUS.exists():
        print(f"[warn] HR corpus not found at {HR_CORPUS}")
        return docs
    for path in sorted(HR_CORPUS.glob("*.md")):
        if path.name == "README.md":
            continue
        docs.append({"filename": path.name, "content": path.read_text(encoding="utf-8")})
    return docs


def simple_retrieve(query: str, docs: list[dict], top_k: int = 2) -> list[dict]:
    """Keyword-based retrieval: score each doc by query word overlap."""
    query_words = set(re.findall(r'\w+', query.lower()))
    scored = []
    for doc in docs:
        words = set(re.findall(r'\w+', doc["content"].lower()))
        score = len(query_words & words)
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:top_k] if _ > 0]


# ---------------------------------------------------------------------------
# Typed agent response
# ---------------------------------------------------------------------------

@dataclass
class AgentResponse:
    agent: str
    answer: str
    tokens_used: int = 0
    source_docs: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Mock LLM (deterministic, no key needed)
# ---------------------------------------------------------------------------

# Calculator signals are checked FIRST (higher specificity than generic policy words).
MOCK_CALC_SIGNALS = [
    "calculat", "how many days", "how many do i have", "how much",
    "days left", "days remaining", "days do i have left", "have used",
    "have left", "i have", "prorat", "accrual rate", "math",
    "compute", "add up", "subtract", "minus", "percent of",
]

MOCK_POLICY_SIGNALS = [
    "policy", "what is the", "what are the", "tell me about",
    "benefits", "handbook", "insurance", "holiday", "expense",
    "reimburs", "remote work", "onboard", "recruit", "performance review",
    "code of conduct", "compensation", "promotion", "it security",
    "vacation", "parental leave", "sick leave policy",
]

def mock_route(query: str) -> str:
    q = query.lower()
    if any(sig in q for sig in MOCK_CALC_SIGNALS):
        return "calculator"
    if any(sig in q for sig in MOCK_POLICY_SIGNALS):
        return "policy"
    return "policy"  # default

MOCK_POLICY_ANSWERS = {
    "pto": "Per the Leave & PTO Policy, full-time employees accrue 15 days of PTO per year (1.25 days/month). Unused PTO up to 5 days rolls over annually.",
    "leave": "The Leave & PTO Policy covers annual leave, sick leave (10 days/year), and parental leave (12 weeks fully paid for primary caregivers).",
    "remote": "The Remote Work Policy allows up to 3 remote days per week for eligible roles. Core hours are 10 AM – 3 PM local time.",
    "default": "Based on the HR policy documents, employees should refer to the relevant policy section or contact HR directly for clarification.",
}

def mock_policy_answer(query: str) -> str:
    q = query.lower()
    for key, answer in MOCK_POLICY_ANSWERS.items():
        if key in q:
            return answer
    return MOCK_POLICY_ANSWERS["default"]

def mock_calc_answer(query: str) -> str:
    # simple pattern: "X days at Y% salary" or just return a canned answer
    return "Calculation (mock): Based on your inputs, the result is 12 days of accrued PTO. At a 20% salary increase, new annual salary would be $72,000."


# ---------------------------------------------------------------------------
# Specialist Agents
# ---------------------------------------------------------------------------

class PolicyExpert:
    """RAG specialist over the HR corpus."""

    def __init__(self):
        self._docs = load_hr_corpus()
        print(f"[PolicyExpert] Loaded {len(self._docs)} HR documents")

    # TODO 6 — Implement run()
    #
    # Steps:
    #   1. Call simple_retrieve(query, self._docs, top_k=2) to get relevant docs.
    #   2. Build a context string from the retrieved doc contents (first 800 chars each).
    #   3. In mock mode: call mock_policy_answer(query) for the answer text.
    #      In live mode: call the LLM with a system prompt + the context + user query.
    #   4. Return AgentResponse(agent="PolicyExpert", answer=..., source_docs=[filenames])
    #
    def run(self, query: str, history: list[dict]) -> AgentResponse:
        """Retrieve relevant HR policy docs and answer the query."""
        # TODO 6: implement
        raise NotImplementedError("TODO 6: implement PolicyExpert.run")


class HRCalculator:
    """Numeric HR calculation specialist."""

    # TODO 7 — Implement run()
    #
    # Steps:
    #   1. Try to extract numbers from the query using re.findall(r'\d+\.?\d*', query).
    #   2. Attempt simple math: if 2 numbers found, try multiply / divide / add based
    #      on keywords ("percent", "days", "multiply", "divide").
    #   3. In mock mode: call mock_calc_answer(query) for the answer.
    #      In live mode: call the LLM with a math-focused system prompt.
    #   4. Return AgentResponse(agent="HRCalculator", answer=...)
    #
    def run(self, query: str, history: list[dict]) -> AgentResponse:
        """Perform HR numeric calculations."""
        # TODO 7: implement
        raise NotImplementedError("TODO 7: implement HRCalculator.run")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Orchestrator:
    """
    Routes user queries to PolicyExpert or HRCalculator.
    Maintains short-term memory (messages list) and long-term memory (ChromaDB).
    """

    def __init__(self):
        self.policy_expert  = PolicyExpert()
        self.hr_calculator  = HRCalculator()
        self.long_term      = LongTermMemory()
        self.messages: list[dict] = []  # short-term memory
        self.total_tokens   = 0
        self.turn           = 0

    def _compact_history(self) -> None:
        """Summarise old messages when history grows long."""
        if len(self.messages) <= HISTORY_COMPACT_AT:
            return
        older = self.messages[:-4]
        recent = self.messages[-4:]
        summary_lines = [f"- {m['role'].upper()}: {m['content'][:120]}..." for m in older]
        summary = "Summary of earlier conversation:\n" + "\n".join(summary_lines)
        self.messages = [{"role": "system", "content": summary}] + recent
        print(f"[memory] History compacted ({len(older)} messages → summary)")

    # TODO 5 — Implement route_query()
    #
    # Classify the query as "policy" or "calculator".
    # In mock mode: call mock_route(query).
    # In live mode: use a short LLM prompt that classifies and returns one word.
    #
    def route_query(self, query: str) -> str:
        """Return 'policy' or 'calculator'."""
        # TODO 5: implement
        raise NotImplementedError("TODO 5: implement route_query")

    # TODO 8 — Implement chat()
    #
    # Full orchestration loop for one user turn:
    #   1. Guard: if self.turn >= MAX_TURNS or self.total_tokens >= MAX_TOKENS_BUDGET, abort.
    #   2. Increment self.turn.
    #   3. Retrieve relevant past Q&A from long-term memory (self.long_term.retrieve(query)).
    #   4. Append user message to self.messages (include memory hint if any past Q&A found).
    #   5. Compact history if needed (self._compact_history()).
    #   6. Route: call self.route_query(query) → "policy" or "calculator".
    #   7. Dispatch: call the appropriate specialist's .run(query, self.messages).
    #   8. Update self.total_tokens += response.tokens_used.
    #   9. Append assistant message to self.messages.
    #  10. Store Q&A in long-term memory: self.long_term.store(query, answer, agent).
    #  11. Return the AgentResponse.
    #
    def chat(self, query: str) -> AgentResponse:
        """Process one user turn through the full multi-agent pipeline."""
        # TODO 8: implement
        raise NotImplementedError("TODO 8: implement Orchestrator.chat")


# ---------------------------------------------------------------------------
# TODO 9 — Demo conversation
#
# Instantiate an Orchestrator and run a 3-turn conversation:
#   Turn 1: "What is the PTO policy for full-time employees?"
#   Turn 2: "Does that policy also cover sick leave?" (tests short-term memory)
#   Turn 3: "I have 15 days PTO and used 7. How many do I have left?" (calculator route)
#
# Print the route chosen and the answer for each turn.
# After all turns, print the long-term memory count.
# ---------------------------------------------------------------------------

def main():
    print("\n" + "="*60)
    print("Day 10 Lab — Multi-Agent HR Assistant (STARTER)")
    print("="*60 + "\n")

    # TODO 9: implement the 3-turn demo
    raise NotImplementedError("TODO 9: implement the demo conversation in main()")


if __name__ == "__main__":
    main()
