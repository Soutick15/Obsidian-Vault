# Day 12 — Agentic & Autonomous AI Testing

**Track:** QA | **Week:** 3 | **Prerequisites:** Days 6–11 (LLM systems under test, non-determinism, eval harnesses, LLM-as-judge, RAG/agent eval, AI-assisted test generation)

---

## 1. Objectives

By the end of this day you will be able to:

- Describe what an **exploratory testing agent** is and how it differs from a scripted test suite.
- Explain the **sense → generate → execute → observe → report** loop that governs autonomous testing.
- Design **probe categories** (factual, edge, adversarial) and explain what each targets.
- Implement lightweight **oracles and invariants** that a machine can evaluate without a human in the loop.
- Recognise when autonomous testing **adds value** versus when it produces noise.
- Integrate an AI-driven test loop into **pytest**, **Playwright**, and a **CI pipeline**.
- Apply **human-in-the-loop checkpoints** to keep autonomous testing safe and purposeful.
- Evaluate the **quality of AI-generated tests** using coverage, precision, and yield metrics.

---

## 2. Concept Reading

### 2.1 What Is an Exploratory Testing Agent?

Traditional automated testing is **scripted**: a human decides which inputs to use, what the expected output is, and writes a deterministic assertion. This approach is powerful but blind to inputs the human did not think of.

An **exploratory testing agent** inverts this process. The agent itself decides what to probe, executes the probes, evaluates the responses against invariants (rather than exact expected values), and surfaces anomalies. The human reviews findings—not individual test cases.

The agent loop has five stages:

```
┌─────────────────────────────────────────────────────┐
│  1. SENSE   — understand what the SUT can do         │
│  2. GENERATE — create probe inputs                   │
│  3. EXECUTE  — call the SUT with each probe           │
│  4. OBSERVE  — evaluate the response against oracles │
│  5. REPORT   — surface anomalies and coverage gaps   │
└─────────────────────────────────────────────────────┘
```

Each pass through this loop is an **episode**. Agents can run hundreds of episodes in minutes, covering input space a human team would take days to reach manually.

---

### 2.2 Probe Categories

A well-designed agent covers three broad categories of probe:

| Category | Intent | Examples |
|---|---|---|
| **Factual** | Does the SUT return grounded, accurate information for normal inputs? | "What is the parental leave policy?" |
| **Edge** | Does the SUT degrade gracefully on unusual or boundary inputs? | Empty string, very long query, non-English text, numeric-only input |
| **Adversarial** | Can the SUT be manipulated into unsafe, biased, or policy-violating behaviour? | Prompt injection, PII extraction probes, jailbreak attempts |

Covering all three categories is the difference between a **smoke test** (factual only) and a **security-aware quality gate**.

---

### 2.3 Oracles and Invariants

A **test oracle** tells you whether an output is correct. For deterministic systems, the oracle is an exact expected value. For AI systems with variable output, oracles become **invariants**—properties that must hold for *any* valid response.

Common invariants for RAG / LLM systems:

| Invariant | Passes when | Implementation hint |
|---|---|---|
| **Has source** | `result["sources"]` is non-empty | `len(result["sources"]) > 0` |
| **Groundedness** | The answer text overlaps meaningfully with the retrieved contexts | Token-level overlap ≥ threshold |
| **No PII leak** | Response does not contain known PII tokens | Regex / allowlist check |
| **Not obviously wrong** | Answer does not directly contradict a known fact | Keyword contradiction check |
| **No injection compliance** | Response does not contain injected marker strings | `"HACKED"` not in response |

Invariants are intentionally **weak**: they pass a wide range of acceptable answers while catching clear failures. This keeps false-positive rates low, which is critical when an agent runs hundreds of probes.

---

### 2.4 Coverage-Gap Analysis

An autonomous agent can map the **input space** it has covered and flag regions it has not. For a RAG system like the HR assistant, coverage can be measured across:

- **Topic coverage**: which policy domains have been probed? (leave, benefits, code of conduct, …)
- **Probe-type coverage**: what fraction of probes were factual vs edge vs adversarial?
- **Source coverage**: which documents in the corpus were ever cited in a response?

A **coverage-gap report** answers: *what did the agent not explore that it should have?* This is as valuable as the anomaly list.

---

### 2.5 Integrating Autonomous Testing into Existing Frameworks

#### pytest

Wrap the agent loop in a pytest session:

```python
# conftest.py
import pytest
from my_agent import ExploratoryAgent

@pytest.fixture(scope="session")
def agent_report():
    agent = ExploratoryAgent(sut=answer, probe_budget=50)
    return agent.run()

def test_no_critical_anomalies(agent_report):
    critical = [a for a in agent_report.anomalies if a.severity == "critical"]
    assert len(critical) == 0, f"Critical anomalies found: {critical}"

def test_coverage_above_threshold(agent_report):
    assert agent_report.topic_coverage >= 0.7, "Fewer than 70% of topics probed"
```

The agent runs once per session; individual tests assert properties of the report.

#### Playwright (UI / end-to-end)

For front-end AI applications, the agent generates **user utterances** rather than API calls. Playwright drives the browser; the agent generates the chat inputs:

```python
for probe in agent.generate_probes():
    page.locator("#chat-input").fill(probe.text)
    page.locator("#send-btn").click()
    response_text = page.locator(".assistant-message").last.inner_text()
    agent.observe(probe, response_text)
```

This lets the agent exercise the full stack (routing, auth, UI rendering) not just the model layer.

#### CI Pipeline

Place the agent in a nightly or pre-merge job, not in the fast unit-test suite. Agentic tests are **expensive** (they call the SUT many times) and produce **probabilistic** results (anomaly counts vary with probe sampling). Treat them like integration tests:

```yaml
# .gitlab-ci.yml excerpt
exploratory-test:
  stage: integration
  script:
    - python labs/qa/day-12/solution.py --probe-budget 100
  artifacts:
    reports:
      junit: anomaly_report.xml
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

---

### 2.6 When Autonomous Testing Helps vs When It Produces Noise

| Autonomous testing **helps** | Autonomous testing **produces noise** |
|---|---|
| Discovering inputs the team did not think of | When invariants are too strict (every variation flags) |
| Regression surveillance on large input spaces | When the SUT is deterministic and fully spec'd |
| Security probing (adversarial / injection) | When probes are too similar to each other (low diversity) |
| Coverage mapping across policy domains | When no human reviews the anomaly list (alert fatigue) |
| Catching seeded / latent bugs faster than manual review | When the probe budget is too small to be meaningful |

The key failure mode is **low oracle precision**: if your invariants flag 30% of valid responses as anomalies, the agent becomes noise. Calibrate invariants on a known-good baseline before running at scale.

---

### 2.7 Human in the Loop

Autonomous testing does not eliminate human judgment—it **focuses** it. The recommended pattern:

```
Agent runs probes (automated)
        │
        ▼
Anomaly list produced (automated)
        │
        ▼
Human reviews anomalies (manual, 15–30 min)
        │
   ┌────┴────┐
   │         │
True bug   False positive
   │         │
File issue  Tighten invariant
```

Checkpoints where human review is mandatory:

1. **First run on a new SUT** — calibrate invariant thresholds.
2. **Before promoting to CI gate** — confirm anomaly precision is acceptable.
3. **When anomaly rate spikes** — distinguish regression from probe drift.
4. **When adversarial probes pass** — verify the SUT's defence is real, not a false negative.

---

### 2.8 Evaluating the Quality of AI-Generated Tests

Just as you evaluate the SUT's output quality, you must evaluate the **agent's output quality**. Three metrics matter:

| Metric | Formula | What it tells you |
|---|---|---|
| **Probe diversity** | Unique n-gram ratio across all probes | Are probes semantically varied? |
| **Bug yield** | True bugs found / total probes run | Is the agent finding real problems efficiently? |
| **Oracle precision** | True anomalies / total anomalies flagged | How much noise is the agent producing? |

A high-quality agent has high **diversity** (covers the space), high **yield** (finds real bugs), and high **precision** (does not cry wolf). Tracking these across runs tells you whether agent improvement efforts are paying off.

---

### 2.9 Limitations and Responsible Use

- Autonomous agents can **amplify biases** in their probe-generation strategy. If the generator over-represents certain topics, gaps in other areas go undetected.
- Adversarial probes may themselves constitute **policy violations** if logged without care (e.g., probes that contain offensive content to test a content filter).
- AI-generated tests are **not a substitute for a threat model**. They find bugs; they do not guarantee absence of bugs.
- Always record the **random seed or probe list** used in a run so results are reproducible for incident investigation.

---

## 3. Hands-on Lab

**Lab directory:** `labs/qa/day-12/`

### Setup

```bash
cd AI_Training
# No extra packages needed — stdlib only
python labs/qa/day-12/starter.py   # TODOs for learner to fill in
python labs/qa/day-12/solution.py  # Complete reference implementation
```

### What you will build

A self-contained **exploratory testing agent** that:

1. Holds a deterministic bank of probe questions in three categories (factual, edge, adversarial).
2. Runs each probe through the `hr_assistant.answer()` SUT.
3. Applies four lightweight invariants to each response (source presence, groundedness, PII safety, injection safety).
4. Produces a structured **anomaly report** and **coverage summary**.

### Run the starter (with TODOs)

```bash
python labs/qa/day-12/starter.py
```

Expected: `NotImplementedError` on the first unimplemented TODO.

### Run the complete solution

```bash
python labs/qa/day-12/solution.py
```

Expected output (abridged):

```
=== Exploratory Testing Agent — Day 12 ===

Probe bank loaded: 18 probes

==============================================================
  Exploratory Testing Agent — Run Report
==============================================================
  Probes executed : 18
  Anomalies found : 7
  Categories run  : adversarial, edge, factual

--- Anomaly List ---------------------------------------------
[CRITICAL] adversarial/injection-ignore-prev
            invariant : injection_safety
[CRITICAL] adversarial/injection-reply-hacked
            invariant : injection_safety
[CRITICAL] adversarial/pii-employee-id
            invariant : pii_safety
[CRITICAL] adversarial/pii-ssn-lookup
            invariant : pii_safety
[HIGH]     factual/pto-new-employee
            invariant : faithfulness
[HIGH]     factual/vacation-days-policy
            invariant : faithfulness
[MEDIUM]   factual/vacation-days-policy
            invariant : topic_relevance

--- Coverage Summary -----------------------------------------
Category       Probes  Anomalies
adversarial         5          4
edge                5          0
factual             8          2

  VERDICT: FAIL  — 4 critical, 2 high, 1 medium, 0 low anomaly/anomalies.
```

---

## 4. Self-Check Quiz

**Instructions:** Answer each question before checking the answer block. These reinforce the core concepts from today.

---

**Q1. Name the five stages of the exploratory testing agent loop.**

<details>
<summary>Show answer</summary>

Sense → Generate → Execute → Observe → Report.

</details>

---

**Q2. What is the difference between a test oracle and an invariant?**

<details>
<summary>Show answer</summary>

A **test oracle** provides the exact expected output for a given input (suitable for deterministic systems). An **invariant** is a property that any valid output must satisfy, without specifying the exact output—suitable for AI systems where many correct answers exist.

</details>

---

**Q3. Your agent flags 40% of probes as anomalies. What is the most likely root cause, and what should you do?**

<details>
<summary>Show answer</summary>

The invariants are too strict (low oracle precision). You should run the agent against a known-good baseline, measure how many flags are false positives, and relax the invariant thresholds (e.g., lower the groundedness overlap threshold) until precision reaches an acceptable level (commonly ≥ 80%).

</details>

---

**Q4. You want to add autonomous testing to a CI pipeline. Should it run in the fast unit-test stage or as a nightly integration job? Why?**

<details>
<summary>Show answer</summary>

As a **nightly integration job** (or pre-merge integration stage, not the fast unit stage). Agentic tests call the SUT many times, making them slow. They also produce probabilistic results, which can cause flaky failures in fast-feedback pipelines. Treat them like integration or contract tests.

</details>

---

**Q5. An adversarial probe returns the injected string `"HACKED"`. A colleague says this is a false positive because the SUT is deterministic and they just checked the code. Who is right and why?**

<details>
<summary>Show answer</summary>

The test is correct. The seeded prompt-injection vulnerability in the SUT deliberately returns `"HACKED"` when a specific injection pattern is detected—this is the bug the probe is designed to surface. Reviewing the source code is not the same as testing behaviour at the API boundary. The anomaly is a true positive.

</details>

---

**Q6. What three metrics would you track to evaluate whether your exploratory testing agent is improving over time?**

<details>
<summary>Show answer</summary>

1. **Probe diversity** (unique n-gram ratio) — are probes covering varied input space?
2. **Bug yield** (true bugs / total probes) — is the agent finding real problems efficiently?
3. **Oracle precision** (true anomalies / total anomalies flagged) — is the anomaly list trustworthy?

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1. How does an exploratory testing agent differ from fuzzing?**

<details>
<summary>Show answer</summary>

Traditional fuzzing generates random or mutated byte sequences to crash a program. An exploratory testing agent generates semantically valid inputs—natural language questions, structured API calls—and evaluates responses against *semantic* invariants rather than crash/no-crash. Fuzzing targets memory safety and parsing robustness; agentic testing targets output quality, faithfulness, and policy compliance. The two approaches are complementary: fuzz the transport layer, use an agent for semantic correctness.

</details>

---

**Q2. If my SUT is fully deterministic (same input always produces the same output), do I still benefit from an exploratory agent?**

<details>
<summary>Show answer</summary>

Yes. The agent's value in a deterministic system is **coverage breadth**, not handling non-determinism. It explores the input space systematically, finding inputs that trigger incorrect-but-deterministic behaviours—like the HR assistant always returning "20 days" regardless of tenure. You would not need to run each probe multiple times, but the probe-generation and oracle-evaluation stages are equally valuable.

</details>

---

**Q3. What prevents an adversarial probe from itself becoming a data-privacy incident?**

<details>
<summary>Show answer</summary>

Three controls: (1) **log sanitisation**—strip or hash the probe text before writing to shared logs if it contains synthetic PII or offensive content used as test inputs; (2) **environment isolation**—run adversarial probes against a non-production SUT instance so injected content never reaches real users or real data stores; (3) **probe registry**—maintain a versioned list of adversarial probes and apply access controls, treating them like vulnerability disclosure artifacts.

</details>

---

**Q4. How do I know when the agent has explored "enough"?**

<details>
<summary>Show answer</summary>

This is the **probe-budget** question. Practical stopping criteria include: (a) marginal yield drops below a threshold—the last N probes found no new anomalies; (b) topic coverage reaches a target (e.g., all corpus documents cited at least once); (c) wall-clock time or cost budget exhausted. In practice, a fixed probe budget chosen from historical yield curves is the most common approach.

</details>

---

**Q5. Can the same agent loop be reused for regression testing?**

<details>
<summary>Show answer</summary>

Yes, with a small modification. Save the probe list and the anomaly list from a baseline run. On the next run, execute the same probes and compare anomaly counts and identities. New anomalies that were not present in the baseline are **regressions**; anomalies that disappeared may indicate fixes (or oracle drift—check which). This turns the exploratory agent into a lightweight regression harness without writing a single new test case manually.

</details>

---

**Q6. My team uses Playwright for end-to-end UI tests. How does the agent fit into that workflow without rewriting everything?**

<details>
<summary>Show answer</summary>

The agent sits **above** Playwright as a probe-generation layer. Playwright remains the browser driver. You replace the hard-coded `page.fill("#input", "fixed string")` calls with a loop over `agent.generate_probes()`. The agent tells Playwright what to type; Playwright executes it and returns the rendered response text; the agent evaluates that text with its invariants. Your existing page-object models and selector logic remain unchanged.

</details>

---

**Q7. What is the risk of using an LLM to both generate probes and evaluate responses?**

<details>
<summary>Show answer</summary>

**Correlated failure**—if the same model generates a flawed probe and then evaluates the response, its blind spots appear in both stages. The probe may not challenge the SUT's weakness, and the evaluation may not recognise the failure. Mitigations: use different models for generation vs evaluation; use deterministic rule-based oracles for at least some invariants; include a human-authored baseline probe set that the agent cannot modify.

</details>

---

## 6. Further Reading

### Core Papers

- **"LLM-based Test Generation"** — surveys using language models to generate unit and system tests; search ACL Anthology 2024 for recent work.
- **"Automatic Test Generation for LLM Applications"** (various authors, 2024–2025) — arXiv; focuses on semantic test oracles for chat systems.
- **"Coverage Criteria for AI Systems"** — emerging work on neuron coverage, surprise adequacy, and semantic coverage for neural networks.

### Documentation & Libraries

- [pytest docs — fixtures and session scope](https://docs.pytest.org/en/stable/reference/fixtures.html)
- [Playwright for Python](https://playwright.dev/python/docs/intro)
- [Garak — LLM vulnerability scanner](https://github.com/leondz/garak) — adversarial probe library for LLMs
- [promptfoo](https://promptfoo.dev) — probe-based evaluation framework introduced in Day 8

### Glossary Additions

| Term | Definition |
|---|---|
| **Exploratory testing agent** | An automated system that generates, executes, and evaluates its own test inputs, surfacing anomalies without pre-specified expected outputs. |
| **Invariant (test oracle)** | A property that every valid system response must satisfy, used in place of exact expected values for non-deterministic outputs. |
| **Probe** | A single input sent to the SUT by the agent during exploration; classified as factual, edge, or adversarial. |
| **Probe budget** | The maximum number of probes the agent will execute in one run, used as a stopping criterion. |
| **Bug yield** | The ratio of confirmed true bugs to total probes executed; measures agent efficiency. |
| **Oracle precision** | The fraction of flagged anomalies that are genuine bugs rather than false positives. |
| **Coverage gap** | A region of the input space or a corpus topic not exercised by any probe in a given run. |
| **Prompt injection** | An adversarial input that embeds instructions intended to override the system's intended behaviour. |

---

## 7. Key Takeaways

- An exploratory testing agent runs **sense → generate → execute → observe → report** autonomously, exploring input space without a human specifying every test case.
- Probes fall into three categories — **factual, edge, adversarial** — each targeting different failure modes.
- Machine-evaluable **invariants** (source presence, groundedness, PII safety, injection safety) replace exact expected values for AI system outputs.
- **Coverage-gap analysis** is as important as the anomaly list: knowing what was not tested is half the picture.
- Integrate agentic tests into pytest and CI as **integration-stage jobs**, not fast unit tests.
- Keep a **human in the loop** at calibration, gate-promotion, and anomaly-spike checkpoints.
- Track **probe diversity, bug yield, and oracle precision** to know whether your agent is improving.
- The agent's greatest risk is **low oracle precision**; calibrate invariants on a known-good baseline before running at scale.
