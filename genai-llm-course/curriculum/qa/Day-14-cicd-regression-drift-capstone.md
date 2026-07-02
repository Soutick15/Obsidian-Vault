# Day 14 — CI/CD for LLM Evals, Regression Testing, Production Drift, and Capstone Introduction

**Track:** QA | **Week:** 3 | **Prerequisites:** Days 6–13 (eval harnesses, LLM-as-judge, RAG evals, metrics, adversarial testing)

---

## 1. Objectives

By the end of this day you will be able to:

- Explain why CI/CD pipelines are the right home for LLM quality gates and how to implement the **eval-gate pattern**.
- Design a two-stage CI pipeline that separates fast offline checks from slower online LLM-judge checks.
- Write a **GitHub Actions workflow** (`llm-eval.yml`) that runs eval harnesses and fails the build on score regression.
- Implement **snapshot baseline regression testing** with threshold tolerances rather than exact-match comparisons.
- Distinguish **input drift** from **output-quality drift** and describe detection strategies for each.
- Describe how **Langfuse** maps to eval concepts (traces, spans, scores, datasets) for production monitoring.
- Explain the end-to-end **QA lifecycle** for LLM features and articulate where Days 6–14 skills fit within it.
- Orient yourself to the **QA Capstone project** (`capstone/qa/project-brief.md`) and plan your Day 14–15 work.

---

## 2. Concept Reading

### 2.1 Putting LLM Evaluations into CI/CD

#### Why CI Is Where Quality Lives

In traditional software engineering, the continuous integration pipeline is where quality gates live. Unit tests, integration tests, linters, and type checkers all run on every push — not because engineers distrust each other, but because automated gates catch regressions before they accumulate. The same logic applies to LLM systems. An eval score that only gets checked manually, occasionally, and informally is not a quality gate: it is a suggestion.

**Continuous integration for LLM systems** treats eval harnesses as first-class citizens of the build pipeline. Every pull request that touches a prompt, a retrieval configuration, a chunking strategy, or a model version runs the eval suite before it can merge. This transforms LLM quality from a periodic manual activity into a systematic, auditable, version-controlled process.

#### The Eval-Gate Pattern

The **eval-gate pattern** has three steps:

1. Run the eval harness against the SUT (with the proposed change applied).
2. Compute a scalar summary score (faithfulness mean, pass rate, ROUGE-L average, or a composite).
3. Exit with a non-zero exit code if the score falls below the configured threshold.

Step 3 is what makes this a gate rather than a report. CI systems (GitHub Actions, GitLab CI, Jenkins, CircleCI) interpret a non-zero exit code as a build failure. The job turns red. The pull request cannot merge if branch protection rules require the job to pass.

A minimal Python gate script looks like this:

```python
# eval_gate.py
import sys
import json

THRESHOLD = 0.82          # minimum acceptable mean faithfulness
REPORT_PATH = "reports/eval_results.json"

with open(REPORT_PATH) as f:
    results = json.load(f)

mean_faithfulness = results["metrics"]["faithfulness"]["mean"]
print(f"Mean faithfulness: {mean_faithfulness:.4f} (threshold: {THRESHOLD})")

if mean_faithfulness < THRESHOLD:
    print("FAIL: score is below threshold — blocking merge")
    sys.exit(1)

print("PASS: score meets threshold")
sys.exit(0)
```

The script is self-contained and testable. It does not require an API key. It reads a JSON report that the eval harness writes to disk.

#### Two-Stage CI: Fast Gate Then Slow Gate

Running an LLM-judge-based eval on every pull request is expensive in tokens and time. The practical solution is a **two-stage pipeline**:

| Stage | What runs | Trigger | Duration | Cost |
|---|---|---|---|---|
| **Fast offline gate** | Deterministic metrics (exact match, ROUGE, keyword checks, schema validation) | Every PR push | Seconds to milliseconds | Zero (no API calls) |
| **Slow online gate** | LLM-as-judge scoring (faithfulness, coherence, answer relevancy) | On merge to `main`, nightly, or manual trigger | Minutes | Token costs |

The fast gate catches the most obvious regressions immediately, on every commit, with no cost. The slow gate provides higher-signal quality assessment at lower frequency. Together they balance speed, cost, and coverage.

**When to trigger each stage:**

- **Fast gate** — on every push to a pull request branch. Should complete in under 60 seconds.
- **Slow gate** — on merge to `main` (or `staging`), and on a nightly schedule for drift detection.
- **Full eval suite** — before major releases, when the model version changes, or when the eval dataset is updated.

#### Example GitHub Actions Workflow Structure

```yaml
# .github/workflows/llm-eval.yml (structure only — see Section 2.3 for annotated version)
name: LLM Eval Gate

on:
  pull_request:
    branches: [main, staging]
  push:
    branches: [main]

jobs:
  fast-offline-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install pytest
      - run: python eval_gate_offline.py --report reports/offline_results.json
      - run: python eval_gate.py --report reports/offline_results.json

  slow-online-gate:
    runs-on: ubuntu-latest
    needs: fast-offline-gate      # only runs if fast gate passes
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install pytest deepeval
      - run: python eval_gate_online.py --report reports/online_results.json
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

---

### 2.2 Regression Testing with Baselines and Thresholds

#### The Snapshot Baseline Approach

A **baseline** is a historical eval score captured at a known-good point — typically when a feature is first considered production-ready. The baseline is saved to a version-controlled JSON file:

```json
{
  "version": "2024-11-15",
  "commit": "a3f9c21",
  "metrics": {
    "faithfulness": { "mean": 0.89, "p10": 0.74 },
    "answer_relevancy": { "mean": 0.83, "p10": 0.68 },
    "pass_rate": 0.91
  }
}
```

Future CI runs load this file, compute the current scores, and compare them. This is **snapshot regression testing**: the SUT's current behavior is compared against a frozen historical snapshot.

#### Threshold-Based Comparison (Not Exact Match)

Exact-match comparison against baselines is too brittle for LLM systems. LLM-as-judge scores have inherent variance — the same pipeline on the same test cases can produce slightly different scores on each run due to model temperature, batching order, or minor infrastructure differences. Requiring an exact match would produce constant false failures.

Instead, use **threshold-based comparison** with a tolerance multiplier:

```python
# regression_check.py
import json, sys

TOLERANCE = 0.05          # allow up to 5 percentage points of degradation
BASELINE_PATH = "baselines/qa_baseline.json"
CURRENT_PATH = "reports/eval_results.json"

with open(BASELINE_PATH) as f:
    baseline = json.load(f)
with open(CURRENT_PATH) as f:
    current = json.load(f)

failures = []
for metric, base_val in baseline["metrics"].items():
    cur_val = current["metrics"].get(metric)
    if cur_val is None:
        failures.append(f"Missing metric: {metric}")
        continue
    floor = base_val * (1 - TOLERANCE)
    if cur_val < floor:
        delta = base_val - cur_val
        failures.append(
            f"{metric}: dropped {delta:.4f} "
            f"(baseline={base_val:.4f}, current={cur_val:.4f}, floor={floor:.4f})"
        )

if failures:
    print("REGRESSION DETECTED:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("No regression detected.")
sys.exit(0)
```

A common practice is to set TOLERANCE at 0.05 (5%) for faithfulness-class metrics and 0.10 (10%) for higher-variance metrics like answer relevancy. These values should be calibrated against the observed run-to-run variance of your eval suite.

#### Regression Delta Over Absolute Value

The **regression delta** — how far a score has dropped from the baseline — matters more than the absolute value. A faithfulness score of 0.78 might be acceptable if your baseline was 0.80 (delta = 0.02), but alarming if your baseline was 0.92 (delta = 0.14). Framing gates in terms of delta rather than absolute thresholds makes the gate resilient to differences between eval datasets while remaining sensitive to genuine degradations.

#### Updating Baselines Intentionally

Baselines must not update automatically. Automatic updates allow regressions to silently "lock in" as new baselines, defeating the entire purpose of the gate. Instead:

1. A human explicitly runs `python update_baseline.py --approve` after verifying the new scores represent a genuine improvement or an intentional quality trade-off.
2. The updated baseline JSON is committed to version control with a commit message explaining why the baseline changed: `chore: update eval baseline after switching to text-embedding-3-large`.
3. The pull request updating the baseline requires review from at least one other team member.

This creates an **audit trail**: every baseline change is tied to a commit, a timestamp, and a human decision.

---

### 2.3 Running Evals in GitHub Actions

The following is a complete, annotated GitHub Actions workflow for an LLM eval gate. It assumes the SUT is the mock RAG HR assistant used throughout this course, which requires no API key for offline evaluation.

```yaml
# .github/workflows/llm-eval.yml
name: LLM Eval Gate

on:
  pull_request:
    branches: [main, staging]
    paths:
      # Only run when relevant files change — avoids running on doc-only PRs
      - "src/**"
      - "prompts/**"
      - "eval/**"
      - "baselines/**"
  push:
    branches: [main]
  schedule:
    # Nightly run for drift detection (slow online gate)
    - cron: "0 2 * * *"

jobs:
  # ── Stage 1: Fast offline gate ─────────────────────────────────────────────
  fast-offline-gate:
    name: Fast Offline Eval Gate
    runs-on: ubuntu-latest

    steps:
      # Step 1: Checkout the repository at the PR's HEAD commit
      - name: Checkout code
        uses: actions/checkout@v4

      # Step 2: Set up Python
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      # Step 3: Cache pip dependencies to speed up subsequent runs
      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      # Step 4: Install dependencies (stdlib + pytest only for offline gate)
      - name: Install dependencies
        run: pip install -r requirements.txt

      # Step 5: Run the eval harness — writes results to reports/offline_results.json
      - name: Run offline eval harness
        run: |
          python -m pytest eval/offline/ \
            --tb=short \
            --json-report \
            --json-report-file=reports/offline_results.json

      # Step 6: Run the gate script — exits non-zero if score is below threshold
      - name: Check eval gate
        run: python eval/eval_gate.py --report reports/offline_results.json

      # Step 7: Check for regression against the saved baseline
      - name: Regression check against baseline
        run: python eval/regression_check.py \
               --baseline baselines/qa_baseline.json \
               --current reports/offline_results.json

      # Step 8: Upload the eval report as a CI artifact (retained for 30 days)
      - name: Upload eval report artifact
        if: always()    # upload even if the gate fails, so you can inspect results
        uses: actions/upload-artifact@v4
        with:
          name: offline-eval-report-${{ github.sha }}
          path: reports/offline_results.json
          retention-days: 30

  # ── Stage 2: Slow online gate (LLM-judge) ──────────────────────────────────
  slow-online-gate:
    name: Slow Online Eval Gate (LLM Judge)
    runs-on: ubuntu-latest
    needs: fast-offline-gate        # Only runs after fast gate passes
    # Only run on merge to main or on the nightly schedule
    if: |
      (github.event_name == 'push' && github.ref == 'refs/heads/main') ||
      github.event_name == 'schedule'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-online-${{ hashFiles('requirements-online.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-online-

      - name: Install online eval dependencies
        run: pip install -r requirements-online.txt    # includes deepeval, ragas, etc.

      - name: Run online eval harness
        run: python eval/run_online_eval.py --output reports/online_results.json
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Check online eval gate
        run: python eval/eval_gate.py \
               --report reports/online_results.json \
               --config eval/thresholds_online.json

      - name: Upload online eval report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: online-eval-report-${{ github.sha }}
          path: reports/online_results.json
          retention-days: 30
```

#### Branch Protection Configuration

In your GitHub repository settings, add a branch protection rule for `main` that requires the `fast-offline-gate` job to pass before merging. This ensures no pull request can merge without the offline eval gate passing.

Navigate to: **Settings → Branches → Branch protection rules → Add rule** and enable:
- "Require status checks to pass before merging"
- Add `fast-offline-gate` to the required checks list

The slow online gate is informational on PRs (not required for merge) but required for the nightly health check. If the nightly run fails, your on-call channel should receive an alert.

#### Caching and Artifact Notes

- **Pip caching**: The `actions/cache` step hashes `requirements.txt`. When dependencies change, the cache key changes and pip reinstalls from scratch. Otherwise the cache hit saves 30–90 seconds per run.
- **Artifacts**: Uploading the eval report with `if: always()` means you can inspect the failing report even when the gate step exits non-zero. Without this, CI artifacts are only uploaded on success.
- **Artifact naming**: Including `${{ github.sha }}` in the artifact name makes it easy to correlate a report with the exact commit it was generated from.

---

### 2.4 Production Monitoring and Drift Detection

Passing the CI eval gate is a necessary condition for shipping a change. It is not a sufficient condition for production quality. The eval dataset is a finite sample; production queries are an infinite, evolving distribution. **Production monitoring** is what catches quality problems that the static eval dataset does not cover.

#### Two Types of Drift

**Input drift** occurs when the distribution of user queries shifts away from the distribution you designed your eval dataset to cover. Examples:

- A new HR policy is announced and users suddenly flood the system with questions about it — questions that were never in the golden set.
- Users in a new country start using the system, asking questions in different phrasing or about locale-specific policies.
- Seasonal events (open enrollment, performance review cycles) shift query topics dramatically.

**Output-quality drift** occurs when the system's responses degrade over time, even if the input distribution is stable. Examples:

- A dependency (embedding model API, vector database version) changes upstream.
- The underlying LLM is updated by the provider without notice.
- Prompt drift: small ad-hoc prompt changes accumulate and interact in unexpected ways.
- Knowledge base staleness: retrieved documents are outdated, causing the LLM to hallucinate or contradict current policy.

Input drift and output-quality drift are distinct problems requiring different detection strategies. Input drift is detected by observing the query stream. Output-quality drift is detected by observing the response quality metrics.

#### Detecting Input Drift

Compare the distribution of incoming queries against a **baseline window** (e.g., the first 30 days of production traffic after launch). Useful signals:

- **Token length distribution**: Are queries getting longer (more complex) or shorter (simpler)? A mean shift in token count suggests a population change.
- **Topic cluster distribution**: Embed incoming queries and cluster them. If the proportion of queries in each cluster shifts significantly, topic distribution has changed.
- **Keyword frequency**: Track the frequency of key policy terms. A spike in "parental leave" queries might not be a problem, but it might mean your golden set needs new coverage.
- **Out-of-distribution queries**: If a new embedding cluster appears that does not overlap with any cluster in your eval dataset, you have uncovered a coverage gap.

A practical starting point is to use a sliding window (last 7 days of production queries) and compare it against the baseline window using a statistical test. For token length, a two-sample Kolmogorov-Smirnov test works well. For topic proportions, a chi-squared test is straightforward.

#### Detecting Output-Quality Drift

Track **rolling metric averages** over time windows. For each metric (faithfulness, answer relevancy, pass rate on known test cases), compute:

- The 7-day rolling mean
- The 7-day rolling standard deviation
- A comparison against the baseline mean

Alert when the rolling mean drops below a configured threshold for a configured number of consecutive windows. This **sustained threshold breach** logic avoids alerting on single-day noise while catching genuine degradation.

```
Example alert rule:
  metric: faithfulness_rolling_7d_mean
  condition: value < 0.80 for 3 consecutive daily windows
  action: page on-call, open incident ticket
```

A complementary approach is **shadow evaluation**: on a sample of production queries (e.g., 5%), run the LLM-as-judge scorer asynchronously after the response is returned to the user. This gives you a continuous stream of real-world quality scores without affecting latency.

#### The Role of Observability Platforms: Langfuse

**Langfuse** is an open-source observability platform purpose-built for LLM applications. It provides structured tracing, scoring, and dataset management that maps directly onto the eval concepts from this course.

Key Langfuse concepts and their eval equivalents:

| Langfuse concept | Eval equivalent | Description |
|---|---|---|
| **Trace** | Test run / conversation | A complete user interaction from first query to final response. Contains all spans within it. |
| **Span** | Step / operation | A single step within a trace (e.g., the retrieval call, the LLM generation call). Has latency and input/output logged. |
| **Score** | Eval metric value | A numeric or categorical quality signal attached to a trace or span. Can come from human raters, automated eval scripts, or LLM judges. |
| **Dataset** | Golden set / eval dataset | A curated collection of input/expected-output pairs stored in Langfuse for reproducible evals. |
| **Dataset run** | Eval harness execution | Running an eval harness against a dataset and recording the resulting scores. |

Langfuse integrates with your application via an SDK. You instrument your RAG pipeline to emit traces automatically:

```python
# Langfuse integration (conceptual — not required for offline labs)
from langfuse import Langfuse

langfuse = Langfuse()

def handle_query(user_query: str) -> str:
    trace = langfuse.trace(name="hr-assistant-query", input=user_query)

    retrieval_span = trace.span(name="retrieval")
    retrieved_docs = retrieve(user_query)
    retrieval_span.end(output={"num_docs": len(retrieved_docs)})

    generation_span = trace.span(name="generation")
    response = generate(user_query, retrieved_docs)
    generation_span.end(output=response)

    # Attach an automated faithfulness score
    trace.score(name="faithfulness", value=compute_faithfulness(response, retrieved_docs))
    trace.update(output=response)

    return response
```

Over time, the Langfuse dashboard shows score trends, latency trends, and the ability to drill into any individual trace. When a quality regression is suspected, you can filter traces from the degraded time window, inspect individual examples, and often identify the root cause.

#### Alerting

Alerting closes the feedback loop. Without alerts, drift can go undetected for weeks. A practical alerting strategy:

- **Threshold alerts**: Fire when a rolling metric drops below a fixed floor (e.g., faithfulness 7d mean < 0.78).
- **Trend alerts**: Fire when the metric has declined for N consecutive windows, even if it has not crossed the absolute floor yet.
- **Anomaly alerts**: Fire when a day's score is more than 2–3 standard deviations below the rolling baseline (useful for catching sudden model changes).
- **Coverage alerts**: Fire when the proportion of queries outside known topic clusters exceeds a threshold (input drift detection).

Route alerts to your team's incident channel and tie them to runbooks that describe investigation steps.

---

### 2.5 The QA Lifecycle for LLM Features

The skills from Days 6–14 fit together into a repeatable **end-to-end QA lifecycle**. Understanding the full cycle helps you see not just what to do at each stage, but why each stage exists and what it depends on.

```
Requirements
     │
     ▼
Golden set design
(Days 6–7: what to test, how to handle non-determinism)
     │
     ▼
Offline eval gate construction
(Days 8–10: harnesses, LLM-as-judge, RAG metrics)
     │
     ▼
PR eval gate (CI)
(Day 14: GitHub Actions, fast offline gate)
     │
     ▼
Merge to staging
     │
     ▼
Staging eval + slow online gate
(Day 14: LLM-judge gate post-merge)
     │
     ▼
Production deployment
     │
     ▼
Production monitoring + drift detection
(Day 14: Langfuse, rolling metrics, alerting)
     │
     ▼
Drift alert / quality incident
     │
     ├──► Root cause: input drift → expand golden set
     │                              (back to golden set design)
     │
     └──► Root cause: output-quality regression → investigate SUT change
                                                   fix → PR → gate
```

Each stage creates artifacts that feed the next. The golden set (Days 6–7) becomes the eval dataset that the harness (Days 8–10) runs against. The harness output becomes the score that the CI gate (Day 14) checks. Production monitoring signals when the golden set needs to grow.

#### Ownership Model

In a team with dedicated QA engineers:

- **QA engineers own**: the eval datasets (golden sets), the gate configuration (thresholds), the alerting rules, and the monitoring dashboards. These are the quality contracts.
- **Developers own**: the SUT implementation. They run the gates locally before pushing.
- **Both own**: the baseline files — updating a baseline requires joint sign-off.

This ownership model ensures quality decisions are made deliberately rather than incidentally.

---

### 2.6 Introducing the QA Capstone

The **QA Capstone project** is the culminating assessment of this track. It is introduced on Day 14 and completed on Day 15.

The project brief is located at: `capstone/qa/project-brief.md`

#### What You Will Build

You will design and implement a **comprehensive automated test and evaluation suite** for the Acme HR Assistant — the same mock RAG system you have been working with throughout the course. The capstone requires you to integrate skills from all nine days of the QA track:

| Capstone component | Source days |
|---|---|
| Test plan and golden set | Days 6–7 |
| Offline eval harness (pytest) | Days 8–9 |
| RAG-specific metrics | Day 10 |
| Adversarial and edge-case tests | Days 11–13 |
| CI eval gate (GitHub Actions YAML + gate script) | Day 14 |
| Baseline file + regression check | Day 14 |
| Production monitoring plan | Day 14 |

#### Suggested Approach and Timeline

**Day 14 (today) — Foundation work:**
1. Read the project brief (`capstone/qa/project-brief.md`) completely before starting.
2. Design your golden set: what queries will you include, and why? Document your decisions.
3. Build and run your offline eval harness. Verify it produces a JSON report.
4. Write the eval gate script and verify it exits non-zero on a simulated regression.
5. Write the `llm-eval.yml` workflow file (it does not need to run in an actual GitHub repo — the YAML itself is the deliverable).

**Day 15 (tomorrow) — Integration and presentation:**
1. Implement the baseline file and regression check script.
2. Write the production monitoring plan (a structured document, not a running system).
3. Assemble all components into the directory structure specified in the project brief.
4. Write a brief reflective summary of design decisions made.

The capstone is intentionally open-ended. The project brief specifies what to build; how you build it, and the tradeoffs you navigate, reflect your understanding of the material.

---

## 3. Lab Overview

**Lab directory:** `labs/qa/day-14/`

The Day 14 lab has three exercises, each building on the previous. No API key is required. All exercises use the mock Acme HR RAG assistant and stdlib/pytest only.

| Exercise | File | What you build |
|---|---|---|
| **Exercise 1: Eval Gate Script** | `labs/qa/day-14/exercise_01_eval_gate.py` | A gate script that reads a JSON eval report and exits non-zero on failure |
| **Exercise 2: Regression Check** | `labs/qa/day-14/exercise_02_regression_check.py` | A baseline comparison script with tolerance-based thresholding |
| **Exercise 3: GitHub Actions Workflow** | `labs/qa/day-14/exercise_03_workflow/llm-eval.yml` | A complete two-stage workflow YAML with caching, artifacts, and branch gates |

Each exercise directory contains a `README.md` with step-by-step instructions, a `fixtures/` folder with sample JSON reports and baselines, and a `solutions/` folder (consult only after attempting the exercise).

Run the exercises from the repo root:

```bash
cd labs/qa/day-14
python exercise_01_eval_gate.py --report fixtures/sample_results.json
python exercise_02_regression_check.py \
    --baseline fixtures/baseline.json \
    --current fixtures/sample_results.json
```

---

## 4. Self-Check Quiz

Test your understanding before moving to the Deep-Dive Q&A. Write your answers before checking.

---

**Q1. An eval gate script runs successfully and writes a quality report to disk, but the faithfulness score is 0.71, below the configured threshold of 0.80. What should the script do, and why does it matter for CI?**

<details>
<summary>Show answer</summary>

The script should exit with a non-zero exit code (e.g., `sys.exit(1)`). CI systems (including GitHub Actions) interpret any non-zero exit code as a job failure. This causes the job to turn red, the pull request status check to fail, and — if branch protection is configured — the pull request to be blocked from merging. Simply logging a warning and exiting with 0 would allow the regression to merge silently.

</details>

---

**Q2. In a two-stage CI pipeline for LLM evals, what is the primary reason for separating the fast offline gate from the slow online gate, rather than running everything together on every pull request?**

<details>
<summary>Show answer</summary>

Cost and speed. LLM-as-judge evaluation requires API calls that cost tokens and can take minutes to complete. Running this on every push to every pull request would slow developer feedback loops and accumulate significant API costs. The fast offline gate (deterministic metrics, no API calls) provides immediate, free feedback on obvious regressions. The slow online gate runs less frequently — on merge to main or nightly — providing higher-signal quality checks where the cost is justified.

</details>

---

**Q3. You have saved a baseline eval report showing a mean faithfulness of 0.88. Your regression check script uses a tolerance of 5%. What is the minimum faithfulness score that would pass the regression check, and what formula did you use?**

<details>
<summary>Show answer</summary>

The floor is `0.88 × (1 - 0.05) = 0.88 × 0.95 = 0.836`. Any current score at or above 0.836 would pass. A score below 0.836 would trigger a regression failure. The formula is `floor = baseline_score × (1 - tolerance)`.

</details>

---

**Q4. A QA engineer notices that production query lengths have gradually increased over three months, while retrieval quality scores have remained stable. What type of drift is this, and should it trigger an alert?**

<details>
<summary>Show answer</summary>

This is **input drift** — the distribution of user queries is shifting (getting longer or more complex) compared to the baseline window. Whether it should trigger an alert depends on whether the shift threatens coverage: if production queries are drifting toward topics not covered in the golden set, the drift represents a latent quality risk even if current scores are stable. The correct response is to investigate whether the longer queries are being handled correctly and to expand the golden set to cover the new query patterns.

</details>

---

**Q5. What are the four main Langfuse concepts, and how does each map to an eval concept you used earlier in this course?**

<details>
<summary>Show answer</summary>

- **Trace** maps to a complete test case or conversation — one user interaction from input to output.
- **Span** maps to a step within a test case — e.g., the retrieval step or the generation step, with latency and inputs/outputs logged.
- **Score** maps to a metric value (e.g., faithfulness = 0.84) attached to a trace or span, whether from an automated eval or a human rater.
- **Dataset** maps to the golden set / eval dataset — curated input/expected-output pairs stored centrally and used to run reproducible evals.

</details>

---

**Q6. Place the following QA lifecycle stages in the correct order: A. PR eval gate (CI) / B. Drift alert / quality incident / C. Golden set design / D. Production monitoring / E. Staging eval / F. Requirements**

<details>
<summary>Show answer</summary>

F → C → A → E → D → B. The correct order is: Requirements → Golden set design → PR eval gate (CI) → Staging eval → Production monitoring → Drift alert / quality incident. (After a drift alert, the cycle returns to golden set design to expand coverage or to the SUT to fix a regression.)

</details>

---

## 5. Concept Deep-Dive Q&A

These questions reflect the kind of reasoning practitioners encounter when integrating LLM evals into real development workflows. Read each question, formulate your own answer, then compare to the model answer.

---

**Q1. Why exit non-zero instead of just logging a warning when the eval score drops?**

<details>
<summary>Show answer</summary>

The distinction between "log a warning" and "exit non-zero" is the distinction between an advisory and a gate. A warning informs; a gate enforces.

When a CI job exits with 0 (success), GitHub Actions marks the check as passed. If branch protection requires that check to pass before merging, a zero exit means the pull request can merge — even if the eval report sitting in the artifacts folder shows a faithfulness score of 0.60. Nobody may look at those artifacts. The regression ships.

When a CI job exits with non-zero (failure), the check is marked as failed. The pull request cannot merge (assuming branch protection is configured). A developer must actively investigate, understand the regression, and either fix the underlying issue or make a conscious decision to override the gate. The regression cannot ship passively.

This matters because the entire value of an eval gate is in preventing passive regression. Engineers are busy. If reviewing the eval report is optional — something you do when you remember to — then the gate's effectiveness is proportional to how diligent the team is on a given day. A non-zero exit makes the gate mandatory rather than optional, encoding quality standards into the process rather than relying on individual discipline.

Logging a warning has its place: you might log a warning when a metric is in a "caution zone" (slightly below the ideal but above the mandatory floor) without blocking the PR. But if the score is below the threshold that represents an unacceptable quality floor, exit non-zero. Every time.

</details>

---

**Q2. How do I set the right threshold for an eval gate — how do I avoid both false failures and false passes?**

<details>
<summary>Show answer</summary>

Setting eval gate thresholds is an empirical process, not a one-time configuration decision. There are two failure modes to balance:

- **False failures** (the gate fails on a good change): too tight a threshold triggers on normal score variance, frustrating developers and training them to ignore or override the gate.
- **False passes** (the gate passes on a bad change): too loose a threshold lets genuine regressions through, undermining trust in the deployed system.

A practical calibration process:

1. **Measure your baseline variance first.** Run the eval harness 10–20 times on an unchanged, known-good version of the SUT. Record the score distribution. The standard deviation of this distribution is the noise floor of your eval suite. Your threshold must be below `mean - 2σ` or you will have constant false failures from noise alone.

2. **Determine the minimum acceptable quality floor.** Talk to product stakeholders: what is the lowest faithfulness score at which the system is still acceptable for users? This is the absolute floor, independent of the baseline. Set this as a hard lower bound on your threshold.

3. **Use a tolerance relative to the baseline.** A threshold of `baseline × 0.95` (5% tolerance) is a common starting point. This adapts automatically when the baseline improves — if your team improves faithfulness from 0.82 to 0.91, the floor rises from 0.779 to 0.865 automatically, without a config change.

4. **Run the gate retrospectively against recent history.** Apply your threshold to the last 30 eval runs. How many false failures would it have produced? How many genuine regressions would it have caught? Adjust until the false-failure rate is acceptable (typically below 5% of non-regressing runs).

5. **Revisit after major changes.** When you update the eval dataset, the model version, or the SUT architecture, re-calibrate the threshold using fresh baseline runs. A threshold calibrated for one configuration may be wrong for another.

There is no threshold that eliminates both failure modes entirely. The goal is an informed, deliberate tradeoff — generous enough to avoid developer frustration, tight enough to catch quality regressions before they reach users.

</details>

---

**Q3. What is the difference between a regression test and a drift detection system?**

<details>
<summary>Show answer</summary>

Regression testing and drift detection are complementary but structurally different systems operating in different contexts.

A **regression test** runs against a fixed eval dataset (the golden set) in a controlled environment (CI). It answers: "does the current code produce at least as good results as the baseline on these specific test cases?" It is deterministic with respect to inputs — the test cases are the same every run. It runs before deployment. It is binary: pass or fail.

A **drift detection system** runs against the live production query stream in an operational environment. It answers: "is the quality of real user interactions trending downward, and is the distribution of real user queries shifting away from what we tested?" It is probabilistic — it works with samples, statistical tests, and rolling averages rather than exact comparisons. It runs after deployment, continuously. It produces alerts and trends rather than binary pass/fail signals.

The key differences:

| Dimension | Regression test | Drift detection |
|---|---|---|
| When it runs | Pre-deployment (CI) | Post-deployment (production) |
| Inputs | Fixed golden set | Live production queries (sampled) |
| What it detects | Score degradation vs. a snapshot | Score trends, distribution shifts over time |
| Output | Pass/fail (exit code) | Alerts, trend charts, anomaly flags |
| Cost | Runs on every PR | Runs continuously |

A system that has only regression tests but no drift detection is blind to the many failure modes that emerge after deployment: upstream model changes, knowledge base staleness, and query population shifts that the golden set never covered. A system that has only drift detection but no regression tests has no pre-deployment quality gate — regressions are discovered in production rather than in CI. A complete QA program needs both.

</details>

---

**Q4. Our CI eval gate passes but production quality has degraded — what could explain this?**

<details>
<summary>Show answer</summary>

This is one of the most common and instructive failure patterns in LLM QA. It reveals the gap between the static eval dataset and the dynamic production environment. There are several possible explanations:

**1. Golden set coverage gap.** The eval dataset does not cover the types of queries where quality has degraded. If users recently started asking about a new policy area and the golden set has no questions in that domain, the CI gate will happily pass while real users receive poor answers. The fix: monitor which production query clusters are underrepresented in the golden set and expand coverage.

**2. Upstream model or service change.** The LLM provider updated the model (a minor version bump, a safety tuning change) without a visible version change in the API response. The embedded model or reranker may have also changed. These changes affect production but not offline CI evals (which may use a pinned version or a mock). The fix: pin model versions explicitly and monitor for provider-side changes.

**3. Knowledge base staleness.** The retrieval index was not updated with new policy documents, or outdated documents were not removed. The LLM faithfully summarizes what it retrieves — but what it retrieves is now wrong. The CI gate (which uses a static fixture knowledge base) passes because the fixture is still correct. The fix: include knowledge base freshness as a monitored metric; automate index updates.

**4. Distribution shift in evaluation vs. production.** The production queries are longer, more ambiguous, or use phrasing the golden set does not reflect. The CI gate is a sample; production is the full population. The fix: use shadow evaluation to continuously score real production queries and add representative examples to the golden set.

**5. Infrastructure or configuration drift.** A deployment configuration change (context window size, temperature, system prompt encoding) was not captured in the CI test environment. The fix: ensure the CI eval environment mirrors the production configuration as closely as possible, and include configuration parameters in the diff that triggers eval runs.

When this pattern appears, investigate all five causes before assuming the eval dataset is the sole fix. Usually it is a combination.

</details>

---

**Q5. When should we update the eval baseline, and what approval process prevents gaming the gate?**

<details>
<summary>Show answer</summary>

Updating the baseline is a quality decision, not a maintenance task. The baseline is the record of what the team accepted as "good enough" at a specific point in time. Changing it without discipline allows regressions to be silently absorbed as new normals — a process sometimes called "baseline drift" or "ratchet reversal."

**Legitimate reasons to update the baseline:**

- The SUT has genuinely improved (new embedding model, better prompts, improved chunking) and the new scores reflect a real quality gain. The team wants to lock in the higher bar so that future changes cannot regress below it.
- The eval dataset was significantly revised (new questions added, outdated questions removed) and the old baseline no longer reflects the current test suite.
- An intentional product decision accepts a trade-off (e.g., slightly lower faithfulness in exchange for significantly lower latency) and this trade-off has been reviewed and approved.

**Reasons that are NOT legitimate:**

- A developer's change caused a score drop and they want to update the baseline to make the gate pass. This is the primary abuse case.
- The score has been slowly drifting down and the team "just wants to stop the noise." The correct response to this is to investigate the drift, not to lower the bar.

**A practical approval process:**

1. Baseline updates require an explicit script invocation (`python eval/update_baseline.py --reason "..."`) that forces the operator to document the reason in the commit message.
2. The updated `baselines/qa_baseline.json` is committed to version control as a separate, standalone commit (not bundled with feature code), so the change is visible in the git log.
3. The pull request updating the baseline requires review from at least one QA engineer (enforced via CODEOWNERS: `baselines/ @qa-team`).
4. The PR description must include: the before and after scores, the reason for the update, and confirmation that the new scores have been validated by running the eval suite at least twice (to rule out run-to-run variance as the explanation).

This process ensures that every baseline change is traceable, intentional, and reviewed — making it structurally difficult to game the gate without leaving an audit trail.

</details>

---

**Q6. A team argues they don't need a CI eval gate because they already have 100% unit test coverage and a manual QA sign-off step before every release. Are they right? What is the eval gate adding that those two practices cannot?**

<details>
<summary>Show answer</summary>

The team has strong traditional QA hygiene, but unit tests and manual sign-off cannot substitute for a CI eval gate in an LLM pipeline. Each mechanism covers a different failure mode:

**What unit tests cover:** Unit tests verify deterministic code paths — parsing logic, retrieval plumbing, output formatting, guardrail pattern matching. They catch bugs where the code does the wrong thing. They are entirely blind to *semantic quality*: a unit test cannot tell you whether the RAG answer is faithful to the retrieved context, relevant to the question, or meaningfully better or worse than the previous version.

**What manual sign-off covers:** A human reviewer can catch obvious quality regressions on a handful of representative queries. However, manual review does not scale to the full golden dataset (dozens to hundreds of items), cannot reliably detect subtle score trends (a 4% drop in faithfulness across the suite), and is inconsistent across reviewers and release cycles. "Looks good to me" is not a repeatable metric.

**What the CI eval gate adds:**

1. **Automatic, quantitative, every-run measurement** — the eval score is computed against the full golden set on every pull request, not just when a reviewer happens to scrutinise the output.
2. **Regression anchoring** — scores are compared to a versioned baseline, so a gradual quality decline across many PRs becomes visible as a cumulative trend, not just a one-time reviewer impression.
3. **Semantic coverage** — metrics like faithfulness, contains-check, and semantic similarity measure *what the answer says*, not just *whether the code ran correctly*.
4. **Non-human-scalable cases** — as the golden set grows to cover hundreds of query types, human sign-off becomes a bottleneck and a reliability risk (reviewer fatigue, varying thresholds across people). The eval gate scales linearly with compute, not with human bandwidth.

The eval gate is not a replacement for unit tests or human review — it is a third layer that closes the gap they leave open: the quality of the model's semantic output under the full range of golden test cases, measured consistently and automatically on every change.

</details>

---

## 6. Further Reading

| Resource | URL | Why it matters |
|---|---|---|
| GitHub Actions documentation | https://docs.github.com/en/actions | Authoritative reference for workflow syntax, triggers, caching, artifacts, and branch protection rules — everything needed to implement the CI patterns from Section 3.3. |
| Langfuse documentation | https://langfuse.com/docs | Covers traces, spans, scores, datasets, and SDK integration for production observability. Essential for implementing the monitoring strategy in Section 3.4. |
| MLflow documentation | https://mlflow.org/docs/latest/index.html | MLflow's experiment tracking and model registry concepts apply directly to managing eval baselines and tracking score history over time. Useful as an alternative to hand-rolled baseline JSON files. |
| "Evals Are All You Need" (general reference) | Search for the blog post by title | Widely cited framing of the case for treating eval harnesses as the primary engineering artifact for LLM quality — reinforces the philosophy behind the eval-gate pattern in Section 2.1. |
| DORA metrics (DevOps Research and Assessment) | https://dora.dev/ | DORA's four key metrics (deployment frequency, lead time, change failure rate, recovery time) can be adapted to LLM pipelines: eval gate failure rate, time from regression detection to fix, and baseline update frequency are direct analogs. |
| Evidently AI documentation | https://docs.evidentlyai.com/ | Specialized library for data drift detection, including statistical tests for distribution comparison. Directly applicable to the input drift detection strategies in Section 2.4. |

---

## 7. Key Takeaways

- **CI is where LLM quality gates belong.** An eval score checked manually and occasionally is not a gate. Integrating eval harnesses into CI — with non-zero exit on failure and branch protection — makes quality enforcement automatic and auditable.

- **The eval-gate pattern is simple: run harness → compute score → exit non-zero if below threshold.** The simplicity is intentional. A complex gate is a gate that breaks, gets circumvented, or cannot be explained to a developer whose PR just failed.

- **Two-stage CI balances speed and signal.** Fast offline gates (milliseconds, no API cost) run on every push. Slow online LLM-judge gates (minutes, token cost) run on merge or nightly. Use each where it is appropriate.

- **Baselines enable regression detection without requiring exact match.** Save scores to a version-controlled JSON file. Compare future runs against it with a tolerance (e.g., 5%). Never update the baseline automatically — every change requires a human decision and leaves an audit trail.

- **Input drift and output-quality drift are different problems.** Input drift is detected by comparing the production query distribution against a baseline window. Output-quality drift is detected by tracking rolling metric averages over time. A complete monitoring strategy addresses both.

- **Langfuse maps LLM observability concepts to eval concepts.** Traces, spans, scores, and datasets correspond directly to test runs, steps, metric values, and golden sets. Using an observability platform transforms production monitoring from manual inspection into structured, searchable, alertable data.

- **The QA lifecycle is a loop, not a line.** Requirements → golden set → CI gate → staging eval → production monitoring → drift alert → back to golden set. Each stage creates artifacts that feed the next, and production signals continuously inform what the golden set needs to cover next.

- **Day 15 is the capstone.** Use the remainder of today to read `capstone/qa/project-brief.md`, design your golden set, and build the offline eval harness. You will integrate the CI gate, baseline check, and monitoring plan on Day 15.
