# Day 9 — LLM-as-Judge: Automated Scoring When There Is No Ground Truth

## 1. Objectives

By the end of Day 9 you will be able to:

- Explain what LLM-as-judge is and why it matters for evaluating open-ended LLM outputs
- Distinguish the three judging modes: single-output rubric grading, pairwise comparison, and reference-based grading
- Design a good rubric — specific, non-overlapping criteria with clear scoring anchors
- Name and describe the four main biases (position/order, verbosity, self-preference, leniency) and apply practical mitigations
- Implement a deterministic mock judge and a real judge with calibrated rubric scoring
- Demonstrate position bias using pairwise comparison and mitigate it by swapping order and requiring agreement
- Articulate when LLM-as-judge is the right tool versus when deterministic checks are cheaper and more reliable
- Reason about cost trade-offs (judge model choice, batch size, call frequency)

---

## 2. Concept Reading

### 2.1 The Core Problem: No Reference Answer

On Days 6–8 you built failure taxonomies, assertion strategies, and an eval harness. Many of those checks were *deterministic* — you knew the expected answer and could compare it exactly (or fuzzily) to the model output.

But for open-ended questions — "explain our parental leave policy in plain language" — there is no single correct answer. Dozens of wordings are equally valid. Human labelling is accurate but expensive and slow. This is where **LLM-as-judge** enters: you prompt a capable LLM to evaluate the quality of another system's output against a rubric.

The pattern is:

```
[question] + [system_output] + [rubric] → judge LLM → {score, rationale}
```

Or for pairwise:

```
[question] + [output_A] + [output_B] + [criteria] → judge LLM → {winner, rationale}
```

### 2.2 Three Judging Modes

#### Mode 1 — Single-Output Rubric Grading
The judge receives one output and scores it against criteria (e.g. 1–5 per dimension). Best for: regression testing a single pipeline, tracking quality over time, CI gates.

**Rubric example (HR assistant, 3 criteria):**

| Criterion | 1 (Poor) | 3 (Acceptable) | 5 (Excellent) |
|---|---|---|---|
| **Groundedness** | Fabricates facts not in the retrieved context | Mostly uses context but adds minor unsupported claims | Every factual claim is traceable to retrieved text |
| **Completeness** | Misses the main point of the question | Covers the main point, omits some detail | Covers all key points the question asked for |
| **On-topic** | Answers a different question entirely | Partially addresses the question | Precisely addresses what was asked |

**Composite score** = mean of criteria scores, or weighted if some criteria matter more.

#### Mode 2 — Pairwise Comparison
The judge sees two outputs (A and B) and picks the winner (or declares a tie). Best for: A/B testing two versions of a prompt or pipeline; generating preference data for RLHF.

**Critical vulnerability:** position/order bias. Judges tend to prefer whichever output they saw first. Mitigation: always run both orderings (A vs B, then B vs A) and only accept a result when both agree.

#### Mode 3 — Reference-Based Grading
A ground-truth reference answer is included in the judge prompt. The judge compares the candidate answer to the reference rather than scoring in a vacuum. Best for: when you have a curated golden set (built from human annotations or domain expert review).

Reference-based grading reduces leniency bias because the judge can anchor on a known-good answer.

### 2.3 Designing Good Rubrics

A rubric is the most important input you control. Common mistakes:

1. **Overlapping criteria** — "relevance" and "on-topic" measure the same thing. One inflates the other.
2. **Vague anchors** — "good" vs "bad" with no specifics forces the judge to invent thresholds.
3. **Too many criteria** — beyond 5–6 dimensions, judges lose reliability on each dimension.
4. **No output format instruction** — without a structured output requirement (JSON with keys per criterion), rationale and score get tangled.

**Good rubric prompt structure:**

```
You are evaluating an AI assistant's answer to a user question.
Score the answer on each criterion from 1 (poor) to 5 (excellent).
Return ONLY valid JSON: {"groundedness": <1-5>, "completeness": <1-5>, "on_topic": <1-5>, "rationale": "<one sentence per criterion>"}

Question: {question}
Answer: {answer}
Context (retrieved passages): {context}
```

### 2.4 Known Biases and Mitigations

#### Position / Order Bias
**What it is:** In pairwise comparison, the judge systematically favours the first or second answer it reads, independent of actual quality.

**Mitigation:** Run both orderings. Accept the verdict only when both agree. If they disagree, call it a tie or escalate to human review.

```python
result_ab = judge_pairwise(question, answer_a, answer_b)  # A presented first
result_ba = judge_pairwise(question, answer_b, answer_a)  # B presented first

if result_ab["winner"] == "A" and result_ba["winner"] == "B":
    # Agreement (both say A): consistent
    final = "A"
elif result_ab["winner"] == "B" and result_ba["winner"] == "A":
    # Agreement (both say B): consistent
    final = "B"
else:
    # Flip — position bias detected; call it a tie
    final = "tie"
```

#### Verbosity Bias
**What it is:** Judges rate longer, more verbose answers higher even when extra length adds no information.

**Mitigation:** Include an instruction in the rubric: *"Length alone does not indicate quality. Score only information value, not word count."* You can also normalise — strip markdown and whitespace before presenting to the judge.

#### Self-Preference Bias
**What it is:** A judge model prefers outputs generated by the same model family. GPT-4o-as-judge may favour GPT-4o outputs; Claude-as-judge may favour Claude outputs.

**Mitigation:** Use a judge from a *different* model family when evaluating a specific system, or use two judges from different families and require agreement.

#### Leniency Bias
**What it is:** Judges tend to award scores above the midpoint even for mediocre outputs; the score distribution clusters around 4/5 rather than being spread across the full range.

**Mitigation:** (1) Add explicit negative examples to the rubric ("a score of 1 looks like…"). (2) Use reference-based grading to anchor the 5/5 tier. (3) Calibrate the judge against a small set of human-labelled examples.

### 2.5 Calibration Against Human Labels

Calibration is the process of measuring how closely the judge's scores match human-assigned scores on the same set of examples.

**Process:**
1. Collect 20–50 question-answer pairs.
2. Have 2–3 humans independently score each pair with the same rubric.
3. Compute inter-annotator agreement (Cohen's κ or Pearson r) as the human ceiling.
4. Run the LLM judge on the same pairs.
5. Compute judge-human agreement and compare to the ceiling.

A well-calibrated judge should achieve ≥ 0.7 correlation with human scores on the rubric dimensions. If not, the rubric needs refinement (clearer anchors, fewer criteria) or the judge model needs to be upgraded.

### 2.6 When LLM-as-Judge Is and Is Not Appropriate

#### Use LLM-as-judge when:
- The output space is open-ended (free-text, creative, explanatory) with no single correct answer
- Human review at scale is cost-prohibitive
- You need to compare two pipelines or prompt versions systematically
- You are tracking quality regression over time and want a fast signal

#### Prefer deterministic checks when:
- You have an exact expected value (JSON field, number, code output, regex pattern)
- The check is safety-critical — deterministic assertions never hallucinate
- Latency matters — a regex runs in microseconds; a judge call takes 0.5–2 seconds
- You already tested for this property with a deterministic harness

**Rule of thumb:** deterministic first, LLM-as-judge for what deterministic checks cannot reach.

### 2.7 Cost Considerations

Every judge call is a paid API call. At scale this adds up quickly.

| Factor | Impact | Mitigation |
|---|---|---|
| Judge model tier | GPT-4o/Claude Sonnet = expensive | Use a smaller judge (Haiku, gpt-5-mini) for regression; reserve large models for calibration |
| Token count per call | Long rubric + long answer = more tokens | Cap answer length before judging; use concise rubrics |
| Call frequency | Every build in CI | Gate judge calls behind a cheaper filter; run only on failing builds or nightly |
| Pairwise duplication | Order-swap mitigation = 2× calls | Accept this cost as insurance against bias; or run single-pass and accept lower confidence |

A practical approach: use a cheap judge for continuous CI; use a strong judge for weekly regression snapshots and for calibrating the cheap judge.

---

## 3. Hands-on Lab

**Lab directory:** `labs/qa/day-09/`

### Setup
```bash
cd /path/to/AI_Training
python -m venv .venv && source .venv/bin/activate   # if not already active
pip install -r labs/qa/day-09/requirements.txt
```

### Run the starter (with TODOs)
```bash
python labs/qa/day-09/starter.py
```

The starter will fail with `NotImplementedError` or produce placeholder output — fill in the TODO blocks.

### Run the complete solution
```bash
# No API key required — uses the deterministic mock judge
python labs/qa/day-09/solution.py

# With a real judge (optional — requires ANTHROPIC_API_KEY in .env)
ANTHROPIC_API_KEY=sk-ant-... python labs/qa/day-09/solution.py
```

**What you will build:**
1. A `MockJudge` that applies a grounded/complete/on-topic rubric deterministically (no API key)
2. A `score_single()` function that returns `{score, rationale}` per criterion
3. A `compare_pairwise()` function that detects position bias by swapping A/B order
4. A `mitigate_position_bias()` function that requires agreement across both orderings
5. An optional `RealJudge` that calls `claude-haiku-4-5` when an API key is present

---

## 4. Self-Check Quiz

Answer each question before revealing the answers below.

**1.** What problem does LLM-as-judge solve that deterministic assertion strategies cannot?

<details>
<summary>Show answer</summary>

Deterministic assertions require a known expected value; for open-ended text outputs — where many valid wordings exist — there is no single correct answer to compare against. LLM-as-judge can evaluate quality across subjective dimensions (fluency, completeness, groundedness) without needing an exact reference.

</details>

**2.** Name the three LLM-as-judge modes and give one use case for each.

<details>
<summary>Show answer</summary>

(1) *Single-output rubric grading* — CI regression check on a RAG pipeline's answer quality. (2) *Pairwise comparison* — A/B testing two prompt templates to see which produces better answers. (3) *Reference-based grading* — scoring generated answers against a domain expert's golden reference.

</details>

**3.** What is position bias, and how do you detect it?

<details>
<summary>Show answer</summary>

The judge systematically prefers whichever candidate it saw first in the prompt. Detect it by running pairwise comparison in both orders (A vs B, then B vs A) — if the winner changes when order changes, position bias is present.

</details>

**4.** Why is verbosity bias a problem, and how does the rubric help?

<details>
<summary>Show answer</summary>

Judges inflate scores for longer answers even when the extra length is padding, not information. A rubric that explicitly says "length alone does not indicate quality" and anchors scoring on information value corrects this.

</details>

**5.** When should you choose a deterministic assertion over LLM-as-judge?

<details>
<summary>Show answer</summary>

When you can extract an exact expected value (a number, a JSON field, a code output, a regex match), or when the check is safety-critical. Deterministic checks are faster, cheaper, and cannot hallucinate false passes.

</details>

**6.** What does calibration measure, and what is a reasonable target?

<details>
<summary>Show answer</summary>

Calibration measures the correlation between the judge's scores and human scores on the same examples. A correlation ≥ 0.7 (Pearson r) between judge and human labels is a commonly used threshold for a reliable automated judge.

</details>

**7.** How does reference-based grading mitigate leniency bias?

<details>
<summary>Show answer</summary>

The judge is anchored on a known-good reference answer; the 5/5 tier is explicitly defined by that reference rather than by the judge's internal prior. Without a reference, the judge has no external anchor and tends to be generous.

</details>

**8.** Describe two cost strategies for running LLM-as-judge in a CI pipeline.

<details>
<summary>Show answer</summary>

(1) Use a small, cheap judge model (e.g. Haiku) for every build and reserve the stronger model for weekly calibration snapshots. (2) Gate judge calls: only trigger LLM-as-judge when a cheaper deterministic check fails, reducing the volume of judge calls.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1: What makes LLM-as-judge fundamentally different from the eval harness built in Day 8?**

<details>
<summary>Show answer</summary>

The Day 8 harness relied on deterministic assertions — regex, exact string match, schema checks, keyword presence. These have no uncertainty and cannot hallucinate a pass. LLM-as-judge introduces a *probabilistic* scoring step: the judge itself can be wrong, biased, or inconsistent. This means you must calibrate the judge, monitor its agreement with humans, and treat its scores as noisy estimates rather than ground truth. The tradeoff is the ability to evaluate dimensions (tone, completeness, nuance) that are genuinely impossible to capture with a regex.

</details>

**Q2: How does self-preference bias interact with the choice of judge model?**

<details>
<summary>Show answer</summary>

If you use Claude Sonnet as your judge and your system under test also calls Claude, the judge will tend to rate its own family's outputs more favourably — the same training data, RLHF signal, and style conventions produce mutual preference. The most straightforward mitigation is to use a different model family as judge. If that is not possible (e.g. policy constrains you to one provider), use a model from a different size tier and add explicit rubric instructions to score the content, not the style.

</details>

**Q3: Can a small judge model (e.g. Haiku) reliably evaluate a complex rubric?**

<details>
<summary>Show answer</summary>

For simple, concrete criteria (on-topic: yes/no; contains a number: yes/no) a small model works well. As rubric complexity increases — especially for criteria requiring world knowledge or nuanced reasoning (e.g. "Is this advice legally sound?") — small models become unreliable. The practical strategy is: use a small model for shallow criteria (completeness, format) in CI, and a larger model for nuanced criteria (accuracy, legal correctness) in periodic deep audits. Always calibrate both against human labels on the same set to quantify the reliability gap.

</details>

**Q4: In pairwise comparison, what if both orderings return "tie"? Is that valid?**

<details>
<summary>Show answer</summary>

Yes, ties are valid outcomes — they mean the judge considers the outputs roughly equivalent on the criteria. Ties should not be treated as position bias unless you see a systematic pattern where the judge returns a tie whenever it would otherwise flip. In practice, a high tie rate (> 40%) may indicate the rubric criteria are too coarse to discriminate, or the two candidates genuinely are similar and you need a more sensitive rubric.

</details>

**Q5: How would you scale LLM-as-judge to evaluate thousands of outputs per day?**

<details>
<summary>Show answer</summary>

(1) Batch calls — group multiple question-answer pairs into a single prompt (structured JSON array) when the judge model supports it; reduces per-call overhead. (2) Cache deterministic subsets — if the question and answer are identical to a prior run, reuse the cached score. (3) Sample rather than evaluate every output — randomly sample 5–10% and run the judge on that subset; use the sample score as a proxy for the full population. (4) Tier by risk — always judge high-stakes queries (PII-adjacent, policy questions) and sample low-stakes ones.

</details>

**Q6: What is the relationship between rubric design and inter-annotator agreement?**

<details>
<summary>Show answer</summary>

Poor rubrics produce low inter-annotator agreement even among humans, because annotators have to interpret vague anchors differently. Before running an LLM judge, you should verify that humans can apply the rubric consistently (target κ > 0.6). If humans disagree, the rubric itself is the problem — not the judge model. Fixing rubric clarity (explicit anchors, examples of 1/3/5 scores) improves both human agreement and judge calibration simultaneously.

</details>

**Q7: Is it valid to use the same model as both the system under test and the judge?**

<details>
<summary>Show answer</summary>

Technically possible but methodologically weak due to self-preference bias. It is acceptable as a *development-time* proxy (fast, cheap iteration loop) as long as you validate key claims with a different-family judge before treating results as trustworthy. In production evaluations, a same-family judge should be explicitly flagged as potentially biased in any report.

</details>

**Q8: How does LLM-as-judge relate to RLHF?**

<details>
<summary>Show answer</summary>

RLHF trains a reward model on human preference labels, then uses that reward model to fine-tune a policy model. LLM-as-judge is effectively replacing the human labellers with a strong LLM for the preference-ranking step — this is sometimes called RLAIF (Reinforcement Learning from AI Feedback). The key difference is that a reward model trained from human labels is a specialised discriminator, while an LLM judge is a general-purpose model prompted to act as a discriminator. RLAIF scales better but accumulates the biases of the judge model rather than human annotation noise.

</details>

---

## 6. Further Reading

### Core Papers
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. arXiv:2306.05685 — the foundational empirical study of LLM judging modes and biases.
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. arXiv:2305.17926 — systematic analysis of position and verbosity biases.
- Lee, H. et al. (2023). *RLAIF: Scaling Reinforcement Learning from Human Feedback with AI Feedback*. arXiv:2309.00267 — using LLM-as-judge to replace human annotators for RLHF.
- Bai, Y. et al. (2022). *Constitutional AI: Harmlessness from AI Feedback*. arXiv:2212.08073 — Anthropic's approach using an AI judge for safety alignment.

### Documentation & Libraries
- [RAGAS framework](https://docs.ragas.io/) — automated RAG evaluation including LLM-based faithfulness and answer relevance scoring.
- [DeepEval](https://docs.confident-ai.com/) — open-source LLM evaluation framework with built-in judge metrics (G-Eval, faithfulness, hallucination).
- [promptfoo](https://promptfoo.dev/docs/intro) — provider-flexible LLM testing framework with LLM-as-judge support.
- [Anthropic Models Overview](https://docs.anthropic.com/en/docs/about-claude/models/overview) — current model list; use `claude-haiku-4-5` for cost-efficient judging.

### Glossary Additions

| Term | Definition |
|---|---|
| **LLM-as-judge** | Using a capable LLM to score or rank outputs of another model against a rubric, in place of or alongside human evaluators. *(Day 9)* |
| **rubric** | A set of named, explicitly anchored criteria used to evaluate open-ended outputs; each criterion has a defined scale (e.g. 1–5) with descriptions of what each level looks like. *(Day 9)* |
| **position bias** | The tendency of an LLM judge to prefer whichever output it encountered first in a pairwise prompt, independent of actual quality. *(Day 9)* |
| **verbosity bias** | The tendency of an LLM judge to rate longer answers higher regardless of their actual information value. *(Day 9)* |
| **self-preference bias** | The tendency of an LLM judge to rate outputs from its own model family more favourably than equivalent outputs from other families. *(Day 9)* |
| **leniency bias** | The tendency of an LLM judge to assign scores above the midpoint of the scale even for mediocre outputs; score distributions skew high. *(Day 9)* |
| **calibration** | Measuring judge-human score agreement (e.g. Pearson r) on a shared labelled set; a calibrated judge tracks human judgement within acceptable error bounds. *(Day 9)* |
| **RLAIF** | Reinforcement Learning from AI Feedback — using an LLM judge to generate preference labels for RL training, scaling the RLHF process without human annotators. *(Day 9)* |
| **pairwise comparison** | An LLM-as-judge mode where two candidate outputs are presented side-by-side and the judge selects the better one or declares a tie. *(Day 9)* |
| **reference-based grading** | An LLM-as-judge mode that includes a ground-truth reference answer so the judge can anchor scores against a known-good example. *(Day 9)* |

---

## 7. Key Takeaways

1. **LLM-as-judge fills the gap** where deterministic assertions cannot reach — open-ended text where many valid answers exist and human review at scale is impractical.
2. **Three modes** serve different purposes: single-output rubric grading for regression tracking, pairwise comparison for A/B testing, reference-based grading when golden answers exist.
3. **Rubric quality is the lever you control** — specific anchors, non-overlapping criteria, and explicit output format instructions are the biggest drivers of judge reliability.
4. **Four biases are well-documented** — position/order, verbosity, self-preference, and leniency — each has a practical mitigation that belongs in your evaluation harness.
5. **Calibrate before you trust** — always validate a new judge against human labels on a sample set; target ≥ 0.7 correlation before using scores to gate deployments.
6. **Deterministic checks come first** — LLM-as-judge is the tool of last resort for dimensions that cannot be checked deterministically; use both in combination.
7. **Cost is a first-class constraint** — choose judge model tier by risk level, cache repeated evaluations, and sample rather than evaluate exhaustively at scale.
