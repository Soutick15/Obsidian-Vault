# Day 15 — Capstone Completion & Course Review

**Track:** QA Engineering with AI
**Day:** 15 of 15 — Course Finale
**Prerequisites:** Days 1–14 (all QA track modules); capstone work in `capstone/qa/`

---

## 1. Learning Objectives

By the end of today you will be able to:

1. **Complete and present** your QA capstone project, running the full evaluation suite end-to-end and narrating results clearly.
2. **Consolidate the whole QA track** by mapping every technique you applied back to its conceptual foundation across Days 1–14.
3. **Self-assess** your own test suite against the rubric categories (correctness, coverage, robustness, automation quality, documentation) and identify your strongest and weakest areas.
4. **Articulate design decisions** — why you chose particular assertion strategies, judge configurations, and red-team scenarios — with principled reasoning.
5. **Plan continued learning** with a concrete roadmap into advanced evals, observability, and AI-assisted test automation beyond this course.

---

## 2. Capstone Completion & Demo

### 2.1 What to Submit

All deliverables live in `capstone/qa/`. Before running the demo, verify each item exists and passes a basic sanity check:

```
capstone/qa/
├── README.md           # project overview, how to run, design decisions
├── data/               # golden datasets, red-team prompt sets
├── tests/              # eval harness (pytest or plain Python)
│   ├── test_correctness.py
│   ├── test_groundedness.py
│   ├── test_safety.py
│   └── test_regression.py
├── evals/              # LLM-as-judge configurations / promptfoo YAML
├── results/            # last run output (JSON/CSV) committed for review
└── requirements.txt    # pinned deps
```

### 2.2 Finishing Checklist (mapped to rubric categories)

Work through this checklist before your walkthrough. Each item maps to a rubric category.

#### Correctness & Assertion Quality
- [ ] Every test has a meaningful assertion — not just `assert response is not None`
- [ ] Semantic-similarity or LLM-as-judge is used for at least the open-ended tests; exact-match is reserved for structured outputs (JSON fields, enums)
- [ ] Faithfulness / groundedness checks are wired to the RAG pipeline (if applicable)
- [ ] At least one regression guard compares against a stored baseline

#### Coverage
- [ ] Happy-path, edge-case, and boundary inputs are represented
- [ ] At least one red-team / adversarial category is covered (prompt injection, off-topic jailbreak, or data-poisoning probe)
- [ ] The golden dataset has ≥ 20 cases with diverse question types
- [ ] Agent tool-call trajectory is validated (if the capstone targets an agent)

#### Robustness & Non-Determinism Handling
- [ ] Tests use probabilistic assertions (threshold-based, not brittle exact strings) where appropriate
- [ ] Temperature / sampling variability is documented; determinism is used (`temperature=0`) for golden-set regression runs
- [ ] Flaky test mitigation is in place (retry logic or documented acceptable variance)

#### Automation Quality
- [ ] Tests run with a single command (`pytest capstone/qa/tests/` or `python run_evals.py`)
- [ ] CI-readiness: no hardcoded personal API keys; env vars or `.env` file pattern used
- [ ] Results are persisted to `capstone/qa/results/` for auditing

#### Documentation
- [ ] `README.md` explains the system under test, test strategy, how to run, and how to interpret results
- [ ] Each test file has a module-level docstring explaining what it covers and why
- [ ] Design decisions (why LLM-as-judge here, why exact-match there) are documented inline or in README

### 2.3 Running the Full Eval Suite

```bash
# 1. Activate your virtual environment
source .venv/bin/activate

# 2. Install / confirm dependencies
pip install -r capstone/qa/requirements.txt

# 3. Run all tests and save output
pytest capstone/qa/tests/ -v --tb=short 2>&1 | tee capstone/qa/results/run-$(date +%Y%m%d).txt

# 4. Run LLM-as-judge evals (if using promptfoo)
npx promptfoo eval --config capstone/qa/evals/promptfooconfig.yaml

# 5. Run LLM-as-judge evals (if using deepeval)
python -m pytest capstone/qa/evals/ -v
```

### 2.4 Walkthrough Structure (10 minutes)

Prepare a short walkthrough that answers these four questions in order:

1. **What is the system under test?** (1–2 sentences on the SUT's purpose and architecture)
2. **What can go wrong?** (Your failure-mode taxonomy: top 3–5 risk categories you identified)
3. **How did you test it?** (Walk through one test from each major category — correctness, groundedness, safety, regression)
4. **What did the eval suite find?** (Show actual results output; highlight any bugs or regressions caught)

Tip: walk through `capstone/qa/results/` output live rather than slides — it shows the eval harness actually runs.

---

## 3. Capstone Review & Reflection

These questions are for your own deepening of understanding — not an external evaluation. Work through them in writing (a notebook or scratchpad). For each question, a model answer and "what strong understanding looks like" note follow.

---

**Q1. Why did you use semantic similarity (or LLM-as-judge) instead of exact-match for certain assertions? When is exact-match the right choice?**

<details>
<summary>Show answer</summary>

*Model answer:* LLM outputs for open-ended questions are one-to-many: many valid phrasings exist for the same correct answer. Exact-match fails valid paraphrases and is brittle to whitespace or punctuation changes. Semantic similarity (cosine over embeddings) checks meaning regardless of wording. LLM-as-judge adds rubric-based nuance (groundedness, completeness). Exact-match is correct when the output is structurally constrained: a JSON field value, an enum, a date, a URL — places where there is exactly one correct string.

*What strong understanding looks like:* You can name a specific test in your suite where exact-match would have produced a false failure, and another where it is the right tool.

</details>

---

**Q2. How would you detect that your system's output quality has drifted over time — say, after a model version upgrade or a knowledge-base update?**

<details>
<summary>Show answer</summary>

*Model answer:* Maintain a versioned golden dataset with expected outputs (or expected score ranges). Run the full eval suite against every new deployment and compare aggregate metrics (mean faithfulness, pass-rate, semantic similarity scores) to the baseline stored in `results/`. A drop of more than a defined threshold (e.g., faithfulness < 0.85) triggers a CI gate failure. For model upgrades specifically, also run pairwise LLM-as-judge comparisons (old vs. new) on a representative sample.

*What strong understanding looks like:* You can describe what a regression dashboard for your capstone would look like and what threshold would trigger a human review.

</details>

---

**Q3. How did you measure red-team (adversarial) coverage in your test suite? What gaps remain?**

<details>
<summary>Show answer</summary>

*Model answer:* Coverage is measured by category — prompt injection attempts, off-topic jailbreaks, data-poisoning probes, persona-override attacks, and confidentiality extraction attempts each count as a distinct category. A coverage matrix lists each attack category and whether at least one test exercises it. Gaps are categories with zero tests. Common remaining gaps: multi-turn jailbreaks (most eval harnesses test single turns), indirect prompt injection via retrieved documents, and low-resource language attacks.

*What strong understanding looks like:* You have an explicit coverage matrix, not just a count of "I have 5 red-team tests."

</details>

---

**Q4. What are the trade-offs of using a large, powerful model as your LLM judge versus a smaller, faster, cheaper one?**

<details>
<summary>Show answer</summary>

*Model answer:* Larger judges (e.g., claude-opus-class) are more accurate at nuanced rubric evaluation, show lower leniency bias, and handle long-context comparisons better. But they cost more per call, add latency to CI runs, and have higher rate-limit exposure. Smaller judges are faster and cheaper — suitable for high-volume regression runs where each call tests a simple criterion. Best practice: use a small judge for deterministic bulk regression (schema compliance, keyword presence) and reserve large judges for open-ended quality dimensions (groundedness, coherence) run on a sample, not every output.

*What strong understanding looks like:* You can point to a specific place in your suite where you made this trade-off consciously and explain why.

</details>

---

**Q5. If your golden dataset was built primarily from outputs of the same model you are now testing, what bias might that introduce?**

<details>
<summary>Show answer</summary>

*Model answer:* The golden set inherits the model's own failure modes — if the model consistently hallucinates a particular fact, that hallucination may have been validated into the golden set. This is "reference contamination." Mitigations: (1) have a domain expert or independent data source validate golden answers before they are locked; (2) periodically regenerate golden answers from an authoritative ground truth (e.g., policy documents) rather than model outputs; (3) use retrieval-grounded references where the correct answer is verifiable from source text.

*What strong understanding looks like:* You can identify at least one case in your golden dataset where this bias could plausibly exist.

</details>

---

**Q6. How do you handle the inherent non-determinism of LLM outputs in a repeatable CI pipeline?**

<details>
<summary>Show answer</summary>

*Model answer:* Three layers: (1) **Deterministic runs** — set `temperature=0` for regression suites; most models become near-deterministic at temperature 0 for factual queries. (2) **Threshold assertions** — instead of asserting `score == 0.95`, assert `score >= 0.80`; this tolerates minor variance. (3) **Aggregation** — for any metric that is still noisy, run N trials (typically 3–5) and assert on the mean or median. Document the N and variance in the test.

*What strong understanding looks like:* You know which tests in your suite are still flaky despite these mitigations and why.

</details>

---

**Q7. What is position bias in pairwise LLM-as-judge evaluation, and how did you (or should you) mitigate it?**

<details>
<summary>Show answer</summary>

*Model answer:* Position bias is the tendency of LLM judges to prefer whichever response appears first in the prompt, independent of actual quality. It is a form of recency/primacy bias compounded by the judge's pretraining. Standard mitigation: run every pairwise comparison twice — once with output A first, once with output B first — and only accept a verdict when both orderings agree. Ties are recorded when orderings disagree. This doubles call count but makes verdicts statistically trustworthy.

*What strong understanding looks like:* You implemented this double-swap in your pairwise judge (or can explain exactly where in the code you would add it).

</details>

---

**Q8. Your eval suite passes in the development environment but you suspect it would miss bugs in production. What observability additions would strengthen coverage?**

<details>
<summary>Show answer</summary>

*Model answer:* Offline evals only cover known failure modes against a fixed dataset. Production adds: (1) **Sampling + online eval** — log a random 1–5% of live requests, run LLM-as-judge on them, alert if quality drops; (2) **User feedback signals** — thumbs-up/down, explicit corrections, or absence of follow-up ("did the answer satisfy?"); (3) **Latency and cost tracking** — P95 latency and cost-per-query regressions are measurable without ground truth; (4) **Anomaly detection on output distributions** — sudden shifts in response length, refusal rate, or format-error rate signal model or pipeline changes. Tools: Langfuse, Arize Phoenix, or a simple logging pipeline to a time-series store.

*What strong understanding looks like:* You can sketch a monitoring dashboard with at least 4 metrics and their alert thresholds.

</details>

---

**Q9. Which part of your capstone test suite are you least confident in, and what would you do with more time?**

<details>
<summary>Show answer</summary>

*(Open-ended — no single model answer)*

*What strong understanding looks like:* The answer is specific and honest. It names a concrete gap (e.g., "my red-team coverage only has 3 prompt-injection probes and no multi-turn tests") and a concrete improvement (e.g., "I would add a multi-turn adversarial harness using the PyRIT library and expand to 20+ injection variants"). Vague answers ("I would add more tests") indicate shallow self-assessment.

</details>

---

**Q10. How does your test suite encode the difference between a safety failure (the model says something harmful) and a quality failure (the model gives a correct but poorly worded answer)?**

<details>
<summary>Show answer</summary>

*Model answer:* Safety failures and quality failures need separate, non-overlapping assertion paths. Safety checks should be binary gates — PASS or FAIL, no partial credit — and their failure should block a release regardless of overall quality scores. Quality checks are graduated (scores, thresholds, trend lines) and inform improvement work without necessarily blocking a release. In code: safety assertions raise hard `AssertionError` (or `pytest.fail`) with no threshold tolerance; quality assertions compare to a configurable threshold and log warnings when near the boundary. They also run on different scopes: safety runs on every input including red-team; quality aggregates run on the golden set.

*What strong understanding looks like:* Your capstone test suite has distinct test files or test classes for safety vs. quality, and safety tests have no threshold tolerance.

</details>

---

## 4. Concept Deep-Dive Q&A — Whole-Track Consolidation (Days 1–14)

These questions consolidate the full 15-day arc. Work through them after finishing your capstone reflection.

---

**Q1. What makes an LLM system fundamentally harder to test than a deterministic REST API, and what is the primary strategy for each added difficulty?**

<details>
<summary>Show answer</summary>

| Difficulty | Strategy |
|---|---|
| No single correct output | Semantic / rubric-based assertions instead of exact-match |
| Output varies across calls | Threshold assertions + temperature=0 for regression runs |
| Failure modes are emergent & hard to enumerate | Failure-mode taxonomy (Day 6) + structured red-teaming |
| Ground truth is expensive to obtain | LLM-as-judge for automated quality scoring (Day 9) |
| System is a pipeline, not a single function | Component-level + end-to-end evals (Days 8, 10) |

</details>

---

**Q2. Explain the RAG evaluation triad: context precision, context recall, and faithfulness. What does each measure and what bug does it catch?**

<details>
<summary>Show answer</summary>

**Context precision** — of the chunks retrieved, what fraction were actually relevant? Catches over-retrieval / noise. **Context recall** — of the chunks that were needed to answer the question, what fraction did retrieval return? Catches under-retrieval / missing information. **Faithfulness** — does the generated answer contain only claims supported by the retrieved context? Catches hallucination independent of whether retrieval was good. You need all three: a system can have perfect retrieval but still hallucinate (low faithfulness), or high faithfulness on the retrieved context but wrong context (low recall).

</details>

---

**Q3. Describe the promptfoo assertion pipeline. What is the difference between a `contains` assertion and a `llm-rubric` assertion, and when do you use each?**

<details>
<summary>Show answer</summary>

promptfoo evaluates a list of assertions against each model output. `contains` is a deterministic string check — it passes if the output includes the specified substring. Fast, free, no API call needed. `llm-rubric` sends the output plus a rubric description to a judge model and passes if the judge scores it as passing. Slow, costs tokens, but can evaluate quality criteria that cannot be expressed as string patterns. Use `contains` for structured outputs, required keywords, format compliance. Use `llm-rubric` for nuanced quality dimensions (e.g., "the answer is empathetic and professional").

</details>

---

**Q4. What is the RAGAS framework and what gap does it fill compared to a handwritten eval harness?**

<details>
<summary>Show answer</summary>

RAGAS (Retrieval-Augmented Generation Assessment) is an open-source framework providing ready-made metrics for RAG pipelines: faithfulness, answer relevancy, context precision, context recall, and context entity recall. The gap it fills: implementing these metrics correctly from scratch requires careful prompt engineering (for the judge-based metrics) and handling edge cases (empty retrievals, multi-chunk contexts). RAGAS provides battle-tested implementations with calibrated prompts. The trade-off: it calls an LLM internally for the judge-based metrics, adding cost and latency, and metric definitions are fixed — you lose the flexibility of a custom harness.

</details>

---

**Q5. What is a "golden dataset" and what properties make one high quality?**

<details>
<summary>Show answer</summary>

A golden dataset is a curated set of (input, expected-output or expected-score) pairs used as the ground truth for regression and quality evaluation. High-quality properties: (1) **Representative** — covers the distribution of real user inputs, not just easy cases; (2) **Diverse** — includes edge cases, ambiguous queries, boundary inputs; (3) **Verified** — answers validated by domain experts or authoritative sources, not model-generated; (4) **Versioned** — stored in version control so changes are tracked; (5) **Sized appropriately** — large enough for statistical significance on aggregate metrics (typically ≥ 50 cases for a meaningful pass-rate signal).

</details>

---

**Q6. Explain four LLM judge biases and their mitigations.**

<details>
<summary>Show answer</summary>

| Bias | Description | Mitigation |
|---|---|---|
| Position / order bias | Judge prefers whichever output appears first | Run both orderings; only accept agreement |
| Verbosity bias | Judge prefers longer, more detailed outputs regardless of quality | Include length-neutral rubric anchors; penalize verbosity in rubric |
| Self-preference bias | A model judging its own outputs rates them higher | Use a different model family as judge |
| Leniency bias | Judge gives inflated scores to avoid harsh verdicts | Use reference-based grading; include negative examples in rubric |

</details>

---

**Q7. What is prompt injection and how does it differ from a jailbreak? How do you test for each?**

<details>
<summary>Show answer</summary>

A **jailbreak** is a direct user attack — crafting a prompt to make the model ignore its system prompt and produce disallowed content. The attacker is the user. A **prompt injection** is an indirect attack — malicious instructions embedded in data the model processes (a retrieved document, a tool result, a web page) that override system-level instructions without the user's knowledge. Testing jailbreaks: add adversarial user messages to a red-team dataset and assert safety failures are blocked. Testing prompt injection: embed adversarial instructions in retrieved chunks or tool responses and assert the model does not follow them (the output should address the user's question, not the injected instruction).

</details>

---

**Q8. When should you use deepeval's `pytest` integration versus a standalone `promptfoo` YAML configuration?**

<details>
<summary>Show answer</summary>

Use **deepeval + pytest** when you want programmatic control — dynamic test generation, complex fixture setup, integration with existing Python test infrastructure, custom metric classes, or conditional assertion logic. It is the right choice for CI pipelines already using pytest. Use **promptfoo YAML** when you want declarative, human-readable test definitions that non-engineers can review and edit; for rapid iteration on prompt variants (A/B testing across multiple providers); or when your assertion logic maps cleanly to built-in assertion types. The two are not mutually exclusive — some teams use promptfoo for prompt A/B comparisons and deepeval for regression gating.

</details>

---

**Q9. Describe the agent evaluation challenge that standard RAG evals do not address. What additional checks are needed?**

<details>
<summary>Show answer</summary>

Standard RAG evals check retrieval quality and output faithfulness — they assume a fixed pipeline where the LLM generates one response. Agents differ: they take sequences of actions (tool calls), and the quality of the final answer depends on the entire trajectory. Additional checks needed: (1) **Tool-call correctness** — did the agent call the right tools with correct parameters? (2) **Trajectory efficiency** — did it reach the goal in a reasonable number of steps (no infinite loops, no unnecessary calls)? (3) **Error recovery** — when a tool returns an error, does the agent handle it gracefully or hallucinate a result? (4) **Goal completion** — was the final user goal actually satisfied, regardless of the intermediate path?

</details>

---

**Q10. Explain the difference between offline evaluation and online monitoring. Why do you need both?**

<details>
<summary>Show answer</summary>

**Offline evaluation** runs against a fixed, pre-collected dataset before deployment. It catches known failure modes, enables controlled regression testing, and is reproducible. But it only covers scenarios you thought to include. **Online monitoring** samples live production traffic, applies automated quality checks (LLM-as-judge, format validators, latency tracking), and aggregates signals over real user behavior. It catches unknown failure modes that emerge in production (unexpected query distributions, new edge cases, model-version drift). You need both because offline eval gives you a controlled quality gate pre-release, and online monitoring gives you continuous visibility into post-release quality degradation.

</details>

---

## 5. Common Pitfalls & Best Practices

### Pitfalls to Avoid

**1. Exact-match assertions on open-ended outputs**
The test always passes when the model gives the expected wording and always fails on valid paraphrases. Use semantic similarity or LLM-as-judge for any output where multiple phrasings are correct.

**2. Checking only the happy path**
A suite that only tests well-formed queries on clean data misses the majority of production failure modes. Build adversarial, boundary, and edge-case inputs from day one.

**3. Golden dataset built entirely from model outputs**
A model's own outputs inherit its biases and hallucinations. Anchor your golden set in authoritative source documents or human-verified answers.

**4. Treating LLM-as-judge scores as ground truth**
Judge scores are estimates, not facts. They have biases (leniency, verbosity, position). Always calibrate your judge against human annotations before trusting scores for release gates.

**5. No temperature control in regression tests**
Running regression tests at high temperature means the same input can pass one run and fail the next. Set `temperature=0` for all deterministic regression suites.

**6. Single-score pass/fail with no diagnostic breakdown**
An overall score of 3.2/5 tells you the system has a problem. Scores broken out by criterion (groundedness: 4.8, completeness: 2.1, safety: 5.0) tell you what to fix.

**7. Hardcoded API keys in test files**
Any eval that calls an LLM needs a key. Store it in environment variables or `.env` files excluded from version control. A hardcoded key is a security incident waiting to happen.

**8. No versioning of eval results**
Without a stored baseline, you cannot detect regressions. Commit `results/` snapshots and diff them between releases.

**9. Red-teaming only with obvious attacks**
Simple jailbreaks ("ignore previous instructions") are now well-defended. Effective red-teaming uses multi-turn attacks, indirect injection, semantic paraphrases of disallowed requests, and low-resource language inputs.

**10. Skipping component-level tests and only testing end-to-end**
End-to-end test failures are hard to debug when the pipeline has 4+ components. Component-level tests (retrieval precision in isolation, LLM faithfulness in isolation) pinpoint failures faster.

### Best Practices Summary

- Layer your assertions: fast deterministic checks first, expensive LLM-as-judge second.
- Build a coverage matrix mapping test cases to failure-mode categories.
- Separate safety assertions (hard gates, no tolerance) from quality assertions (thresholds, trends).
- Run eval suites in CI on every PR that touches prompts, pipeline code, or knowledge-base data.
- Set a quality threshold you are willing to defend, document it, and hold to it.
- Budget for ongoing eval work: golden datasets decay as the world changes.

---

## 6. Continued Learning Roadmap

### Immediate Next Steps (0–4 weeks)

- **Solidify deepeval and promptfoo** — work through their full documentation and add their advanced metric classes to your capstone.
- **Implement online monitoring** — add Langfuse or Arize Phoenix logging to a sample project and observe real-traffic quality metrics.
- **Expand your red-team vocabulary** — read OWASP Top 10 for LLM Applications (2025 edition); implement at least 3 categories not covered in the course.

### Short-Term Learning (1–3 months)

| Area | Resource / Action |
|---|---|
| Evaluation frameworks | `github.com/confident-ai/deepeval` — full docs + community eval recipes |
| Red-teaming at scale | Microsoft PyRIT library; Garak adversarial probing framework |
| RAG quality at depth | RAGAS documentation; "ARES: An Automated Evaluation Framework for RAG" (paper) |
| Observability | Langfuse open-source; Arize Phoenix; OpenTelemetry for LLM traces |
| Standards | NIST AI RMF (AI Risk Management Framework) — maps directly to eval categories |
| Agent evaluation | Inspect AI (UK AISI) — open-source agent eval framework |

### Medium-Term Skill Building (3–6 months)

- **AI-assisted test generation** — use LLMs to generate adversarial test cases, golden-set candidates, and edge-case seeds, then human-verify them.
- **Continuous eval pipelines** — build a full CI/CD eval pipeline with quality gates, trend dashboards, and automated rollback triggers.
- **Human-in-the-loop annotation** — learn Label Studio or Argilla for systematic human annotation workflows that feed golden datasets.
- **Benchmark participation** — run your system on public benchmarks (MMLU, HellaSwag, BIG-Bench) to calibrate your private evals against community standards.

### Key Papers & References

- "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" — Zheng et al. (foundational LLM-as-judge research)
- "RAGAS: Automated Evaluation of Retrieval Augmented Generation" — Es et al.
- "Constitutional AI: Harmlessness from AI Feedback" — Anthropic (red-teaming approach)
- "Sparks of Artificial General Intelligence" — contains useful failure-mode taxonomy
- OWASP LLM Top 10 (2025) — `owasp.org/www-project-top-10-for-large-language-model-applications/`

---

## 7. Key Takeaways

1. **LLM QA is a discipline, not a checklist.** The techniques in this course — failure taxonomies, golden datasets, LLM-as-judge, red-teaming, RAGAS metrics — are a toolkit. Applying them well requires judgment about which tool fits each situation.

2. **Assertions must match the nature of the output.** Deterministic outputs get deterministic checks; open-ended outputs get semantic or rubric-based evaluation. Mismatching creates tests that are either brittle or blind.

3. **Safety and quality are separate concerns with separate gates.** Safety failures block releases unconditionally. Quality failures inform improvement work and trigger review when they cross thresholds.

4. **Eval is not a one-time activity.** Models change, knowledge bases change, user behavior changes. A QA system that runs once at launch and never again is not a QA system — it is a snapshot.

5. **Red-teaming is a creative discipline.** Effective adversarial testing requires thinking like an attacker — anticipating misuse, not just probing known attack patterns. It improves continuously as you learn new attack vectors.

6. **LLM judges have biases.** They are useful tools, not oracles. Calibrate them, mitigate their known biases, and layer them with deterministic checks rather than relying on them alone.

7. **The goal is production confidence, not test-suite size.** A suite of 10 well-designed, well-maintained tests covering the real failure-mode surface is more valuable than 200 tests that only exercise the happy path.

8. **QA engineers own LLM evaluation.** This is not solely an ML research function. The skills you built in this course — test design, automation, assertion strategy, CI integration — are core QA skills applied to a new class of systems.

---

*Congratulations on completing the QA Engineering with AI track. The capstone in `capstone/qa/` is your artifact — a working, documented eval system you can extend, reference, and build on throughout your career.*
