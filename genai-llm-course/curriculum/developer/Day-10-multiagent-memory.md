
# Day 10 — Multi-Agent Patterns & Agent Memory

**Track:** Developer | **Week:** 2 | **Day:** 10 of 15

---

## 1. Objectives

By the end of this day you will be able to:

- Describe four core multi-agent patterns (orchestrator/router, sequential pipeline, worker/specialist, debate/critic) and know when each applies.
- Explain the trade-offs of multi-agent systems: improved modularity and specialisation vs. added latency, cost, and failure surface.
- Implement short-term conversation memory (in-context history + summarisation/compaction) and long-term memory (embedding-based vector store of past Q&A).
- Design clean handoffs between agents, including typed messages and termination conditions.
- Apply guardrails to prevent runaway loops and control cost.
- Name at least two orchestration frameworks and explain what problem they solve.

---

## 2. Concept Reading

### 2.1 Why Multiple Agents?

A single LLM call is powerful but limited: it has one context window, one system prompt, and one "personality". Real tasks often require *specialisation*, *parallelism*, or *iterative critique*. Multi-agent systems address this by decomposing work across agents that communicate via structured messages.

The core promise: **each agent is small, focused, and testable**. The downside: orchestration adds latency, cost, and new failure modes (dropped messages, loops, conflicting outputs). Apply multi-agent only when the added complexity is justified.

---

### 2.2 Multi-Agent Patterns

#### Pattern 1 — Orchestrator / Router + Workers

An **Orchestrator** receives the user request and decides *which* specialist agent to invoke. It does not answer directly; it routes.

```
User ──► Orchestrator ──► PolicyExpert  ──► Orchestrator ──► User
                     └──► HRCalculator ──┘
```

**When to use:** The task space is well-partitioned (HR policy vs. calculations, coding vs. research). The router is typically a cheap, fast model.

**Trade-offs:** Extra LLM call per turn (the routing call). Requires a routing prompt that is stable under paraphrase.

#### Pattern 2 — Sequential Pipeline

Agents form a chain: A → B → C. Each agent refines the output of the previous one.

```
Drafter → Editor → FactChecker → Formatter
```

**When to use:** Tasks with clear stages (draft → review → format). Easy to reason about; failures are localised.

**Trade-offs:** Latency grows linearly with pipeline length. An error early in the chain propagates downstream.

#### Pattern 3 — Parallel Worker / Specialist Pool

The orchestrator fans out the same query (or sub-queries) to multiple specialists simultaneously and merges results.

```
Orchestrator ──► SpecialistA ──┐
             ├──► SpecialistB ──┼──► Merger
             └──► SpecialistC ──┘
```

**When to use:** Sub-tasks are independent (e.g. retrieve from three different knowledge bases in parallel). Reduces total latency vs. sequential calls.

**Trade-offs:** Increased token spend; requires a merging/synthesis step that can itself be expensive.

#### Pattern 4 — Debate / Critic

One agent generates a draft; a second agent critiques it; the first (or a judge) revises.

```
Generator ──► Critic ──► Generator (revised) ──► [repeat or stop]
```

**When to use:** High-stakes outputs (legal docs, safety checks, code review) where one pass is insufficient.

**Trade-offs:** Latency multiplied by iteration count; risk of infinite loop if no stopping criterion is defined.

---

### 2.3 When Multi-Agent *Helps* vs. When It *Adds Cost / Latency / Failure*

| Situation | Single agent | Multi-agent |
|---|---|---|
| Simple Q&A over one domain | ✅ Better | ❌ Overkill |
| Heterogeneous tasks (policy + maths + code) | ❌ Brittle | ✅ Cleaner |
| Critique / adversarial review needed | ❌ Self-serving | ✅ Debate pattern |
| Tight latency budget | ✅ One round-trip | ❌ Multiple hops |
| Large context that exceeds one window | ❌ Truncates | ✅ Distribute |
| Small, well-defined problem | ✅ Simple | ❌ Over-engineered |

**Rule of thumb:** start single-agent; add agents only when you can name the specific failure mode each agent fixes.

---

### 2.4 Agent Memory

Agents forget everything between API calls unless you explicitly give them memory. There are three layers:

#### Short-Term Memory — Conversation History

The simplest form: pass the full `messages` list on every call.

```python
messages = []
messages.append({"role": "user", "content": "What is the PTO policy?"})
# ... call LLM ...
messages.append({"role": "assistant", "content": response_text})
# Next turn: pass the same messages list
```

Limitation: context windows are finite. A long conversation eventually exceeds the limit.

#### Summarisation / Compaction

When history grows long, summarise older turns and replace them with a compact summary:

```python
if token_count(messages) > THRESHOLD:
    summary = summarise(messages[:-KEEP_LAST_N])
    messages = [{"role": "system", "content": f"Summary of earlier conversation: {summary}"}] \
               + messages[-KEEP_LAST_N:]
```

This keeps the effective memory window unlimited at the cost of some fidelity.

#### Long-Term Memory — Vector Store of Past Interactions

Persist Q&A pairs as embeddings. On each new query, retrieve semantically similar past interactions and inject them into the prompt as context.

```
Query → embed → similarity search over past Q&A → inject top-k results → LLM call
```

This enables the agent to "remember" conversations from previous sessions. Typical implementation: ChromaDB or FAISS with `sentence-transformers` for embeddings.

---

### 2.5 State & Workflow Design

Each agent needs to know:
1. **Its role** — system prompt defines identity and constraints.
2. **The conversation so far** — short-term memory.
3. **Relevant past context** — long-term memory retrieval.
4. **What to hand back** — a typed result (text, structured JSON, tool call).

Design your state object early. A common pattern:

```python
@dataclass
class AgentState:
    session_id: str
    messages: list[dict]       # short-term
    retrieved_memories: list   # long-term hits
    route: str                 # which specialist was chosen
    turn: int
```

---

### 2.6 Handoffs Between Agents

A **handoff** is a structured transfer of state from one agent to another. Key principles:

- **Explicit, not implicit** — the orchestrator passes a typed message, not raw prose.
- **Include context** — the specialist receives enough context to answer without re-reading the full conversation.
- **Include constraints** — "Answer only from HR policy documents; do not speculate."
- **Define the return format** — JSON preferred so the orchestrator can parse and merge.

---

### 2.7 Guardrails on Loops and Cost

Without guardrails, a debate loop or orchestrator retry can run indefinitely.

| Guardrail | Implementation |
|---|---|
| Max iterations | `if turn >= MAX_TURNS: break` |
| Max tokens spent | Track cumulative tokens; abort if over budget |
| Loop detection | Hash last N outputs; break if identical |
| Timeout | `asyncio.wait_for(...)` with a wall-clock limit |
| Confidence threshold | Stop critic loop when score > THRESHOLD |

Always log which agent ran and how many tokens it consumed.

---

### 2.8 Orchestration Frameworks (Brief Note)

Several frameworks wrap the patterns above into higher-level abstractions:

| Framework | Key abstraction |
|---|---|
| **LangGraph** | State machine / graph of nodes (agents) + edges (transitions) |
| **AutoGen (Microsoft)** | Chat-based multi-agent with GroupChat |
| **CrewAI** | Role-based agents with tasks and crews |
| **Semantic Kernel** | Plugin + planner model for .NET / Python |
| **LlamaIndex Workflows** | Event-driven agent steps |

These frameworks reduce boilerplate but add dependencies and lock-in. For learning purposes, building from primitives (as in today's lab) is more instructive.

---

## 3. Hands-On Lab

**Location:** `labs/developer/day-10/`

**What you will build:** Extend the Day 9 HR-docs retriever agent into a small multi-agent system:

- An **Orchestrator** that routes user queries to the right specialist.
- A **PolicyExpert** agent that does RAG over the HR corpus (carries forward the Day 9 retriever).
- An **HRCalculator** agent that handles numeric HR calculations (leave days, salary percentages, etc.).
- **Short-term memory** via rolling conversation history.
- **Long-term memory** via ChromaDB embeddings of past Q&A pairs.
- A **deterministic mock path** so the lab runs with zero API keys.

See `labs/developer/day-10/README.md` for full setup and run instructions.

---

## 4. Self-Check Quiz

**Instructions:** Answer each question before revealing the answer.

**Q1.** In the orchestrator/router pattern, which agent talks directly to the user?




The **orchestrator** handles the user-facing conversation. Specialists (workers) only receive structured messages from the orchestrator and return structured results back to it; they never talk directly to the user.



---

**Q2.** A sequential pipeline has four stages. Stage 2 produces a hallucination. What happens in stages 3 and 4?




Stages 3 and 4 process the hallucinated output as if it were correct — they have no way to know it is wrong unless a fact-checking agent is explicitly included. This is the key risk of sequential pipelines: errors propagate downstream.



---

**Q3.** You have a 20-turn conversation and the context window is nearly full. What technique keeps the agent from losing all earlier context?




**Summarisation / compaction**: compress earlier turns into a short summary, prepend that as a system message, and keep only the most recent N turns in full. This maintains an effective unlimited memory at the cost of some fidelity.



---

**Q4.** What is the difference between short-term and long-term agent memory?




- **Short-term memory** lives in the current context window (the `messages` list). It is lost when the session ends.
- **Long-term memory** is persisted externally (e.g., a vector store). Q&A pairs from past sessions are embedded and retrieved via similarity search, injecting relevant past knowledge into new sessions.



---

**Q5.** Name two guardrails that prevent a debate/critic loop from running forever.




Any two of: (1) **max iteration count** (`turn >= MAX_TURNS`), (2) **token budget cap**, (3) **loop detection** (hash last N outputs), (4) **wall-clock timeout**, (5) **confidence threshold** (stop when critic score exceeds a threshold).



---

**Q6.** When should you prefer a *single* agent over a multi-agent system?




When the task is **homogeneous** (one domain, one skill set), the **latency budget is tight**, or the problem is **small and well-defined**. Adding agents only makes sense when you can name a specific failure mode that multi-agent architecture fixes.



---

**Q7.** What does LangGraph add over writing multi-agent orchestration by hand?




LangGraph provides a **state machine / graph abstraction**: nodes are agents/functions, edges are transitions. It handles state passing, conditional routing, cycles, and checkpointing out of the box, reducing orchestration boilerplate — at the cost of a framework dependency and learning curve.



---

**Q8.** In a parallel worker pattern, an orchestrator fans out to three specialists. What extra step is always required?




A **merging / synthesis step**: the orchestrator (or a dedicated merger agent) must combine the three specialist outputs into a single coherent response before returning it to the user.



---

## 5. Concept Deep-Dive Q&A

**Q1.** How do you design a routing prompt that is robust to paraphrase and ambiguous queries?




Use a **few-shot classification prompt** that maps diverse phrasings to a fixed set of route labels. Include at minimum 2–3 examples per route. For ambiguous inputs, instruct the router to return a **confidence score** alongside the label; if confidence is below a threshold, route to a **disambiguation** path (ask the user a clarifying question) rather than guessing. Regularly evaluate the router on a held-out set of real queries and update examples when it misclassifies.



---

**Q2.** What are the failure modes unique to multi-agent systems that do not exist in single-agent systems?




Key failure modes include: (1) **message loss** — an agent returns no output and the orchestrator hangs; (2) **conflicting outputs** — two specialists give contradictory answers and the merger produces an incoherent blend; (3) **cascade failure** — an early pipeline stage error propagates unchecked; (4) **infinite loops** — debate/critic cycles with no stopping criterion; (5) **context fragmentation** — each specialist sees only a slice of the full conversation and misses important context; (6) **cost explosion** — each routing hop multiplies token spend; (7) **prompt injection across agents** — malicious content from one agent's output corrupts the next agent's prompt.



---

**Q3.** How does summarisation-based compaction differ from RAG-based long-term memory, and when would you use each?




**Summarisation/compaction** compresses the *current session's* history into a rolling summary that stays in the context window. It is lossless at the sentence level but lossy at the detail level; all information is still "in context" in compressed form.

**RAG-based long-term memory** indexes *past sessions* as embeddings and retrieves only the *most semantically relevant* past Q&A on each turn. It can recall information from months ago but only surfaces what the retriever ranks as relevant — less relevant past facts are not injected.

Use compaction when you need the agent to track the *flow* of the current conversation (e.g., "as I mentioned two turns ago…"). Use long-term RAG when the agent should recall *facts established in previous sessions* (e.g., "last week you told me your leave balance is X").



---

**Q4.** Describe a concrete strategy for passing state between an orchestrator and a specialist agent without leaking full conversation history into the specialist's context.




Construct a **specialist brief**: extract only the fields the specialist needs — the current query, relevant retrieved documents, and a short summary of prior turns relevant to this sub-task. Pass this as a structured input (JSON or a formatted system prompt). The specialist never receives the raw full `messages` list. This keeps specialist context small (lower cost, lower distraction) and prevents the specialist from "going off-script" based on tangential earlier context.



---

**Q5.** What embedding model trade-offs matter when choosing between `all-MiniLM-L6-v2` and `all-mpnet-base-v2` for long-term memory retrieval?




`all-MiniLM-L6-v2` is ~22 M parameters, produces 384-dim vectors, and runs in ~15–30 ms per sentence on CPU. It is excellent for high-throughput, latency-sensitive applications. `all-mpnet-base-v2` is ~110 M parameters, produces 768-dim vectors, and is 3–5× slower but consistently outperforms MiniLM on retrieval benchmarks (BEIR suite). For HR Q&A memory retrieval where latency is not critical (pre-conversation), `mpnet` gives higher recall. For real-time in-conversation retrieval under a <100 ms budget, `MiniLM` is the safer choice.



---

**Q6.** How would you implement a "cost guardrail" that aborts an orchestrator loop when cumulative token spend exceeds a budget?




Track a `total_tokens` counter. After each LLM call, add the tokens reported by the API response (`usage.input_tokens + usage.output_tokens` for Anthropic; `usage.prompt_tokens + usage.completion_tokens` for OpenAI). Before each new call, check `if total_tokens + estimated_next_call > BUDGET: raise CostLimitExceeded(...)`. In mock mode, simulate token counts deterministically. Log the final token tally so operators can tune the budget. Optionally expose a `remaining_budget_pct` field in the agent state so downstream agents can self-throttle (e.g., produce shorter responses when budget is low).



---

**Q7.** In a debate pattern, how do you prevent the critic from becoming sycophantic (always approving the generator's output)?




Include an explicit **adversarial instruction** in the critic's system prompt: "Your role is to find flaws, not to validate. You MUST identify at least one specific issue per review. If the answer is genuinely correct, say so but explain exactly why it is correct rather than just approving it." Use **structured output** (JSON with fields `issues: list[str]`, `score: int 1–5`, `approved: bool`) so you can detect an empty `issues` list mechanically. If `issues` is empty too often in evaluation runs, tighten the adversarial instruction or add few-shot examples of rigorous critiques.



---

**Q8.** What is the semantic difference between an agent *tool call* (Day 9) and an agent *handoff* (Day 10)?




A **tool call** invokes a deterministic function (search index, calculator, API) that returns a value. The calling agent remains in control; it uses the returned value to compose its final answer. A **handoff** transfers *responsibility and context* to another LLM-backed agent. The receiving agent exercises its own reasoning, may make its own tool calls, and returns a *synthesised answer* rather than a raw value. Handoffs are higher-level, more expensive, and introduce a second point of potential failure or hallucination.



---

## 6. Further Reading

> **Note to maintainers:** add these entries to `resources/glossary.md` and `resources/cheatsheets.md` as appropriate.

### Papers & Articles

- **"Agents" (Anthropic, 2024)** — <https://www.anthropic.com/research/building-effective-agents> — canonical patterns for effective LLM agents including multi-agent considerations.
- **"ReAct: Synergizing Reasoning and Acting in Language Models"** (Yao et al., 2023) — <https://arxiv.org/abs/2210.03629> — the reasoning-action loop underlying most modern agents.
- **"MemGPT: Towards LLMs as Operating Systems"** (Packer et al., 2023) — <https://arxiv.org/abs/2310.08560> — a deep treatment of hierarchical memory for agents.
- **"AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation"** (Wu et al., 2023) — <https://arxiv.org/abs/2308.08155> — Microsoft's multi-agent framework paper.

### Documentation

- **LangGraph** — <https://langchain-ai.github.io/langgraph/> — state-machine orchestration for agents.
- **ChromaDB** — <https://docs.trychroma.com/> — open-source vector database used in today's lab.
- **sentence-transformers** — <https://www.sbert.net/> — local embedding models (no API key required).
- **Anthropic Agents guide** — <https://docs.anthropic.com/en/docs/build-with-claude/agents>

### Glossary Additions (for `resources/glossary.md`)

| Term | Definition |
|---|---|
| Orchestrator | An agent that receives user input and routes to specialist agents; does not generate end-user answers directly. |
| Specialist / Worker agent | An agent with a narrow, focused capability invoked by an orchestrator. |
| Sequential pipeline | A multi-agent pattern where agents form a chain, each processing the previous agent's output. |
| Debate / Critic pattern | A multi-agent pattern where a generator and critic iterate to improve output quality. |
| Short-term memory | In-context conversation history passed with each LLM call; lost at session end. |
| Long-term memory | Persisted embeddings of past interactions, retrieved via similarity search across sessions. |
| Summarisation / compaction | Technique to compress older conversation turns into a summary, freeing context window space. |
| Handoff | Structured transfer of responsibility and context from one agent to another. |
| Loop guardrail | A hard limit (max turns, token budget, timeout) that prevents infinite agent loops. |

---

## 7. Key Takeaways

1. **Four patterns cover most multi-agent use cases:** orchestrator/router, sequential pipeline, parallel workers, and debate/critic. Know which to reach for and why.
2. **The lab implements Pattern 1 (orchestrator/router):** the orchestrator routes each query to one specialist at a time (serially), not Pattern 3 (parallel workers) — specialists are never invoked concurrently in the lab.
3. **Multi-agent is not free** — every routing hop adds latency, token cost, and a new failure point. Apply only when a single agent demonstrably fails.
4. **Memory has three layers:** in-context history (short-term), summarisation/compaction (extended short-term), and vector-store retrieval (long-term, cross-session).
5. **Handoffs must be explicit and typed** — passing raw conversation prose between agents leads to context pollution and unpredictable behaviour.
6. **Guardrails are non-negotiable** — always cap iterations, token spend, and wall-clock time before deploying any loop-capable agent system.
7. **Frameworks (LangGraph, AutoGen, CrewAI) reduce boilerplate** but add abstraction overhead. Building from primitives first produces better intuition.
8. **Mock paths are essential** — every multi-agent lab and production system should have a deterministic mock path for testing without API spend.
