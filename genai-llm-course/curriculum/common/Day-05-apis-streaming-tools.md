# Day 5 — The API in Depth: Messages, Streaming & Tool Calling

> **Week 1 · Day 5 of 15** | Mini-project day — caps the foundations week.

---

## 1. Learning Objectives

By the end of this day you will be able to:

1. Construct a correctly-shaped `messages` API request for both Claude (Anthropic) and OpenAI, understanding every field in the request and response.
2. Consume a streaming response in Python, printing tokens as they arrive.
3. Implement a single-tool calling round-trip: define a tool schema, detect when the model requests a call, execute it, and return the result.
4. Describe multimodal image inputs at a high level and know when to reach for them.
5. Handle practical production concerns: token/usage accounting, retry on rate limits, error categories, and timeouts.

---

## 2. Concept Reading

### 2.1 The Messages API — Shape & Fields

Both Anthropic (Claude) and OpenAI use the same conceptual shape. Understanding the overlap makes you provider-flexible, which is what clients expect.

#### 2.1.1 Anthropic (Claude) — request anatomy

```python
import anthropic

client = anthropic.Anthropic(api_key="sk-ant-...")

response = client.messages.create(
    model="claude-haiku-4-5",        # which model to call
    max_tokens=1024,                  # hard ceiling on output tokens
    temperature=0.7,                  # 0=deterministic, 1=default, >1=creative
    system="You are a helpful assistant.",  # optional system prompt (string)
    messages=[                        # conversation history
        {"role": "user",    "content": "What is 12 * 7?"},
        {"role": "assistant","content": "The answer is 84."},
        {"role": "user",    "content": "Now add 100."},
    ],
)

print(response.content[0].text)      # "184"
print(response.usage)                # input_tokens, output_tokens
```

Key Claude-specific points:
- `system` is a **top-level field**, not a message with `role: "system"`.
- `content` in the response is a **list** of content blocks (`TextBlock`, `ToolUseBlock`, etc.).
- `stop_reason`: `"end_turn"`, `"max_tokens"`, `"tool_use"`, or `"stop_sequence"`.

#### 2.1.2 OpenAI (GPT) — request anatomy

```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")

response = client.chat.completions.create(
    model="gpt-5-mini",
    max_tokens=1024,
    temperature=0.7,
    messages=[
        {"role": "system",    "content": "You are a helpful assistant."},
        {"role": "user",      "content": "What is 12 * 7?"},
        {"role": "assistant", "content": "The answer is 84."},
        {"role": "user",      "content": "Now add 100."},
    ],
)

print(response.choices[0].message.content)
print(response.usage)   # prompt_tokens, completion_tokens, total_tokens
```

Key OpenAI-specific points:
- `system` is a **message** with `role: "system"` at index 0 of the list.
- Response is `response.choices[0].message.content` (a string, not a list).
- `finish_reason`: `"stop"`, `"length"`, `"tool_calls"`, `"content_filter"`.

#### 2.1.3 Multi-turn conversations

The API is **stateless** — every request must carry the entire conversation history. You maintain state in your application:

```python
history = []

def chat(user_input: str, system: str = "") -> str:
    history.append({"role": "user", "content": user_input})
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        system=system,
        messages=history,
    )
    assistant_text = response.content[0].text
    history.append({"role": "assistant", "content": assistant_text})
    return assistant_text
```

**Practical concern:** as history grows it consumes input tokens and cost. Production apps truncate, summarize, or use sliding-window strategies.

#### 2.1.4 Side-by-side field comparison

| Concept | Claude (Anthropic) | OpenAI |
|---|---|---|
| System prompt | Top-level `system=` field | `{"role":"system","content":"..."}` |
| User turn | `{"role":"user","content":"..."}` | Same |
| Assistant turn | `{"role":"assistant","content":"..."}` | Same |
| Temperature range | 0–1 (recommended) | 0–2 |
| Response text | `response.content[0].text` | `response.choices[0].message.content` |
| Token usage | `response.usage.input_tokens` | `response.usage.prompt_tokens` |
| Stop reason | `response.stop_reason` | `response.choices[0].finish_reason` |
| Tool signal | `stop_reason == "tool_use"` | `finish_reason == "tool_calls"` |

---

### 2.2 Streaming Responses

#### Why stream?

Without streaming, the user stares at a blank screen until the entire response is generated — 5–30 seconds for long outputs. Streaming sends each token as soon as it's produced, so the UI feels fast even for long replies. This is the standard UX pattern for chat interfaces (ChatGPT, Claude.ai, etc.).

Streaming uses **Server-Sent Events (SSE)**: the HTTP connection stays open and the server sends small `data:` frames. Each frame contains a JSON chunk with one or a few tokens.

#### Streaming with Claude

```python
with client.messages.stream(
    model="claude-haiku-4-5",
    max_tokens=512,
    messages=[{"role": "user", "content": "Tell me a short story."}],
) as stream:
    for text_chunk in stream.text_stream:
        print(text_chunk, end="", flush=True)   # print token-by-token
    print()  # newline at end
    final = stream.get_final_message()           # full Message object
    print(f"\nTokens used: {final.usage.input_tokens} in / {final.usage.output_tokens} out")
```

#### Streaming with OpenAI

```python
stream = client.chat.completions.create(
    model="gpt-5-mini",
    max_tokens=512,
    messages=[{"role": "user", "content": "Tell me a short story."}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
print()
```

#### Key streaming concepts

- **`flush=True`** on `print()`: Python buffers stdout; flush forces each chunk to appear immediately.
- **Usage stats** are only available in the final event (or via `stream.get_final_message()` in the Anthropic SDK). With the Claude SDK, `usage` appears on the object returned by `get_final_message()`, not on individual streamed chunks.
- **Tool calls** can also be streamed, though for clarity beginners often disable streaming when calling tools.

---

### 2.3 Tool / Function Calling

Tool calling (also called "function calling") lets the model request execution of real-world functions. The model does NOT execute code — it outputs a structured JSON request, your code runs the function, then you feed the result back for the model to incorporate.

#### The tool-calling loop

```
User message
    ↓
[1] POST /messages  (with tool definitions)
    ↓
Model returns stop_reason="tool_use"  → contains tool name + args
    ↓
[2] Your code executes the real function
    ↓
[3] POST /messages  (append tool_result to history)
    ↓
Model returns final text answer
```

#### Step 1 — Define the tool schema (Claude)

```python
tools = [
    {
        "name": "calculate",
        "description": "Evaluate a simple arithmetic expression and return the numeric result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A Python-evaluable arithmetic expression, e.g. '3 * (7 + 2)'"
                }
            },
            "required": ["expression"],
        },
    }
]
```

For OpenAI the wrapper key is `"type": "function"` and the schema lives under `"function"`:

```python
tools_oai = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a simple arithmetic expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"],
            },
        },
    }
]
```

#### Step 2 — First request (Claude example)

```python
response = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=512,
    tools=tools,
    messages=[{"role": "user", "content": "What is (45 * 3) + 17?"}],
)

if response.stop_reason == "tool_use":
    tool_block = next(b for b in response.content if b.type == "tool_use")
    tool_name  = tool_block.name          # "calculate"
    tool_input = tool_block.input         # {"expression": "45 * 3 + 17"}
    tool_id    = tool_block.id            # unique call ID
```

#### Step 3 — Execute and return result (Claude)

```python
import ast, operator

def safe_calc(expr: str) -> float:
    # naive safe eval — production code would use a proper parser
    allowed = {ast.Add: operator.add, ast.Sub: operator.sub,
               ast.Mult: operator.mul, ast.Div: operator.truediv}
    def _eval(node):
        if isinstance(node, ast.Constant): return node.value
        if isinstance(node, ast.BinOp):
            return allowed[type(node.op)](_eval(node.left), _eval(node.right))
        raise ValueError("Unsafe expression")
    return _eval(ast.parse(expr, mode='eval').body)

result = safe_calc(tool_input["expression"])  # 152.0

# Append assistant turn + tool result, then call again
messages = [
    {"role": "user",      "content": "What is (45 * 3) + 17?"},
    {"role": "assistant", "content": response.content},       # include tool_use block
    {"role": "user",      "content": [                        # tool_result block
        {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": str(result),
        }
    ]},
]

final = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=512,
    tools=tools,
    messages=messages,
)
print(final.content[0].text)  # "(45 × 3) + 17 = 152"
```

#### Step 3 (OpenAI) — return the tool result

For OpenAI the tool result is appended as a separate message after the assistant message that contained `tool_calls`:

```python
messages.append(choice.message)            # assistant message with tool_calls list
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,          # must match the id in tool_calls[0].id
    "content": str(result),                # result as a string
})
# then call client.chat.completions.create() again with the updated messages
```

#### Why tool calling matters

- Grounds the model in real data (current time, live prices, DB queries).
- Enables structured side effects (send email, update record).
- Forms the core of agent systems (Day 9 goes deep on agents).

---

### 2.4 Multimodal Inputs (Images)

Both providers support sending images alongside text. The model "sees" the image and can answer questions about it.

```python
# Claude — base64 image
import base64

with open("chart.png", "rb") as f:
    img_data = base64.b64encode(f.read()).decode()

response = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=512,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_data,
                },
            },
            {"type": "text", "text": "Summarize this chart in one paragraph."},
        ],
    }],
)
```

Key points:
- Images count as tokens (roughly 1000–1700 tokens per image depending on size/provider).
- Supported formats: PNG, JPEG, GIF, WebP.
- URLs are also accepted (pass `"type": "url"` with `"url": "https://..."`) for providers that support it.
- Use cases: document understanding, chart reading, UI screenshot analysis, OCR, visual QA.

---

### 2.5 Practical Production Concerns

#### Token / usage accounting

Every API response includes a usage object. Track these to manage costs:

```python
usage = response.usage
# Claude:  usage.input_tokens, usage.output_tokens
# OpenAI:  usage.prompt_tokens, usage.completion_tokens, usage.total_tokens

cost_estimate = (usage.input_tokens / 1_000_000) * 0.25  # Claude Haiku pricing ~$0.25/Mtok in
```

**Tip:** log `(model, input_tokens, output_tokens, timestamp)` to a file or DB so you can track spend over time.

#### Retries and rate limits

Providers return HTTP 429 (rate limit) or 529 (overloaded) under heavy load. The correct strategy:

```python
import time, anthropic

def create_with_retry(client, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return client.messages.create(**kwargs)
        except anthropic.RateLimitError as e:
            wait = 2 ** attempt          # exponential backoff: 1s, 2s, 4s
            print(f"Rate limited. Waiting {wait}s…")
            time.sleep(wait)
        except anthropic.APIStatusError as e:
            if e.status_code in (500, 529) and attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
    raise RuntimeError("Max retries exceeded")
```

The Anthropic Python SDK ≥0.20 has built-in retry with `max_retries=` on the client constructor.

#### Error categories

| Error type | Cause | Action |
|---|---|---|
| `AuthenticationError` (401) | Bad API key | Check env var; don't retry |
| `PermissionDeniedError` (403) | Model not available on plan | Switch model or upgrade |
| `NotFoundError` (404) | Invalid model ID | Fix the model name |
| `RateLimitError` (429) | Too many requests | Exponential backoff |
| `APIStatusError` (500/529) | Provider outage | Retry with backoff |
| `APITimeoutError` | Request took too long | Retry or increase timeout |

#### Timeouts

```python
import httpx

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    timeout=httpx.Timeout(60.0, connect=5.0),  # 60s read, 5s connect
    max_retries=2,
)
```

---

## 3. Hands-On Lab

**Lab location:** `labs/common/day-05/`

**What you'll build:** A CLI assistant that:
- Holds a multi-turn conversation (remembers context across messages)
- Streams the response token-by-token to the terminal
- Can call a `calculate` tool when you ask a math question

**Provider detection:**
- If `ANTHROPIC_API_KEY` is set → uses real Claude streaming + tools
- Elif `OPENAI_API_KEY` is set → uses real OpenAI streaming + tools
- Otherwise → runs a deterministic **mock** that simulates streaming and auto-triggers the tool

**Files:**

```
labs/common/day-05/
├── README.md          # setup, run commands, expected output
├── requirements.txt   # anthropic, openai (both optional)
├── starter.py         # skeleton with TODO markers
└── solution.py        # complete working implementation
```

**Run (no API key needed):**
```bash
cd labs/common/day-05
python solution.py
```

**Run with a real key:**
```bash
ANTHROPIC_API_KEY=sk-ant-... python solution.py
```

See `labs/common/day-05/README.md` for full instructions.

---

## 4. Self-Check Quiz

Answer these before looking at the answers. They test whether you actually understood the concepts, not just skimmed them.

---

**Q1.** You're building a multi-turn chat app with the Anthropic API. After five exchanges, your 6th request fails with "messages must alternate user/assistant roles." What's the most likely cause?

<details>
<summary>Show answer</summary>

You appended the assistant reply to `history` but didn't include it — or you accidentally added two user messages in a row. The API requires strict alternating roles. Check that each `messages.create()` call ends with a user message, and that the history list strictly alternates `user → assistant → user → assistant → …`.

</details>

**Q2.** What does `flush=True` do in `print(chunk, end="", flush=True)` and why is it needed for streaming?

<details>
<summary>Show answer</summary>

Python buffers stdout by default — text accumulates in a buffer and only appears when the buffer fills or the program ends. `flush=True` forces the buffer to write immediately after each `print()` call. Without it, streaming tokens would all appear at once at the end, defeating the purpose.

</details>

**Q3.** A user asks "What time is it?" The model returns `stop_reason = "tool_use"` with `tool_name = "get_current_time"`. What exact steps must your code take before calling the API again?

<details>
<summary>Show answer</summary>

1. Extract `tool_id`, `tool_name`, and `tool_input` from the `tool_use` content block.
2. Execute `get_current_time()` locally.
3. Append the **assistant's full response content** (the tool_use block) as an `assistant` message to history.
4. Append a `user` message containing a `tool_result` block with `tool_use_id`, `content` (the result), and `type: "tool_result"`.
5. Call `messages.create()` again with the updated history.

</details>

**Q4.** What is the difference between how Claude and OpenAI handle the system prompt in their messages arrays?

<details>
<summary>Show answer</summary>

Claude accepts `system` as a **separate top-level parameter** (`system="…"`) — it is not a message in the list. OpenAI embeds it as the first element of the `messages` list with `role: "system"`. This is a common source of bugs when writing provider-flexible code.

</details>

**Q5.** Your app is receiving HTTP 429 errors. You add a `time.sleep(60)` before every retry. What's wrong with this approach?

<details>
<summary>Show answer</summary>

A fixed 60-second wait is too long most of the time (rate limits often clear in seconds) and may still be too short during heavy load. The correct approach is **exponential backoff**: wait 1s, then 2s, then 4s, etc., often with a small random jitter. The Anthropic SDK also offers built-in retry with `max_retries=` on the client.

</details>

**Q6.** An image you send with a Claude request is 1024×1024 pixels. Roughly how many tokens does it consume, and how does that affect your `max_tokens` setting?

<details>
<summary>Show answer</summary>

A large image consumes roughly 1000–1700 input tokens. These count against your **context window** (input side) but not against `max_tokens`, which only limits the output. However, if total input tokens (text + images) approach the context limit, the model may truncate or error. Budget accordingly.

</details>

**Q7.** What does `stop_reason = "max_tokens"` tell you, and what should you do about it?

<details>
<summary>Show answer</summary>

It means the model hit the output token limit before finishing its answer — the response is truncated. You should either: (a) increase `max_tokens`, (b) ask the model for a shorter response via your prompt, or (c) send a follow-up message asking the model to continue (be careful — it may repeat context).

</details>

**Q8.** True or False: the model executes the function/tool code directly when it outputs a `tool_use` block.

<details>
<summary>Show answer</summary>

**False.** The model only outputs a *request* in JSON form — `{"name": "calculate", "input": {"expression": "3+4"}}`. Your application code is entirely responsible for executing the function and returning the result. The model has no ability to run code directly.

</details>

---

## 5. Concept Deep-Dive Q&A

These questions test deeper, applied understanding of the day's concepts on APIs, streaming, and tool use.

---

**Q1. "Walk me through how tool calling works end-to-end."**

<details>
<summary>Show answer</summary>

Tool calling is a two-request loop. In the first request, you send the user's message along with a list of tool definitions — each is a JSON schema describing the tool's name, purpose, and parameters. If the model determines a tool is needed, it returns early with `stop_reason = "tool_use"` and a structured JSON block containing the tool name and arguments it wants passed. Your application code then executes the real function locally. You add the assistant's tool-request block and your function's result (as a `tool_result` message) to the conversation history, then send a second API request. The model reads the result and produces the final answer. The model never executes code itself — it only requests execution.

</details>

**Q2. "Why would you use streaming in a production application? What are the trade-offs?"**

<details>
<summary>Show answer</summary>

Streaming dramatically improves perceived latency. Without it, the user waits 5–30 seconds before seeing any output. With streaming, the first tokens appear within ~200ms, which feels interactive. The trade-off: streaming complicates error handling (you've already started writing to the UI when a mid-stream error occurs), makes it harder to post-process the full response before displaying it (e.g., filtering, parsing JSON), and usage stats only arrive at the end of the stream. For simple chat UIs, streaming is almost always worth it. For batch processing or when you need to validate the full response before showing it, non-streaming is simpler.

</details>

**Q3. "How do you handle rate limits in a production LLM application?"**

<details>
<summary>Show answer</summary>

Rate limits mean you've exceeded the provider's tokens-per-minute or requests-per-minute quota. The correct pattern is exponential backoff with jitter: catch the 429 error, wait 2^attempt seconds (plus a random 0–1s jitter to avoid thundering herd), and retry up to a maximum number of attempts. Most modern SDKs (Anthropic, OpenAI) have `max_retries` built in, so you often don't need to implement this manually. For high-throughput systems you also want to track your token usage against the rate limit budget and throttle proactively. At scale, a request queue with a leaky-bucket rate controller is the proper architecture.

</details>

**Q4. "How does a multi-turn conversation work under the hood? Why is it stateless?"**

<details>
<summary>Show answer</summary>

LLM APIs are stateless — every request is independent. There is no server-side session. To create a multi-turn conversation you maintain the full message history in your application and send it with every request. The model reads the entire history and produces the next reply. This means cost and latency grow with conversation length. In production you manage this by truncating old messages, summarizing older context, or using dedicated memory systems. The stateless design is intentional: it makes the API horizontally scalable and gives developers full control over what context the model sees.

</details>

**Q5. "What's the difference between `max_tokens` and the context window?"**

<details>
<summary>Show answer</summary>

`max_tokens` is a **hard cap on output length** — it limits how many tokens the model is allowed to generate in one response. The **context window** is the total token budget for a single forward pass, covering both input (system prompt + conversation history + tool definitions) and output combined. If your input is 3000 tokens and the context window is 4096, you have at most 1096 tokens available for output regardless of what `max_tokens` says. Setting `max_tokens` higher than the remaining context window budget has no effect — the model simply stops when the window fills.

</details>

**Q6. "How would you let an LLM access a live database during a conversation?"**

<details>
<summary>Show answer</summary>

I'd use tool calling. I'd define a tool schema for, say, `query_database` with parameters like `table`, `filter`, and `limit`. The model, when it needs data, outputs a `tool_use` block with its query intent. My code intercepts this, translates it into a safe SQL query (parameterized, never built from raw model output), executes it against the DB, and returns the rows as a JSON string in a `tool_result` block. The model then incorporates the data into its answer. Security is critical — always validate and sanitize tool inputs before execution; treat them like untrusted user input.

</details>

**Q7. "When comparing Claude and GPT-4 for a new chat feature, how do you approach the evaluation?"**

<details>
<summary>Show answer</summary>

I'd ask a few clarifying questions first: what's the primary use case, what's the volume and budget, do they have an existing cloud relationship, and are there data residency requirements? Technically, both are excellent for chat. Claude tends to excel at long-context tasks, nuanced instruction-following, and being more conservative about harmful outputs by default. GPT-4 has a broader ecosystem and more third-party integrations. For a new project I'd recommend a provider-flexible architecture: abstract the API call behind a thin provider interface so you can swap models without rewriting application logic. Then run an eval on your actual data before committing — benchmark differences on your specific task matter far more than general benchmarks.

</details>

**Q8. "Explain Server-Sent Events. Why does streaming use SSE rather than WebSockets?"**

<details>
<summary>Show answer</summary>

SSE (Server-Sent Events) is a one-directional HTTP-based protocol: the server holds open an HTTP/1.1 or HTTP/2 connection and pushes `data:` frames as they become available. It uses plain HTTP, works through proxies and firewalls, has automatic reconnect built into browsers, and requires no protocol upgrade. WebSockets are bidirectional and more complex to proxy/scale. For LLM streaming the communication is inherently one-directional (server → client) once the request is sent, making SSE the simpler and more robust choice. At the Python level you just iterate over the stream — the SSE framing is handled by the SDK.

</details>

**Q9. "What are the main error types you need to handle when calling an LLM API?"**

<details>
<summary>Show answer</summary>

I group them into three buckets. **Don't retry**: authentication errors (401 — fix the key), permission errors (403 — fix the plan/model), and validation errors (400 — fix the request shape). **Retry with backoff**: rate limit (429), service overloaded (529), and server errors (500). **Retry with a longer timeout or reduced payload**: timeout errors. In addition I watch for `stop_reason = "max_tokens"` which isn't an HTTP error but signals a truncated response, and `content_filter` which means the request was blocked by safety systems. Good production code wraps every API call in structured error handling with logging.

</details>

**Q10. "How do images affect token usage and cost?"**

<details>
<summary>Show answer</summary>

Images are converted into tokens before processing — a typical 1024×1024 image costs roughly 1000–1700 input tokens depending on the provider's tiling strategy. These count against the context window and are billed as input tokens. For cost-sensitive applications this matters a lot: one image can cost as much as 1000+ words of text. Strategies to manage this: resize images before sending (smaller = fewer tokens), use lower-resolution thumbnails when full resolution isn't needed, and cache responses when the same image is repeatedly queried. Always confirm the per-image token cost in the provider's documentation for the specific model you're using.

</details>

---

## 6. Further Reading

| Resource | Why read it |
|---|---|
| [Anthropic Messages API reference](https://docs.anthropic.com/en/api/messages) | Definitive field-by-field reference for the Claude API |
| [Anthropic Tool Use guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) | Full tool calling documentation with examples |
| [Anthropic Streaming guide](https://docs.anthropic.com/en/api/messages-streaming) | SSE stream events, best practices |
| [OpenAI Chat Completions reference](https://platform.openai.com/docs/api-reference/chat) | OpenAI's equivalent API docs |
| [OpenAI Function Calling guide](https://platform.openai.com/docs/guides/function-calling) | OpenAI's tool/function calling walkthrough |
| [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) | SSE protocol explained from first principles |
| [Anthropic SDK (Python) — GitHub](https://github.com/anthropics/anthropic-sdk-python) | Source code; see `examples/` for streaming and tool patterns |
| [OpenAI Python SDK — GitHub](https://github.com/openai/openai-python) | Equivalent for OpenAI |
| [Exponential Backoff And Jitter — AWS Blog](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) | Why jitter matters; classic reference |

---

## 7. Key Takeaways

- **Messages API shape:** provider-flexible code keeps the provider abstracted behind a thin wrapper. The key difference is system-prompt placement (top-level vs first message).
- **Conversation state is yours to manage:** the API is stateless; you send full history every request. This scales well but grows cost with conversation length.
- **Streaming = perceived speed:** SSE delivers tokens as generated; `flush=True` is required to show them in real time.
- **Tool calling is a two-request loop:** model → requests tool → you execute → you return result → model answers. The model never runs code.
- **Error handling is non-negotiable in production:** authenticate once, retry with exponential backoff on 429/5xx, never retry on 4xx config errors.
- **Images cost tokens:** a single image can consume 1000–1700 input tokens; budget accordingly and resize when full resolution isn't needed.
- **`max_tokens` vs context window:** `max_tokens` caps output; context window caps input + output combined. Both limits matter.

---

## Week 1 Review

### What We Covered (Days 1–5)

| Day | Topic | Core skill gained |
|---|---|---|
| 1 | LLM landscape, tokens & embeddings | Tokenize text; compute cosine similarity |
| 2 | Transformer architecture & attention | Understand how attention shapes model behaviour |
| 3 | Generation, decoding & model selection | Tune temperature/top-p; pick the right model |
| 4 | Prompt engineering | Few-shot, chain-of-thought, structured output |
| 5 | Messages API, streaming & tools | Build a streaming multi-turn CLI assistant with tool calling |

### Week 1 Competency Checklist

After completing Days 1–5 you should be able to:

- [ ] Explain what a token is and why costs scale with token count.
- [ ] Describe self-attention and why transformers replaced RNNs.
- [ ] Choose temperature, top-p, and model size for a given task.
- [ ] Write effective zero-shot, few-shot, and chain-of-thought prompts.
- [ ] Construct a valid `messages.create()` call for both Claude and OpenAI.
- [ ] Maintain a multi-turn conversation history correctly in Python.
- [ ] Stream a response token-by-token and display it in real time.
- [ ] Implement a complete tool-calling round-trip (define schema → detect request → execute → return result).
- [ ] Handle rate limits with exponential backoff.
- [ ] Describe the difference between `max_tokens` and the context window.
- [ ] Explain clearly how tool calling works and why streaming matters for user experience.

### Next: Choose Your Track (Days 6–15)

Days 1–5 are the shared foundation everyone completes. From here the course **splits into three role-based tracks** — continue on the track assigned to you. Each track is 10 days (Days 6–15) and ends with a hands-on capstone.

- **Developer — building LLM applications:** embeddings & vector search, RAG, agents, fine-tuning, and deployment.
  → `curriculum/developer/Day-06-embeddings-vector-search.md`
- **QA — testing & automating LLM systems:** evaluation harnesses, LLM-as-judge, AI-assisted test automation, and red-teaming.
  → `curriculum/qa/Day-06-llm-systems-under-test.md`
- **DevOps — running LLM systems in production:** serving, scaling, observability, reliability, security, and CI/CD.
  → `curriculum/devops/Day-06-llm-systems-to-operate.md`

See the [README](../../README.md) for the full per-track day-by-day map. All three tracks build on the same foundation you just completed.
