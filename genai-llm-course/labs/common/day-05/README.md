# Day 5 Lab -- Streaming CLI Assistant with Tool Calling

## Objective

Build a small command-line assistant that:

1. Holds a multi-turn conversation -- remembers context across messages.
2. Streams the response token-by-token -- tokens appear as they are generated.
3. Calls a calculate tool -- when you ask a maths question the model requests the tool,
   your code evaluates the expression, and the model incorporates the result.

This is the Week 1 mini-project. It ties together everything from Days 1-5.


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

The mock simulates streaming word-by-word and auto-triggers the calculator tool when
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

Work through the TODO markers. Check solution.py if you get stuck.


## Expected Session (mock mode)

```
============================================================
  Day 5 Mini-Project -- Streaming CLI Assistant
  Provider: MOCK (no API key detected)
  Tool available: calculate
  Type 'quit' or 'exit' to end the session.
============================================================

You: Hello!