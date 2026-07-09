# Day 5 — APIs, Async & Testing

> **Python Foundation · Day 5 of 5** | Pulls everything together — HTTP, async I/O, pytest, and the CLI shape every lab uses.

---

## 1. Learning Objectives

By the end of this day you will be able to:

1. Explain HTTP methods, status codes, and the JSON request/response cycle for REST APIs.
2. Make GET and POST requests with `requests` and `httpx`, handle errors with `raise_for_status`, and read API documentation confidently.
3. Describe what `async def`, `await`, and `asyncio.run` do, and explain why async helps with I/O-bound work like calling LLM APIs.
4. Write `pytest` test functions, use `assert`, run the test suite from the command line, apply fixtures, and parametrize tests with `@pytest.mark.parametrize`.
5. Parse command-line arguments with `argparse` and implement the `--selftest` / `--smoke` pattern used throughout the course labs.
6. Recognise the typical shape of a lab module: a core module, a `pytest` test file, and an `argparse` CLI entry point.

---

## 2. Concept Reading

### 2.1 HTTP & REST Recap

REST APIs communicate over HTTP. Every request has:

| Part        | Description                                                                                              |
| ----------- | -------------------------------------------------------------------------------------------------------- |
| **Method**  | `GET` (read), <br>`POST` (create/send), <br>`PUT` (replace), <br>`PATCH` (update), <br>`DELETE` (remove) |
| **URL**     | Identifies the resource — e.g. `https://api.example.com/v1/completions`                                  |
| **Headers** | Metadata — <br>`Content-Type: application/json`, <br>`Authorization: Bearer <token>`                     |
| **Body**    | JSON payload (POST/PUT/PATCH only; GET has none)                                                         |

**Common status codes:**

| Code | Meaning |
|---|---|
| 200 OK | Request succeeded |
| 201 Created | Resource created |
| 400 Bad Request | Your payload is malformed |
| 401 Unauthorized | Missing or invalid API key |
| 404 Not Found | Resource doesn't exist |
| 422 Unprocessable Entity | Valid JSON but bad semantics |
| 429 Too Many Requests | Rate limited — back off and retry |
| 500 Internal Server Error | Server-side problem |

**Typical JSON round-trip:**

```python
# Request
POST /v1/chat/completions
Content-Type: application/json
Authorization: Bearer sk-...

{
  "model": "gpt-4o-mini",
  "messages": [
	  {
		  "role": "user",
		  "content": "Hello"
		}
	]
}

# Response (200 OK)
{
  "id": "chatcmpl-abc",
  "choices": [
	  {
		  "message": 
			  {
			  "role": "assistant",
			  "content": "Hi there!"
			  }
		}
	],
  "usage": 
	  {
	  "prompt_tokens": 10,
	  "completion_tokens": 6
	  }
}
```

#### Reading API documentation

When you open an API reference, look for:
1. **Authentication** — how to send the API key (usually an `Authorization` header).
2. **Base URL** — every endpoint is relative to this.
3. **Request schema** — required vs. optional fields and their types.
4. **Response schema** — where your data lives in the JSON.
5. **Error schema** — how errors are structured (so you can parse them in your `except` block).
6. **Rate limits** — requests per minute / tokens per minute.

---

### 2.2 Making Requests with `requests` and `httpx`

Both libraries feel very similar. 
- `requests` is synchronous; 
- `httpx` supports both sync and async, 

In this course labs prefer `httpx`, cause it supports both sync and async operation.

#### 2.2.1 `requests` — GET and POST

```python
import requests

# --- GET ---
response = requests.get
	("https://httpbin.org/get",
    params = {
	    "foo": "bar"           # query params appended as ?foo=bar
	},          
    headers = {
	    "Accept": "application/json"
	},
    timeout = 10,                # seconds — always set this
)
response.raise_for_status()# checks Status Code raises HTTPError for 4xx/5xx
data = response.json()         # parse body as JSON → dict
print(data["url"])
```


```python
# --- POST with JSON body ---
payload = {
	"prompt": "Hello",
	"max_tokens": 50
	}
response = requests.post(
    "https://api.example.com/v1/complete",
    json = payload,                    # sets Content-Type: application/json
    headers = {
    "Authorization": "Bearer sk-abc"
    },
    timeout=30,
)
response.raise_for_status()
result = response.json()
```

#### 2.2.2 `httpx` — sync and async

```python
import httpx

# --- Sync (same feel as requests) ---
with httpx.Client(timeout = 10) as client:
    r = client.get("https://httpbin.org/get")
    r.raise_for_status()
    print(r.json())
```


```python
# --- Async (used in async contexts) ---
import asyncio

async def fetch_data():
    async with httpx.AsyncClient(timeout = 10) as client:
        r = await client.get("https://httpbin.org/get")
        r.raise_for_status()
        return r.json()

data = asyncio.run(fetch_data())
```
#### 2.2.3 Error handling pattern

```python
import httpx

def call_api(url: str, payload: dict) -> dict:
    try:
        with httpx.Client(timeout = 15) as client:
            r = client.post(url, json = payload)
            r.raise_for_status()
            return r.json()
    except httpx.TimeoutException:
        raise RuntimeError("Request timed out — is the server reachable?")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"API error {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error: {e}")
```

Key points :
- Always set a **timeout** — a hanging request blocks your program forever.
- `raise_for_status()` turns 4xx/5xx into a Python exception you can `except`.
- Distinguish network errors (`RequestError`) from HTTP errors (`HTTPStatusError`).

---
### 2.3 Async / Await Basics

Python's `asyncio` lets a single thread do other work while waiting for I/O (network calls, file reads). This is exactly what you need when calling LLM APIs — the model spends most time "thinking" on the server, so your Python process can handle other requests meanwhile.

#### Key vocabulary

| Term | Meaning |
|---|---|
| **coroutine** | A function defined with `async def`. It doesn't run immediately; it returns a coroutine object. |
| **`await`** | Suspends the current coroutine until the awaited thing finishes. Only valid inside `async def`. |
| **event loop** | The engine that runs coroutines. Created by `asyncio.run(...)`. |
| **`asyncio.run(coro)`** | Entry point: creates an event loop, runs the coroutine, closes the loop. Call this from synchronous code. |

#### Minimal example

```python
import asyncio
import httpx

async def fetch_one(url: str) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text[:80]          # first 80 chars

async def fetch_many(urls: list[str]) -> list[str]:
    tasks = [fetch_one(url) for url in urls]
    # asyncio.gather runs all coroutines concurrently
    return await asyncio.gather(*tasks)

if __name__ == "__main__":
    urls = [
        "https://httpbin.org/get",
        "https://httpbin.org/ip",
    ]
    results = asyncio.run(fetch_many(urls))
    for r in results:
        print(r)
```

Without `asyncio.gather`, fetching two URLs sequentially takes `t1 + t2` seconds. With `gather`, it takes roughly `max(t1, t2)` — both requests are in-flight at the same time.

#### Why async matters for LLM / streaming

Streaming LLM responses send tokens one by one over an open HTTP connection. With `async for chunk in response.aiter_text():`, your program can process each token as it arrives (print it, pipe it to a UI) without blocking. The DevOps and QA labs both use this pattern.

> **Conceptual note for Day 5:** You don't need to write production async code today. The goal is to be able to read an `async def` function and understand what it does. You'll write real async code in the main course labs.

---

### 2.4 Testing with pytest

`pytest` is the standard Python testing library. Every lab in this course ships with a `test_*.py` file — understanding how to read and run those tests is essential, especially for the QA track.

#### 2.4.1 A first test

```python
# test_math.py
def add(a, b):
    return a + b

def test_add_positive():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, -1) == -2
```

Run with:
```bash
pytest test_math.py -v
```

pytest automatically discovers any file named `test_*.py` or `*_test.py` and any function starting with `test_`.

#### 2.4.2 `assert` is the core

`assert <expression>` raises `AssertionError` if the expression is falsy. pytest intercepts that and gives you a detailed diff:

```python
assert normalize("  Hello World  ") == "hello world"
# If it fails:
# AssertionError: assert 'Hello World' == 'hello world'
```

#### 2.4.3 Fixtures — shared setup

A **fixture** is a function decorated with `@pytest.fixture` that provides data or resources to tests. pytest injects it by name:

```python
import pytest

@pytest.fixture
def sample_text():
    return "  Hello, World!  "

def test_strip(sample_text):
    assert sample_text.strip() == "Hello, World!"

def test_lower(sample_text):
    assert sample_text.lower() == "  hello, world!  "
```

Fixtures can set up (and tear down) databases, temporary files, mock HTTP clients, and so on.

#### 2.4.4 Parametrize — one test, many inputs

`@pytest.mark.parametrize` runs a test function once per set of arguments:

```python
import pytest

@pytest.mark.parametrize("text,expected", [
    ("Hello World", "hello world"),
    ("  SPACES  ",  "  spaces  "),
    ("MiXeD",       "mixed"),
])
def test_to_lower(text, expected):
    assert text.lower() == expected
```

This generates three separate test cases. If one fails, pytest tells you exactly which input failed.

#### 2.4.5 Running pytest

```bash
# Run all tests in the current directory (recursive)
pytest

# Run a specific file
pytest test_example.py

# Verbose output (one line per test)
pytest -v

# Quiet (dots only)
pytest -q

# Stop at first failure
pytest -x
```

#### 2.4.6 Test discovery rules

pytest looks for:
- Files: `test_*.py` or `*_test.py`
- Functions: `test_*`
- Classes: `Test*` (methods starting with `test_`)

Name your test files accordingly; otherwise pytest won't find them automatically.

---

### 2.5 CLI Arguments with `argparse`

Command-line tools accept arguments so they can be driven from scripts, CI, and the terminal without editing source code. Python's `argparse` handles this.

#### 2.5.1 `sys.argv` — the raw list

```python
import sys
# python myscript.py hello --count 3
# sys.argv == ['myscript.py', 'hello', '--count', '3']
```

Parsing `sys.argv` by hand is error-prone. Use `argparse` instead.

#### 2.5.2 `argparse` basics

```python
import argparse

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Text processing tool")
    p.add_argument("input", help="Input text to process")
    p.add_argument("--upper", action="store_true", help="Uppercase the result")
    p.add_argument("--count", type=int, default=1, help="Repeat N times")
    return p

if __name__ == "__main__":
    args = build_parser().parse_args()
    result = args.input.upper() if args.upper else args.input
    for _ in range(args.count):
        print(result)
```

```bash
python myscript.py "hello world" --upper --count 2
# HELLO WORLD
# HELLO WORLD
```

#### 2.5.3 The `--selftest` / `--smoke` pattern

Every lab in this course follows this pattern:

```python
import argparse

def process(text: str) -> str:
    """Core logic — pure, testable, no I/O."""
    return text.strip().lower()

def build_parser():
    p = argparse.ArgumentParser()
    p.add_argument("text", nargs="?", help="Text to process")
    p.add_argument("--selftest", action="store_true",
                   help="Run built-in smoke tests and exit")
    return p

if __name__ == "__main__":
    args = build_parser().parse_args()

    if args.selftest:
        # Quick sanity checks — no network, no keys needed
        assert process("  Hello  ") == "hello", "strip+lower failed"
        assert process("WORLD") == "world",      "lower failed"
        print("All self-tests passed.")
    elif args.text:
        print(process(args.text))
    else:
        build_parser().print_help()
```

```bash
python lab.py --selftest
# All self-tests passed.
```

Why this pattern?
- **CI pipelines** can run `--selftest` to confirm the script is importable and logic works, without needing real API keys.
- **QA engineers** can smoke-test a lab instantly before diving into the full `pytest` suite.
- It documents the expected behaviour right in the file.

---

### 2.6 Putting It All Together: The Shape of a Lab

A typical course lab has three files:

```
lab_name/
├── solution.py          # Core module + argparse CLI + --selftest
├── test_solution.py     # pytest tests for the core functions
└── starter.py           # Same structure with TODOs for learners
```

The core functions in `solution.py` are **pure** — they take plain Python values in, return plain Python values out, with no global state. That makes them easy to unit-test without mocking anything.

The `test_solution.py` file imports those functions and tests edge cases that `--selftest` doesn't cover. In the QA track, you'll extend these test files significantly.

---

## 3. Hands-on Exercise

**Exercise directory:** `exercises/day-05/`

You will work with two pure functions — `normalize_text` and `word_frequencies` — that could be part of a real text-pre-processing pipeline.

### Files

| File | Purpose |
|---|---|
| `starter.py` | Fill in the `TODO` sections |
| `solution.py` | Reference implementation (look after you try) |
| `test_example.py` | pytest tests — run these to check your work |

### What to do

1. Open `starter.py`. Read the docstrings.
2. Implement `normalize_text` and `word_frequencies`.
3. Add the `--selftest` flag to the `argparse` CLI at the bottom.
4. Run your tests:
   ```bash
   pytest curriculum/python-foundation/exercises/day-05/ -v
   ```
5. Run the self-test:
   ```bash
   python curriculum/python-foundation/exercises/day-05/starter.py --selftest
   ```
6. Compare with `solution.py` when done.

> **No network or API key required.** All functions operate on plain strings and standard-library data structures.

---

## 4. Self-Check Quiz

**Q1. What does `response.raise_for_status()` do?**


Show answer

It raises an `httpx.HTTPStatusError` (or `requests.HTTPError`) if the HTTP response status code is 4xx or 5xx. 2xx responses pass through silently. This lets you turn bad HTTP responses into Python exceptions you can `except` and handle.



**Q2. What is the difference between a positional argument and an optional argument in `argparse`?**


Show answer

A **positional argument** is defined without a leading `--` (e.g. `add_argument("input")`). It is required by position — the first bare word on the command line. An **optional argument** starts with `--` (e.g. `add_argument("--upper")`). It is optional and identified by its flag name, not position. Optional arguments can have defaults; positional arguments usually don't.



**Q3. What does `@pytest.mark.parametrize` do, and why is it useful?**


Show answer

It runs the decorated test function once for each set of parameters you provide. For example, `@pytest.mark.parametrize("x,y", [(1,2), (3,4)])` generates two test cases. It is useful because it lets you test many inputs without copying the same assertion logic — and if one case fails, pytest tells you exactly which input caused it.



**Q4. You call `asyncio.run(fetch_data())`. What does that line do?**


Show answer

`asyncio.run` creates a new event loop, runs the coroutine `fetch_data()` until it completes, then closes the event loop. It is the standard entry point for running async code from synchronous Python (e.g. from `if __name__ == "__main__"`). You should only call it once per program — don't nest `asyncio.run` calls.



**Q5. Which HTTP status code signals that you are being rate-limited, and what should your code do when it receives it?**


Show answer

**429 Too Many Requests.** Your code should back off — wait before retrying. A common strategy is exponential backoff: wait 1 second, then 2, then 4, etc. Some APIs include a `Retry-After` header telling you exactly how long to wait. Never retry immediately in a tight loop, as this will keep triggering the rate limit.



**Q6. What is a pytest fixture and when would you use one?**


Show answer

A fixture is a function decorated with `@pytest.fixture` that provides a test with data, objects, or setup/teardown logic. You use one when multiple tests need the same starting state — for example, a pre-loaded dictionary, a temporary file, or a mock HTTP client. Pytest injects the fixture by matching the parameter name in the test function to the fixture name.



**Q7. Why does the `--selftest` pattern set a `nargs="?"` or `nargs="*"` on the main positional argument in many labs?**


Show answer

When `--selftest` is passed, the script doesn't need any positional input — it uses hardcoded sample data. Making the positional argument optional (`nargs="?"` means zero or one value) prevents `argparse` from raising an error about a missing argument when the user only passes `--selftest`. The script then checks `if args.selftest:` first and exits before ever reading the positional argument.



---

## 5. Concept Deep-Dive Q&A

**Q1. Why do `requests` and `httpx` both exist, and when should you choose one over the other?**


Show answer

`requests` is the original, widely-used synchronous HTTP library. It has a large ecosystem, great documentation, and works perfectly for scripts and CLI tools that don't need concurrency.

`httpx` is a newer library with an almost identical API but adds native `async`/`await` support via `AsyncClient`. Choose `httpx` when you need to make concurrent HTTP calls (e.g. fetching from multiple API endpoints at once, or streaming LLM responses in an async web server). The course labs use `httpx` because the LLM API calls they make are naturally async.

For simple one-off scripts with no concurrency requirement, either works fine.



**Q2. What exactly is an event loop, and why can't you just call `await` anywhere in your code?**


Show answer

An event loop is a running process that manages a queue of coroutines and callbacks. It decides which coroutine runs next when the currently running one hits an `await` and suspends. `asyncio.run()` creates this loop.

You can only use `await` inside a function defined with `async def`. This is a **grammar rule enforced at parse time**: Python's syntax simply does not allow the `await` keyword outside an `async def` function — attempting it causes a `SyntaxError` before the code even runs. It is not a runtime check for whether an event loop exists; it is a compile-time/grammar restriction.



**Q3. What is the difference between `asyncio.gather` and calling coroutines sequentially with `await`?**


Show answer

Sequential awaits run the coroutines one after the other — total time is `t1 + t2`:

```python
async def run_sequential():
    result1 = await coro1()
    result2 = await coro2()
```

`asyncio.gather` schedules both concurrently on the same event loop. When `coro1` hits an `await` (e.g. waiting for a network response), the event loop immediately starts `coro2` instead of sitting idle — total time is approximately `max(t1, t2)`:

```python
async def run_concurrent():
    result1, result2 = await asyncio.gather(coro1(), coro2())
```

Use `gather` whenever you have multiple independent I/O operations that don't depend on each other's results.



**Q4. How does `pytest` test discovery work, and what happens if you name a test file `helpers.py`?**


Show answer

By default, pytest searches for test files matching `test_*.py` or `*_test.py` in the current directory and all subdirectories. Inside those files it collects functions starting with `test_` and classes starting with `Test`.

If you name your file `helpers.py`, pytest will not discover it unless you explicitly pass it on the command line (`pytest helpers.py`) or configure pytest to change its discovery pattern in `pytest.ini` / `pyproject.toml`. This is intentional — it lets you have helper modules alongside your test files without them being collected as tests.



**Q5. What is the purpose of `raise_for_status()` vs. checking `response.status_code` manually?**


Show answer

Both approaches can work, but `raise_for_status()` is more reliable in practice.

Checking `status_code` manually — e.g. `if response.status_code != 200` — is fragile because you might forget to check, forget edge cases (201, 204, 301, etc.), or handle only some error codes. It also spreads error-handling logic across your code.

`raise_for_status()` raises an exception for *any* 4xx or 5xx, making it impossible to accidentally proceed with a failed response. You can then catch `HTTPStatusError` in one place. The exception includes the response object, so you can still read the status code and body for logging.



**Q6. How does the `--selftest` pattern relate to what pytest is already doing? Are they redundant?**


Show answer

They are complementary, not redundant.

`--selftest` is a **smoke test built into the module itself** — it checks that the module loads, imports work, and a few happy-path cases run correctly. It needs no test runner, no installed `pytest`, and no discovery configuration. A CI pipeline can run `python lab.py --selftest && echo OK` in a minimal environment.

`pytest` provides **structured, comprehensive test coverage** — parametrized edge cases, fixtures, failure diffs, and a test report. It is the right tool for QA work, regression suites, and coverage tracking.

Think of `--selftest` as "is this even running?" and `pytest` as "does it behave correctly in all cases?"



**Q7. Can you use `httpx.AsyncClient` inside a `pytest` test function? What do you need?**


Show answer

Yes, but you need the test function to be `async def` and you need `pytest-asyncio` (or similar) installed so pytest knows how to run async test functions. With `pytest-asyncio`, you either decorate the test with `@pytest.mark.asyncio` or set `asyncio_mode = "auto"` in your pytest config.

In this course's exercises, the runnable tests are synchronous (no network calls) to avoid adding that dependency. The async patterns you learn in section 2.3 are applied in the main course labs, which have their own async test infrastructure.



**Q8. What makes a function "pure" and why does that matter for testing?**


Show answer

A **pure function** always returns the same output for the same input, and has no side effects (no network calls, no file writes, no global state mutations, no random numbers unless seeded).

Pure functions are trivial to test because:
- No setup or teardown is needed — just call the function with input and `assert` the output.
- No mocking is needed — there are no external dependencies to fake.
- Tests run instantly and deterministically.
- Failures always mean the logic is wrong, not that the network was down.

The course labs deliberately keep core logic in pure functions and isolate I/O in thin wrapper layers, so the tests stay fast and reliable even without API keys.



---

## 6. Key Takeaways

- REST APIs use HTTP methods (`GET`, `POST`, etc.) and status codes. Always set a timeout and call `raise_for_status()` — never silently proceed after an error.
- `requests` is synchronous; `httpx` supports both sync and async. The course labs use `httpx` because LLM API calls benefit from async I/O.
- `async def` defines a coroutine. `await` suspends it until an I/O operation completes. `asyncio.run()` is the entry point from synchronous code. `asyncio.gather()` runs coroutines concurrently.
- `pytest` discovers tests in `test_*.py` files. Use `assert` for checks, fixtures for shared setup, and `@pytest.mark.parametrize` to test many inputs without duplicating code.
- `argparse` parses command-line flags. The `--selftest` flag is a smoke-test pattern every course lab uses — it lets CI (and you) verify a script works without needing real API keys.
- Keep core logic in **pure functions**: same input → same output, no side effects. Pure functions are easy to test, easy to reason about, and make the rest of the code easier to debug.
- Every lab in this course follows the same shape: a module of pure functions, a `pytest` test file, and an `argparse` CLI with `--selftest`. You now know why each piece exists.
