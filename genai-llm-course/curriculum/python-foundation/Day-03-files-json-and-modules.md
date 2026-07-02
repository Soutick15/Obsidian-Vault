# Day 3 — Files, JSON, and Modules

## 1. Learning Objectives

By the end of Day 3 you will be able to:

- Open, read, and write text files safely using the `with` statement.
- Navigate the filesystem with `pathlib.Path`, including resolving the repo root from any nested file.
- Parse and produce JSON with Python's standard `json` module, including safe error handling.
- Write your own module, import it from another file, and understand how Python finds modules via `sys.path`.
- Read environment variables with `os.getenv` and load a `.env` file with `python-dotenv`.
- Work with dates and times using the `datetime` module.
- Write basic regular expressions to search, extract, and redact text patterns.

---

## 2. Concept Reading

### 2.1 File I/O and the `with` Statement

Types of files :
- Text : `.txt`, `.docx`, `.log` etc
- Binary : `.mp4`, `.mp3`, `.jpeg` etc

First we need to open file before we can read or write :

```python

f = open ("demo.txt", "r")
data = f.read()

print(data) # Hi, Welcome to Python course.
print(type(data)) # <class 'str'>

# close the file we've open
f.close()
```
		

Python's built-in `open()` returns a file object. Always use it as a context manager so the file is closed even if an error occurs:

```python
# Read an entire file as a string
with open("notes.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Write (creates or overwrites)
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("Hello, file!\n")

# Append to an existing file
with open("log.txt", "a", encoding="utf-8") as f:
    f.write("Another line\n")
```

**Encoding matters.** Always pass `encoding="utf-8"` when working with text files that may contain non-ASCII characters. On Windows the default is often `cp1252`; on macOS/Linux it is usually UTF-8 — but being explicit removes the ambiguity.

Common file modes:

| Mode | Meaning |
|------|---------|
| `"r"` | Read (default) |
| `"w"` | Write — creates or truncates |
| `"a"` | Append |
| `"rb"` / `"wb"` | Binary read / write |

---

### 2.2 `pathlib` — The Modern Way to Handle Paths

`pathlib.Path` treats paths as objects rather than plain strings. It works on Windows, macOS, and Linux without string surgery.

```python
from pathlib import Path

p = Path("data") / "hr-corpus" / "employee-handbook-overview.md"
print(p)           # data/hr-corpus/employee-handbook-overview.md
print(p.name)      # employee-handbook-overview.md
print(p.stem)      # employee-handbook-overview
print(p.suffix)    # .md
print(p.parent)    # data/hr-corpus

# Check existence
if p.exists():
    text = p.read_text(encoding="utf-8")

# List all markdown files in a directory
for md in Path("data/hr-corpus").glob("*.md"):
    print(md.name)
```

**Resolving the repo root from a deeply nested file** — a pattern used throughout this course's labs:

```python
# Suppose this file lives at:
#   curriculum/python-foundation/exercises/day-03/solution.py
# parents[0] = day-03/
# parents[1] = exercises/
# parents[2] = python-foundation/
# parents[3] = curriculum/
# parents[4] = AI_Training/  ← repo root

REPO_ROOT = Path(__file__).resolve().parents[4]
corpus_dir = REPO_ROOT / "data" / "hr-corpus"
```

`Path(__file__).resolve()` converts the current file's path to an absolute path, removing symlinks. `.parents[N]` walks N levels up. This means any script can find shared data without hard-coded absolute paths.

---

### 2.3 JSON — Encoding and Decoding Structured Data

JSON (JavaScript Object Notation) maps almost directly to Python:

| JSON | Python |
|------|--------|
| object `{}` | `dict` |
| array `[]` | `list` |
| string `""` | `str` |
| number | `int` / `float` |
| `true` / `false` | `True` / `False` |
| `null` | `None` |

```python
import json

# dict → JSON string
data = {"name": "Alice", "score": 42, "active": True}
json_str = json.dumps(data, indent=2)
print(json_str)

# JSON string → dict
parsed = json.loads(json_str)
print(parsed["name"])   # Alice

# Write JSON to a file
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

# Read JSON from a file
with open("output.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)
```

**Safe parsing with error handling** — always wrap untrusted JSON in a try/except:

```python
raw = '{"key": "value", broken}'   # invalid JSON
try:
    result = json.loads(raw)
except json.JSONDecodeError as e:
    print(f"JSON parse error: {e}")
    result = {}
```

`json.JSONDecodeError` is the specific exception for malformed JSON. Catching the broad `Exception` would hide other bugs, so prefer the specific class.

---

### 2.4 Modules and Imports

Every `.py` file is a **module**. Python finds modules by searching directories listed in `sys.path`.

```python
# Import a whole module
import math
print(math.sqrt(16))

# Import specific names
from pathlib import Path
from datetime import date, timedelta

# Import with an alias
import json as j
```

**Writing your own module:**

```python
# utils.py
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

```python
# main.py (same directory)
from utils import greet
print(greet("World"))
```

**Packages** are directories with an `__init__.py` file:

```
my_package/
    __init__.py
    helpers.py
    parsers.py
```

```python
from my_package.helpers import some_function
```

**`sys.path` note:** When Python imports a module it searches `sys.path` in order. The first entry is usually the directory of the script being run. If you get a `ModuleNotFoundError`, check that the package directory is reachable from where you are running the script. In this course the labs are always run from the repo root so relative imports work consistently.

---

### 2.5 `os` Module and Environment Variables

```python
import os

# Read an environment variable (returns None if missing)
db_url = os.getenv("DATABASE_URL")

# Provide a default value
log_level = os.getenv("LOG_LEVEL", "INFO")

# List all env vars
for key, value in os.environ.items():
    print(f"{key}={value}")
```

**`.env` files with `python-dotenv`:** Storing secrets in environment variables rather than source code is a standard practice. A `.env` file holds these variables locally:

```
# .env  (never commit this file to git)
API_KEY=abc123
DATABASE_URL=postgresql://localhost/mydb
```

```python
from dotenv import load_dotenv
load_dotenv()          # loads .env from the current directory
api_key = os.getenv("API_KEY")
```

`load_dotenv()` reads the `.env` file and sets the variables in `os.environ`. If the file doesn't exist it does nothing silently, so it is safe to call in all environments.

---

### 2.6 `datetime` Basics

```python
from datetime import date, datetime, timedelta

today = date.today()
print(today)                        # 2026-06-22

now = datetime.now()
print(now.strftime("%Y-%m-%d %H:%M:%S"))

# Arithmetic
tomorrow = today + timedelta(days=1)
delta = date(2026, 12, 31) - today
print(f"{delta.days} days until year end")

# Parse a date string
d = datetime.strptime("2026-01-15", "%Y-%m-%d").date()
```

`strftime` formats a datetime to a string; `strptime` parses a string into a datetime. The format codes (`%Y`, `%m`, `%d`, etc.) are the same in both.

---

### 2.7 Regular Expressions (`re`)

The `re` module provides pattern matching over strings. It is particularly useful for extracting structured data from unstructured text — and for redacting sensitive information, a pattern used repeatedly in the AI labs later in this course.

```python
import re

text = "Contact hr@example.com or support@company.org for help."

# Search for the first match
m = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", text)
if m:
    print(m.group())   # hr@example.com

# Find ALL matches
emails = re.findall(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", text)
print(emails)          # ['hr@example.com', 'support@company.org']

# Substitute / redact
redacted = re.sub(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", "[REDACTED]", text)
print(redacted)

# Named groups for structured extraction
log_line = "2026-06-22 14:05:32 ERROR Database timeout"
pattern = r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<level>\w+)"
m = re.search(pattern, log_line)
if m:
    print(m.group("level"))   # ERROR
```

Key functions:

| Function | Returns |
|----------|---------|
| `re.search(pat, s)` | First `Match` object, or `None` |
| `re.findall(pat, s)` | List of all matching strings |
| `re.sub(pat, repl, s)` | String with matches replaced |
| `re.compile(pat)` | Pre-compiled pattern (reuse for speed) |

**Why this matters for AI work:** LLM applications often process documents that contain personally identifiable information (PII) — emails, phone numbers, employee IDs. Regex redaction is the first, lightweight pass before text reaches an LLM. You will build on this in the corpus-loading labs starting in Day 6.

---

## 3. Hands-on Exercise

Exercise files live in `curriculum/python-foundation/exercises/day-03/`.

- **`starter.py`** — scaffolded file with TODO markers. Fill in each TODO.
- **`solution.py`** — complete reference solution.

**What the exercise does:**

1. Uses `pathlib` to locate the shared HR corpus at `data/hr-corpus/` (relative to the repo root).
2. Counts all `.md` files in the corpus, skipping `README.md`.
3. Scans each document for email-like strings using `re.findall`.
4. Builds a summary dictionary and writes it to `summary.json` in the same directory.
5. Reads `summary.json` back and prints a report.

Run from the repo root:

```bash
python curriculum/python-foundation/exercises/day-03/starter.py
# or, once done:
python curriculum/python-foundation/exercises/day-03/solution.py
```

If the corpus directory is not found the script prints a clear message and exits without error.

---

## 4. Self-Check Quiz

**Q1. What is the main advantage of opening files with `with open(...) as f:` instead of just `f = open(...)`?**

<details>
<summary>Show answer</summary>

The `with` statement guarantees that the file is closed when the block exits — even if an exception is raised inside the block. Without it you must call `f.close()` manually, and if an exception occurs before that line the file handle leaks, which can cause data corruption or resource exhaustion.

</details>

**Q2. What does `Path(__file__).resolve().parents[4]` return for a file at `curriculum/python-foundation/exercises/day-03/solution.py`, and why is it useful?**

<details>
<summary>Show answer</summary>

`Path(__file__)` is the path to the current source file. `.resolve()` converts it to an absolute path. `.parents[N]` walks N levels up from the file itself. For a file at `curriculum/python-foundation/exercises/day-03/solution.py` the hierarchy is:

- `parents[0]` = `day-03/`
- `parents[1]` = `exercises/`
- `parents[2]` = `python-foundation/`
- `parents[3]` = `curriculum/`
- `parents[4]` = `AI_Training/` ← repo root

So `parents[4]` returns the repo root. This makes paths portable across machines and avoids hard-coded absolute paths.

</details>

**Q3. What is the difference between `json.loads()` and `json.load()`?**

<details>
<summary>Show answer</summary>

`json.loads(s)` ("load string") parses a JSON **string** and returns a Python object. `json.load(f)` ("load file") reads from an **open file object** and parses it. Similarly, `json.dumps(obj)` produces a JSON string while `json.dump(obj, f)` writes JSON directly to a file.

</details>

**Q4. You call `json.loads(text)` on data from an external source and the application crashes with an unhandled exception. What specific exception should you catch, and why catch the specific type rather than bare `except:`?**

<details>
<summary>Show answer</summary>

Catch `json.JSONDecodeError` (a subclass of `ValueError`). Catching the specific type means only malformed-JSON errors are handled; other unexpected exceptions (like `TypeError` or `MemoryError`) still propagate and are not silently swallowed. Using bare `except:` or `except Exception:` hides bugs that need to be fixed.

</details>

**Q5. What does `re.findall(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", text)` return when `text` contains three email addresses?**

<details>
<summary>Show answer</summary>

A list of three strings — one for each complete email address that the pattern matched. `re.findall` always returns a flat list of matching strings (or a list of tuples when the pattern contains capture groups).

</details>

**Q6. What is the purpose of `os.getenv("KEY", "default")` versus `os.environ["KEY"]`?**

<details>
<summary>Show answer</summary>

`os.getenv("KEY", "default")` returns the environment variable's value if it exists, or the provided default string if it does not — it never raises an exception. `os.environ["KEY"]` raises a `KeyError` if the variable is not set. For optional configuration (log level, feature flags) `os.getenv` with a default is safer; for required variables you may prefer `os.environ["KEY"]` so the program fails fast with a clear error.

</details>

**Q7. How do you make a Python directory into a package that can be imported?**

<details>
<summary>Show answer</summary>

Add an `__init__.py` file (which can be empty) to the directory. Python recognises any directory containing `__init__.py` as a package. After that you can write `from my_package.module import something` from any file that has the parent directory on its `sys.path`.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1. The `with` statement is described as a "context manager." What protocol makes a Python object work as a context manager, and could you write your own?**

<details>
<summary>Show answer</summary>

A context manager implements two dunder methods: `__enter__` (called when the `with` block starts; its return value is bound to the `as` variable) and `__exit__` (called when the block ends, whether normally or via an exception). The `__exit__` method receives the exception type, value, and traceback; returning `True` suppresses the exception. You can write a simple one:

```python
import time

class Timer:
    def __enter__(self):
        self._start = time.time()
        return self
    def __exit__(self, *args):
        elapsed = time.time() - self._start
        print(f"Elapsed: {elapsed:.3f}s")

with Timer():
    sum(range(10_000_000))
```

The `contextlib` module also provides `@contextmanager` to build context managers from generator functions, which is often simpler.

</details>

**Q2. `pathlib.Path` objects support the `/` operator for joining path segments. How does that work in Python?**

<details>
<summary>Show answer</summary>

Python allows any class to override operators by defining special methods. `pathlib.Path` overrides `__truediv__` (the `/` operator). When you write `Path("data") / "hr-corpus"`, Python calls `Path("data").__truediv__("hr-corpus")`, which returns a new `Path` object representing `data/hr-corpus`. This is purely a design choice by the `pathlib` authors to make path joining read naturally rather than requiring a `join()` call.

</details>

**Q3. JSON only supports a fixed set of types. What happens when you try to serialise a Python `datetime` object with `json.dumps()`?**

<details>
<summary>Show answer</summary>

`json.dumps()` raises `TypeError: Object of type datetime is not JSON serializable`. To handle this you have three options: (1) convert to a string before passing to `json.dumps` (`dt.isoformat()`); (2) write a custom encoder by subclassing `json.JSONEncoder` and overriding its `default` method; (3) use a third-party library like `pydantic` or `orjson` that handles common Python types automatically. The explicit approach — converting to ISO 8601 strings — is the most portable because any JSON consumer can parse the string.

</details>

**Q4. Explain what `sys.path` is and why a `ModuleNotFoundError` can appear even when the file clearly exists on disk.**

<details>
<summary>Show answer</summary>

`sys.path` is a list of directory strings that Python searches when resolving an `import` statement. It is populated at startup from: the script's own directory, the `PYTHONPATH` environment variable, and installation-specific defaults. A `ModuleNotFoundError` means Python searched every directory in `sys.path` and did not find a matching module. Common causes: running the script from the wrong directory (so the script's directory is not the project root), forgetting `__init__.py` in a package, or installing a package in one virtual environment while running Python from another. Printing `import sys; print(sys.path)` is the fastest diagnostic.

</details>

**Q5. What makes a regular expression "greedy" and when would you want a "non-greedy" (lazy) match instead?**

<details>
<summary>Show answer</summary>

By default, quantifiers like `*`, `+`, and `?` are **greedy** — they match as many characters as possible while still allowing the overall pattern to succeed. A lazy (non-greedy) quantifier (`*?`, `+?`, `??`) matches as few characters as possible. Example: given `<b>bold</b> and <b>more</b>`, the pattern `<b>.*</b>` greedily captures everything from the first `<b>` to the last `</b>`. The pattern `<b>.*?</b>` lazily captures each tag pair separately. In document parsing, lazy matching is usually what you want when the delimiter can appear multiple times.

</details>

**Q6. `python-dotenv` reads a `.env` file. What security practices should be followed around `.env` files in a project?**

<details>
<summary>Show answer</summary>

Key practices: (1) Add `.env` to `.gitignore` — it must never be committed to version control. (2) Provide a `.env.example` file with placeholder values (no real secrets) that is committed, so other team members know which variables to set. (3) In production environments (CI, cloud), inject secrets through the platform's secret management (GitHub Actions secrets, AWS Parameter Store, Vault, etc.) rather than deploying a `.env` file. (4) Use least-privilege values — each service gets only the secrets it needs. (5) Rotate secrets if a `.env` file is accidentally committed; do not simply delete it from history without also rotating the credentials.

</details>

**Q7. PII redaction with regex is described as a "first pass." Why is regex alone insufficient for production PII removal?**

<details>
<summary>Show answer</summary>

Regex can only match patterns it was explicitly programmed to recognise. It fails on: (1) Novel or regional PII formats (non-standard phone formats, national ID numbers from different countries). (2) Names — "Alice Smith" is PII but has no reliable regex pattern. (3) Context-dependent PII — "Room 42" may or may not be a location identifier depending on context. (4) Obfuscation — an attacker (or innocent typo) can break a regex match while the human meaning remains clear. Production systems layer regex with NLP-based Named Entity Recognition (NER) models and, increasingly, LLM-based classifiers. The AI labs in this course build on exactly this progression: regex first, then model-assisted redaction.

</details>

**Q8. What is the difference between `datetime.date`, `datetime.datetime`, and `datetime.time` in Python?**

<details>
<summary>Show answer</summary>

All three live in the `datetime` module. `datetime.date` represents a calendar date (year, month, day) with no time component. `datetime.time` represents a time of day (hour, minute, second, microsecond, optional timezone) with no date component. `datetime.datetime` combines both — it is a specific point in time (year through microsecond plus optional timezone). In practice: use `date` for things like birthdays or deadlines, `datetime` for log timestamps or API responses, and `time` rarely (usually when you have stripped the date portion for schedule comparisons). The `datetime` class also inherits date's methods, so you can call `.date()` on a `datetime` object to extract just the date part.

</details>

---

## 6. Key Takeaways

- Always use `with open(...)` for file I/O; always specify `encoding="utf-8"`.
- `pathlib.Path` is the modern, cross-platform way to work with files; use `Path(__file__).resolve().parents[N]` to find the repo root from any nested file.
- `json.load`/`json.dump` work with file objects; `json.loads`/`json.dumps` work with strings. Wrap untrusted JSON parsing in `try/except json.JSONDecodeError`.
- Every `.py` file is a module; a directory with `__init__.py` is a package. Python finds them via `sys.path`.
- Store secrets in environment variables, not in source code. Use `os.getenv` to read them and `python-dotenv` to load `.env` files locally.
- `re.search` finds the first match, `re.findall` returns all matches, `re.sub` replaces matches. Regex is the lightweight first layer of PII redaction — the AI labs will add NLP-based layers on top.
- `datetime.date` is a calendar date, `datetime.datetime` is a full timestamp. Use `strftime`/`strptime` to convert between strings and datetime objects.
