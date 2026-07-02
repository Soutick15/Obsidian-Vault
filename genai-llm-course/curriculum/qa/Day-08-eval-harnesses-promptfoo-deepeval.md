# Day 8 — Evaluation Harnesses, promptfoo, and deepeval

## 1. Objectives

By the end of Day 8 you will be able to:

1. Explain what an evaluation harness is and articulate why QA engineers — not just ML researchers — own LLM evaluation in a production team.
2. Design and maintain a **golden dataset** (ground-truth Q&A pairs) and describe what makes it representative and durable.
3. Apply core **offline evaluation metrics**: exact match, contains, semantic similarity, faithfulness/groundedness, and regression delta.
4. Use **promptfoo** to write declarative YAML test cases with assertions and run them from the CLI or CI pipeline.
5. Use **deepeval** to write pytest-style LLM evaluations with built-in metric classes.
6. Build a local evaluation harness in pure Python — no API key required — that catches a faithfulness regression in the shared HR assistant.
7. Describe how eval gates fit into a CI/CD pipeline (preview of Day 14).

---

## 2. Concept Reading

### 2.1 What Is an Evaluation Harness?

An **evaluation harness** is a repeatable, automated pipeline that:

1. Feeds a set of known inputs to a system under test (SUT).
2. Captures each output.
3. Scores each output against one or more metrics.
4. Produces a structured pass/fail report.

Think of it as the LLM equivalent of a unit-test suite — with two key differences:

- **Outputs are not deterministic** (usually). A harness must tolerate minor phrasing variation while still catching semantically wrong answers.
- **Failure modes are diverse.** An answer can be factually wrong, unfaithful to retrieved context, stylistically broken, unsafe, or regressed from a prior-known-good version.

#### Why QA Engineers Own This

LLM evaluation is not purely an ML problem. It lives at the intersection of:

| Domain | QA Engineer's Role |
|--------|--------------------|
| Test design | Define golden datasets, edge cases, adversarial inputs |
| Automation | Integrate eval into CI; enforce gates on PR merge |
| Triaging | Distinguish model regression from prompt regression from data regression |
| Reporting | Track pass rates over time; flag metric drift to stakeholders |

Data scientists own model selection and fine-tuning; QA engineers own **quality gates** — the bar a model must clear before any change ships.

---

### 2.2 Golden / Reference Datasets

A **golden dataset** is the ground-truth corpus your harness runs against. It is the single most important artefact in LLM QA.

#### What Belongs in a Golden Dataset

| Field | Description | Example |
|-------|-------------|---------|
| `question` | The input sent to the SUT | "How many PTO days do new employees get?" |
| `expected_answer` | The factually correct answer (or key facts it must contain) | "15 days" |
| `reference_contexts` | The source passages the SUT should ground its answer in | Extract from `leave-and-pto-policy.md` |
| `source_doc` | Where the ground truth comes from | `leave-and-pto-policy.md` |
| `tags` | Categorisation for filtering | `["pto", "leave", "regression"]` |

#### Building a Golden Dataset

1. **Seed from documentation.** For a RAG assistant, every factual claim in the corpus is a candidate question. Generate one Q per key claim.
2. **Cover edge cases.** Include questions that are *not* in the corpus (the SUT should say it doesn't know) and adversarial inputs (prompt injection, PII leakage triggers).
3. **Review for ambiguity.** Each golden question must have one correct answer — ambiguous questions corrupt the metric.
4. **Version it.** Store the dataset in source control alongside the code. A change to the SUT that shifts the dataset pass rate is a code review concern.
5. **Grow it incrementally.** When a new bug is found in production, add a regression test to the golden set before fixing the bug. This is the LLM equivalent of test-driven bug fixing.

#### Maintaining a Golden Dataset

- **Don't let it go stale.** If the underlying corpus changes, update the golden answers.
- **Track coverage.** Measure which source documents are exercised; gaps are testing blind spots.
- **Add a `skip` flag** for known-broken tests that are under investigation so they don't block CI while being investigated.

---

### 2.3 Offline Evaluation Metrics

These metrics run without any external API call — they are fast, deterministic, and cheap to include in every CI run.

#### Exact Match (EM)

The simplest metric: `predicted_answer.strip().lower() == expected_answer.strip().lower()`.

- **Use when:** the expected output is a single, unambiguous value (a number, a date, a code snippet).
- **Avoid when:** answers are naturally paraphrased or multi-sentence.

```python
def exact_match(pred: str, expected: str) -> bool:
    return pred.strip().lower() == expected.strip().lower()
```

#### Contains Check

Test whether the predicted answer contains one or more required substrings.

```python
def contains_all(pred: str, required: list[str]) -> bool:
    pred_lower = pred.lower()
    return all(r.lower() in pred_lower for r in required)
```

Contains checks are robust to paraphrase while still catching factual errors — for example, ensuring "15" appears in any answer about new-employee PTO.

#### Semantic Similarity

Uses a local sentence-embedding model (e.g. `sentence-transformers`) to compute cosine similarity between the predicted and expected answer.

```python
from sentence_transformers import SentenceTransformer, util

_model = SentenceTransformer("all-MiniLM-L6-v2")  # downloaded once, cached

def semantic_similarity(pred: str, expected: str) -> float:
    embs = _model.encode([pred, expected], convert_to_tensor=True)
    return float(util.cos_sim(embs[0], embs[1]))
```

A score ≥ 0.80 typically indicates the same meaning; < 0.60 typically indicates a wrong answer. Calibrate thresholds on your golden set before using in CI.

> **Note on keys:** This requires no LLM API key — it uses a local model downloaded from HuggingFace. The model is ~90 MB and cached after the first run.

#### Faithfulness / Groundedness

Faithfulness checks whether the stated facts in the answer are **supported by the retrieved contexts** — not just whether the answer is correct in the real world.

**Important caveat with RAG systems:** many RAG pipelines — including the shared SUT — append raw retrieved context chunks to the answer string (e.g. after a "Supporting context:" separator). A naive check on the full answer string would find the correct facts in the appended context and mask bugs in the model's actual claim.

The correct approach is to **extract the generated claim** first, then score it:

```python
def extract_claim(answer_text: str) -> str:
    """Return only the generated claim — before any appended context block."""
    separator = "Supporting context:"
    if separator in answer_text:
        return answer_text.split(separator)[0].strip()
    return answer_text.strip()

def faithfulness_check(reference_fact: str, contexts: list[str]) -> bool:
    """Return True if the reference fact appears in at least one retrieved context."""
    return any(reference_fact.lower() in ctx.lower() for ctx in contexts)
```

Use three complementary checks together:

| Check | What it tests | Passes for PTO bug? |
|-------|--------------|---------------------|
| `expected_contains(["15"], claim)` | Correct value appears in the claim | **FAIL** — claim says "20 days" |
| `forbidden_in_claim(["20 days"], claim)` | Hallucinated value absent from claim | **FAIL** — claim says "20 days" |
| `faithfulness_check("15 days", contexts)` | Correct value is in the retrieved context | PASS — context is correct |

The pattern of "context correct, claim wrong" is the exact signature of a faithfulness hallucination.

**Example of what this catches:**

- SUT claim: "employees receive **20 days of PTO** per year".
- Retrieved contexts contain "15 days" (correct) — the retrieval worked.
- But the generated claim ignored the context and stated "20 days".
- Result: `expected_contains(["15"], claim)` → **FAIL**, bug caught.

#### Regression Delta

Compare the current pass rate against a stored baseline:

```python
def regression_delta(current_score: float, baseline: float, threshold: float = 0.05) -> bool:
    """Return True (pass) if current is not more than threshold below baseline."""
    return current_score >= baseline - threshold
```

Store the baseline in a JSON file committed to the repo. Any PR that drops the score by more than 5% must be explicitly reviewed before merge.

---

### 2.4 The Tools: promptfoo and deepeval

#### promptfoo

[promptfoo](https://promptfoo.dev/) is an open-source CLI tool for evaluating LLM prompts and pipelines. Key characteristics:

- **Declarative YAML test cases** — you write questions and assertions in a config file; no Python needed for basic use.
- **Provider-agnostic** — supports OpenAI, Anthropic (Claude), Ollama, and custom HTTP providers.
- **CLI-first** — `npx promptfoo eval` runs the suite; `npx promptfoo view` opens an HTML report.
- **CI-ready** — exits non-zero on failure; designed to slot into GitHub Actions / GitLab CI.
- **Recent context:** promptfoo joined OpenAI in early 2025 and is now part of OpenAI's tooling ecosystem, though it remains open-source and provider-flexible.

A minimal promptfoo config looks like this:

```yaml
# promptfooconfig.yaml
prompts:
  - "{{question}}"

providers:
  - openai:gpt-5-mini        # swap to anthropic:claude-haiku-4-5 etc.

tests:
  - vars:
      question: "How many PTO days do new employees get?"
    assert:
      - type: contains
        value: "15"
      - type: not-contains
        value: "20"

  - vars:
      question: "What is the parental leave policy for a non-birth parent?"
    assert:
      - type: contains
        value: "parental leave"
```

#### deepeval

[deepeval](https://github.com/confident-ai/deepeval) is a Python framework that brings LLM evaluation into the pytest ecosystem:

- **pytest-style** — `from deepeval import assert_test`; run with `pytest`.
- **Rich metric library** — `AnswerRelevancyMetric`, `FaithfulnessMetric`, `HallucinationMetric`, `ToxicityMetric`, and more.
- **LLM-as-judge** — most metrics use an LLM (configurable) to score outputs, so an API key is required for the full metric suite.
- **Dataset management** — `EvaluationDataset` class for managing golden sets.

```python
# test_deepeval_example.py  (requires API key)
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase

def test_pto_faithfulness():
    metric = FaithfulnessMetric(threshold=0.7)
    test_case = LLMTestCase(
        input="How many PTO days do new employees get?",
        actual_output="Employees receive 20 days of PTO per year.",
        retrieval_context=["New employees with 0–2 years of service receive 15 days of PTO."]
    )
    assert_test(test_case, [metric])   # should FAIL — 20 ≠ 15
```

---

### 2.5 How Eval Fits CI Gating (Preview of Day 14)

On Day 14 you will wire a full eval suite into a GitLab CI pipeline. The pattern is:

```
PR opened
    │
    ▼
CI Stage: unit-tests (fast, no LLM)
    │
    ▼
CI Stage: offline-eval (golden set, local metrics, ~2 min)
    │  fails → PR blocked
    ▼
CI Stage: online-eval (sampled live traffic, LLM-as-judge, ~10 min)
    │  fails → PR flagged for human review
    ▼
Merge to main
```

The offline eval stage is exactly what you build in today's lab — a local harness that runs on every PR with no API cost.

**Gate criteria to define now:**
- Minimum overall pass rate (e.g. ≥ 90%).
- Zero regressions on `regression`-tagged golden items.
- Faithfulness pass rate ≥ 85% on RAG questions.

---

## 3. Hands-On Lab

**Location:** `labs/qa/day-08/`

**Goal:** Build a local evaluation harness that runs a golden Q&A set against the shared HR assistant SUT, scores each result with local assertions, and prints a structured pass/fail report. The harness must catch the seeded faithfulness bug (PTO answer states 20 days; corpus says 15).

**No API key required** for the core harness. The promptfoo and deepeval examples in the lab are documented reference material and clearly marked as requiring an API key.

**Files:**
```
labs/qa/day-08/
├── README.md
├── requirements.txt
├── starter.py          ← work through TODO markers
└── solution.py         ← reference implementation
```

**Run (no API key):**
```bash
python labs/qa/day-08/solution.py
```

See `labs/qa/day-08/README.md` for full instructions and expected output.

---

## 4. Self-Check Quiz

**Instructions:** Answer without looking at the notes. Check answers below.

**Q1.** Name two differences between an LLM evaluation harness and a traditional software unit-test suite.

<details>
<summary>Show answer</summary>

(Any two of:) LLM outputs are not deterministic so assertions must tolerate paraphrase; LLM failure modes include semantic errors and hallucinations not just crashes/exceptions; LLM evals often need reference context (golden answers, retrieved docs) not just expected return values.

</details>

**Q2.** You are building a golden dataset for a RAG assistant over a 20-document HR corpus. List three properties a good golden item must have.

<details>
<summary>Show answer</summary>

(Any three of:) One unambiguous correct answer; grounded in the corpus (source document cited); covers a meaningful factual claim; not duplicated; tagged for regression if it has previously failed.

</details>

**Q3.** The SUT answers "Employees get 20 PTO days" but the retrieved context says "15 days for 0–2 years". Which metric category catches this? What does a local proxy implementation check?

<details>
<summary>Show answer</summary>

Faithfulness / groundedness. The local proxy first extracts the generated claim by splitting off the "Supporting context:" block, then checks two things: (1) the correct fact ("15") appears in the claim, and (2) the hallucinated value ("20 days") is absent from the claim. Because the SUT's generated claim says "20 days" (not "15"), check (1) fails and check (2) also fails, so the faithfulness assertion fails correctly.

</details>

**Q4.** What does promptfoo's `type: not-contains` assertion do? Give a scenario where it is useful.

<details>
<summary>Show answer</summary>

`not-contains` asserts that a specified string does NOT appear in the output. Useful for catching hallucinated values — e.g. asserting "20 days" does not appear when the correct answer is 15.

</details>

**Q5.** deepeval's `FaithfulnessMetric` typically requires an LLM judge. What is the trade-off compared to the local keyword proxy you implemented in the lab?

<details>
<summary>Show answer</summary>

The LLM judge is more powerful (catches paraphrased unsupported claims, logical entailment failures) but requires an API call (latency, cost, non-determinism). The local proxy is fast and free but only catches verbatim-absent facts.

</details>

**Q6.** In a CI pipeline, why should the offline eval stage run *before* the online (live LLM) eval stage?

<details>
<summary>Show answer</summary>

Offline eval is fast (seconds, no API cost) and catches most regressions. Running it first means the expensive online eval only runs when the cheap gate passes — saving time and money, and keeping CI feedback loops short.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1. "What makes a golden dataset go stale, and how do I prevent it?"**

<details>
<summary>Show answer</summary>

A golden dataset goes stale when (a) the underlying corpus changes and the expected answers no longer match, (b) the set is too small to cover new features, or (c) the expected answers were written ambiguously and start producing false failures. Prevention: version the golden set in source control alongside corpus documents; run a `diff` of changed corpus files on every PR and flag any golden items whose `source_doc` was modified; review and update the dataset as part of any corpus change. Treat golden-set updates as code review items — they affect the validity of all future CI results.

</details>

**Q2. "When should I use exact match vs. contains vs. semantic similarity?"**

<details>
<summary>Show answer</summary>

Use exact match when the correct answer is a single unambiguous token — a number, a yes/no, a code string. Use contains when the answer is a sentence or paragraph that must include specific facts but can phrase them freely — e.g. the answer about PTO must contain "15" regardless of surrounding text. Use semantic similarity when you care about meaning but cannot enumerate required substrings — e.g. paraphrases of a policy description. In practice, layer them: contains checks catch the most common factual errors cheaply; semantic similarity catches subtler drift. Reserve LLM-as-judge for complex, multi-criteria quality judgements.

</details>

**Q3. "Our eval suite passes but users are still reporting wrong answers. Why?"**

<details>
<summary>Show answer</summary>

Three likely causes: (1) **Coverage gap** — the golden set does not include questions similar to what users are actually asking; fix by mining production queries and adding them to the golden set. (2) **Distribution shift** — the production corpus or prompt has drifted from what the golden set was built against; fix by keeping the golden set in sync with every corpus/prompt change. (3) **Metric weakness** — your assertions are too loose (e.g. only checking that the answer is non-empty); fix by adding stronger faithfulness and contains checks. Evaluation is only as good as its coverage — treat user-reported bugs as mandatory new golden items.

</details>

**Q4. "promptfoo joined OpenAI — does that mean it only works with OpenAI models now?"**

<details>
<summary>Show answer</summary>

No. As of its acquisition, promptfoo remains open-source and provider-agnostic. Its `providers:` config supports Anthropic (Claude), Ollama local models, Azure OpenAI, and custom HTTP endpoints. The acquisition affects the project's ownership and roadmap, not its current provider support. Always verify against the current promptfoo documentation for the latest provider list, as the tooling ecosystem evolves quickly.

</details>

**Q5. "How do I decide which golden questions to tag as regression tests in CI?"**

<details>
<summary>Show answer</summary>

Regression-tag any question that: (a) has previously produced a wrong answer in a prior version of the SUT — these are documented known-bad cases; (b) covers a business-critical fact (e.g. legal compliance, safety information) where any wrong answer is unacceptable; (c) sits at a capability boundary the team is actively trying to improve. In CI, regression-tagged tests should block the merge on any failure — even a single failure is significant. Non-tagged tests can use an aggregate threshold (e.g. ≥ 90% pass rate). The tagging strategy turns your eval suite into a living specification of what the system must always get right.

</details>

**Q6. "Our faithfulness proxy passes locally but deepeval's `FaithfulnessMetric` fails in CI. What could explain the gap?"**

<details>
<summary>Show answer</summary>

Several factors can cause a local keyword proxy and an LLM-judge metric to disagree: (1) **Scope of check** — the local proxy performs a verbatim substring search for a specific fact token; deepeval's metric asks an LLM whether every claim in the generated answer is entailed by the retrieved context. The LLM judge catches paraphrased or inferred hallucinations that the proxy misses. (2) **Claim segmentation** — deepeval splits the generated answer into individual claims before judging each. A multi-sentence answer can contain one supported claim and one unsupported claim; the proxy's single-pass search may pass on the supported token while missing the unsupported claim. (3) **Context extraction** — if the local proxy inadvertently runs its search on the full answer string (including the appended "Supporting context:" block), it will find the fact in the appended context rather than in the generated claim, producing a false pass. deepeval's metric only evaluates the `actual_output` field, not the retrieved context. Fix: ensure your local proxy always strips the context suffix before scoring, and cross-validate by running both checks on the same extracted-claim string.

</details>

---

## 6. Further Reading

| Resource | Why it matters |
|----------|----------------|
| [promptfoo documentation](https://promptfoo.dev/docs/intro) | Official guide to YAML config, assertions, providers, and CI integration |
| [deepeval documentation](https://docs.confident-ai.com/) | Full metric catalogue, pytest integration, and dataset management |
| [RAGAS framework](https://docs.ragas.io/) | Reference-free RAG evaluation metrics including faithfulness and answer relevancy |
| [LangSmith Evaluation docs](https://docs.smith.langchain.com/evaluation) | Production eval and tracing from the LangChain ecosystem |
| [Databricks LLM Evaluation blog](https://www.databricks.com/blog/LLM-auto-eval-best-practices-RAG) | Practical comparison of auto-eval approaches for RAG pipelines |
| [HELM Benchmark paper (Stanford)](https://crfm.stanford.edu/helm/latest/) | Foundational reference for holistic LLM evaluation methodology |

---

## 7. Key Takeaways

- **QA owns eval.** Evaluation harnesses are quality gates, not research experiments — they belong in CI and QA engineers maintain them.
- **Golden datasets are living artefacts.** Build them from the corpus, version them in source control, grow them with every bug found, and keep them in sync with corpus/prompt changes.
- **Layer your metrics.** Contains checks → semantic similarity → faithfulness. Each layer adds power and cost; use cheap checks first.
- **Faithfulness ≠ correctness.** An answer can be factually correct but unsupported by retrieved context (or vice versa). Test both.
- **promptfoo** gives you declarative YAML eval that runs in CI with one command. **deepeval** gives you pytest-style metrics with a rich library of LLM-judge checks.
- **A local harness costs nothing.** Pure-Python contains/faithfulness checks run in milliseconds, require no API key, and catch the majority of regressions — exactly what you built today.
- **CI gate shape:** offline eval (fast, cheap, no key) → online eval (slower, costs tokens) → merge. Build the offline gate first; it does most of the work.
