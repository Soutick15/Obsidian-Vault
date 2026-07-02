# QA Capstone Rubric

**Total: 100 points**

---

## Scoring Breakdown

| Component | Points | Criteria |
|-----------|--------|----------|
| **Eval Harness** (`eval_harness.py`) | 20 | Golden set contains >= 8 items; `check_contains` uses case-insensitive substring matching (not exact match); `check_faithfulness` verifies claims against contexts; pass rate computed as `passed / total`; PTO question included with `expected_contains=["15"]` |
| **Metric Correctness** | 15 | Metrics are semantically meaningful (not trivially true or always 1.0); PTO hallucination bug caught (expected "15", got "20" → FAIL); at least 2 of the 4 seeded bugs detected across all modules combined |
| **RAG Retrieval Metrics** (`rag_metrics.py`) | 15 | `precision_at_k` correctly counts relevant retrieved contexts divided by k; `recall_at_k` measures fraction of expected keywords found; MRR correctly returns 1/rank of first relevant hit (0 if none); metrics computed for >= 3 questions |
| **LLM-as-Judge** (`judge.py`) | 15 | Mock judge runs without API key or network calls; scoring rubric uses a 1–5 integer scale for both helpfulness and faithfulness; explanations are non-empty strings; average scores returned correctly |
| **Red-Team Suite** (`redteam.py`) | 15 | >= 5 adversarial probes implemented; all four attack types covered (pii_leak, prompt_injection, hallucination, off_topic); each probe has a `detect_failure_fn` that returns a boolean; findings reported with evidence strings |
| **CI Gate** (`ci_gate.py`) | 10 | Exits with code 1 when gate score < threshold; exits with code 0 when gate score >= threshold; `--threshold` argument works; handles `NotImplementedError` from incomplete modules gracefully (no unhandled exception) |
| **Code Quality** | 5 | Functions named clearly (verbs for actions, nouns for data); type hints on all function signatures; no dead code or commented-out blocks; modules importable without side effects |
| **Findings Write-up** (`FINDINGS.md`) | 5 | Documents which of the 4 seeded bugs were caught; includes actual metric values (pass rate %, judge scores, precision@k, vulnerability count); includes at least one observation about why a bug is hard to catch automatically |

---

## Grading Bands

| Score | Grade |
|-------|-------|
| 90–100 | **Distinction** — All components working, all 4 bugs caught, CI gate functional, thorough write-up |
| 75–89 | **Merit** — Core components working, at least 2 bugs caught, CI gate functional |
| 60–74 | **Pass** — Eval harness and at least one other module working, at least 1 bug caught |
| < 60 | **Incomplete** — Core components not implemented or have fundamental logic errors |

---

## Common Mistakes to Avoid

**1. Using exact string match instead of contains check.**
`answer_text == expected` will almost always fail. Use `expected.lower() in answer_text.lower()`.

**2. Hardcoding the pass threshold.**
The CI gate accepts `--threshold` as a CLI argument. Do not hardcode `0.60` inside the gate logic — always read from `args.threshold`.

**3. Crashing when a module is not yet implemented.**
`ci_gate.py` must catch `NotImplementedError` (and `ImportError`) for each module separately. A partially-complete capstone should still run the completed parts.

**4. Not testing adversarial inputs.**
Many learners test only "happy path" questions. The red-team suite must use inputs specifically designed to trigger failure modes — not just unusual-but-valid questions.

**5. Faithfulness check that always returns True.**
If you check `claim in " ".join(contexts)` with very short claims like `"is"` or `"the"`, every claim will pass. Use meaningful multi-word phrases or noun phrases as faithfulness claims.

**6. Not calling `sys.exit(1)` in the CI gate.**
Printing "FAIL" to stdout is not enough for CI systems. The gate must actually exit with a non-zero code. Test with `echo $?` after running the gate.

**7. MRR returning 1 when no relevant context is found.**
If no retrieved context matches the relevant keywords, MRR should be `0.0`, not `1.0`. Double-check your loop boundary conditions.

**8. Judge scores that are always 5/5.**
A mock judge that always returns the maximum score provides no signal. Build in length and keyword checks that can genuinely produce lower scores for poor answers.
