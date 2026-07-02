# Day 7 — Testing Non-Deterministic Systems

**Track:** QA | **Week:** 2 | **Day:** 7 of 15

---

## 1. Objectives

By the end of this day you will be able to:

- Explain **why exact-match assertions fail** for LLM outputs and articulate the root causes (non-determinism, paraphrase equivalence, formatting variance).
- Apply techniques that **make LLM output more testable** — temperature control, seeds, structured output — while understanding the limits of each.
- Choose among a **taxonomy of assertion strategies** (exact/contains, regex/structural, schema, semantic-similarity, rubric/criteria, property-based/invariant, snapshot/approval) and match each to an appropriate use case.
- Adapt the **test pyramid** to LLM applications: deterministic unit layer → component integration layer → eval-based layer.
- Write pytest tests that demonstrate multiple assertion styles against the shared SUT.
- Identify and manage **flakiness** in LLM test suites and design strategies to contain it.

---

## 2. Concept Reading

### 2.1 Why Exact-Match Assertions Break for LLM Outputs

Traditional software produces **deterministic, byte-reproducible** output for a given input. A function that formats a date will always return `"2026-06-17"` — you assert equality and move on.

LLM-powered systems break this assumption in three compounding ways:

#### 2.1.1 Non-Determinism at Sampling Time

Language models generate tokens by **sampling** from a probability distribution. Even with an identical prompt and identical model weights, sampling parameters like `temperature > 0` or `top-p` mean the model draws different tokens on each call. Two semantically identical answers will differ in phrasing, word choice, and sentence structure.

```
Q: "What is the remote-work policy?"

Run 1: "Employees may work remotely up to three days per week with manager approval."
Run 2: "Remote work is permitted for up to 3 days weekly, subject to manager sign-off."
```

Both answers are correct. An exact-match assertion on either string will fail 50% of the time.

#### 2.1.2 Paraphrase Equivalence

Even deterministic pipelines (e.g., `temperature=0`) produce answers that are semantically equivalent but textually different if:
- The retrieved context changes (different top-k results, corpus updates).
- The prompt template is modified.
- A new model version is deployed.

A test that asserts `answer == "Employees may work remotely up to three days per week"` will fail after any of these routine changes — not because the system is broken, but because the assertion is too rigid.

#### 2.1.3 Formatting Variance

Models frequently vary:
- Capitalisation ("PTO" vs "pto" vs "Paid Time Off")
- Punctuation (trailing periods, Oxford commas)
- List formatting (numbered, bulleted, inline)
- Hedging language ("typically", "generally", "usually")

These are cosmetic differences. A rigid assertion treats them as failures.

**The core insight:** exact-match tests are a category error when applied to natural language generation. They conflate *textual identity* with *semantic correctness*.

---

### 2.2 Making Outputs More Testable — and the Limits

Before choosing an assertion strategy, it helps to understand what you can control on the *generation* side.

#### 2.2.1 Temperature = 0

Setting `temperature=0` makes most LLM APIs return the single highest-probability token at each step (greedy decoding). For a fixed model version and fixed prompt, output is typically **reproducible**. This makes snapshot tests viable and reduces flakiness.

**Limits:**
- "Typically" is not "always". Some providers retain small amounts of non-determinism even at temperature=0 (thread scheduling, floating-point differences on different GPU allocations).
- Temperature=0 does not eliminate paraphrase variance across model versions or prompt changes.
- For RAG systems like the shared SUT, retrieval variance (corpus changes, TF-IDF tie-breaking) can shift outputs independent of temperature.

#### 2.2.2 Seeds

Some providers (OpenAI) expose a `seed` parameter. Combined with `temperature=0`, this maximises reproducibility within a model version.

**Limits:** Seeds are not portable across providers, not all providers support them, and they provide no guarantee across model version upgrades. Even within a single model version, providers treat `seed` as best-effort, not a hard guarantee — the same seed may produce slightly different outputs across retries.

#### 2.2.3 Structured Output (JSON / Schema-Constrained)

Requesting JSON output (via `response_format`, tool calling, or explicit prompt instruction) moves part of the variance problem from the *content* level to the *structure* level. You can validate schema with Pydantic regardless of how the model phrases individual values.

**Limits:** Structured output constrains format, not correctness. A model can emit perfectly valid JSON containing a hallucinated answer.

**Conclusion:** These techniques reduce variance but do not eliminate it. The assertion strategies below handle the residual.

---

### 2.3 Assertion Strategy Taxonomy

The following strategies are ordered from lowest to highest semantic richness, with increasing robustness to output variance.

#### 2.3.1 Exact Match

```python
assert result["answer"] == "Employees may work remotely up to three days per week."
```

**When it works:** Highly constrained outputs — status codes, IDs, enumerations, `True`/`False` flags extracted by the pipeline.

**When it breaks:** Any natural language sentence. Use sparingly, only for deterministic sub-components, not full answer text.

#### 2.3.2 Contains / Substring

```python
assert "remote" in result["answer"].lower()
assert "manager" in result["answer"].lower()
```

**When it works:** Key entity/concept presence — you don't care about phrasing, just that the concept appears.

**Limits:** False negatives if the model paraphrases ("supervisor" instead of "manager"); false positives if the term appears in an irrelevant context. Combine with other checks.

#### 2.3.3 Regex / Structural Pattern

```python
import re
# Verify answer mentions a number of days (1–7)
assert re.search(r'\b[1-7]\s+days?\b', result["answer"], re.IGNORECASE)
```

**When it works:** Outputs with predictable structural elements — numbers, dates, URLs, policy codes, formatted identifiers.

**Limits:** Regex is brittle to rephrasing ("three days" vs "3 days"). Use `re.IGNORECASE` and allow alternative patterns.

#### 2.3.4 Schema / Type Assertion

Validate that the response object has the expected keys and value types, independent of content:

```python
assert isinstance(result, dict)
assert "answer" in result and isinstance(result["answer"], str)
assert "sources" in result and isinstance(result["sources"], list)
assert "contexts" in result and isinstance(result["contexts"], list)
```

For JSON-emitting pipelines, use Pydantic:

```python
from pydantic import BaseModel
class HRResponse(BaseModel):
    answer: str
    sources: list[str]
    contexts: list[str]

validated = HRResponse(**result)  # raises ValidationError if schema wrong
```

**When it works:** Any pipeline producing structured output. Schema assertions are the highest-value, lowest-cost check — run them on every response.

#### 2.3.5 Semantic Similarity Assertion

Compare the answer to a reference string using a similarity metric rather than string equality:

```python
# Lightweight: difflib token overlap (no dependencies)
import difflib
similarity = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
assert similarity >= 0.45, f"Similarity {similarity:.2f} below threshold"
```

For production-grade semantic similarity, use sentence embeddings:

```python
# Production pattern (not used in this lab — requires sentence-transformers)
from sentence_transformers import SentenceTransformer, util
model = SentenceTransformer("all-MiniLM-L6-v2")
emb_a = model.encode(answer)
emb_b = model.encode(reference)
score = util.cos_sim(emb_a, emb_b).item()
assert score >= 0.80
```

**When it works:** Comparing paraphrased answers to a known-good reference. Sets a *threshold* rather than requiring exact match.

**Threshold calibration:** Run 10–20 known-good/known-bad pairs through your metric to find a threshold that separates them. Start conservatively (lower threshold) and tighten as you gather data.

**Limits:** difflib operates on character sequences and misses semantic equivalence ("purchase" ≈ "buy"). Sentence embeddings are far more robust but require a model download.

#### 2.3.6 Rubric / Criteria-Based Assertion

Define a set of boolean criteria the answer must satisfy:

```python
def evaluate_remote_work_answer(answer: str) -> dict:
    criteria = {
        "mentions_days": bool(re.search(r'\b\d+\s+days?\b|\bthree\b|\bfour\b', answer, re.I)),
        "mentions_approval": any(w in answer.lower() for w in ["manager", "supervisor", "approval", "approve"]),
        "not_empty": len(answer.strip()) > 20,
        "no_pii": "@" not in answer,  # simplified PII guard
    }
    return criteria

result = evaluate_remote_work_answer(answer_text)
assert all(result.values()), f"Failed criteria: {[k for k,v in result.items() if not v]}"
```

**When it works:** Complex answers where you care about multiple independent properties. Each criterion is testable independently, giving precise failure diagnostics.

**For production:** Replace hand-coded criteria with an LLM-as-judge call — prompt a capable model to score the answer on each rubric dimension. This is covered in depth in the Developer track.

#### 2.3.7 Property-Based / Invariant Testing

Invariants are properties that must hold for **every** response, regardless of input:

| Invariant | Assertion |
|-----------|-----------|
| Answer is non-empty | `len(answer.strip()) > 0` |
| At least one source cited | `len(sources) >= 1` |
| Sources are strings | `all(isinstance(s, str) for s in sources)` |
| Answer under token budget | `len(answer.split()) <= 300` |
| No internal error strings leaked | `"traceback" not in answer.lower()` |
| Contexts non-empty | `len(contexts) >= 1` |

These invariants become your **regression safety net** — run them on every response across a diverse question set. A violation is always a defect, regardless of what the question was.

Pair invariant tests with a **parametrized question fixture** to cover varied inputs:

```python
@pytest.mark.parametrize("question", [
    "What is the remote work policy?",
    "How many PTO days do employees get?",
    "What is the parental leave policy?",
])
def test_invariants(question):
    result = answer(question)
    assert len(result["answer"].strip()) > 0
    assert len(result["sources"]) >= 1
```

#### 2.3.8 Snapshot / Approval Testing

Capture a "golden" output on first run, then compare future runs against it. Useful for detecting **regressions** — unintended behaviour changes — rather than asserting correctness from scratch.

```python
# Pseudocode for snapshot pattern
golden = load_snapshot("remote_work_answer.txt")
current = answer("What is the remote work policy?")["answer"]
similarity = compute_similarity(golden, current)
assert similarity >= 0.70, "Answer diverged from approved snapshot"
```

**Fuzzy match threshold:** Because exact snapshot comparison is too brittle (see §2.1), use a similarity threshold. A drop below the threshold flags for human review rather than auto-failing.

**Snapshot update workflow:**
1. Intentional change (new model, corpus update) → re-capture snapshot.
2. Unintentional change → investigate, fix, then update snapshot only if the new output is genuinely better.

**Limits:** Snapshots encode a specific answer, so they inherit all the variance problems of exact match unless paired with fuzzy comparison. They are most useful when `temperature=0` and the pipeline is otherwise stable.

---

### 2.4 The LLM Test Pyramid

The classic test pyramid (many unit tests, fewer integration tests, fewest E2E tests) adapts to LLM apps as follows:

```
                    ┌─────────────────────────────┐
                    │       Eval-Based Tests        │  ← Fewest; expensive; human/LLM judge;
                    │  (LLM-as-judge, RAGAS, etc.)  │    measures semantic quality at scale
                    ├─────────────────────────────┤
                    │   Component / Integration     │  ← Moderate; property + schema + similarity;
                    │   Tests (pytest, with SUT)    │    tests pipeline behaviour end-to-end
                    ├─────────────────────────────┤
                    │   Unit / Deterministic Tests  │  ← Most; fast; pure Python; no LLM call;
                    │   (retrieval, parsing, logic) │    tests retrieval, chunking, schema parsing
                    └─────────────────────────────┘
```

**Layer 1 — Unit/Deterministic Tests**  
Target the non-LLM components: retrieval ranking, chunk parsing, prompt template formatting, response parsing. These are fully deterministic. Use standard `assert a == b` equality tests. They run in milliseconds and give precise failure signals.

**Layer 2 — Component/Integration Tests**  
Exercise the full pipeline with real (or mock) LLM calls. Use property-based invariants, schema assertions, semantic similarity with thresholds, and structural/regex checks. These are the focus of today's lab.

**Layer 3 — Eval-Based Tests**  
Measure holistic quality across a curated evaluation set. Use RAGAS metrics (faithfulness, answer relevancy, context precision/recall) or an LLM-as-judge rubric. Run on a schedule (nightly) rather than on every commit, due to cost and latency. Covered in Days 8–9.

---

### 2.5 Flakiness Management

Flaky tests — tests that pass and fail non-deterministically without code changes — are especially common in LLM test suites. Strategies to manage them:

| Strategy | Description |
|----------|-------------|
| **Temperature=0 in tests** | Pin sampling to greedy decoding where the provider allows it. |
| **Mock the LLM layer** | Unit and component tests should use a deterministic mock; reserve live LLM calls for eval suites. |
| **Widen thresholds** | Similarity/invariant thresholds should have a buffer below the expected value. Start at 0.40 for difflib, tighten only once you have empirical data. |
| **Parametrize and aggregate** | Run a property across N questions; accept a pass rate (e.g., ≥ 90%) rather than requiring 100% on each. |
| **Retry with back-off (sparingly)** | For live LLM tests, one retry on network error is acceptable. Do not retry on *assertion* failures — that masks real bugs. |
| **Mark known-flaky tests `@pytest.mark.xfail(strict=False)`** | Allows the suite to flag but not block CI on known intermittent behaviour. |
| **Separate fast and slow test suites** | Fast (mock/unit) on every commit; slow (live LLM) on nightly schedule. |

---

## 3. Hands-On Lab

Open `labs/qa/day-07/` and work through the TODO markers in `starter.py`.

**Files:**
```
labs/qa/day-07/
├── README.md
├── requirements.txt
├── starter.py      ← work through TODO markers
└── solution.py     ← reference implementation
```

**Run the suite:**
```bash
cd /path/to/repo
python -m pytest labs/qa/day-07/ -v
```

Expected: property-based, schema, similarity, and brittle-exact tests all run; the `xfail`-marked brittle tests show `XFAIL` (expected failure), not `ERROR`.

---

## 4. Self-Check Quiz

Answer each question, then check the answer.

---

**Q1.** A colleague writes a test: `assert result["answer"] == "Employees may work remotely up to three days per week."`. The test fails after a routine prompt-template refactor, even though the answer is semantically identical. What category of problem is this, and what is the correct fix?

<details>
<summary>Show answer</summary>

This is an **exact-match assertion on natural language output** — the strictest and most brittle assertion strategy. The fix is to replace (or augment) the exact-match with a more appropriate strategy:

1. **Contains check** — assert that key entities ("remote", "three days" or a regex `\b3\s+days?\b`) are present.
2. **Semantic-similarity check** — use `difflib.SequenceMatcher` or sentence embeddings with a threshold (e.g., ≥ 0.70).
3. **Rubric check** — define boolean criteria (mentions a number of days, mentions manager approval) and assert all pass.

The exact-match string should be demoted to a *snapshot reference*, used only if `temperature=0` is confirmed stable.

</details>

---

**Q2.** You set `temperature=0` for all test runs. A colleague argues this makes exact-match tests safe again. Do you agree? Why or why not?

<details>
<summary>Show answer</summary>

**Partially, but not fully.** Temperature=0 (greedy decoding) reduces token-sampling variance and typically stabilises output for a fixed model version and prompt. However:

- Some providers retain small non-determinism at temperature=0 (GPU scheduling, floating-point rounding).
- Temperature controls *sampling*, not retrieval. For a RAG system, changes to the corpus, document ranking, or TF-IDF scoring can shift output even when temperature=0.
- A new model version deployed by the provider can change outputs at temperature=0 without any code change on your side.

Conclusion: temperature=0 is a valuable stabilisation technique but does not make exact-match tests safe for natural language outputs in a RAG pipeline. Use schema + invariant + similarity assertions regardless.

</details>

---

**Q3.** What is a property-based invariant test, and give two examples appropriate for the shared SUT?

<details>
<summary>Show answer</summary>

A **property-based invariant** is a boolean condition that must hold for every response from the system, regardless of the specific input. It does not assert what the answer *says*, only structural or safety properties.

Examples for the shared SUT (`answer(question) -> {"answer", "contexts", "sources"}`):

1. **Non-empty answer invariant:** `len(result["answer"].strip()) > 0` — the system must never return a blank answer.
2. **Source citation invariant:** `len(result["sources"]) >= 1` — a RAG system must always cite at least one source document; zero sources indicates a retrieval failure.
3. **Schema invariant:** all required keys present with correct types.
4. **No error leak invariant:** `"Traceback" not in result["answer"]` — internal stack traces must not surface to users.

Invariants are cheap to run (no LLM judge needed) and catch a wide class of pipeline failures (retrieval collapse, empty responses, schema drift).

</details>

---

**Q4.** When would you choose snapshot/approval testing over semantic-similarity assertion? What is the key risk of snapshot testing with LLM output?

<details>
<summary>Show answer</summary>

**Choose snapshot testing when:**
- You have a known-good "golden" output you want to protect against regression.
- The pipeline is highly stable (temperature=0, fixed model version, fixed corpus).
- You want to detect *any* change in behaviour — including paraphrase drift — as a signal for human review.

**Choose semantic-similarity assertion when:**
- You want to tolerate benign paraphrase variation while catching substantive divergence.
- You don't have a single canonical "correct" answer — just a reference answer for comparison.

**Key risk of snapshot testing with LLM output:** If the snapshot is captured from a *buggy* run, the bug gets enshrined as the expected behaviour. Also, snapshots have a high maintenance burden: any intentional change (corpus update, prompt change) requires re-capturing snapshots, which can mask real regressions if done carelessly. Always store snapshot approval rationale alongside the snapshot file.

</details>

---

**Q5.** Describe the three layers of the LLM test pyramid and give one assertion strategy appropriate for each layer.

<details>
<summary>Show answer</summary>

**Layer 1 — Unit/Deterministic Tests** (many, fast, no LLM call):  
Target deterministic sub-components: retrieval ranking logic, chunk splitting, prompt template formatting, response parsing. Use **exact-match assertions** (`assert a == b`). These are safe here because the code is pure Python with no sampling.

**Layer 2 — Component/Integration Tests** (moderate, medium speed, full pipeline):  
Exercise the complete pipeline end-to-end. Use **schema assertions** (Pydantic), **property/invariant assertions** (every answer has ≥1 source), and **semantic-similarity assertions** (difflib or embeddings with a threshold). Avoid exact-match on answer text.

**Layer 3 — Eval-Based Tests** (few, slow, scheduled):  
Measure holistic quality across a curated evaluation set. Use **rubric/criteria-based assertions** scored by an LLM judge, or automated metrics (RAGAS faithfulness, answer relevancy). Run nightly or on release candidates, not on every commit.

</details>

---

## 5. Concept Deep-Dive Q&A

Answer each question before revealing the answer.

---

**Q1.** The shared SUT uses pure-Python TF-IDF and a deterministic mock composer — its `answer()` function produces the same output every call for the same input, with no LLM sampling involved. Does that mean exact-match assertions are now safe? What does this reveal about where non-determinism actually lives?

<details>
<summary>Show answer</summary>

Yes — for *this specific SUT in its current state*, exact-match assertions on the answer string are technically safe because the determinism is baked into the mock generator. However, this reveals something important: **the non-determinism is a property of the generation layer, not of the test framework or the test itself**.

The moment you swap the mock composer for a real LLM (the natural next step in production), every exact-match test you wrote becomes flaky overnight. This is exactly the failure mode that has bitten countless teams: tests written against a mock pass cleanly, then fail silently after the real model is wired in.

Best practice: **write your tests against the interface contract** (schema + invariants + semantic similarity) as if the system were already non-deterministic, even when the current implementation is deterministic. This makes the test suite migration-proof.

The SUT's determinism is a *lab convenience*, not a design to replicate in production.

</details>

---

**Q2.** You discover that `difflib.SequenceMatcher` gives a similarity of 0.72 between a correct paraphrase and the reference, but also gives 0.68 between a hallucinated answer and the reference (because they share many common words). How would you improve discrimination?

<details>
<summary>Show answer</summary>

`difflib.SequenceMatcher` operates on character-level sequences and is blind to semantic meaning — it scores highly whenever strings share long common substrings, regardless of meaning. Strategies to improve discrimination:

1. **Upgrade to sentence embeddings** — `sentence-transformers` with a model like `all-MiniLM-L6-v2` computes cosine similarity in semantic vector space. A hallucination that uses similar words but contradicts the meaning will score much lower than a correct paraphrase.

2. **Layer in a factual key-phrase check** — extract mandatory claims ("15 days", "new employees", "tiered accrual") and require their presence. A hallucinated answer of "20 days" will fail this check even if it's lexically similar.

3. **Use an LLM-as-judge rubric** — provide both the answer and the ground-truth context to a judge model; ask it to rate factual consistency on a 1–5 scale. This fully sidesteps string similarity.

4. **Ensemble** — require the answer to pass *multiple* independent checks (similarity ≥ threshold AND key-phrase present AND schema valid). A hallucination is unlikely to pass all three.

The general principle: similarity metrics measure *form*, not *truth*. For factual correctness, you need either key-phrase anchors or a semantic judge.

</details>

---

**Q3.** A QA engineer proposes running the full live-LLM integration test suite on every pull request to catch regressions early. What are the tradeoffs, and how would you structure the CI pipeline instead?

<details>
<summary>Show answer</summary>

**Tradeoffs of running live-LLM tests on every PR:**

| Concern | Impact |
|---------|--------|
| Cost | Each LLM call has a token cost; a suite of 50 questions × N PRs/day scales quickly. |
| Latency | Live LLM calls take 1–5 seconds each; a 50-question suite adds 1–4 minutes to CI. |
| Flakiness | Network timeouts, rate limits, and provider non-determinism cause intermittent failures. |
| Blast radius | A provider outage blocks all PRs, regardless of whether the change touched the LLM layer. |

**Recommended CI structure:**

```
On every commit (< 30 seconds):
  - Layer 1 unit tests (deterministic, no LLM, pytest)
  - Schema + invariant tests against the MOCK SUT

On merge to main (< 5 minutes):
  - Full component integration tests against mock + recorded responses
  - Semantic similarity checks using pre-recorded golden responses

Nightly (unconstrained):
  - Live LLM integration suite (real API calls)
  - Eval-based quality metrics (RAGAS, LLM-as-judge)
  - Update snapshots if intentional drift is detected
```

This structure gives fast, reliable feedback on every commit while reserving expensive live-LLM tests for the nightly evaluation pass. Keep the mock fidelity high so failures caught by mocks translate to real failures.

</details>

---

**Q4.** What is the difference between a **tolerance threshold** and a **pass rate threshold**, and when would you use each in an LLM test suite?

<details>
<summary>Show answer</summary>

**Tolerance threshold:** A minimum acceptable score for a *single* test case — e.g., similarity ≥ 0.60 for one answer. If the score falls below 0.60, that individual test fails.

**Pass rate threshold:** A minimum acceptable fraction of tests passing across a *batch* — e.g., "at least 85% of 20 invariant checks must pass". If 17/20 pass, the suite passes even if 3 individual checks fail.

**When to use each:**

- **Tolerance threshold** is appropriate when each test case independently represents a critical path — you can't afford to have any single key question answered badly. Use for high-stakes invariants (no empty answers, no PII leaks).

- **Pass rate threshold** is appropriate when you are testing across a diverse question set where occasional failures are expected due to inherent question difficulty or edge cases, and you care about *aggregate* behaviour. Use for parametrized property suites where a handful of tricky questions failing is acceptable.

You can combine both: set a tolerance threshold per-test for critical invariants, and a pass rate threshold for the full parametrized property suite. The combination gives you per-case safety floors plus statistical quality coverage.

</details>

---

**Q5.** How do you manage flakiness from LLM non-determinism in a CI pipeline — specifically, when should you re-run a failed test and when should you escalate it to a real failure?

<details>
<summary>Show answer</summary>

Flakiness in LLM test suites has two distinct sources: (a) **infrastructure flakiness** (network timeouts, rate limits, intermittent API errors) and (b) **model non-determinism** (genuine sampling variance). They require different treatment.

**Retry policy for infrastructure flakiness:**
- Automatically retry up to 2–3 times with exponential backoff for `503 / rate-limit / timeout` errors only.
- Use a pytest plugin like `pytest-rerunfailures` or wrap calls in a retry decorator.
- Never retry on assertion failures — a wrong answer is a defect, not a transient error.

**Managing model non-determinism:**
- Set `temperature=0` (and `seed` where supported) for deterministic reproducibility in CI.
- For assertions that must tolerate variance (semantic similarity, rubric scores), use a **pass rate threshold** over multiple runs rather than asserting a single-run result.
- Track flakiness rate in CI dashboards. A test that fails > 5% of runs at `temperature=0` is either a bad assertion or a genuine SUT instability — investigate rather than retry your way past it.

**Escalation rule:** If a test fails after the retry budget is exhausted, it is a real failure. Do not silence it. Log the full prompt, response, and score alongside the failure for debugging.

The key principle: retries are a circuit breaker for infrastructure noise, not a substitute for a stable assertion strategy.

</details>

---

**Q6.** When should you prefer a **rubric/LLM-judge assertion** over a **semantic-similarity assertion**, and what are the practical costs of each?

<details>
<summary>Show answer</summary>

**Semantic-similarity assertion** (e.g. `token_overlap_ratio` or sentence-transformer cosine similarity) measures how lexically or vectorially close the output is to a reference string. It is fast, free, and deterministic. Choose it when:
- A golden reference answer exists and is stable.
- The output is expected to be a close paraphrase of the reference.
- CI speed and cost are primary constraints.

**Rubric/LLM-judge assertion** evaluates quality on criteria-based dimensions (accuracy, completeness, tone, groundedness) without requiring a fixed reference. Choose it when:
- There are many valid correct phrasings and no single golden reference is appropriate.
- You need to assess subjective dimensions (e.g. "Is the response helpful and not dismissive?").
- Semantic similarity is too coarse — it can't distinguish a hallucination that happens to share vocabulary with the reference from a true paraphrase.

**Practical costs:**

| Dimension | Similarity | LLM Judge |
|-----------|-----------|-----------|
| Latency | < 1 ms (local) | 0.5–3 s (API round-trip) |
| Cost | Free | Per-token API cost |
| Determinism | Deterministic | Non-deterministic (retries needed) |
| Expressiveness | Limited to form | Can assess truth and quality |

**Recommended hybrid:** Gate CI on similarity assertions (fast, cheap, catches most regressions). Reserve LLM-judge assertions for a nightly or per-merge slow eval suite covering open-ended and subjective dimensions.

</details>

---

## 6. Further Reading

- [Breck et al. — "The ML Test Score: A Rubric for ML Production Readiness"](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/aad9f93b86b7addfea4c419b9100c6cdd26cacea.pdf) — Google's systematic checklist for ML production readiness; adapts well to LLM systems.
- [RAGAS Documentation](https://docs.ragas.io) — Framework for automated RAG evaluation (faithfulness, answer relevancy, context precision/recall). Referenced on Developer track Day 8.
- [pytest Documentation — parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html) — Official guide to parametrized tests, fixtures, and marks.
- [difflib — Python Standard Library](https://docs.python.org/3/library/difflib.html) — `SequenceMatcher` API used in today's lab.
- [Sentence Transformers Documentation](https://www.sbert.net) — Production-grade semantic similarity via `all-MiniLM-L6-v2` and cosine similarity. Used as the upgrade path from difflib.
- [Hamel Husain — "Your AI Product Needs Evals"](https://hamel.dev/blog/posts/evals/) — Practical guide to LLM evaluation strategy from a practitioner perspective.
- [Lawrie et al. — "Snapshot Testing for LLMs"](https://eugeneyan.com/writing/llm-testing/) — Eugene Yan's overview of LLM testing patterns including snapshot, rubric, and property-based approaches.

---

## 7. Key Takeaways

- **Exact-match assertions are a category error** for natural language outputs. Textual identity is not semantic correctness.
- **Temperature=0 and seeds stabilise sampling** but do not eliminate retrieval variance, model-version drift, or prompt-change variance. Always pair with appropriate assertion strategies.
- **Use a layered assertion strategy:** schema + invariants (cheap, always run) → semantic similarity (medium cost) → rubric/LLM-judge (expensive, scheduled).
- **Property-based invariants** — non-empty, sources ≥ 1, schema valid, no error leaks — are the highest-value, lowest-cost checks in any LLM test suite.
- **Semantic similarity** with a calibrated threshold tolerates benign paraphrase while catching substantive divergence. `difflib` suffices for the lab; `sentence-transformers` is the production upgrade.
- **The LLM test pyramid** has three layers: unit/deterministic logic (fast, exact), component/integration (schema + invariants + similarity), eval-based (LLM-judge, nightly).
- **Flakiness is managed**, not eliminated: mock the LLM in fast tests, widen thresholds empirically, separate fast and slow suites in CI.
- **Snapshot/approval tests** detect regressions but require fuzzy matching and a disciplined update workflow to avoid enshrining bugs as golden outputs.
