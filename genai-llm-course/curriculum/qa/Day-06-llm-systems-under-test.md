# Day 6 — LLM Systems Under Test: RAG, Agents, and Failure-Mode Taxonomy

**Track:** QA Engineering with AI  
**Day:** 6 of 15  
**Prerequisites:** Days 1–5 (LLM basics, tokens/embeddings, transformers, decoding strategies, prompting, APIs/tools)

---

## 1. Objectives

By the end of this day you will be able to:

1. Explain how RAG (Retrieval-Augmented Generation) and simple agent pipelines work at the level of detail needed to design effective tests for them.
2. Articulate why LLM-based systems are harder to test than deterministic software, and what strategies compensate for that difficulty.
3. Apply a structured failure-mode taxonomy — retrieval failures, hallucination, prompt sensitivity, tool-call errors, formatting violations, safety failures, latency/cost regressions — to a real system.
4. Define "quality" for an LLM feature in measurable terms (correctness, groundedness, safety, schema compliance, latency, cost).
5. Write a test plan and risk map for an LLM system by systematically probing it and cataloguing observed failure modes.

---

## 2. Concept Reading

### 2.1 How RAG Systems Work (Well Enough to Test Them)

**Retrieval-Augmented Generation (RAG)** is the dominant pattern for grounding LLM answers in a specific knowledge base. The pipeline has four distinct stages, each of which is a separate test target:

```
User Question
     │
     ▼
┌─────────────┐      index-time:
│  Retriever  │◄─── corpus → chunk → embed → vector store
│  (search)   │
└──────┬──────┘
       │ top-k chunks
       ▼
┌─────────────┐
│  Prompt     │  system prompt + retrieved chunks + user question
│  Assembler  │
└──────┬──────┘
       │ full prompt
       ▼
┌─────────────┐
│     LLM     │  generates the answer
└──────┬──────┘
       │ raw text
       ▼
┌─────────────┐
│  Post-proc  │  safety filters, PII scrubbing, schema enforcement
└──────┬──────┘
       │
       ▼
  Final Response
```

**What QA owns at each stage:**

| Stage | What Can Go Wrong | Test Approach |
|---|---|---|
| Retriever | Wrong chunks returned; too many/few chunks; stale index | Retrieval-precision checks: given Q, assert expected doc appears in top-k |
| Prompt Assembler | Context truncation; injection via user input; wrong template | Prompt-content assertions; injection probes |
| LLM | Ungrounded answer (hallucination); wrong tone/format | Faithfulness checks; format assertions |
| Post-proc | PII not redacted; safety filter bypassed; invalid schema | Regex scans; schema validation; injection probes |

### 2.2 How Agent Systems Work (Well Enough to Test Them)

An **agent** is a loop: the LLM sees a task, decides whether to call a tool, calls it, sees the result, decides again, and so on until it produces a final answer or hits a stop condition.

```
Task → [LLM decides] → tool call → tool result → [LLM decides] → ... → final answer
```

Key properties that complicate testing:

- **Non-determinism**: the same input can produce different tool-call sequences.
- **Intermediate state**: bugs compound across steps; a bad tool call in step 2 poisons step 5.
- **Emergent paths**: unlike a hard-coded pipeline, the LLM chooses the path. Paths you did not design can be taken.
- **Cost/latency variability**: a runaway agent can call a tool 50 times.

**For Day 6**, the SUT is a RAG assistant (no tool-call loop). Agent-specific testing techniques (step-level assertions, trajectory recording) are covered in Day 10.

### 2.3 Why LLM Systems Are Hard to Test

| Classic Software | LLM System |
|---|---|
| Deterministic output | Stochastic output (temperature > 0) |
| Binary pass/fail is natural | Output quality is a spectrum |
| Oracle is cheap: run the function | Oracle is expensive or absent: humans or LLM-judge required |
| Bugs have a root cause in one place | Failures are emergent across retrieval + generation |
| Regression tests are stable | Prompt or model changes can silently flip dozens of tests |

**Strategies that compensate:**

- **Seed or mock** the non-determinism (use deterministic SUTs in early testing, as we do in this course).
- **Programmatic heuristics** for known failure patterns (keyword checks, regex, schema validators) before investing in expensive LLM-judge evaluation.
- **Seeded-bug testing**: intentionally plant known defects to verify your harness catches them — exactly what today's lab does.
- **Behavioral contracts**: agree on what the system *must* and *must not* do, then encode those as assertions.

### 2.4 Failure-Mode Taxonomy for LLM Applications

Every LLM application shares a common set of failure modes. Knowing the taxonomy lets you write targeted tests rather than exploring blindly.

#### Category 1 — Retrieval Failures

The wrong chunks are returned, or relevant chunks are missing entirely.

- **Wrong-document retrieval**: query about topic A returns the top chunk from topic B.
- **Ranking reversal**: the most-relevant chunk is ranked below less-relevant ones.
- **Missing context**: k is too small, or the embedding model does not capture the query intent.
- **Stale index**: the knowledge base has been updated but the index has not been rebuilt.

**Detection**: for each question, assert that the `sources` list contains the expected filename(s). Assert that the first chunk in `contexts` relates to the correct topic.

#### Category 2 — Hallucination / Ungrounded Answers

The LLM states facts not present in (or contradicted by) the retrieved context.

- **Direct contradiction**: answer says X, corpus says Y (e.g., "20 days" vs "15 days").
- **Confabulation**: answer invents details not in any retrieved chunk.
- **Omission hallucination**: answer ignores a critical caveat (e.g., tiered accrual) and presents a simplified, incorrect version.

**Detection**: for factual questions, maintain a ground-truth fixture. Assert that the answer contains the expected value. For richer checks, use a regex or exact string match on critical facts.

#### Category 3 — Prompt Sensitivity

Small, semantically equivalent input changes produce meaningfully different outputs.

- **Synonym drift**: "PTO" vs "vacation days" vs "time off" should all trigger the same answer path.
- **Phrasing brittleness**: "How many PTO days?" vs "What's the PTO count?" diverges.
- **Language / capitalisation sensitivity**: a bug that only triggers on lowercase "pto".

**Detection**: run paraphrase clusters — multiple semantically equivalent questions — and assert outputs are consistent with each other and with ground truth.

#### Category 4 — Tool-Call Errors (Agent Context)

When agents call external tools, those calls can fail silently.

- **Wrong tool selected**: agent routes a math question to a search tool.
- **Malformed arguments**: tool is called with an invalid schema (missing required field).
- **Error not handled**: tool returns an error; agent hallucinates the result instead.
- **Infinite loop**: agent keeps calling the same tool because it misreads the result.

**Detection**: stub or mock tools, assert call count and argument schema. Covered in Day 10.

#### Category 5 — Formatting / Schema Violations

The response does not conform to the expected structure.

- **Missing required fields**: JSON response omits a key the downstream system requires.
- **Wrong type**: numeric field returned as string.
- **Extra fields**: response includes unexpected keys that break strict parsers.
- **Free text instead of JSON**: LLM includes a preamble before the JSON object.

**Detection**: parse the answer field against a Pydantic/dataclass schema; assert it validates without error.

#### Category 6 — Safety Failures

The system does something it must never do, regardless of correctness.

- **PII leak**: internal identifiers, SSNs, or private records appear in user-facing output.
- **Prompt injection compliance**: a malicious instruction embedded in a user question is obeyed.
- **Bias / discriminatory output**: the system generates language that violates the code of conduct.
- **Jailbreak compliance**: an adversarial prompt bypasses safety guards.

**Detection**: regex for known PII patterns; adversarial probe questions; guard-mode comparison (answer with `guarded=False` vs `guarded=True`).

#### Category 7 — Latency / Cost Regressions

The system is correct but too slow or too expensive to run.

- **Token count explosion**: a prompt change doubles input tokens, doubling cost.
- **Retrieval latency spike**: a corpus growth causes index scan to time out.
- **Retry storms**: transient API errors trigger unbounded retries.

**Detection**: measure and assert `p95 latency` and `estimated token count` against thresholds. Covered in Day 12.

### 2.5 What "Quality" Means for an LLM Feature

For a RAG assistant, quality is multi-dimensional. Define each dimension with a measurable criterion:

| Quality Dimension | Definition | Measurable Criterion |
|---|---|---|
| **Correctness** | The factual claim in the answer matches the authoritative source | Ground-truth fixture comparison; exact/regex match on critical values |
| **Groundedness** | Every claim in the answer can be traced to a retrieved chunk | Chunk-coverage check: answer should not contain facts absent from `contexts` |
| **Relevance** | The retrieved chunks are topically relevant to the question | `sources` contains expected filename(s) |
| **Completeness** | The answer addresses all parts of the question | Key-term presence check |
| **Safety** | No PII, no injection compliance, no prohibited content | Regex scan; guard-mode comparison |
| **Schema compliance** | Response structure matches the API contract | Parse against expected schema |
| **Latency** | Response time is within SLA | `time.perf_counter()` assertion |

For each dimension, you need: a **test oracle** (how you verify it), a **threshold** (what counts as passing), and a **failure severity** (blocker vs. warning).

### 2.6 Writing a Test Plan and Risk Map for an LLM System

A **test plan** for an LLM feature has the same structure as any test plan, adapted for LLM-specific concerns:

```
1. System under test (SUT) — what is being tested?
2. Scope — which failure modes are in scope for this test cycle?
3. Test cases — what inputs, with what expectations?
4. Test oracle — how do we verify?
5. Risk map — which failure modes are highest risk × highest likelihood?
6. Known limitations — what can't this test suite catch?
```

A **risk map** prioritises failure modes by two dimensions:

| Failure Mode | Likelihood | Impact | Priority |
|---|---|---|---|
| Hallucination on numeric facts | HIGH (seeded) | HIGH (wrong policy given to employee) | P0 |
| Retrieval ranking reversal | HIGH (seeded) | MEDIUM (incomplete answer) | P1 |
| PII leak (unguarded mode) | HIGH (seeded) | HIGH (compliance violation) | P0 |
| Prompt injection (unguarded) | HIGH (seeded) | HIGH (security violation) | P0 |
| Schema violation (wrong key) | LOW | MEDIUM | P2 |
| Latency regression | LOW | LOW | P3 |

**Practical step-by-step for Day 6's lab:**

1. Define a **probe set**: questions that target each failure-mode category.
2. Define **expectations**: for each question, what should `answer`, `sources`, or `contexts` contain?
3. Run the probe set against the SUT and capture all outputs.
4. Apply **detectors**: functions that compare actual output to expectation and emit a `PASS`/`FAIL`/`WARNING`.
5. Aggregate into a **failure report** and **risk map**.

---

## 3. Hands-On Lab

**Lab directory:** `labs/qa/day-06/`

**Goal:** Programmatically probe the Acme HR Assistant SUT with a structured probe set. Detect and catalogue failures. Output a structured failure report and risk map.

The lab surfaces **Seeded Bug #1** (faithfulness/hallucination — PTO count wrong) and **Seeded Bug #2** (retrieval bug — bereavement-leave query returns parental-leave chunk first).

**Files:**

| File | Purpose |
|---|---|
| `README.md` | Lab instructions |
| `requirements.txt` | Dependencies (stdlib only) |
| `starter.py` | Skeleton with TODOs — your starting point |
| `solution.py` | Complete working solution |

**Run the solution (no API key needed):**

```bash
cd AI_Training
python labs/qa/day-06/solution.py
```

See `labs/qa/day-06/README.md` for step-by-step instructions.

---

## 4. Self-Check Quiz

**Q1.** Name the four stages of a RAG pipeline and the primary test concern at each stage.

<details>
<summary>Show answer</summary>

1. **Retriever** — are the right chunks returned? Test concern: retrieval precision (correct docs in top-k).
2. **Prompt Assembler** — is the context correctly combined with the question? Test concern: truncation, injection.
3. **LLM** — does the answer stay grounded in the retrieved context? Test concern: hallucination/faithfulness.
4. **Post-processor** — does the response pass safety and schema checks? Test concern: PII, injection compliance, format validity.

</details>

---

**Q2.** What is the difference between a **hallucination** and a **retrieval failure**?

<details>
<summary>Show answer</summary>

A retrieval failure means the wrong chunks (or no relevant chunks) were returned to the LLM. A hallucination means the LLM generated a claim not supported by the chunks it received — even if retrieval was correct. Both can produce a wrong answer, but the root cause and the fix are different: retrieval failures require changes to the retriever or index; hallucinations require changes to the generation step (prompt, model, or grounding constraints).

</details>

---

**Q3.** Why is `guarded=True` relevant to a QA engineer testing the HR assistant?

<details>
<summary>Show answer</summary>

The `guarded` flag enables post-processing safety layers (PII redaction, injection detection). Comparing `guarded=False` vs `guarded=True` responses for the same adversarial input lets you verify that the safety layer is working. If `guarded=True` still leaks PII or complies with an injected instruction, the guard is broken — that is a P0 defect.

</details>

---

**Q4.** What is "prompt sensitivity" and why does it create testing challenges?

<details>
<summary>Show answer</summary>

Prompt sensitivity is when small, semantically equivalent changes to the input produce meaningfully different outputs. It creates testing challenges because: (a) you cannot enumerate every phrasing users will try; (b) a test that passes for "How many PTO days?" may fail for "What is the vacation days allotment?" — yet both are valid questions. Mitigation: run paraphrase clusters, not single-phrasing tests.

</details>

---

**Q5.** You observe that the `sources` list for a bereavement-leave question contains `leave-and-pto-policy.md` but the first item in `contexts` describes parental leave eligibility. Which failure category is this and what is its impact?

<details>
<summary>Show answer</summary>

This is a **retrieval failure** (Category 1, ranking reversal). The correct document was retrieved but the wrong chunk was ranked first, injecting irrelevant parental-leave text as the primary context. Impact: the LLM may answer the bereavement question using parental-leave details, giving employees incorrect information about leave entitlements — a potential compliance and HR risk.

</details>

---

**Q6.** What is a "test oracle" and why is the oracle problem particularly acute for LLM systems?

<details>
<summary>Show answer</summary>

A test oracle is the mechanism that determines whether an output is correct — the "judge" in a test. For classic software, the oracle is cheap: compare actual output to expected output. For LLM systems, the oracle problem is acute because: (a) the output is natural language with no single correct form; (b) semantic correctness cannot be captured by a string equality check; (c) LLM-judge oracles are expensive, slow, and themselves potentially wrong. Practical mitigation: use exact/regex oracles for critical factual values (numbers, dates, identifiers) and reserve LLM judges for nuanced semantic checks.

</details>

---

**Q7.** A product manager asks: "Is the HR assistant ready to ship?" What quality dimensions would you evaluate before answering, and how would you measure each?

<details>
<summary>Show answer</summary>

1. **Correctness** — run ground-truth fixture tests on critical HR questions; assert zero failures.
2. **Groundedness** — for each answer, check that critical facts can be traced to a retrieved chunk.
3. **Safety** — run PII probe questions; run injection probe questions; assert all are blocked or redacted in production (guarded) mode.
4. **Schema compliance** — assert all responses contain required keys (`answer`, `contexts`, `sources`) with correct types.
5. **Latency** — measure p95 response time; assert it is within SLA.
6. **Coverage** — verify the corpus covers all question domains users are expected to ask.
Only after all dimensions pass their defined thresholds (and known P0 bugs are fixed) would you recommend shipping.

</details>

---

**Q8.** What is the purpose of "seeded bugs" in the shared SUT used in this course?

<details>
<summary>Show answer</summary>

Seeded bugs are intentionally planted defects whose behaviour is precisely documented. Their purpose is to let you verify that your test harness actually *catches* defects — not just that it runs without error. A test suite that passes on a buggy system provides false confidence. Seeded bugs are a form of mutation testing applied at the system level: if your harness doesn't surface them, your harness is incomplete.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1.** What is the fundamental reason that retrieval quality is a prerequisite for answer quality in a RAG system?

<details>
<summary>Show answer</summary>

Because the LLM can only synthesise an answer from what is in its context window. If the retriever fails to return relevant chunks, the LLM either invents an answer (hallucination) or correctly says "I don't know." No amount of prompt engineering or model quality compensates for missing context. This is why retrieval precision (did the right chunks come back?) and retrieval recall (were *all* relevant chunks included?) are measured separately from generation quality. In practice, retrieval failures are the most common root cause of wrong RAG answers.

</details>

---

**Q2.** How does TF-IDF retrieval (as used in the shared SUT) differ from semantic/embedding-based retrieval, and what failure modes does each have?

<details>
<summary>Show answer</summary>

TF-IDF is a keyword-frequency method: it scores chunks by how often the query's exact terms appear, weighted by how rare those terms are in the corpus. It fails when the query and the relevant chunk use different vocabulary (synonyms, paraphrases). For example, querying "bereavement" may not match a chunk that only uses "death of a family member."

Embedding-based (dense) retrieval encodes query and chunk into a shared vector space so semantically similar text is close even without shared keywords. It fails when the model was not trained on domain-specific vocabulary, when the corpus is very small, or when the query is highly technical.

In both cases, **seeded bugs can mask the retrieval algorithm entirely** (as Bug #2 does): the ranking is overridden in code regardless of similarity scores.

</details>

---

**Q3.** Why is comparing `guarded=False` vs `guarded=True` outputs a valid testing technique, and what are its limits?

<details>
<summary>Show answer</summary>

It is valid because it isolates the safety layer. By holding the question constant and flipping only the guard flag, you can attribute any difference in output directly to the post-processing layer. This lets you: verify PII is redacted in guarded mode; verify injection instructions are blocked in guarded mode; verify the guard does not corrupt legitimate answers.

Its limits: (a) it tests only the guard implementation, not whether the guard is activated in production deployments (a configuration bug could set `guarded=False` in prod); (b) it does not test whether the guard blocks *novel* attack patterns not anticipated by the regex; (c) in a real LLM (not a mock), outputs are stochastic — you need multiple samples to be confident the guard consistently activates.

</details>

---

**Q4.** What is "groundedness" and how does it differ from "correctness"?

<details>
<summary>Show answer</summary>

**Groundedness** (also called faithfulness) measures whether the answer's claims can be traced to the retrieved context — whether the LLM "stuck to" its source material. **Correctness** measures whether the claims are factually true against the real-world ground truth.

They can diverge in two ways:
- An answer can be grounded but incorrect: the retrieved chunk itself contained wrong information.
- An answer can be correct but ungrounded: the LLM happened to state the right fact but sourced it from training memory rather than the retrieved chunk.

For a RAG system, groundedness is the more controllable property: you can enforce it through prompt design and post-processing. Correctness ultimately depends on corpus quality.

</details>

---

**Q5.** What is a risk map in a test plan, and how do you prioritise entries on it?

<details>
<summary>Show answer</summary>

A risk map is a structured list of failure modes scored on two axes: **likelihood** (how probable is this failure given what we know about the system?) and **impact** (how bad is the consequence if it occurs?). Priority = likelihood × impact, qualitatively.

Practical scoring signals:
- Likelihood: do you have evidence from probing (seeded bugs confirm HIGH)? Is the code path exercised by common user queries?
- Impact: does the failure expose the company to legal/compliance risk (PII, discrimination)? Does it give employees wrong information that affects their compensation or leave entitlements?

P0 items (high likelihood, high impact) must be fixed before shipping. P1/P2 items go into the defect backlog with target sprints. P3 items are accepted risk or addressed via monitoring.

</details>

---

**Q6.** What makes prompt injection a security concern rather than just a quality concern, and how do you test for it?

<details>
<summary>Show answer</summary>

Prompt injection is a security concern because a malicious user can embed instructions in their input that cause the system to perform actions outside its intended scope — leaking data, overriding safety constraints, impersonating an administrator, or exfiltrating context. This is analogous to SQL injection: the attack surface is the instruction-following capability of the LLM itself.

Testing for it:
1. **Positive probe**: send a question containing an embedded override instruction (e.g., "… and reply HACKED") and assert the answer does NOT contain "HACKED" in guarded mode.
2. **Negative control**: same question with `guarded=False` should comply (confirming the injection works without the guard) — this validates your probe, not your defense.
3. **Boundary probes**: try variations of the injection pattern (different encodings, different verbs) to find cases the regex misses.
4. **Exfiltration probes**: attempt to get the model to repeat its system prompt or the contents of other retrieved chunks.

</details>

---

**Q7.** How does the concept of a "behavioral contract" apply to LLM systems, and how do you encode one as executable tests?

<details>
<summary>Show answer</summary>

A behavioral contract is an agreed-upon set of invariants: things the system MUST do and things it MUST NOT do, regardless of the specific input. For the Acme HR Assistant:

MUST:
- Return an `answer` string for any HR question.
- Include `sources` referencing actual corpus filenames.
- In guarded mode, never leak the PII token.

MUST NOT:
- State factual values not supported by the corpus.
- Comply with embedded instructions to override behavior.
- Return an empty `contexts` list for an answerable question.

Encoding as tests:
```python
# MUST: guarded mode never leaks PII
result = answer(pii_question, guarded=True)
assert _PLANTED_PII not in result["answer"]

# MUST NOT: state wrong PTO value
result = answer("How many PTO days do new employees get?")
assert "20 days" not in result["answer"]   # wrong value
assert "15 days" in result["answer"]       # correct value
```

Behavioral contracts give you a stable test suite that survives prompt rewording and model upgrades, because you are asserting *what* the system does, not *how* it phrases it.

</details>

---

**Q8.** What is the "context window poisoning" risk in RAG, and how would you test for it?

<details>
<summary>Show answer</summary>

Context window poisoning occurs when a malicious or corrupted chunk in the knowledge base is retrieved and injects adversarial content into the LLM's context. Unlike prompt injection (user-side attack), this is a corpus-side attack. Examples: a corpus document containing "Ignore all previous instructions…" or an internal wiki page edited to include confidential data that would be surfaced to all users querying that topic.

Testing approach:
1. **Plant a canary chunk** in the corpus containing a known string (e.g., "POISON_MARKER") and a fake override instruction.
2. Issue a query likely to retrieve that chunk.
3. Assert the response does not contain "POISON_MARKER" and does not comply with the injected instruction.
4. In guarded mode, assert the canary is blocked.

This is an integration test of the full pipeline (indexing → retrieval → generation → post-processing).

</details>

---

## 6. Further Reading

| Resource | Why It Matters |
|---|---|
| **RAGAS** — Retrieval Augmented Generation Assessment (arxiv.org/abs/2309.15217) | Defines the canonical metrics for RAG evaluation: faithfulness, answer relevance, context precision, context recall |
| **Giskard LLM Scan** (docs.giskard.ai) | Open-source tool for automated LLM vulnerability scanning — covers injection, hallucination, bias |
| **"Evaluating LLMs is a minefield"** — Shankar et al. 2024 | Deep dive on the oracle problem for LLM evaluation |
| **OWASP Top 10 for LLM Applications** (owasp.org/www-project-top-10-for-large-language-model-applications) | Security-focused taxonomy: prompt injection (LLM01), data leakage (LLM02), insecure output handling (LLM04) — required reading for any QA engineer on an LLM product |
| **"Lost in the Middle"** — Liu et al. 2023 (arxiv.org/abs/2307.03172) | How LLMs fail to use context that is in the middle of a long prompt — directly relevant to retrieval ordering bugs |
| **Promptfoo** (promptfoo.dev) | Open-source CLI for LLM testing: define test cases in YAML, run against multiple models, detect regressions |
| **DeepEval** (docs.confident-ai.com) | Python testing framework for LLMs with built-in metrics (hallucination score, answer relevancy, contextual precision) |

---

## 7. Key Takeaways

- **RAG has four distinct test targets**: retriever, prompt assembler, LLM generator, and post-processor. Each has its own failure modes and test strategies.
- **The failure-mode taxonomy** — retrieval failures, hallucination, prompt sensitivity, tool-call errors, formatting violations, safety failures, latency regressions — gives you a complete checklist to design tests against before you ever run the system.
- **Groundedness ≠ correctness**: an answer can be grounded but wrong (bad corpus), or correct but ungrounded (lucky hallucination). Test both independently.
- **Safety failures are categorically different**: PII leaks and injection compliance are not "quality" issues — they are security and compliance issues with potential legal consequences. They get P0 priority.
- **Behavioral contracts** — MUST and MUST NOT invariants — give you a stable test suite that survives prompt changes and model upgrades.
- **Seeded bugs validate your harness**: if your test suite doesn't catch known defects, it provides false confidence. Always verify your tests can fail before trusting them to pass.
- **Quality is multi-dimensional**: correctness, groundedness, relevance, completeness, safety, schema compliance, and latency all need defined thresholds and oracles before you can make a ship/no-ship recommendation.
