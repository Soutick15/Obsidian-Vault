"""
Day 3 Exercise — Files, JSON, and Modules  (SOLUTION)
======================================================
Run from the repo root:

    python curriculum/python-foundation/exercises/day-03/solution.py

Pure stdlib only — no external packages, no network.

File layout (relative to repo root):
  curriculum/python-foundation/exercises/day-03/solution.py
    parents[0]  →  day-03/
    parents[1]  →  exercises/
    parents[2]  →  python-foundation/
    parents[3]  →  curriculum/
    parents[4]  →  <repo root>  (AI_Training/)
"""

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 0. Locate the shared corpus
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[4]
CORPUS_DIR = REPO_ROOT / "data" / "hr-corpus"

if not CORPUS_DIR.exists():
    print(f"Corpus directory not found: {CORPUS_DIR}")
    print("Make sure you are running from inside the AI_Training repo.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# 1. Count documents, skipping README.md
# ---------------------------------------------------------------------------
docs: list[Path] = [
    p for p in CORPUS_DIR.glob("*.md")
    if p.name != "README.md"
]
docs.sort()

print(f"Found {len(docs)} corpus documents (README excluded).")

# ---------------------------------------------------------------------------
# 2. Extract email-like strings with regex
# ---------------------------------------------------------------------------
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.IGNORECASE)

all_emails: list[str] = []
for doc in docs:
    text = doc.read_text(encoding="utf-8")
    found = EMAIL_RE.findall(text)
    all_emails.extend(found)

unique_emails = sorted(set(all_emails))
print(f"Unique email-like strings found: {len(unique_emails)}")
if unique_emails:
    for e in unique_emails:
        print(f"  {e}")

# ---------------------------------------------------------------------------
# 3. Build summary dict and write JSON
# ---------------------------------------------------------------------------
summary = {
    "corpus_dir": str(CORPUS_DIR),
    "doc_count": len(docs),
    "doc_names": [p.name for p in docs],
    "unique_emails": unique_emails,
}

OUTPUT_PATH = Path(__file__).resolve().parent / "summary.json"

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print(f"\nSummary written to: {OUTPUT_PATH}")

# ---------------------------------------------------------------------------
# 4. Read the JSON back and confirm
# ---------------------------------------------------------------------------
try:
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    print("\n--- Summary (read back from JSON) ---")
    print(f"  corpus_dir   : {loaded['corpus_dir']}")
    print(f"  doc_count    : {loaded['doc_count']}")
    print(f"  unique_emails: {len(loaded['unique_emails'])}")
    print(f"  docs listed  : {', '.join(loaded['doc_names'][:3])}{'...' if len(loaded['doc_names']) > 3 else ''}")
except json.JSONDecodeError as e:
    print(f"JSON parse error when reading back: {e}")

print("\nDone.")
