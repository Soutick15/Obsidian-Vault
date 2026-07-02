# Cheatsheets — Quick Reference

Skeleton sections; each is expanded in the linked curriculum day. Use this file as your field reference when building.

---

## Prompting Patterns

> Expanded in **Day 4** (prompt engineering) with worked examples and anti-patterns.

Key patterns to know:

- **Zero-shot** — instruction only, no examples.
- **Few-shot** — instruction + 2–5 input/output examples in the prompt.
- **Chain-of-thought (CoT)** — ask the model to reason step-by-step before answering ("Think step by step…").
- **Self-consistency** — sample multiple CoT paths, take the majority answer.
- **ReAct** — interleave Thought / Action / Observation turns for agentic tasks.
- **Structured output** — instruct the model to return JSON or a fixed schema; validate with a parser.
- **System prompt layering** — persona + constraints in system; task in user turn.

*Full pattern catalogue with templates: see Day-04-prompt-engineering.md.*

---

## API Quick-Reference — Claude + OpenAI

> Expanded in **Day 5** (messages, streaming, tools).

### Anthropic Claude (messages API)

```python
import anthropic, os
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Basic completion
response = client.messages.create(
    model="claude-haiku-4-5",          # cheapest model for dev/test
    max_tokens=1024,
    system="You are a helpful assistant.",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.content[0].text)

# Streaming
with client.messages.stream(model="claude-haiku-4-5", max_tokens=512,
                             messages=[{"role": "user", "content": "Count to 5"}]) as s:
    for text in s.text_stream:
        print(text, end="", flush=True)

# Tool / function calling — stub; see Day 5 for full schema
response = client.messages.create(
    model="claude-haiku-4-5", max_tokens=512,
    tools=[{"name": "get_weather", "description": "...", "input_schema": {...}}],
    messages=[{"role": "user", "content": "What's the weather in London?"}],
)
```

### OpenAI (chat completions API)

```python
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Basic completion
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[{"role": "system", "content": "You are helpful."},
              {"role": "user",   "content": "Hello"}],
)
print(response.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="gpt-5-mini", stream=True,
    messages=[{"role": "user", "content": "Count to 5"}],
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)

# Tool calling — stub; see Day 5
response = client.chat.completions.create(
    model="gpt-5-mini",
    tools=[{"type": "function", "function": {"name": "get_weather", "parameters": {...}}}],
    messages=[{"role": "user", "content": "Weather in London?"}],
)
```

*Full parameter table (temperature, top_p, stop, max_tokens, tool_choice): Day-05-apis-streaming-tools.md.*

---

## RAG Pipeline Steps

> Expanded in **Day 7** (basic RAG) and **Day 8** (advanced retrieval & evaluation).

```
1. INGEST
   Load documents (PDF, HTML, plain text) → split into chunks
   Chunk params: chunk_size=512 tokens, overlap=64 tokens

2. EMBED
   chunks → embedding model → float vectors
   Free/local: sentence-transformers (all-MiniLM-L6-v2)
   API: text-embedding-3-small (OpenAI) | voyage-2 (Anthropic partner)

3. INDEX
   vectors → vector store (FAISS for local, Chroma for persistent)
   store with metadata: source, chunk_id, page_number

4. RETRIEVE  (at query time)
   query → embed → ANN search → top-k chunks
   Optional: hybrid search (BM25 + dense), re-ranking (cross-encoder)

5. AUGMENT
   Build prompt: system + retrieved chunks as context + user question

6. GENERATE
   Send augmented prompt to LLM → stream response

7. EVALUATE
   Faithfulness (is the answer grounded in context?)
   Answer relevancy (does it answer the question?)
   Context recall (did retrieval find the right chunks?)
   Tools: RAGAS, TruLens, custom LLM-as-judge
```

*Full implementation walkthrough: Day-07-rag-basics.md and Day-08-rag-advanced.md.*

---

## Agent / Tool-Calling Shape

> Expanded in **Day 9** (agents & tool use) and **Day 10** (multi-agent orchestration).

### ReAct loop (pseudocode)

```
while not done:
    Thought = LLM("Given [history], what should I do next?")
    if Thought signals final answer:
        return FinalAnswer
    Action = LLM selects tool + arguments
    Observation = execute(tool, arguments)
    history.append(Thought + Action + Observation)
```

### Tool definition shape (provider-agnostic concept)

```python
tool = {
    "name": "search_web",
    "description": "Search the web and return a snippet.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"}
        },
        "required": ["query"],
    },
}
```

### Multi-agent roles (Day 10)

| Role | Responsibility |
|------|----------------|
| Supervisor | Decomposes task, routes sub-tasks to workers |
| Worker | Executes one specialised sub-task with its own tool set |
| Memory | Stores conversation and session state across turns |

*Full implementation with LangChain / direct API: Day-09-agents-tools.md, Day-10-multiagent-memory.md.*
