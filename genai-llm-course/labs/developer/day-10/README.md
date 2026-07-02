# Day 10 Lab — Multi-Agent HR Assistant with Memory

## Objective

Extend the Day 9 tool-using HR agent into a **multi-agent system** with:

1. An **Orchestrator** that classifies queries and routes to the right specialist.
2. A **PolicyExpert** agent — RAG over the HR corpus (retrieves relevant policy docs).
3. An **HRCalculator** agent — handles numeric HR calculations (PTO days, salary %, etc.).
4. **Short-term memory** — rolling multi-turn conversation history.
5. **Long-term memory** — ChromaDB vector store that persists and retrieves past Q&A pairs.

A **deterministic mock path** lets you run the entire lab with no API key.

---

## Directory Layout

```
labs/developer/day-10/
├── README.md          ← this file
├── requirements.txt   ← dependencies
├── starter.py         ← your starting point (TODO markers)
└── solution.py        ← complete reference implementation
```

HR corpus lives at: `data/hr-corpus/` (repo root — 13 policy documents).

---

## Setup

```bash
# From repo root
cd /path/to/AI_Training
pip install -r labs/developer/day-10/requirements.txt
```

Optional — set API keys in a `.env` file at the repo root (not required):

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

---

## Run (Mock Mode — No Key Required)

```bash
# From repo root
python labs/developer/day-10/solution.py
```

The script auto-detects available providers. With no key set, it runs in **MOCK** mode with deterministic, pre-scripted responses that demonstrate routing and memory.

## Run (With API Key)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python labs/developer/day-10/solution.py
```

---

## What to Observe

The demo runs a **3-turn conversation**:

- Turn 1: Policy question → routed to **PolicyExpert** → answer retrieved from HR corpus.
- Turn 2: Follow-up referencing Turn 1 → short-term memory keeps context.
- Turn 3: Numeric calculation → routed to **HRCalculator** → long-term memory stores and retrieves past interactions.

After the conversation, the script prints a **memory report** showing what was stored.

---

## Lab Tasks (starter.py)

Work through the TODO markers in `starter.py` in order:

| TODO | Task |
|---|---|
| TODO 1 | Provider detection (anthropic / openai / mock) |
| TODO 2 | Implement `embed_text()` using sentence-transformers |
| TODO 3 | Implement `LongTermMemory.store()` — embed and upsert into ChromaDB |
| TODO 4 | Implement `LongTermMemory.retrieve()` — similarity search |
| TODO 5 | Implement `route_query()` — keyword/LLM-based routing |
| TODO 6 | Implement `PolicyExpert.run()` — RAG over HR corpus |
| TODO 7 | Implement `HRCalculator.run()` — numeric calculation handler |
| TODO 8 | Implement `Orchestrator.chat()` — glue: route → specialist → memory → history |
| TODO 9 | Wire up the 3-turn demo conversation |

---

## Concepts Exercised

- Orchestrator/router + specialist pattern
- Structured handoffs (typed `AgentResponse` dataclass)
- In-context conversation history (short-term memory)
- Summarisation trigger (automatic compaction when history > threshold)
- ChromaDB vector store (long-term memory, persists across runs)
- Loop/cost guardrails (`MAX_TURNS`, `MAX_TOKENS_BUDGET`)
- Provider-flexible + mock path
