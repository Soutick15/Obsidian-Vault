# Day 9 Lab — Tool-Using Agent (Framework-Free)

**Track:** Developer | **Day:** 9 | **Time:** ~60–75 min

---

## What You Will Build

A minimal, framework-free agent loop that answers a multi-step HR question:

> *"How many PTO days do I get after 2 years of service, and how many work-hours is that at 8 hours per day?"*

The agent has three tools:

| Tool | Purpose |
|---|---|
| `search_hr_docs` | RAG over the shared Acme HR corpus (reuses Day 7 approach) |
| `calculator` | Evaluates simple arithmetic expressions safely |
| `get_today` | Returns today's ISO date (demonstrates a zero-argument tool) |

---

## Provider Flexibility

The lab runs in two modes determined by environment variables:

| Mode | Trigger | Behaviour |
|---|---|---|
| **Real LLM** | `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` set | Full tool-calling via Claude (`claude-haiku-4-5`) or gpt-5-mini |
| **Mock agent** | No key set | Deterministic keyword-rule agent — same tools, same output, zero API cost |

The mock path is the **default** and is sufficient for completing all exercises.

---

## Setup

```bash
# From the repo root
cd /path/to/AI_Training

# Create a virtual environment (or reuse your existing one)
python3 -m venv labs/developer/day-09/.venv
source labs/developer/day-09/.venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r labs/developer/day-09/requirements.txt
```

**Optional** — set API keys in `.env` at the repo root to use real LLM mode:
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

---

## Running the Lab

```bash
# From the repo root (important — paths are resolved relative to repo root)
python labs/developer/day-09/solution.py
```

Expected output (mock mode, no key required):
```
=== Day 9 Agent — HR Policy Q&A ===
Mode: MOCK (no API key detected)

[Turn 1] Agent reasoning...
  -> Tool call: search_hr_docs({"query": "annual PTO days accrual years of service"})
  <- Result: 15 days (120 hours) for 0-2 years; 20 days (160 hours) for 3-5 years...

[Turn 2] Agent reasoning...
  -> Tool call: calculator({"expression": "15 * 8"})
  <- Result: 120

[Turn 3] Agent reasoning...
Final Answer: After 2 years of service you receive 15 PTO days per year. At 8 hours per day, that equals 120 work-hours of paid time off.
```

---

## Exercises (starter.py)

Open `labs/developer/day-09/starter.py` and complete the six `# TODO` sections:

1. **`build_hr_index()`** — load HR corpus files, chunk, embed with `sentence-transformers`, store in ChromaDB.
2. **`search_hr_docs()`** — embed the query and return the top-3 chunks.
3. **`calculator()`** — safely evaluate an arithmetic expression and return the result as a string.
4. **`execute_tool()`** — dispatch incoming tool-call requests to the right Python function.
5. **`mock_agent_step()`** — implement the keyword-rule mock that selects tools without an LLM.
6. **`run_agent()`** — implement the agent loop (real LLM or mock; loop until done or max iterations).

---

## File Layout

```
labs/developer/day-09/
├── README.md           # This file
├── requirements.txt    # Dependencies
├── starter.py          # Skeleton with TODOs
└── solution.py         # Complete working implementation
```

---

## Key Concepts Practised

- Tool schema design (JSON Schema)
- The tool-call cycle: request → execute → return result → continue
- ReAct-style reasoning trace in the mock agent
- RAG retrieval as a first-class tool
- Graceful error handling in tool execution
- `max_iterations` guard against infinite loops
