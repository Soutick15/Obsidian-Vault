# QA Capstone — Comprehensive Automated Test & Evaluation Suite for the Acme HR Knowledge Assistant

## 1. Goal

Build a comprehensive automated test and evaluation suite for the Acme HR Knowledge Assistant (SUT). This is the culminating project of the QA track, integrating skills from Days 6–14. By completing this capstone, you will demonstrate that you can design, implement, and run a full LLM quality assurance pipeline — from golden-set evaluation through adversarial red-teaming and CI integration.

## 2. System Under Test

The **Acme HR Knowledge Assistant** is a deterministic mock RAG (Retrieval-Augmented Generation) pipeline that answers employee questions about HR policy. Key characteristics:

- **No API key required** — the SUT is a Python mock that uses seeded in-memory data.
- **Deterministic** — the same question always returns the same answer, making it ideal for automated testing.
- **Interface**: `answer(question, k=3, guarded=False)` returns `{"answer": str, "contexts": [str], "sources": [str]}`.
- **Four seeded bugs** you must find and document:
  1. **Faithfulness / PTO hallucination** — the assistant returns "20 days" for new-employee PTO when the policy says "15 days".
  2. **Retrieval bug** — for certain queries, the retriever returns irrelevant chunks (low precision@k).
  3. **PII leak** — an internal `EMPLOYEE_SECRET_TOKEN` value appears in answers under specific inputs.
  4. **Prompt injection susceptibility** — injecting instructions into the question string can alter assistant behavior.

## 3. Required Components

Each component maps to skills taught on specific course days.

| Component | Course Days | File |
|-----------|-------------|------|
| Golden-set eval harness + metrics | Days 8, 14 | `eval_harness.py` |
| LLM-as-judge scorer | Day 9 | `judge.py` (mock, no API key) |
| RAG retrieval metrics | Day 10 | `rag_metrics.py` |
| Adversarial / red-team suite | Days 11–12 | `redteam.py` |
| AI-generated test cases (pattern) | Day 13 | described in `eval_harness.py` comments |
| CI eval gate with exit code | Day 14 | `ci_gate.py` |

### Component Descriptions

**`eval_harness.py`** — Defines a golden set of question/answer pairs with expected-contains checks and faithfulness checks. Runs all items, computes pass rate, and prints a report.

**`judge.py`** — A mock LLM-as-judge that scores answers on helpfulness (1–5) and faithfulness (1–5) using keyword heuristics. No external API calls needed.

**`rag_metrics.py`** — Computes Precision@k, Recall@k, and MRR for the assistant's retrieval component, using a list of questions with known relevant keywords.

**`redteam.py`** — Runs adversarial probes including PII leak triggers, prompt injection attempts, hallucination triggers, off-topic questions, and jailbreak attempts. Reports which probes found vulnerabilities.

**`ci_gate.py`** — Orchestrates all modules, computes a weighted gate score, and exits with code 0 (pass) or 1 (fail) based on a configurable threshold. The primary entry point for CI/CD integration.

## 4. Deliverables

By the end of the capstone you should have:

1. **All starter modules completed** — every TODO in `eval_harness.py`, `judge.py`, `rag_metrics.py`, `redteam.py`, and `ci_gate.py` filled in with working code.
2. **A test report printed to stdout** (or optionally saved as JSON) when `python ci_gate.py` is run.
3. **A CI gate** that exits non-zero when the overall quality score falls below the configured threshold.
4. **A `FINDINGS.md` file** (you create this) documenting:
   - Which of the four seeded bugs were caught by your tests.
   - Which tests failed and why.
   - The metric values your suite produced (pass rate, judge scores, retrieval metrics, vulnerability count).
   - Any observations about the SUT's failure modes.

## 5. How to Run / Demo

```bash
# Run the full CI gate (primary entry point)
python capstone/qa/starter/ci_gate.py

# Run with a stricter threshold
python capstone/qa/starter/ci_gate.py --threshold 0.9

# Skip the judge for a faster run
python capstone/qa/starter/ci_gate.py --skip-judge

# Run any pytest-based tests in the starter package
python -m pytest capstone/qa/starter/ -v

# Run individual modules
python capstone/qa/starter/eval_harness.py
python capstone/qa/starter/judge.py
python capstone/qa/starter/rag_metrics.py
python capstone/qa/starter/redteam.py
```

**Demo goal**: When you run `python ci_gate.py`, the output should show:
- The eval harness report with at least one FAIL (catching the PTO hallucination bug).
- The RAG metrics report with at least one low-precision question.
- At least one VULNERABLE probe in the red-team report.
- A final gate score and PASS/FAIL decision.

## 6. Suggested Approach

Work through this capstone over two sessions.

### Session 1 — Day 14 Lab Time

1. Read `project-brief.md` and `rubric.md` thoroughly.
2. Open `eval_harness.py`. Fill in `build_golden_set()` first — aim for 10 items covering PTO, remote work, onboarding, benefits, and at least one negative test.
3. Implement `check_contains()` and `check_faithfulness()` — these are the core checkers.
4. Implement `score_item()` and `run_harness()`.
5. Run `python eval_harness.py` — you should see the PTO hallucination appear as a FAIL.
6. Open `rag_metrics.py`. Implement `precision_at_k()`, `recall_at_k()`, and `compute_mrr()`.
7. Implement `evaluate_retrieval()` and run `python rag_metrics.py`.

### Session 2 — Day 15

1. Open `judge.py`. Implement `mock_judge()` — start simple with length and keyword checks.
2. Implement `run_judge_suite()` and run `python judge.py`.
3. Open `redteam.py`. Implement `build_probe_suite()` with at least 5 probes.
4. Implement `run_probe()` and `run_red_team_suite()`, run `python redteam.py`.
5. Open `ci_gate.py`. Wire up all four modules, compute the weighted gate score, and test `sys.exit()` behavior.
6. Create `FINDINGS.md` — document your findings. See rubric for what to include.

## 7. Grading

See `rubric.md` for the full weighted rubric (100 points total).
