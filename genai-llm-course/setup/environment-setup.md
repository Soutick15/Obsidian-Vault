# Environment Setup Guide

This guide walks you through setting up a local Python environment for the 15-day GenAI/LLM training program.

---

## 1. Install Python 3.11+

Check your current version:

```bash
python3 --version
```

If you have Python < 3.11, install via your platform's package manager:

- **macOS**: `brew install python@3.11`
- **Ubuntu/Debian**: `sudo apt install python3.11 python3.11-venv`
- **Windows**: Download the installer from [python.org](https://www.python.org/downloads/) and check "Add to PATH".

---

## 2. Create a Virtual Environment

```bash
# From the AI_Training directory
python3.11 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

Your prompt will show `(.venv)` when active. Always activate before running lab code.

---

## 3. Install Baseline Packages

With the venv active:

```bash
pip install --upgrade pip

pip install \
  anthropic \
  openai \
  sentence-transformers \
  chromadb \
  faiss-cpu \
  langchain \
  llama-index \
  python-dotenv \
  jupyter \
  tiktoken
```

> **Note:** `sentence-transformers` enables free local embeddings — many labs default to this so you can run without spending API credits.

---

## 4. Set Up API Keys via `.env`

Create a `.env` file in the project root (already listed in `.gitignore` — never commit this):

```bash
# AI_Training/.env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

Load the keys in any Python script:

```python
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env in the current or parent directory

anthropic_key = os.getenv("ANTHROPIC_API_KEY")
openai_key    = os.getenv("OPENAI_API_KEY")
```

---

## 5. Where to Get API Keys

| Provider | Console URL | Notes |
|----------|-------------|-------|
| Anthropic (Claude) | [console.anthropic.com](https://console.anthropic.com) | Create an account → API Keys → New Key |
| OpenAI | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | Create an account → Dashboard → API Keys |

Both providers offer free trial credits. Labs are designed to use the smallest/cheapest models by default.

---

## 6. Cost-Control Notes

- Labs default to **small models** (`claude-haiku-4-5` or `gpt-5-mini`) to minimise token costs.
- **Embedding labs** use `sentence-transformers` (runs locally, free) unless the lab explicitly needs a provider API.
- Every lab has a **mock / offline path** (`USE_MOCK=true` env var or a `--mock` flag) for verifying logic without spending credits.
- For Week 1–2 labs, expect < $0.05 per lab run on the default small models.
- Set [usage limits](https://console.anthropic.com/settings/limits) in both consoles to cap monthly spend.

---

## 7. Verification Snippet

Run this to confirm your environment is ready:

```python
# setup/verify.py
import sys
from dotenv import load_dotenv
import os

load_dotenv()

print(f"Python: {sys.version}")

packages = [
    "anthropic",
    "openai",
    "sentence_transformers",
    "chromadb",
    "faiss",
    "langchain",
    "llama_index",
    "dotenv",
    "jupyter",
    "tiktoken",
]

all_ok = True
for pkg in packages:
    try:
        __import__(pkg)
        print(f"  [OK]  {pkg}")
    except ImportError:
        print(f"  [MISSING]  {pkg}")
        all_ok = False

anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
openai_key    = os.getenv("OPENAI_API_KEY", "")

print()
print(f"ANTHROPIC_API_KEY set: {'yes' if anthropic_key else 'NO - add to .env'}")
print(f"OPENAI_API_KEY    set: {'yes' if openai_key    else 'NO - add to .env'}")

if all_ok:
    print("\nEnvironment ready.")
else:
    print("\nSome packages missing — re-run pip install step.")
```

```bash
python setup/verify.py
```

Expected output (with keys set):
```
Python: 3.11.x ...
  [OK]  anthropic
  [OK]  openai
  ...
ANTHROPIC_API_KEY set: yes
OPENAI_API_KEY    set: yes

Environment ready.
```

---

## 8. Running Jupyter Notebooks (optional)

```bash
jupyter notebook
```

Navigate to any `labs/` subfolder to open `.ipynb` files if provided alongside `.py` labs.

---

## 9. Updating Packages

```bash
pip install --upgrade anthropic openai langchain llama-index
```

Repeat this at the start of Week 2 and Week 3 as the landscape moves quickly.
