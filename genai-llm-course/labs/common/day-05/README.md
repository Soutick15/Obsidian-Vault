# Day 5 Lab -- Streaming CLI Assistant with Tool Calling

## Objective

Build a small command-line assistant that:

1. Holds a multi-turn conversation -- remembers context across messages.
2. Streams the response token-by-token -- words appear as they are generated.
3. Calls a calculate tool -- when you ask a maths question the model requests the tool,
   your code evaluates the expression, and the model incorporates the result.

This ties together the messages format, streaming, and tool calling from
`curriculum/common/Day-05-apis-streaming-tools.md`. Read Section 3 (Worked
Example) first -- it walks through the exact two moves you'll wire together
here: a plain request/reply, and a tool-call round trip.


## Setup

```
cd labs/common/day-05
pip install -r requirements.txt
```

Optionally create a .env file in the AI_Training root with API keys (not required):

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```


## Run

No API key required (mock mode):

```
python solution.py
```

The mock simulates streaming word-by-word and triggers the calculator tool when
you type a maths question such as "what is 45 * 3 + 17?".

With a real Anthropic key:

```
ANTHROPIC_API_KEY=sk-ant-... python solution.py
```

With a real OpenAI key:

```
OPENAI_API_KEY=sk-... python solution.py
```

Provider priority: Anthropic -> OpenAI -> Mock.

Practice with the starter file:

```
python starter.py
```

Work through the three TODO markers in `mock_chat()`. Everything else --
the mock model client, the tool schemas, the safe calculator, and the
streaming print helper -- is already written for you. Check `solution.py`
if you get stuck.


## Expected Session (mock mode)

This is a real, unedited capture of `python solution.py` with `Hello!` and
`What is 45 * 3 + 17?` typed at the two `You:` prompts:

```
============================================================
  Day 5 Mini-Project -- Streaming CLI Assistant
  Provider: MOCK
  Tool available: calculate
  Type 'quit' or 'exit' to end the session.
============================================================

You: Hello!

Assistant: I am your AI assistant. I can hold a multi-turn conversation, stream responses token by token, and call a calculator tool when you ask a maths question. Try asking something like: 'What is 45 * 3 + 17?'

You: What is 45 * 3 + 17?

[Tool call: calculate('45 * 3 + 17')]
[Tool result: 152]

Assistant: The result of 45 * 3 + 17 is 152.

You: quit
Goodbye!
```

Notes on what you're seeing:
- The first reply has no tool call -- it's a plain streamed answer (Section 3, Move 1).
- The second reply prints `[Tool call: ...]` and `[Tool result: ...]` *before*
  the streamed answer -- that's the round trip from Section 2.5 / Section 3,
  Move 2: the model asks for the tool, your code runs it, the result feeds
  into the final answer.
- In your own terminal the words in the `Assistant:` lines will appear one
  at a time (a ~0.04s pause between each) rather than all at once, since the
  mock simulates streaming with `time.sleep(0.04)` between chunks.


## What's given vs. what you write (`starter.py`)

| Given (pre-written) | You write |
|---|---|
| Provider detection, tool schemas, `safe_calculate` | `mock_chat()` -- three numbered TODOs |
| `mock_check_for_tool_call()` -- detects a maths question | |
| `mock_stream_answer()` -- the mock's streaming generator | |
| `stream_print()` -- the streaming print helper | |
| `anthropic_chat()` / `openai_chat()` -- full real-API implementations | |
| `main()` -- the conversation loop | |

The three TODOs in `mock_chat()` map directly to curriculum Section 3:

1. **Build the messages list** -- understand that `history` is the shared
   `{"role": ..., "content": ...}` list from Section 2.1.3, already updated
   with the user's new turn before `mock_chat()` runs.
2. **Detect the tool request and call the given tool** -- call
   `mock_check_for_tool_call(history)`; if it returns an expression, print
   the `[Tool call: ...]` line, run `safe_calculate(expr)`, and print
   `[Tool result: ...]`.
3. **Append the tool result and continue** -- call `stream_print(mock_stream_answer(...))`
   with the tool expression/result, and return the full text.


## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Mock response -- implement mock_chat to see streaming.` never changes | The three TODOs in `starter.py` haven't been filled in yet | Work through TODO 1-3 in `mock_chat()`, or run `solution.py` to see the working version |
| Words print all at once instead of one at a time | Missing `flush=True` on a `print()` call | Check that every `print(chunk, end="", flush=True)` in your code keeps `flush=True` -- Python buffers stdout otherwise (Section 2.4) |
| `[Tool call: ...]` never appears for a maths question | `mock_check_for_tool_call()` didn't detect the expression | Try a clearer phrasing like `What is 45 * 3 + 17?`; the heuristic in `_extract_math_expression` looks for digits and `+ - * / ( )` after stripping question words |
| `ModuleNotFoundError: No module named 'anthropic'` (or `openai`) | You set an API key but didn't install the matching SDK | `pip install -r requirements.txt`, or unset the key to fall back to mock mode |
| `AuthenticationError` / `401` with a real key | Bad or missing API key | Double-check the env var name (`ANTHROPIC_API_KEY` / `OPENAI_API_KEY`) and that the key is valid |
| Real-API run hangs with no output | Network/firewall blocking the request, or a very large `max_tokens` on a non-streaming call | Confirm internet access; the lab already uses streaming for the final answer to avoid this (Section 2.4) |
| `Error: invalid expression --` in the tool result | `safe_calculate` only supports `+ - * / ** ( )` on numbers, not general Python | Rephrase the expression using just arithmetic operators |
