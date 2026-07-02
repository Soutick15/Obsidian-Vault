"""
Day 3 Exercise — Files, JSON, and Modules
==========================================
Work through each TODO in order.
Run this file from the repo root:

    python curriculum/python-foundation/exercises/day-03/starter.py

You need only the Python standard library — no external packages, no network.
"""

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Locate the shared corpus
# ---------------------------------------------------------------------------
# This file lives at:  curriculum/python-foundation/exercises/day-03/starter.py
# parents[0] = day-03/
# parents[1] = exercises/
# parents[2] = python-foundation/
# parents[3] = curriculum/
# parents[4] = repo root  ← we need one level above curriculum
#
# TODO 1: Fill in the correct index so REPO_ROOT points to the repo root.
#         Then build the path to data/hr-corpus/.

REPO_ROOT = Path(__file__).resolve().parents[4]   # TODO 1: adjust index if needed
CORPUS_DIR = REPO_ROOT / "data" / "hr-corpus"

if not CORPUS_DIR.exists():
    print(f"Corpus directory not found: {CORPUS_DIR}")
    print("Make sure you are running from inside the AI_Training repo.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Task 1 — Count documents (skip README.md)
# ---------------------------------------------------------------------------
# TODO 2: Use Path.glob to collect all *.md files in CORPUS_DIR.
#         Filter out any file whose name is "README.md".
#         Store the list in `docs`.

docs = []   # TODO 2: replace with your glob + filter

print(f"Found {len(docs)} corpus documents (README excluded).")

# ---------------------------------------------------------------------------
# Task 2 — Extract email addresses with regex
# ---------------------------------------------------------------------------
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.IGNORECASE)

all_emails: list[str] = []

# TODO 3: Iterate over each Path in `docs`.
#         Read the file text (use .read_text(encoding="utf-8")).
#         Use EMAIL_RE.findall() to get all emails in that text.
#         Extend all_emails with the results.

# --- your code here ---

unique_emails = sorted(set(all_emails))
print(f"Unique email-like strings found: {len(unique_emails)}")
if unique_emails:
    for e in unique_emails:
        print(f"  {e}")

# ---------------------------------------------------------------------------
# Task 3 — Build a summary dict and write it as JSON
# ---------------------------------------------------------------------------
# TODO 4: Build a dict called `summary` with these keys:
#   "corpus_dir"   : str(CORPUS_DIR)
#   "doc_count"    : int, number of docs (not counting README)
#   "unique_emails": unique_emails  (the list you built above)

summary = {}   # TODO 4: replace with the real dict

OUTPUT_PATH = Path(__file__).resolve().parent / "summary.json"

# TODO 5: Write `summary` to OUTPUT_PATH as pretty-printed JSON (indent=2).
#         Use json.dump() inside a with-open block.

print(f"\nSummary written to: {OUTPUT_PATH}")

# ---------------------------------------------------------------------------
# Task 4 — Read the JSON back and print it
# ---------------------------------------------------------------------------
# TODO 6: Open OUTPUT_PATH, read with json.load(), and print a confirmation.
#         Wrap the load in a try/except json.JSONDecodeError block.

# --- your code here ---

print("\nDone.")
