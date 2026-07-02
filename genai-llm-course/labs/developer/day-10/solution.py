"""
Day 10 Lab — Multi-Agent HR Assistant with Memory  (SOLUTION)
=============================================================
Complete reference implementation. Run with no key for mock mode.

Architecture:
  User ──► Orchestrator ──► PolicyExpert  (RAG over HR corpus)
                        └──► HRCalculator (numeric HR calcs)

Memory layers:
  - Short-term : rolling messages list (current session, auto-compacted)
  - Long-term  : ChromaDB in-memory collection of past Q&A embeddings

Usage:
    python labs/developer/day-10/solution.py
    ANTHROPIC_API_KEY=sk-ant-... python labs/developer/day-10/solution.py
"""

from __future__ import annotations

import os
import re
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
# Provider detection
# ---------------------------------------------------------------------------
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

if ANTHROPIC_KEY:
    PROVIDER = "anthropic"
elif OPENAI_KEY:
    PROVIDER = "openai"
else:
    PROVIDER = "mock"

print(f"[config] Provider : {PROVIDER.upper()}")
print(f"[config] HR corpus: {HR_CORPUS}")

# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------
MAX_TURNS = 10
MAX_TOKENS_BUDGET = 5000
HISTORY_COMPACT_AT = 6  # compact after this many messages in history

# ---------------------------------------------------------------------------
# Embedding  (sentence-transformers, local, free)
# ---------------------------------------------------------------------------
_embed_model = None


def embed_text(text: str) -> list[float]:
    """Return a 384-dim embedding. Falls back to a zero vector in pure-mock mode."""
    global _embed_model
    try:
        from sentence_transformers import SentenceTransformer

        if _embed_model is None:
            _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        return _embed_model.encode(text).tolist()
    except Exception:
        # fallback: deterministic hash-based pseudo-vector (no model needed)
        import hashlib
        import struct

        h = hashlib.sha256(text.encode()).digest()
        # repeat to fill 384 floats (384 * 4 bytes = 1536 bytes; sha256=32 bytes → repeat)
        raw = (h * 48)[: 384 * 4]
        floats = list(struct.unpack("384f", raw))
        # normalise to unit sphere
        norm = sum(x * x for x in floats) ** 0.5 or 1.0
        return [x / norm for x in floats]


# ---------------------------------------------------------------------------
# Long-Term Memory
# ---------------------------------------------------------------------------


class LongTermMemory:
    """Persists and retrieves Q&A pairs via ChromaDB + sentence-transformers."""

    def __init__(self, collection_name: str = "hr_agent_memory"):
        import chromadb

        self._client = (
            chromadb.Client()
        )  # in-memory; swap for PersistentClient for cross-session
        self._col = self._client.get_or_create_collection(collection_name)

    def store(self, question: str, answer: str, agent_name: str) -> None:
        """Embed and upsert a Q&A pair."""
        embedding = embed_text(question)
        self._col.upsert(
            ids=[str(uuid.uuid4())],
            embeddings=[embedding],
            documents=[question],
            metadatas=[{"answer": answer[:500], "agent": agent_name}],
        )

    def retrieve(self, query: str, k: int = 3) -> list[dict]:
        """Return top-k past Q&A pairs most similar to query."""
        n = self._col.count()
        if n == 0:
            return []
        embedding = embed_text(query)
        results = self._col.query(
            query_embeddings=[embedding],
            n_results=min(k, n),
        )
        out = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            out.append(
                {"question": doc, "answer": meta["answer"], "agent": meta["agent"]}
            )
        return out

    @property
    def count(self) -> int:
        return self._col.count()


# ---------------------------------------------------------------------------
# HR Corpus helpers
# ---------------------------------------------------------------------------


def load_hr_corpus() -> list[dict]:
    docs = []
    if not HR_CORPUS.exists():
        print(f"[warn] HR corpus not found at {HR_CORPUS}")
        return docs
    for path in sorted(HR_CORPUS.glob("*.md")):
        if (
            path.name == "README.md"
        ):  # skip README; corpus has 12 policy docs + 1 README
            continue
        docs.append(
            {"filename": path.name, "content": path.read_text(encoding="utf-8")}
        )
    return docs


def simple_retrieve(query: str, docs: list[dict], top_k: int = 2) -> list[dict]:
    """Keyword overlap retrieval — no embedding required."""
    query_words = set(re.findall(r"\w+", query.lower()))
    scored = []
    for doc in docs:
        words = set(re.findall(r"\w+", doc["content"].lower()))
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
# Mock helpers (deterministic — no API key)
# ---------------------------------------------------------------------------

# Calculator signals take priority — checked BEFORE policy keywords.
# Use multi-word phrases for high-precision matches, single words only where unambiguous.
MOCK_CALC_SIGNALS = [
    "calculat",
    "how many days",
    "how many do i have",
    "how much",
    "days left",
    "days remaining",
    "days do i have left",
    "have used",
    "have left",
    "i have",
    "prorat",
    "accrual rate",
    "math",
    "compute",
    "add up",
    "subtract",
    "minus",
    "percent of",
]

MOCK_POLICY_SIGNALS = [
    "policy",
    "what is the",
    "what are the",
    "tell me about",
    "benefits",
    "handbook",
    "insurance",
    "holiday",
    "expense",
    "reimburs",
    "remote work",
    "onboard",
    "recruit",
    "performance review",
    "code of conduct",
    "compensation",
    "promotion",
    "it security",
    "vacation",
    "parental leave",
    "sick leave policy",
]


def mock_route(query: str) -> str:
    q = query.lower()
    # Calculator wins if any high-specificity calc signal is present
    if any(sig in q for sig in MOCK_CALC_SIGNALS):
        return "calculator"
    # Fall back to policy for general HR knowledge queries
    if any(sig in q for sig in MOCK_POLICY_SIGNALS):
        return "policy"
    return "policy"


MOCK_POLICY_ANSWERS = {
    "pto": (
        "Per the Leave & PTO Policy, full-time employees accrue 15 days of PTO per year "
        "(1.25 days/month). Unused PTO up to 5 days rolls over annually."
    ),
    "sick": (
        "The Leave & PTO Policy grants 10 days of paid sick leave per calendar year, "
        "separate from PTO. Unused sick leave does not roll over."
    ),
    "leave": (
        "Leave types include annual PTO (15 days/year), sick leave (10 days/year), and "
        "parental leave (12 weeks fully paid for primary caregivers, 4 weeks for secondary)."
    ),
    "remote": (
        "The Remote Work Policy allows up to 3 remote days per week for eligible roles. "
        "Core hours are 10 AM – 3 PM local time. Home-office equipment is reimbursed up to $500."
    ),
    "expense": (
        "The Expense & Reimbursement Policy requires receipts for all expenses over $25. "
        "Claims must be submitted within 30 days. Per-diem meal allowance is $75/day for travel."
    ),
    "holiday": (
        "2026 public holidays include: 1 Jan, 18 Jan (MLK Day), 30 Mar (Good Friday), "
        "25 May (Memorial Day), 3 Jul (Independence Day observed), 7 Sep (Labor Day), "
        "26 Nov (Thanksgiving), 25 Dec (Christmas). Total: 11 days."
    ),
    "default": (
        "Based on the HR policy documents, employees should refer to the relevant policy "
        "section or contact HR at hr@company.com for clarification."
    ),
}


def mock_policy_answer(query: str) -> str:
    q = query.lower()
    for key, answer in MOCK_POLICY_ANSWERS.items():
        if key in q:
            return answer
    return MOCK_POLICY_ANSWERS["default"]


def mock_calc_answer(query: str) -> str:
    """Simple deterministic calc from numbers in the query."""
    nums = re.findall(r"\d+\.?\d*", query)
    if len(nums) >= 2:
        a, b = float(nums[0]), float(nums[1])
        if any(
            w in query.lower()
            for w in ["left", "remaining", "minus", "subtract", "used"]
        ):
            result = a - b
            return (
                f"Calculation: {a} - {b} = {result:.0f}. "
                f"You have {result:.0f} days remaining."
            )
        if "percent" in query.lower() or "%" in query:
            result = a * b / 100
            return (
                f"Calculation: {b}% of {a} = {result:.2f}. "
                f"At a {b:.0f}% increase, your new value would be {a + result:.2f}."
            )
        result = a + b
        return f"Calculation: {a} + {b} = {result:.0f}."
    return (
        "Calculation (mock): Please provide specific numbers for an exact result. "
        "Example: '15 days PTO, used 7 — how many remain?'"
    )


# ---------------------------------------------------------------------------
# Live LLM helpers
# ---------------------------------------------------------------------------


def llm_call(
    system: str, messages: list[dict], max_tokens: int = 400
) -> tuple[str, int]:
    """
    Call the configured provider. Returns (text, tokens_used).
    Falls back gracefully if library not installed.
    """
    if PROVIDER == "anthropic":
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
            resp = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            text = resp.content[0].text
            tokens = resp.usage.input_tokens + resp.usage.output_tokens
            return text, tokens
        except Exception as e:
            print(f"[warn] Anthropic call failed ({e}); falling back to mock")

    if PROVIDER == "openai":
        try:
            import openai

            client = openai.OpenAI(api_key=OPENAI_KEY)
            all_msgs = [{"role": "system", "content": system}] + messages
            resp = client.chat.completions.create(
                model="gpt-5-mini",
                messages=all_msgs,
                max_tokens=max_tokens,
            )
            text = resp.choices[0].message.content
            tokens = resp.usage.total_tokens
            return text, tokens
        except Exception as e:
            print(f"[warn] OpenAI call failed ({e}); falling back to mock")

    return "", 0  # caller handles mock branch


# ---------------------------------------------------------------------------
# Specialist Agents
# ---------------------------------------------------------------------------


class PolicyExpert:
    """RAG specialist: retrieves relevant HR policy docs and answers queries."""

    def __init__(self):
        self._docs = load_hr_corpus()
        print(f"[PolicyExpert] Loaded {len(self._docs)} HR documents")

    def run(self, query: str, history: list[dict]) -> AgentResponse:
        retrieved = simple_retrieve(query, self._docs, top_k=2)
        source_fnames = [d["filename"] for d in retrieved]

        if PROVIDER == "mock" or not retrieved:
            answer = mock_policy_answer(query)
            if retrieved:
                answer += f"\n[Sources: {', '.join(source_fnames)}]"
            return AgentResponse(
                agent="PolicyExpert",
                answer=answer,
                tokens_used=50,  # simulated
                source_docs=source_fnames,
            )

        # Live path: build RAG context
        context_parts = []
        for doc in retrieved:
            snippet = doc["content"][:800]
            context_parts.append(f"### {doc['filename']}\n{snippet}")
        context = "\n\n".join(context_parts)

        system = (
            "You are an HR PolicyExpert. Answer the user's question using ONLY the provided "
            "HR policy documents. Be concise (2-4 sentences). If the answer is not in the "
            "documents, say 'This is not covered in the provided policy documents.'"
        )
        msgs = list(history[-4:]) + [
            {
                "role": "user",
                "content": f"HR Policy Context:\n{context}\n\nQuestion: {query}",
            }
        ]
        text, tokens = llm_call(system, msgs)
        if not text:
            text = mock_policy_answer(query)
            tokens = 50

        return AgentResponse(
            agent="PolicyExpert",
            answer=text,
            tokens_used=tokens,
            source_docs=source_fnames,
        )


class HRCalculator:
    """Numeric HR calculation specialist."""

    def run(self, query: str, history: list[dict]) -> AgentResponse:
        if PROVIDER == "mock":
            answer = mock_calc_answer(query)
            return AgentResponse(
                agent="HRCalculator",
                answer=answer,
                tokens_used=30,
            )

        system = (
            "You are an HR Calculator assistant. Perform precise numeric calculations for HR "
            "topics such as PTO accrual, salary adjustments, leave balances, and expense totals. "
            "Show your working. Be concise."
        )
        msgs = list(history[-4:]) + [{"role": "user", "content": query}]
        text, tokens = llm_call(system, msgs)
        if not text:
            text = mock_calc_answer(query)
            tokens = 30

        return AgentResponse(
            agent="HRCalculator",
            answer=text,
            tokens_used=tokens,
        )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class Orchestrator:
    """
    Routes user queries to specialists.
    Maintains short-term memory (messages) and long-term memory (ChromaDB).
    """

    def __init__(self):
        self.policy_expert = PolicyExpert()
        self.hr_calculator = HRCalculator()
        self.long_term = LongTermMemory()
        self.messages: list[dict] = []
        self.total_tokens = 0
        self.turn = 0

    # ------------------------------------------------------------------
    # Short-term memory compaction
    # ------------------------------------------------------------------
    def _compact_history(self) -> None:
        if len(self.messages) <= HISTORY_COMPACT_AT:
            return
        older = self.messages[:-4]
        recent = self.messages[-4:]
        lines = [f"- {m['role'].upper()}: {m['content'][:120]}" for m in older]
        summary = "Summary of earlier conversation:\n" + "\n".join(lines)
        self.messages = [{"role": "system", "content": summary}] + recent
        print(f"  [memory] History compacted ({len(older)} msgs → summary)")

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    def route_query(self, query: str) -> str:
        if PROVIDER == "mock":
            return mock_route(query)

        system = (
            "Classify this HR assistant query into exactly one category.\n"
            "Categories:\n"
            "  policy     — questions about HR policies, benefits, rules, procedures\n"
            "  calculator — requests for numeric calculations, leave balances, salary math\n\n"
            "Reply with only the single word: policy  OR  calculator"
        )
        text, tokens = llm_call(
            system, [{"role": "user", "content": query}], max_tokens=5
        )
        self.total_tokens += tokens
        route = text.strip().lower()
        if "calc" in route:
            return "calculator"
        return "policy"

    # ------------------------------------------------------------------
    # Main orchestration loop (one user turn)
    # ------------------------------------------------------------------
    def chat(self, query: str) -> AgentResponse:
        # Guardrails
        if self.turn >= MAX_TURNS:
            return AgentResponse(
                "Orchestrator",
                "Session turn limit reached. Please start a new session.",
            )
        if self.total_tokens >= MAX_TOKENS_BUDGET:
            return AgentResponse(
                "Orchestrator", "Token budget exhausted. Please start a new session."
            )

        self.turn += 1
        print(f"\n  [turn {self.turn}] Query: {query[:80]}")

        # Long-term memory retrieval
        past = self.long_term.retrieve(query, k=2)
        memory_hint = ""
        if past:
            snippets = "\n".join(
                f"  Q: {p['question']}\n  A: {p['answer'][:120]}" for p in past
            )
            memory_hint = f"\n\n[Relevant past interactions]\n{snippets}"
            print(
                f"  [memory] Retrieved {len(past)} past Q&A pair(s) from long-term store"
            )

        # Append user message (with memory hint if available)
        user_content = query + memory_hint
        self.messages.append({"role": "user", "content": user_content})

        # Compact if needed
        self._compact_history()

        # Route
        route = self.route_query(query)
        print(f"  [route ] → {route.upper()}")

        # Dispatch
        if route == "calculator":
            response = self.hr_calculator.run(query, self.messages)
        else:
            response = self.policy_expert.run(query, self.messages)

        # Track tokens
        self.total_tokens += response.tokens_used

        # Append assistant message
        self.messages.append({"role": "assistant", "content": response.answer})

        # Store in long-term memory
        self.long_term.store(query, response.answer, response.agent)
        print(
            f"  [memory] Stored Q&A in long-term memory (total: {self.long_term.count})"
        )

        return response


# ---------------------------------------------------------------------------
# Demo conversation
# ---------------------------------------------------------------------------


def main():
    print("\n" + "=" * 60)
    print("Day 10 Lab — Multi-Agent HR Assistant with Memory")
    print("=" * 60)

    orc = Orchestrator()

    turns = [
        "What is the PTO policy for full-time employees?",
        "Does that policy also cover sick leave?",
        "I have 15 days PTO and have used 7. How many days do I have left?",
    ]

    print()
    for i, query in enumerate(turns, 1):
        print(f"\n{'─' * 55}")
        print(f"USER [{i}]: {query}")
        resp = orc.chat(query)
        print(f"AGENT   : {resp.agent}")
        if resp.source_docs:
            print(f"SOURCES : {', '.join(resp.source_docs)}")
        print(f"ANSWER  : {resp.answer}")

    # Summary
    print(f"\n{'=' * 55}")
    print("SESSION SUMMARY")
    print(f"  Turns completed : {orc.turn}")
    print(f"  Tokens used     : {orc.total_tokens}")
    print(f"  Long-term store : {orc.long_term.count} Q&A pair(s)")
    print(f"  Short-term msgs : {len(orc.messages)}")
    print()
    print("Long-term memory contents:")
    for pair in orc.long_term.retrieve("policy leave calculation", k=5):
        print(f"  [{pair['agent']}] Q: {pair['question'][:60]}...")
    print()
    print("Done. Re-run to see long-term memory retrieval from a fresh session.")
    print(
        "  (Swap chromadb.Client() for chromadb.PersistentClient(path=...) to persist across runs.)"
    )


if __name__ == "__main__":
    main()
