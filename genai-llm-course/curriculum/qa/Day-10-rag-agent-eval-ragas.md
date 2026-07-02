# Day 10 — RAG & Agent Evaluation: Metrics, Ragas, and Trajectory Testing

**Track:** QA | **Week:** 2 | **Prerequisites:** Days 6–9 (RAG basics, advanced retrieval, agents, tool use)

---

## 1. Objectives

By the end of this day you will be able to:

- Explain the **retrieval / generation split** and why it demands separate metrics.
- Define and compute **Context Precision@k**, **Context Recall@k**, **Faithfulness**, and **Answer Relevancy**.
- Describe how the **Ragas** framework measures each metric (including its LLM-assisted scoring).
- Build a **labeled relevance set** and run local retrieval evaluation against a real SUT.
- Evaluate **agent trajectories**: tool-call correctness and task success rate.
- Identify the five most common RAG evaluation pitfalls and how to avoid them.

---

## 2. Concept Reading

### 2.1 The Retrieval / Generation Split

A RAG pipeline has two distinct failure modes:

1. **Retrieval failure** — the right document never reaches the LLM. The answer will be wrong no matter how capable the generator is.
2. **Generation failure** — the right documents are retrieved but the LLM ignores them, misinterprets them, or invents facts not present in them.

These two modes require **separate metrics** evaluated on separate evidence:

| Mode | Evidence needed | Metrics |
|---|---|---|
| Retrieval | Ground-truth relevant docs per query | Context Precision, Context Recall |
| Generation | Ground-truth answer + retrieved contexts | Faithfulness, Answer Relevancy |

Conflating the two hides root causes. A low end-to-end accuracy score does not tell you whether to fix the embeddings or the prompt.

---

### 2.2 Context Precision@k

**What it measures:** Of the k documents the retriever returned, what fraction were actually relevant to the query?

**Formula:**

```
Context Precision@k = (number of relevant docs in top-k) / k
```

**How it is computed:**

1. For each query in your labeled set, retrieve the top-k documents from the SUT.
2. Compare each retrieved document against the ground-truth relevant set for that query.
3. A document is relevant if its source identifier appears in the ground-truth set.
4. Average across all queries.

**Interpretation:** A precision of 1.0 means every retrieved chunk was useful. A low precision indicates the retriever is returning noisy or off-topic chunks that dilute the context the LLM sees.

**Relation to retrieval bug #2:** When a bereavement-leave query triggers the wrong document (parental leave) as the top result, precision@1 drops to 0 for that query.

---

### 2.3 Context Recall@k

**What it measures:** Of all the documents that *should* have been retrieved, what fraction actually appeared in the top-k results?

**Formula:**

```
Context Recall@k = (number of relevant docs in top-k) / (total number of relevant docs for the query)
```

**How it is computed:**

1. Count the ground-truth relevant documents for a query (your labeled set provides this).
2. Check how many of those appear in the retriever's top-k output.
3. Divide; average across queries.

**Interpretation:** Recall measures coverage. A pipeline with high precision but low recall retrieves only a clean slice of the evidence — it might answer some questions well but miss critical supporting context for complex queries.

**Trade-off:** Increasing k improves recall but may hurt precision. Choosing k is a calibration exercise informed by both metrics together.

---

### 2.4 Faithfulness / Groundedness

**What it measures:** Does the answer contain only claims that are supported by the retrieved context? Faithfulness is the fraction of answer claims that can be traced back to at least one retrieved chunk.

**How it is computed (LLM-assisted, Ragas style):**

1. Parse the answer into atomic claims (e.g., "employees receive 20 days of PTO").
2. For each claim, ask an LLM: "Is this claim supported by the following context passages?" → yes/no.
3. `Faithfulness = (number of supported claims) / (total claims in answer)`.

**Local heuristic (no API key required):** Check whether key numeric or named entities from the answer appear verbatim in the retrieved context strings. This is a proxy, not a substitute for LLM-assisted scoring, but it catches obvious hallucinations.

**Relation to bug #1:** The SUT answers "20 days of PTO" for new employees. The corpus says 15 days for 0–2 years of service. A faithfulness check that looks for "20 days" in the retrieved context will fail because the context chunk contains "15 days" — the answer is not grounded.

---

### 2.5 Answer Relevancy

**What it measures:** How well does the answer address the question that was actually asked? A faithful answer can still be irrelevant if it answers a different question.

**How it is computed (Ragas style):**

1. Feed the answer to an LLM and ask it to generate *n* questions that the answer could plausibly be responding to.
2. Embed both the original question and the *n* generated questions.
3. `Answer Relevancy = mean cosine similarity(original question, generated question_i)`.

High similarity means the answer stays on topic. Low similarity means the answer drifted — perhaps answering a related but different question than the one asked.

**Note:** This metric requires an LLM and an embedding model; it is in the Ragas reference snippet in the lab, not the no-key section.

---

### 2.6 The Ragas Framework

[Ragas](https://docs.ragas.io) is an open-source Python library (pip install ragas) that operationalises all four metrics above as a unified evaluation suite.

**Key design choices:**

| Property | Detail |
|---|---|
| LLM-assisted scoring | Uses a configurable LLM (any provider) for faithfulness claim decomposition and answer relevancy question generation |
| Batch evaluation | Accepts a `Dataset` of `{question, contexts, answer, ground_truth}` rows |
| Metric objects | `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall` are importable objects passed to `evaluate()` |
| Provider-flexible | Works with OpenAI, Anthropic (claude-haiku-4-5 recommended for cost), or any LiteLLM-supported model |

**Minimal Ragas usage (requires API key + `pip install ragas`):**

```python
# --- REFERENCE ONLY — requires ANTHROPIC_API_KEY or OPENAI_API_KEY ---
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

data = {
    "question":    ["How many PTO days do new employees get?"],
    "contexts":    [["[PTO Policy] Employees with 0-2 yrs of service accrue 15 days..."]],
    "answer":      ["Based on Acme Corp policy, employees receive 20 days of PTO per year."],
    "ground_truth":["New employees (0-2 years) receive 15 days of PTO per year."],
}
dataset = Dataset.from_dict(data)
result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision, context_recall])
print(result)
# Expected: faithfulness ~ 0.0 (hallucinated claim), context_precision ~ 1.0 (correct doc retrieved)
```

See `labs/qa/day-10/solution.py` for the full annotated reference block.

---

### 2.7 Building a Labeled Relevance Set

A **labeled relevance set** is a list of `(query, relevant_doc_ids)` pairs created by human annotators (or bootstrapped from the corpus). It is the ground truth that all retrieval metrics are evaluated against.

**Steps to build one:**

1. **Sample representative queries** — cover common user intents, edge cases, and known failure modes.
2. **Identify relevant documents** — for each query, read the corpus and list every document that a correct answer would need to cite.
3. **Label relevance** — binary (relevant / not relevant) is sufficient for precision and recall; graded relevance (0/1/2) enables NDCG.
4. **Review for completeness** — a query might have more than one relevant document; recall cannot be measured if any are missed.
5. **Version control the set** — treat it as a test fixture; changes require review.

**Size guidance:** 20–50 queries covering the major intents is enough to detect the most impactful retrieval failures. Precision and recall estimates stabilise quickly once queries span all major document categories.

---

### 2.8 Evaluating Agents and Tool Use

Evaluating agents requires metrics beyond retrieval and generation because agents make sequential decisions, call tools, and accumulate state.

#### Trajectory Evaluation

An **agent trajectory** is the full sequence of steps an agent takes: `[(thought, tool_call, tool_result), ...]`. Trajectory evaluation checks whether the path to the answer was correct, not just whether the final answer was correct.

**Why trajectories matter:**

- An agent might reach the right answer via lucky guessing or an inefficient path.
- A trajectory that calls unnecessary tools wastes latency and money.
- A trajectory that skips a required tool (e.g., policy lookup before answering a leave question) may work today but fail on a harder variant.

#### Tool-Call Correctness

For each step in the trajectory, check:

| Check | Question |
|---|---|
| **Tool selection** | Did the agent call the right tool for this step? |
| **Argument correctness** | Were the arguments well-formed and semantically correct? |
| **Order** | Did tools get called in a sensible sequence? |
| **Redundancy** | Were any tools called unnecessarily? |

Tool-call correctness is typically evaluated against a **reference trajectory** — the ideal sequence of tool calls for a given task.

#### Task Success Rate

```
Task Success Rate = (number of tasks completed correctly) / (total tasks attempted)
```

A task is "completed correctly" when:
- The final answer matches the expected answer (exact match or semantic similarity).
- Required tool calls were made (if specified).
- No disallowed side effects occurred.

---

### 2.9 Common RAG Evaluation Pitfalls

| Pitfall | What goes wrong | Mitigation |
|---|---|---|
| **Evaluating only end-to-end accuracy** | Hides whether retrieval or generation is the bottleneck | Always measure retrieval and generation separately |
| **Labeled set built from the same corpus the retriever was tuned on** | Metrics look good but the system fails on real queries | Use held-out queries; include adversarial and out-of-distribution examples |
| **Ignoring position bias in precision** | Relevant doc at rank 5 counts the same as rank 1 in Precision@k | Supplement with MRR or NDCG for rank-sensitive analysis |
| **Using LLM-as-judge without calibration** | LLM judges vary by prompt; scores are not comparable across runs | Fix the judge model and prompt; report inter-annotator agreement on a sample |
| **Testing only happy-path queries** | Misses retrieval failures on edge cases (e.g., bereavement leave) | Seed the labeled set with known-hard queries that target every document category |

---

## 3. Hands-on Lab

**Location:** `labs/qa/day-10/`

### Setup

```bash
# From repo root
pip install -r labs/qa/day-10/requirements.txt
```

### Run the starter (with TODOs)

```bash
python labs/qa/day-10/starter.py
```

### Run the complete solution

```bash
python labs/qa/day-10/solution.py
```

Expected output includes:
- A per-query table of Context Precision@3 and Context Recall@3.
- A per-query faithfulness heuristic score.
- Clear flags for bug #2 (bereavement retrieval failure) and bug #1 (PTO faithfulness failure).
- An illustrative agent trajectory correctness check.

See `labs/qa/day-10/README.md` for full instructions.

---

## 4. Self-Check Quiz

**Q1.** You retrieve 3 documents for a query. 2 are relevant. What is Context Precision@3?

<details>
<summary>Show answer</summary>

2/3 ≈ 0.667. Two relevant docs out of three retrieved.

</details>

---

**Q2.** Your labeled set says a query has 4 relevant documents. Your retriever returns 3 of them in the top-5. What is Context Recall@5?

<details>
<summary>Show answer</summary>

3/4 = 0.75. Three of the four ground-truth relevant documents appear in the top-5 results.

</details>

---

**Q3.** An answer says "Acme employees get 30 days of parental leave." The retrieved context chunk says "Acme Corp provides 12 weeks of parental leave." Is this answer faithful?

<details>
<summary>Show answer</summary>

No. The answer states "30 days" which does not appear in the context. 12 weeks ≈ 84 days, not 30. The claim is not grounded in the retrieved context.

</details>

---

**Q4.** Why does Ragas use an LLM to compute Answer Relevancy rather than simple string matching?

<details>
<summary>Show answer</summary>

Answer Relevancy measures whether the answer addresses the intent of the question. That requires semantic understanding — a paraphrase of the question should score the same as the original. String matching cannot capture this; an LLM (or embedding similarity) is needed to measure semantic alignment.

</details>

---

**Q5.** You are evaluating an agent that helps users book time off. The final answer ("Your time off is booked") is correct, but the agent never called the `check_leave_balance` tool before booking. Is this a problem?

<details>
<summary>Show answer</summary>

Yes. Trajectory evaluation would flag the missing `check_leave_balance` call. The agent reached the right answer without verifying the user had sufficient leave — a latent failure mode that will surface when a user with no balance tries to book.

</details>

---

**Q6.** What is the difference between a Faithfulness score of 0.5 and an Answer Relevancy score of 0.5?

<details>
<summary>Show answer</summary>

Faithfulness 0.5 means half the claims in the answer are grounded in the retrieved context; the other half are hallucinated or unsupported. Answer Relevancy 0.5 means the answer is only partially on-topic — it may be responding to a related but different question than the one asked. Both are quality problems, but in different dimensions.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1. Can I achieve high Faithfulness and still have a wrong answer?**

<details>
<summary>Show answer</summary>

Yes, easily. Faithfulness only checks whether the answer is grounded in the *retrieved* context. If the retriever returned the wrong document (bug #2: parental-leave text for a bereavement query), the answer can be perfectly faithful to that wrong context and still be factually incorrect for the user's question. This is why retrieval and generation metrics must both be measured.

</details>

---

**Q2. Context Precision@k penalises irrelevant docs equally regardless of rank. Is that a problem?**

<details>
<summary>Show answer</summary>

It is a simplification. Precision@k treats rank 1 and rank k as equal, but an LLM reading a context window actually pays more attention to content at the beginning and end (the "lost-in-the-middle" effect). For rank-sensitive evaluation, use Mean Reciprocal Rank (MRR) or NDCG@k alongside Precision@k. For most practical RAG debugging, Precision@k and Recall@k together are sufficient to identify the root cause.

</details>

---

**Q3. Ragas requires an LLM to score Faithfulness. Which model should I use and does it matter?**

<details>
<summary>Show answer</summary>

Model choice matters significantly. Stronger models produce more reliable claim decomposition and entailment judgements. For production evaluation pipelines, use a capable model (e.g., claude-haiku-4-5 for cost efficiency, or a stronger model for high-stakes evals). Always fix the judge model version — changing it invalidates historical comparisons. Run a calibration check on 20–30 hand-labelled examples to verify the judge agrees with human judgement before treating Ragas scores as ground truth.

</details>

---

**Q4. How large does a labeled relevance set need to be to be statistically meaningful?**

<details>
<summary>Show answer</summary>

For retrieval metrics (Precision@k, Recall@k), 30–50 queries typically gives stable estimates if queries cover all major document categories and include both easy and hard cases. Statistical power matters more when metrics are close (e.g., comparing two retrievers at 0.72 vs 0.74 precision). In that case, use bootstrap confidence intervals over the query set. For LLM-assisted metrics like Faithfulness, the LLM's variance adds noise — averaging over at least 30 queries with 3 runs each provides more reliable estimates.

</details>

---

**Q5. What is the difference between trajectory evaluation and outcome evaluation for agents?**

<details>
<summary>Show answer</summary>

Outcome evaluation only asks: "Did the agent produce the correct final answer?" Trajectory evaluation additionally asks: "Did the agent take the right path to get there?" An agent can pass outcome evaluation by luck (guessing the right answer without reasoning) or by taking a roundabout path that happens to work. Trajectory evaluation catches these cases by comparing the agent's sequence of tool calls to a reference sequence. For safety-critical applications (medical, legal, financial), trajectory correctness is often as important as final answer correctness.

</details>

---

**Q6. My faithfulness heuristic (keyword matching) gives false negatives for paraphrased answers. How do I improve it?**

<details>
<summary>Show answer</summary>

Keyword matching is a lower bound — it catches only exact-match hallucinations. To catch paraphrases, use one of:
1. **Semantic similarity:** Embed each answer sentence and each context chunk; if no chunk is above a cosine threshold, flag the sentence.
2. **NLI model:** Use a natural language inference model (e.g., cross-encoder/nli-deberta-v3-small via sentence-transformers) to check entailment between each answer claim and the context.
3. **LLM-as-judge:** Ask an LLM to assess entailment — this is what Ragas does.

For Day 10, the heuristic is deliberately simple to run without an API key. The Ragas snippet in the lab shows the production-quality approach.

</details>

---

**Q7. How do I handle queries where multiple documents are all relevant (multi-hop questions)?**

<details>
<summary>Show answer</summary>

In multi-hop questions, the correct answer requires synthesising information from two or more documents. For retrieval evaluation:
- Label all required documents as relevant in your ground-truth set.
- Context Recall will correctly penalise a retriever that only finds one of the two needed documents.
- Context Precision will correctly penalise a retriever that retrieves irrelevant documents alongside the needed ones.

For generation evaluation, faithfulness becomes more complex because each claim may be grounded in a different context chunk. LLM-assisted Ragas handles this naturally by checking each claim against the full context list.

</details>

---

## 6. Further Reading

### Core Papers

- **RAGAS: Automated Evaluation of Retrieval Augmented Generation** (Es et al., 2023) — Defines the four core metrics and the LLM-assisted evaluation methodology. [arXiv:2309.15217](https://arxiv.org/abs/2309.15217)
- **ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems** (Saad-Falcon et al., 2023) — Alternative LLM-judge approach with statistical confidence intervals. [arXiv:2311.09476](https://arxiv.org/abs/2311.09476)
- **Lost in the Middle: How Language Models Use Long Contexts** (Liu et al., 2023) — Empirical study of position bias in LLM context reading. [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)
- **Trajectory Evaluation for LLM-Based Agents** — See the AgentBench paper (Liu et al., 2023) for agent trajectory benchmarking methodology. [arXiv:2308.03688](https://arxiv.org/abs/2308.03688)

### Documentation & Libraries

- [Ragas Documentation](https://docs.ragas.io) — Full API reference, metric definitions, and integration guides.
- [Ragas GitHub](https://github.com/explodinggradients/ragas) — Source code and examples.
- [Anthropic Evals Guide](https://docs.anthropic.com/en/docs/test-and-evaluate/eval-intro) — Evaluation best practices including LLM-as-judge patterns.

### Glossary Additions

| Term | Definition |
|---|---|
| **Context Precision@k** | Fraction of retrieved top-k documents that are relevant to the query; measures retrieval noise. *(Day 10)* |
| **Context Recall@k** | Fraction of ground-truth relevant documents that appear in the retriever's top-k output; measures retrieval coverage. *(Day 10)* |
| **Faithfulness** | Fraction of answer claims that are grounded in (entailed by) the retrieved context; a measure of hallucination absence. *(Day 10)* |
| **Answer Relevancy** | Semantic similarity between the original question and questions an LLM generates from the answer; measures on-topic alignment. *(Day 10)* |
| **Ragas** | Open-source Python framework for automated RAG evaluation using the four core metrics above. *(Day 10)* |
| **Labeled relevance set** | A test fixture mapping queries to ground-truth relevant document IDs, used to compute retrieval metrics. *(Day 10)* |
| **Trajectory evaluation** | Assessment of an agent's full sequence of reasoning and tool-call steps, not just its final answer. *(Day 10)* |
| **Tool-call correctness** | Whether an agent selected the right tool, with correct arguments, in the correct order for a given task. *(Day 10)* |
| **Task success rate** | Proportion of agent tasks completed with both correct final answer and correct tool-use behaviour. *(Day 10)* |
| **LLM-as-judge** | Using a language model to evaluate another model's output; requires calibration against human labels to be reliable. *(Day 10)* |

---

## 7. Key Takeaways

- **Always split retrieval and generation evaluation.** A single end-to-end accuracy number hides the root cause of failures.
- **Context Precision and Recall require a labeled relevance set** — there is no shortcut around annotating ground-truth relevant documents per query.
- **Faithfulness is the primary hallucination guard.** High faithfulness means the answer is grounded in what was retrieved; it does not guarantee the retrieved content was correct.
- **Ragas automates all four metrics** but requires an LLM for faithfulness and answer relevancy; local heuristics cover the retrieval half at zero API cost.
- **Agent evaluation must include trajectory correctness**, not just final answer correctness — a correct answer reached via the wrong tool sequence is a latent failure.
- **The five pitfalls** (end-to-end-only evaluation, in-distribution labeled sets, ignoring rank, uncalibrated LLM judges, happy-path-only queries) are the most common reasons RAG evaluation reports look good while production fails.
