# Python Foundation — 5-Day Pre-Course

The python foundation is deliberately **reverse-engineered from our own labs** — every topic here is Python you will actually use later (loading the corpus with `pathlib`, parsing JSON, validating data with Pydantic, calling APIs with `httpx`, writing `pytest` tests, the `--selftest` CLI pattern, and so on).

## The 5 days

| Day | Topic | What it unlocks later |
|----|-------|------------------------|
| 1 | [Running Python & the Basics](Day-01-running-python-and-basics.md) | venv/pip, running scripts, variables, control flow, `if __name__ == "__main__"` |
| 2 | [Data Structures & Functions](Day-02-data-structures-and-functions.md) | lists/dicts/sets, comprehensions, functions, error handling |
| 3 | [Files, JSON & Modules](Day-03-files-json-and-modules.md) | `pathlib`, reading the corpus, JSON parsing, imports, regex — mirrors RAG ingestion |
| 4 | [Classes, Type Hints & Pydantic](Day-04-OOPs-typing-and-pydantic.md) | classes, dataclasses, typing, **Pydantic** validation — mirrors structured-output labs |
| 5 | [APIs, Async & Testing](Day-05-apis-async-and-testing.md) | `requests`/`httpx`, async basics, **pytest**, `argparse`/`--selftest` — how every lab is built |

## How to use each day
Read the concept section → do the hands-on exercise in `exercises/day-NN/` → take the self-check quiz → review the Concept Deep-Dive Q&A → skim key takeaways. Quiz and Q&A answers are hidden behind **"Show answer"** toggles so you can test yourself first.

## Setup
One-time, from the repo root:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r curriculum/python-foundation/exercises/requirements.txt
```
Days 1–3 use only the Python standard library; the dependencies above are for Days 4–5. See the main [`setup/environment-setup.md`](../../setup/environment-setup.md) for full environment setup.

## Format note
Each day follows a 6-section structure (Objectives · Concept reading · Hands-on exercise · Self-check quiz · Concept Deep-Dive Q&A · Key takeaways). Everything runs locally with **no API key**.
