# Day 5 — The API in Depth: Messages, Streaming & Tool Calling

**Week 1 — Foundations** | Prerequisite: Day 4 (prompt engineering, the `messages` format)

---

## 1. Learning Objectives

By the end of Day 5 you will be able to:

1. Explain what happens, step by step, when your code "calls an API" — and construct a correctly-shaped `messages` request for both Claude (Anthropic) and OpenAI.
2. Explain why streaming makes a chat interface feel fast, and consume a streaming response in Python, printing words as they arrive.
3. Explain the tool-calling round trip in plain language, and implement it: define a tool, detect when the model requests it, run it, and hand back the result.
4. Describe multimodal image inputs at a high level and know when to reach for them.
5. Handle practical, everyday concerns: reading token/usage numbers, and retrying safely when a request fails.

---

## 2. Concept Reading

### 2.1 What Happens When You "Call an API"

Every time you use Claude.ai, ChatGPT, or any AI-powered app, the same basic exchange happens under the hood:

1. Your app sends the model a list of **messages** — the conversation so far, plus your new question.
2. The model reads all of it and writes a reply.
3. Your app gets that reply back and shows it to you.

That's it. There's no persistent "session" running on the model's side between requests — every single call is self-contained: you send the *whole* conversation, and you get one reply back. This is why the format matters so much: get the shape of that "list of messages" wrong, and the request fails before the model even sees it.

The rest of today builds on that one idea: what exactly goes in the message list, how the reply comes back (all at once, or word by word), and what happens when the model wants your code to run something on its behalf before it can answer.

**Recap:** An API call is a request containing the conversation so far, and a response containing the model's reply. Nothing is remembered between calls unless you resend it.

---

### 2.2 The Messages Format — Claude & OpenAI

Both Anthropic (Claude) and OpenAI use the same basic shape: a `messages` list, where each entry has a `role` (`"user"` or `"assistant"`) and `content` (the text). You saw this in Day 4. Today you'll see the *rest* of the request — the fields around that list — and exactly what comes back.

#### 2.2.1 Anthropic (Claude) — request and response

```python
import anthropic

client = anthropic.Anthropic(api_key="sk-ant-...")

response = client.messages.create(
    model = "claude-haiku-4-5",        # which model to call
    max_tokens = 1024,                  # hard ceiling on output tokens
    temperature = 0.7,                  # 0=deterministic, 1=default, >1=creative
    system="You are a helpful assistant.",  # optional system prompt (string)
    messages=[                        # conversation history
        {
	        "role": "user",
	        "content": "What is 12 * 7?"
        },
        {
	        "role": "assistant",
	        "content": "The answer is 84."
	    },
        {
	        "role": "user",
	        "content": "Now add 100."
	    },
    ],
)

print(response.content[0].text)      # "184"
print(response.usage)                # input_tokens, output_tokens
```

Key Claude-specific points:
- `system` is a **top-level field**, not a message with `role: "system"`.
- `content` in the response is a **list** of content blocks (`TextBlock`, `ToolUseBlock`, etc.) — you read the reply from `response.content[0].text`.
- `stop_reason` tells you *why* the model stopped: `"end_turn"`, `"max_tokens"`, `"tool_use"`, or `"stop_sequence"`.

#### 2.2.2 OpenAI (GPT) — request and response

```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")

response = client.chat.completions.create(
    model = "gpt-5.4-mini",
    max_tokens = 1024,
    temperature = 0.7,
    messages = [
        {
	        "role": "system",
	        "content": "You are a helpful assistant."
		},
        {
	        "role": "user",
	        "content": "What is 12 * 7?"
	    },
        {
	        "role": "assistant",
	        "content": "The answer is 84."
	    },
        {
	        "role": "user",
	        "content": "Now add 100."
	    },
    ],
)

print(response.choices[0].message.content)
print(response.usage)   # prompt_tokens, completion_tokens, total_tokens
```

Key OpenAI-specific points:
- `system` is a **message** with `role: "system"` at index 0 of the list — not a separate parameter.
- The reply is `response.choices[0].message.content` (a plain string, not a list).
- `finish_reason` tells you why the model stopped: `"stop"`, `"length"`, `"tool_calls"`, `"content_filter"`.

#### 2.2.3 Side-by-side field comparison

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

**Recap:** Both providers send a `messages` list and return a reply — the differences are mostly *where the system prompt lives* and *how you dig the text out of the response*.

---

### 2.3 Multi-Turn Conversations Are Stateless

Because nothing is remembered between calls, *your application* is responsible for keeping track of the conversation — appending each new turn to a list, and sending the whole list back every time:

```python
history = []

def chat(user_input: str, system: str = "") -> str:
    history.append(
	    {
		    "role": "user",
		    "content": user_input
		}
	)
    response = client.messages.create(
        model = "claude-haiku-4-5",
        max_tokens = 512,
        system = system,
        messages = history,
    )
    assistant_text = response.content[0].text
    history.append(
	    {
		    "role": "assistant",
			"content": assistant_text
		}
	)
    return assistant_text
```

**Practical concern:** as `history` grows, it takes more input tokens (and costs more) with every call. Production apps truncate, summarize, or use a sliding window of recent turns rather than sending an ever-growing transcript forever.

**Recap:** The API has no memory of its own — your code holds the conversation in a list and resends it on every call.

---

### 2.4 Streaming — "Words Arrive As They're Written"

#### Why stream?

Without streaming, you send a request and then... wait. Nothing appears on screen until the *entire* reply is finished generating — anywhere from 1 to 30 seconds for a long answer. Streaming changes that: instead of waiting for the whole reply, the model sends each word (technically, each small chunk of a word, called a token) the moment it's produced. Your screen fills in as the model "thinks out loud." This is the same trick behind ChatGPT and Claude.ai's live-typing effect.

Under the hood, streaming uses **Server-Sent Events (SSE)** — the connection to the server stays open, and small chunks of data trickle in one at a time instead of arriving as one big blob at the end.

#### Streaming with Claude

```python

# with client.messages.create() :
with client.messages.stream(
    model="claude-haiku-4-5",
    max_tokens=512,
    messages=[
	    {
			"role": "user",
			"content": "Tell me a short story."
		}
	],
) as stream:
    for text_chunk in stream.text_stream:
        print(text_chunk, end="", flush=True)   # print each chunk as it arrives
    print()  # newline at the end
    final = stream.get_final_message()           # the complete Message, once done
    print(
	    f"\nTokens used: 
	    {final.usage.input_tokens} in / 
	    {final.usage.output_tokens}
	     out"
	)
```

#### Streaming with OpenAI

```python
stream = client.chat.completions.create(
    model = "gpt-5.4-mini",
    max_tokens = 512,
    messages = [
	    {
		    "role": "user",
		    "content": "Tell me a short story."
		}
	],
    stream = True,
)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
print()
```

#### Key streaming details

- **`flush=True`** on `print()`: Python normally holds printed text in a buffer and only shows it in bursts. `flush=True` forces each chunk onto the screen the moment it's printed — skip it, and streaming looks just as slow as not streaming at all.
- **Usage stats arrive last.** You only find out the total token count once the stream finishes — via `stream.get_final_message()` in the Anthropic SDK, or the final chunk of an OpenAI stream.
- **Tool calls can be streamed too**, but many people disable streaming for the tool-detection step and only stream the *final* answer — that's the pattern Section 3 walks through.

**Recap:** Streaming sends the reply piece by piece instead of all at once; `flush=True` is what actually makes those pieces show up immediately on screen.

---

### 2.5 Tool / Function Calling — "The Model Asks, You Run It"

Tool calling (also called "function calling") lets the model ask *your code* to do something it can't do itself — run a calculation, look something up, check today's date. In plain terms:

1. You tell the model what tools are available (name, description, what inputs it takes).
2. The model, instead of answering directly, says "please run `calculate` with this input."
3. Your code actually runs it.
4. You send the result back to the model.
5. *Now* the model gives you a final answer that uses that result.

**The model never runs any code itself.** It only ever asks — your application is 100% responsible for actually executing anything.

```
User message
    ↓
[1] POST /messages  (with tool definitions attached)
    ↓
Model replies: "please run this tool" (stop_reason="tool_use")
    ↓
[2] Your code actually runs the function
    ↓
[3] POST /messages  (send the result back, appended to history)
    ↓
Model replies with the final answer
```

#### Step 1 — Define the tool (Claude)

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
    messages=[
	    {
		    "role": "user",
		    "content": "What is (45 * 3) + 17?"
		}
	],
)

if response.stop_reason == "tool_use":
    tool_block = next(
	    b 
	    for b in response.content 
	    if b.type == "tool_use"
	)
    tool_name  = tool_block.name          # "calculate"
    tool_input = tool_block.input         # {"expression": "45 * 3 + 17"}
    tool_id    = tool_block.id            # unique call ID -- you'll need this to reply
```

#### Step 3 — Run the tool and send the result back (Claude)

```python
result = safe_calc(tool_input["expression"])  # your own function -- see the lab's safe_calculate

# Append the assistant's tool request + your tool result, then call again
messages = [
    {
	    "role": "user",
	    "content": "What is (45 * 3) + 17?"
	},
    {
	    "role": "assistant",
	    "content": response.content # includes the tool_use block
	},       
    {
	    "role": "user",
	    "content": [       # tool_result block
        {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": str(result),
        }
    ]},
]

final = client.messages.create(
    model = "claude-haiku-4-5",
    max_tokens = 512,
    tools = tools,
    messages = messages,
)
print(final.content[0].text)  # "(45 × 3) + 17 = 152"
```

#### Step 3 (OpenAI) — return the tool result

For OpenAI the tool result is appended as its own message, right after the assistant message that contained `tool_calls`:

```python
messages.append(choice.message)            # assistant message with tool_calls list
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,          # must match tool_calls[0].id
    "content": str(result),                # result as a string
})
# then call client.chat.completions.create() again with the updated messages
```

#### Why this matters

- It grounds the model in real, current data — not just what it learned during training.
- It lets the model trigger real side effects — send an email, update a record.
- It's the foundation of AI *agents* — Day 9 builds on this directly.

**Recap:** Tool calling is a two-request loop — the model asks for a tool, you run it, you send the result back, and only then does the model give its final answer.

---

### 2.6 Multimodal Inputs — Sending Images

Both Claude and OpenAI can accept images alongside text in the same `messages` list, and the model "sees" and reasons about them — useful for reading charts, screenshots, scanned documents, or answering "what's in this photo?"

```python
# Claude -- base64-encoded image
import base64

with open("chart.png", "rb") as f:
    img_data = base64.b64encode(f.read()).decode()

response = client.messages.create(
    model = "claude-haiku-4-5",
    max_tokens = 512,
    messages = [
	    {
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
	            {
		            "type": "text",
		            "text": "Summarize this chart in one paragraph."
		        },
	        ],
	    }
	],
)
```

A few things worth knowing: images consume input tokens (roughly 1,000–1,700 for a typical image, more at high resolution), the common formats (PNG, JPEG, GIF, WebP) are all supported, and some providers also accept a plain image URL instead of base64 data.

**Recap:** Images go in the same `content` list as text, just as a different block type — and they cost tokens like everything else the model reads.

---

### 2.7 Practical, Everyday Concerns

#### Reading token / usage numbers

Every response includes a usage object — this is how you track what a conversation is costing:

```python
usage = response.usage
# Claude:  usage.input_tokens, usage.output_tokens
# OpenAI:  usage.prompt_tokens, usage.completion_tokens, usage.total_tokens

cost_estimate = (usage.input_tokens / 1_000_000) * 1.00  # Claude Haiku 4.5 pricing: $1.00 / Mtok in
```

**Tip:** logging `(model, input_tokens, output_tokens, timestamp)` somewhere — a file, a database — lets you see spend trends over time instead of finding out at the end of the month.

#### Retrying safely

Providers return HTTP 429 (rate limited) or 5xx/529 (temporarily overloaded) when things get busy. The fix is **exponential backoff** — wait a little, then a little longer, then longer still:

```python
import time, anthropic

def create_with_retry(client, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return client.messages.create(**kwargs)
        except anthropic.RateLimitError:
            wait = 2 ** attempt          # 1s, 2s, 4s, ...
            print(f"Rate limited. Waiting {wait}s…")
            time.sleep(wait)
        except anthropic.APIStatusError as e:
            if e.status_code >= 500 and attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
    raise RuntimeError("Max retries exceeded")
```

The Anthropic Python SDK already retries rate limits and server errors for you by default (`max_retries=2` out of the box) — write your own retry loop only if you need different behavior.

#### Error categories, at a glance

| Error type | Cause | What to do |
|---|---|---|
| `AuthenticationError` (401) | Bad API key | Check the env var; don't retry |
| `PermissionDeniedError` (403) | Model not available on your plan | Switch model or upgrade |
| `NotFoundError` (404) | Invalid model ID | Fix the model name |
| `RateLimitError` (429) | Too many requests | Exponential backoff |
| `APIStatusError` (5xx) | Provider having issues | Retry with backoff |
| `APITimeoutError` | Request took too long | Retry, or raise the timeout |

#### Timeouts

```python
import httpx

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    timeout=httpx.Timeout(60.0, connect=5.0),  # 60s to read, 5s to connect
    max_retries=2,
)
```

**Recap:** Track token usage so you know what you're spending; retry with growing delays on 429/5xx, never on 4xx; give slow requests a sane timeout instead of letting them hang forever.

---

## 3. Worked Example

This walks through the exact two moves the lab's mock assistant makes: one plain request→reply, and one tool-call round trip. The code shown here is the same code used in `labs/common/day-05/solution.py` — the lab wires it into a small chat loop you'll build yourself.

### Move 1 — A plain request and reply

No tool involved: the user says hello, and the assistant streams back a reply.

**Plain steps:**
1. Add the user's message to the conversation history.
2. Ask the model for a reply.
3. Print each streamed chunk as it arrives.

**Annotated code** (this is `mock_stream_answer` + `stream_print` from the lab):

```python
def mock_stream_answer(history, system, tool_expr=None, tool_result=None):
    """Stands in for client.messages.stream(...).text_stream on a real API call."""
    if tool_expr is not None and tool_result is not None:
        answer = f"The result of {tool_expr} is {tool_result}."
    else:
        answer = (
            "I am your AI assistant. I can hold a multi-turn conversation, "
            "stream responses token by token, and call a calculator tool "
            "when you ask a maths question. Try asking something like: "
            "'What is 45 * 3 + 17?'"
        )
    for word in answer.split():
        yield word + " "
        time.sleep(0.04)   # simulate the small delay between real streamed chunks


def stream_print(chunks) -> str:
    """The streaming print helper -- Section 2.4's flush=True pattern."""
    full_text = ""
    for chunk in chunks:
        print(chunk, end="", flush=True)
        full_text += chunk
    print()
    return full_text.strip()
```

**Run it** (typing "Hello!" at the prompt):

```
You: Hello!

Assistant: I am your AI assistant. I can hold a multi-turn conversation, stream responses token by token, and call a calculator tool when you ask a maths question. Try asking something like: 'What is 45 * 3 + 17?'
```

The words appeared one at a time on screen as `stream_print` printed each chunk — that's streaming, working exactly as described in Section 2.4, just with a mock model instead of a real one.

### Move 2 — A tool-call round trip

Now the user asks a math question. This time the model can't just answer directly — it needs the calculator tool.

**Plain steps (mirrors Section 2.5's diagram exactly):**
1. The model looks at "What is 45 * 3 + 17?" and decides it needs the `calculate` tool, with input `"45 * 3 + 17"`.
2. Your code runs that tool — here, the given `safe_calculate` function — and gets `152`.
3. You feed the result back in.
4. The model streams a final answer that uses the result.

**Annotated code** (this is `mock_check_for_tool_call` + the tool-call branch of `mock_chat` from the lab):

```python
def mock_check_for_tool_call(history):
    """Stands in for checking response.stop_reason == "tool_use" on a real call."""
    last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
    return _extract_math_expression(last_user)   # returns "45 * 3 + 17" or None


def mock_chat(history, system):
    tool_expr = mock_check_for_tool_call(history)     # Step 1: does the model want a tool?
    tool_result = None

    if tool_expr:
        print(f"\n[Tool call: calculate({tool_expr!r})]", flush=True)
        tool_result = safe_calculate(tool_expr)        # Step 2: your code runs it
        print(f"[Tool result: {tool_result}]", flush=True)

    print("\nAssistant: ", end="", flush=True)
    full_text = stream_print(                          # Steps 3-4: result flows in, answer streams
        mock_stream_answer(history, system, tool_expr=tool_expr, tool_result=tool_result)
    )
    return full_text
```

**Run it** (typing "What is 45 * 3 + 17?" at the prompt):

```
You: What is 45 * 3 + 17?

[Tool call: calculate('45 * 3 + 17')]
[Tool result: 152]

Assistant: The result of 45 * 3 + 17 is 152.
```

That output is a direct capture of running `python solution.py` — nothing edited. The `[Tool call: ...]` and `[Tool result: ...]` lines appeared *before* the streamed answer, exactly matching the round trip diagram in Section 2.5: ask → run → send result → final answer.

The lab wires these same pieces — a shared `history` list, a tool-detection check, `safe_calculate`, and `stream_print` — into a small chat loop you'll build yourself.

---

## 4. Hands-On Lab

**Lab location:** `labs/common/day-05/`

**What you'll build:** A CLI assistant that:
- Holds a multi-turn conversation (remembers context across messages)
- Streams the response token-by-token to the terminal
- Calls a `calculate` tool when you ask a math question

**Provider detection:**
- If `ANTHROPIC_API_KEY` is set → uses real Claude streaming + tools
- Elif `OPENAI_API_KEY` is set → uses real OpenAI streaming + tools
- Otherwise → runs a deterministic **mock** that simulates streaming and triggers the tool — this is the path Section 3 just walked through

**What's already given** in `starter.py` — the mock "model client" (`mock_check_for_tool_call`, `mock_stream_answer`), the streaming print helper (`stream_print`), the tool schemas, the safe calculator, and the real Anthropic/OpenAI implementations (for if you have a key). **What you'll write:** the `mock_chat` function that wires them together — three numbered TODOs, each mapped to a step in Section 3.

**Files:**

```
labs/common/day-05/
├── README.md          # setup, run commands, expected output, troubleshooting
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

See `labs/common/day-05/README.md` for full instructions, expected output, and a troubleshooting table.

---

## 5. Self-Check Quiz

Answer these before looking at the answers.

---

**Q1.** You're building a multi-turn chat app with the Anthropic API. After five exchanges, your 6th request fails with "messages must alternate user/assistant roles." What's the most likely cause?




You appended the assistant reply to `history` but didn't include it — or you accidentally added two user messages in a row. The API requires strict alternating roles. Check that each `messages.create()` call ends with a user message, and that the history list strictly alternates `user → assistant → user → assistant → …`.



**Q2.** What does `flush=True` do in `print(chunk, end="", flush=True)` and why is it needed for streaming?




Python buffers stdout by default — text accumulates in a buffer and only appears when the buffer fills or the program ends. `flush=True` forces the buffer to write immediately after each `print()` call. Without it, streaming tokens would all appear at once at the end, defeating the purpose.



**Q3.** A user asks "What time is it?" The model returns `stop_reason = "tool_use"` with `tool_name = "get_current_time"`. What exact steps must your code take before calling the API again?




1. Extract `tool_id`, `tool_name`, and `tool_input` from the `tool_use` content block.
2. Execute `get_current_time()` locally.
3. Append the **assistant's full response content** (the tool_use block) as an `assistant` message to history.
4. Append a `user` message containing a `tool_result` block with `tool_use_id`, `content` (the result), and `type: "tool_result"`.
5. Call `messages.create()` again with the updated history.



**Q4.** What is the difference between how Claude and OpenAI handle the system prompt in their messages arrays?




Claude accepts `system` as a **separate top-level parameter** (`system="…"`) — it is not a message in the list. OpenAI embeds it as the first element of the `messages` list with `role: "system"`. This is a common source of bugs when writing provider-flexible code.



**Q5.** Your app is receiving HTTP 429 errors. You add a `time.sleep(60)` before every retry. What's wrong with this approach?




A fixed 60-second wait is too long most of the time (rate limits often clear in seconds) and may still be too short during heavy load. The correct approach is **exponential backoff**: wait 1s, then 2s, then 4s, etc., often with a small random jitter. The Anthropic SDK also offers built-in retry with `max_retries=` on the client.



**Q6.** An image you send with a Claude request is 1024×1024 pixels. Roughly how many tokens does it consume, and how does that affect your `max_tokens` setting?




A typical image consumes roughly 1,000–1,700 input tokens. These count against your **context window** (input side) but not against `max_tokens`, which only limits the output. However, if total input tokens (text + images) approach the context limit, the model may truncate or error. Budget accordingly.



**Q7.** What does `stop_reason = "max_tokens"` tell you, and what should you do about it?




It means the model hit the output token limit before finishing its answer — the response is truncated. You should either: (a) increase `max_tokens`, (b) ask the model for a shorter response via your prompt, or (c) send a follow-up message asking the model to continue (be careful — it may repeat context).



**Q8.** True or False: the model executes the function/tool code directly when it outputs a `tool_use` block.




**False.** The model only outputs a *request* in JSON form — `{"name": "calculate", "input": {"expression": "3+4"}}`. Your application code is entirely responsible for executing the function and returning the result. The model has no ability to run code directly.



---

## 6. Concept Deep-Dive Q&A

These questions test deeper, applied understanding of the day's concepts on APIs, streaming, and tool use.

---

**Q1. "Walk me through how tool calling works end-to-end."**




Tool calling is a two-request loop. In the first request, you send the user's message along with a list of tool definitions — each is a JSON schema describing the tool's name, purpose, and parameters. If the model determines a tool is needed, it returns early with `stop_reason = "tool_use"` and a structured JSON block containing the tool name and arguments it wants passed. Your application code then executes the real function locally. You add the assistant's tool-request block and your function's result (as a `tool_result` message) to the conversation history, then send a second API request. The model reads the result and produces the final answer. The model never executes code itself — it only requests execution.


**Q2. "Why would you use streaming in an application? What are the trade-offs?"**




Streaming dramatically improves perceived latency. Without it, the user waits 5–30 seconds before seeing any output. With streaming, the first tokens appear within ~200ms, which feels interactive. The trade-off: streaming complicates error handling (you've already started writing to the UI when a mid-stream error occurs), makes it harder to post-process the full response before displaying it (e.g., filtering, parsing JSON), and usage stats only arrive at the end of the stream. For simple chat UIs, streaming is almost always worth it. For batch processing or when you need to validate the full response before showing it, non-streaming is simpler.


**Q3. "How do you handle rate limits reliably?"**




Rate limits mean you've exceeded the provider's tokens-per-minute or requests-per-minute quota. The correct pattern is exponential backoff with jitter: catch the 429 error, wait 2^attempt seconds (plus a random 0–1s jitter to avoid thundering herd), and retry up to a maximum number of attempts. Most modern SDKs (Anthropic, OpenAI) have `max_retries` built in, so you often don't need to implement this manually. For high-throughput systems you also want to track your token usage against the rate limit budget and throttle proactively. At scale, a request queue with a leaky-bucket rate controller is the proper architecture.



**Q4. "How does a multi-turn conversation work under the hood? Why is it stateless?"**




LLM APIs are stateless — every request is independent. There is no server-side session. To create a multi-turn conversation you maintain the full message history in your application and send it with every request. The model reads the entire history and produces the next reply. This means cost and latency grow with conversation length. In production you manage this by truncating old messages, summarizing older context, or using dedicated memory systems. The stateless design is intentional: it makes the API horizontally scalable and gives developers full control over what context the model sees.



**Q5. "What's the difference between `max_tokens` and the context window?"**




`max_tokens` is a **hard cap on output length** — it limits how many tokens the model is allowed to generate in one response. The **context window** is the total token budget for a single forward pass, covering both input (system prompt + conversation history + tool definitions) and output combined. If your input is 3000 tokens and the context window is 4096, you have at most 1096 tokens available for output regardless of what `max_tokens` says. Setting `max_tokens` higher than the remaining context window budget has no effect — the model simply stops when the window fills.



**Q6. "How would you let an LLM access a live database during a conversation?"**




I'd use tool calling. I'd define a tool schema for, say, `query_database` with parameters like `table`, `filter`, and `limit`. The model, when it needs data, outputs a `tool_use` block with its query intent. My code intercepts this, translates it into a safe SQL query (parameterized, never built from raw model output), executes it against the DB, and returns the rows as a JSON string in a `tool_result` block. The model then incorporates the data into its answer. Security is critical — always validate and sanitize tool inputs before execution; treat them like untrusted user input.


**Q7. "How would you compare Claude and GPT for a new chat feature?"**




I'd start with a few clarifying questions: what's the primary use case, what's the expected volume, and are there specific data-handling requirements? Technically, both are excellent for chat. Claude tends to excel at long-context tasks and nuanced instruction-following. GPT has a broad ecosystem and many third-party integrations. For a new project I'd recommend a provider-flexible architecture: abstract the API call behind a thin provider interface so you can swap models without rewriting application logic. Then run an eval on your actual data before committing — benchmark differences on your specific task matter far more than general benchmarks.



**Q8. "Explain Server-Sent Events. Why does streaming use SSE rather than WebSockets?"**




SSE (Server-Sent Events) is a one-directional HTTP-based protocol: the server holds open an HTTP/1.1 or HTTP/2 connection and pushes `data:` frames as they become available. It uses plain HTTP, works through proxies and firewalls, has automatic reconnect built into browsers, and requires no protocol upgrade. WebSockets are bidirectional and more complex to proxy/scale. For LLM streaming the communication is inherently one-directional (server → client) once the request is sent, making SSE the simpler and more robust choice. At the Python level you just iterate over the stream — the SSE framing is handled by the SDK.



**Q9. "What are the main error types you need to handle when calling an LLM API?"**




I group them into three buckets. **Don't retry**: authentication errors (401 — fix the key), permission errors (403 — fix the plan/model), and validation errors (400 — fix the request shape). **Retry with backoff**: rate limit (429), service overloaded (529), and server errors (500). **Retry with a longer timeout or reduced payload**: timeout errors. In addition I watch for `stop_reason = "max_tokens"` which isn't an HTTP error but signals a truncated response, and `content_filter` which means the request was blocked by safety systems. Good production code wraps every API call in structured error handling with logging.



**Q10. "How do images affect token usage and cost?"**




Images are converted into tokens before processing — a typical 1024×1024 image costs roughly 1,000–1,700 input tokens depending on the provider's tiling strategy. These count against the context window and are billed as input tokens. For cost-sensitive applications this matters a lot: one image can cost as much as 1000+ words of text. Strategies to manage this: resize images before sending (smaller = fewer tokens), use lower-resolution thumbnails when full resolution isn't needed, and cache responses when the same image is repeatedly queried. Always confirm the per-image token cost in the provider's documentation for the specific model you're using.



---

## 7. Further Reading (optional)

*Nothing here is required for the quiz, the lab, or later days — these are supplementary resources for further exploration in a different format.*

| Resource | Why read it |
|---|---|
| [Anthropic Messages API reference](https://docs.anthropic.com/en/api/messages) | Definitive field-by-field reference for the Claude API |
| [Anthropic Tool Use guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) | Full tool calling documentation with examples |
| [Anthropic Streaming guide](https://docs.anthropic.com/en/api/messages-streaming) | SSE stream events, best practices |
| [OpenAI Chat Completions reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) | OpenAI's equivalent API reference |
| [OpenAI Function Calling guide](https://developers.openai.com/api/docs/guides/function-calling) | OpenAI's tool/function calling walkthrough |
| [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) | SSE protocol explained from first principles |
| [Anthropic SDK (Python) — GitHub](https://github.com/anthropics/anthropic-sdk-python) | Source code; see `examples/` for streaming and tool patterns |
| [OpenAI Python SDK — GitHub](https://github.com/openai/openai-python) | Equivalent for OpenAI |
| [Exponential Backoff And Jitter — AWS Blog](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) | Why jitter matters; classic reference |

---

## 8. Key Takeaways

- **An API call is a request/reply pair, nothing more.** You send the whole conversation every time; nothing is remembered on the server between calls.
- **Messages API shape:** the key difference between providers is system-prompt placement (Claude: top-level field; OpenAI: first message) and how you read the reply back out of the response.
- **Streaming = perceived speed, not less work.** SSE delivers words as they're generated; `flush=True` is what actually makes them show up on screen immediately.
- **Tool calling is a two-request loop:** model asks for a tool → you run it → you send the result back → model answers. The model never runs code itself.
- **Images cost tokens** just like text — budget for roughly 1,000–1,700 tokens per typical image.
- **Track usage, retry with backoff, and set sane timeouts** — the three habits that keep a real application from silently failing or silently overspending.
- **`max_tokens` vs context window:** `max_tokens` caps output; the context window caps input + output combined. Both limits matter.

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
