# Day 6 Lab — LLM System Exploration & Failure Cataloguing

**Track:** QA Engineering with AI  
**Day:** 6 of 15  
**Time to complete:** ~60–75 minutes

---

## What You Will Build

A **system-exploration and failure-cataloguing harness** that:

1. Defines a structured probe set — questions targeting each failure-mode category.
2. Runs those probes against the Acme HR Assistant SUT (no API key required).
3. Applies programmatic detectors to each response.
4. Aggregates results into a structured **failure report** and **risk map**.
5. Surfaces **Seeded Bug #1** (faithfulness/hallucination — PTO count) and **Seeded Bug #2** (retrieval bug — bereavement leave returns parental-leave chunk first).

---

## Prerequisites

- Python 3.11+
- No API key required — the SUT is a deterministic local mock.
- No external packages required — stdlib only (plus the shared SUT, which is also stdlib-only).

---

## Setup

```bash
# From the repo root
cd AI_Training

# (Optional) Activate your virtual environment
source .venv/bin/activate   # or: .venv\Scripts\activate on Windows

# Verify the SUT works
python labs/qa/_shared/hr_assistant.py
```

You should see smoke-test output confirming the assistant answers a PTO question and a benefits question.

---

## Running the Lab

### Starter file (your starting point):

```bash
python labs/qa/day-06/starter.py
```

The starter file has `# TODO` comments guiding you through each step.

### Solution file (reference implementation):

```bash
python labs/qa/day-06/solution.py
```

Expected output includes a failure report showing at minimum two `FAIL` results — one for Seeded Bug #1 (PTO hallucination) and one for Seeded Bug #2 (bereavement retrieval ranking).

---

## Step-by-Step Guide (for starter.py)

### Step 1 — Define your probe set

Each probe is a dictionary with:
- `id` — short identifier (e.g., `"PTO-001"`)
- `category` — failure-mode category (e.g., `"hallucination"`, `"retrieval"`, `"safety"`)
- `question` — the input to the SUT
- `guarded` — `True` or `False`
- `expect_answer_contains` — substring(s) the answer must contain (or `None`)
- `expect_answer_not_contains` — substring(s) the answer must NOT contain (or `None`)
- `expect_source_contains` — filename that must appear in `sources` (or `None`)
- `expect_first_context_keyword` — keyword that must appear in the first retrieved chunk (or `None`)

### Step 2 — Run probes and capture results

Call `answer(probe["question"], guarded=probe["guarded"])` for each probe. Store the full result dict alongside the probe definition.

### Step 3 — Apply detectors

For each probe, check each expectation field. A probe **FAILS** if any expectation is violated.

### Step 4 — Build the failure report

Print a table of probe ID, category, status (PASS/FAIL), and failure reason.

### Step 5 — Build the risk map

For each failing category, rate likelihood (based on observed failures) and impact (based on consequence to users). Print as a prioritised table.

---

## Key Files

| File | Purpose |
|---|---|
| `starter.py` | Your working file — complete the TODOs |
| `solution.py` | Reference implementation |
| `requirements.txt` | Dependencies (stdlib only — no installs needed) |
| `../../_shared/hr_assistant.py` | The SUT |
| `../../_shared/README.md` | SUT documentation including seeded bugs |

---

## What You Should Observe

After running `solution.py`, you should see:

- **PTO-001**: FAIL — answer says "20 days", corpus says "15 days" for new employees (Bug #1)
- **BRV-001**: FAIL — first context chunk is about Parental Leave, not Bereavement Leave (Bug #2)
- **PTO-002**: PASS — paraphrase variant of PTO question (same bug, consistent detection)
- **SAF-001**: FAIL (unguarded) / PASS (guarded) — PII leak / injection detection
- All other probes: PASS

---

## Discussion Questions

After completing the lab, reflect on:

1. If you only tested the "happy path" (correct questions, no adversarial inputs), which bugs would you have missed?
2. How would you extend this harness to run against a real LLM (with an API key) rather than the mock?
3. What would you add to the risk map to make it actionable for a product manager?
