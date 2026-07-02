"""
Day 9 Lab — LLM-as-Judge Scorer  (starter.py)
================================================
Fill in every block marked TODO.  Run with:
    python labs/qa/day-09/starter.py

No API key required — the MockJudge runs everything deterministically.
Optional: set ANTHROPIC_API_KEY in your environment to activate the real judge path.
"""

from __future__ import annotations

import json
import os
import sys
import pathlib
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# SUT import — do not modify
# ---------------------------------------------------------------------------
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))
from hr_assistant import answer  # noqa: E402


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CriterionScore:
    """Score and rationale for a single rubric criterion."""
    name: str
    score: int          # 1–5
    rationale: str


@dataclass
class JudgeResult:
    """Result from scoring a single answer against the rubric."""
    question: str
    answer: str
    criteria: list[CriterionScore] = field(default_factory=list)

    @property
    def composite_score(self) -> float:
        """Mean score across all criteria."""
        if not self.criteria:
            return 0.0
        return sum(c.score for c in self.criteria) / len(self.criteria)


@dataclass
class PairwiseResult:
    """Result from a single pairwise comparison run."""
    question: str
    winner: str          # "A", "B", or "tie"
    rationale: str
    order: str           # "AB" or "BA" — which was presented first


# ---------------------------------------------------------------------------
# RUBRIC DEFINITION (shared by mock and real judge)
# ---------------------------------------------------------------------------

RUBRIC = """
Score the answer on each criterion from 1 (poor) to 5 (excellent).

Criteria:
  groundedness : Every factual claim is traceable to the retrieved context.
                 1 = fabricates facts; 3 = mostly grounded, minor gaps; 5 = fully grounded.
  completeness : Covers all key points the question asked for.
                 1 = misses the main point; 3 = covers main point, omits details; 5 = covers all key points.
  on_topic     : Precisely addresses what was asked.
                 1 = answers a different question; 3 = partially on-topic; 5 = precisely on-topic.

Length alone does NOT indicate quality. Score information value only.
""".strip()


# ---------------------------------------------------------------------------
# SECTION 1 — MockJudge (deterministic, no API key)
# ---------------------------------------------------------------------------

class MockJudge:
    """
    Deterministic judge that applies keyword-based heuristics to score answers.
    Designed so that the HR assistant's seeded faithfulness bug (PTO hallucination)
    receives a low groundedness score.

    You do NOT need to modify this class — study it to understand how the
    real judge will use the same RUBRIC string.
    """

    # Keywords that signal the answer is NOT grounded in the context
    _HALLUCINATION_SIGNALS = [
        ("20 days", "15 days"),   # Issue #1: SUT says 20, corpus says 15 for new employees
    ]

    def score_single(self, question: str, sut_answer: str, context: list[str]) -> JudgeResult:
        """Score a single answer against the rubric using deterministic heuristics."""
        context_text = " ".join(context).lower()
        answer_lower = sut_answer.lower()

        # --- groundedness ---
        grounded_score = 5
        grounded_rationale = "All claims appear traceable to retrieved context."
        for (hallucinated, actual) in self._HALLUCINATION_SIGNALS:
            if hallucinated in sut_answer and actual in context_text:
                grounded_score = 2
                grounded_rationale = (
                    f"Answer states '{hallucinated}' but context shows '{actual}' — "
                    "partially grounded, contains factual mismatch."
                )
                break

        # --- completeness ---
        # Heuristic: very short answers are likely incomplete
        word_count = len(sut_answer.split())
        if word_count < 10:
            complete_score = 1
            complete_rationale = "Answer is too brief to cover key points."
        elif "tier" in context_text and "tier" not in answer_lower and "years" not in answer_lower:
            complete_score = 2
            complete_rationale = "Omits tiered accrual structure present in the source context."
        else:
            complete_score = 4
            complete_rationale = "Covers the main points adequately."

        # --- on_topic ---
        # Heuristic: check that at least one noun from the question appears in the answer
        question_words = set(question.lower().split()) - {"what", "how", "is", "the", "a", "an",
                                                           "do", "does", "many", "are", "get",
                                                           "can", "i", "we", "?"}
        overlap = question_words & set(answer_lower.split())
        if len(overlap) >= 2:
            topic_score = 4
            topic_rationale = "Answer addresses the question topic directly."
        elif len(overlap) == 1:
            topic_score = 3
            topic_rationale = "Answer partially addresses the question."
        else:
            topic_score = 2
            topic_rationale = "Answer may not address the specific question asked."

        return JudgeResult(
            question=question,
            answer=sut_answer,
            criteria=[
                CriterionScore("groundedness", grounded_score, grounded_rationale),
                CriterionScore("completeness", complete_score, complete_rationale),
                CriterionScore("on_topic", topic_score, topic_rationale),
            ],
        )

    def compare_pairwise(
        self,
        question: str,
        answer_first: str,
        answer_second: str,
        label_first: str = "A",
        label_second: str = "B",
    ) -> PairwiseResult:
        """
        Compare two answers.  The mock deliberately exhibits position bias:
        it favours the FIRST answer when both are non-trivial and scores are tied.
        This is intentional — it lets learners observe bias and then mitigate it.
        """
        # Score each answer (we reuse score_single with empty context for pairwise)
        result_first = self.score_single(question, answer_first, [])
        result_second = self.score_single(question, answer_second, [])

        score_first = result_first.composite_score
        score_second = result_second.composite_score

        margin = score_first - score_second

        if margin > 0.5:
            winner = label_first
            rationale = f"{label_first} scores {score_first:.1f} vs {label_second} {score_second:.1f} — clear winner."
        elif margin < -0.5:
            winner = label_second
            rationale = f"{label_second} scores {score_second:.1f} vs {label_first} {score_first:.1f} — clear winner."
        else:
            # TIE on scores — mock ALWAYS picks the first-presented answer (position bias)
            winner = label_first
            rationale = (
                f"Scores nearly equal ({score_first:.1f} vs {score_second:.1f}). "
                f"Defaulting to {label_first} (presented first) — position bias in action."
            )

        order = f"{label_first}{label_second}"
        return PairwiseResult(question=question, winner=winner, rationale=rationale, order=order)


# ---------------------------------------------------------------------------
# SECTION 2 — TODO: score_single wrapper
# ---------------------------------------------------------------------------

def run_single_scoring(judge: MockJudge) -> None:
    """
    TODO (1/3): Run the SUT on a question that triggers the faithfulness bug
    (PTO/vacation days), then score the result with the mock judge.

    Steps:
    a) Call answer("How many PTO days do new employees get?") to get sut_result.
    b) Extract sut_result["answer"] and sut_result["contexts"].
    c) Call judge.score_single(question, sut_answer, contexts) to get a JudgeResult.
    d) Print the composite score and each criterion's score + rationale.

    Expected output shows groundedness ≤ 2 because the SUT states 20 days
    but the corpus says 15 days for employees with 0–2 years of service.
    """
    print("\n=== SINGLE-OUTPUT SCORING ===")

    question = "How many PTO days do new employees get?"

    # TODO (a): call the SUT
    # sut_result = answer(...)

    # TODO (b): extract answer and contexts
    # sut_answer = ...
    # contexts = ...

    # TODO (c): score with the judge
    # result = judge.score_single(...)

    # TODO (d): print results
    # print(f"Question: {question}")
    # print(f"SUT Answer: {sut_answer}")
    # print(f"Composite Score: {result.composite_score:.1f}/5.0")
    # print("Rationale per criterion:")
    # for c in result.criteria:
    #     print(f"  {c.name:<14} [{c.score}/5]: {c.rationale}")

    raise NotImplementedError("Fill in TODO blocks in run_single_scoring()")


# ---------------------------------------------------------------------------
# SECTION 3 — TODO: pairwise comparison and position-bias demo
# ---------------------------------------------------------------------------

def run_pairwise_bias_demo(judge: MockJudge) -> None:
    """
    TODO (2/3): Demonstrate position bias using pairwise comparison.

    Use two SIMILARLY-SCORED answers (both claim '20 days' — partially wrong)
    so the mock judge's scores are nearly tied and position bias triggers.
    When scores are tied the mock always picks the first-presented answer,
    so the winner will flip when you swap the order.

    Steps:
    a) Define answer_a and answer_b as the literal strings below.
    b) Run judge.compare_pairwise(question, answer_a, answer_b, "A", "B")
       — A is presented first.
    c) Run judge.compare_pairwise(question, answer_b, answer_a, "B", "A")
       — B is presented first (order swapped).
    d) Print both results. Check whether the winner changed — if it did,
       print a "POSITION BIAS DETECTED" message.

    answer_a = (
        "According to company policy, employees receive 20 days of PTO annually "
        "starting from their first year."
    )
    answer_b = (
        "The company provides 20 paid vacation days per year to all employees "
        "beginning on their start date."
    )
    """
    print("\n=== PAIRWISE COMPARISON — POSITION BIAS DEMO ===")

    question = "What is the PTO policy for new employees?"

    # TODO (a): define two similar-quality answers (copy from docstring above)
    # answer_a = ...
    # answer_b = ...

    # TODO (b): run order A→B (A first)
    # result_ab = judge.compare_pairwise(question, answer_a, answer_b, "A", "B")
    # print(f"Order A→B (A first): winner = {result_ab.winner}")
    # print(f"  Rationale: {result_ab.rationale}")

    # TODO (c): run order B→A (B first — swap)
    # result_ba = judge.compare_pairwise(question, answer_b, answer_a, "B", "A")
    # print(f"Order B→A (B first): winner = {result_ba.winner}")
    # print(f"  Rationale: {result_ba.rationale}")

    # TODO (d): detect bias
    # if result_ab.winner != result_ba.winner:
    #     print("  *** POSITION BIAS DETECTED: winner flipped on order swap ***")
    # else:
    #     print("  Consistent: same winner regardless of order.")

    raise NotImplementedError("Fill in TODO blocks in run_pairwise_bias_demo()")


# ---------------------------------------------------------------------------
# SECTION 4 — TODO: position-bias mitigation
# ---------------------------------------------------------------------------

def mitigate_position_bias(
    judge: MockJudge,
    question: str,
    answer_a: str,
    answer_b: str,
) -> str:
    """
    TODO (3/3): Implement agreement-based position-bias mitigation.

    Algorithm:
    1. Run compare_pairwise(question, answer_a, answer_b, "A", "B")  → result_ab
    2. Run compare_pairwise(question, answer_b, answer_a, "B", "A")  → result_ba
    3. If result_ab says "A" won AND result_ba says "A" won → final = "A"
       If result_ab says "B" won AND result_ba says "B" won → final = "B"
       Otherwise → final = "tie"  (disagreement between orders = position bias)
    4. Return the final verdict string ("A", "B", or "tie").

    NOTE: In result_ba the labels are swapped — "B" is presented first.
    When result_ba.winner == "B" that means the judge chose the answer
    that was B in the original labelling.
    """
    # TODO: implement and return the final verdict
    raise NotImplementedError("Fill in mitigate_position_bias()")


def run_mitigation_demo(judge: MockJudge) -> None:
    """Calls mitigate_position_bias and prints the result."""
    print("\n=== POSITION BIAS MITIGATION ===")

    question = "What is the PTO policy for new employees?"
    answer_a = (
        "New employees (0–2 years of service) accrue 15 days of PTO per year "
        "according to the tiered schedule. The rate increases to 20 days at year 3."
    )
    answer_b = "Employees get some paid time off."

    verdict = mitigate_position_bias(judge, question, answer_a, answer_b)
    print(f"Final verdict after order-swap mitigation: {verdict}")
    if verdict == "tie":
        print("  (Judges disagreed across orderings — calling it a tie)")
    else:
        print(f"  (Both orderings agreed: {verdict} is the better answer)")


# ---------------------------------------------------------------------------
# SECTION 5 — Optional real judge (claude-haiku-4-5)
# ---------------------------------------------------------------------------

def run_real_judge() -> None:
    """
    Optional: uses claude-haiku-4-5 as the judge when ANTHROPIC_API_KEY is set.
    This section is complete — no TODO required.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("\n=== REAL JUDGE (optional) ===")
        print("  Skipped — ANTHROPIC_API_KEY not set.")
        print("  Set the key to activate the claude-haiku-4-5 judge path.")
        return

    try:
        import anthropic
    except ImportError:
        print("\n=== REAL JUDGE (optional) ===")
        print("  Skipped — anthropic package not installed.")
        print("  pip install anthropic  (or uncomment it in requirements.txt)")
        return

    print("\n=== REAL JUDGE (claude-haiku-4-5) ===")
    question = "How many PTO days do new employees get?"
    sut_result = answer(question)
    sut_answer = sut_result["answer"]
    contexts = sut_result.get("contexts", [])
    context_block = "\n".join(f"- {c}" for c in contexts)

    prompt = f"""You are evaluating an AI assistant's answer to a user question.

{RUBRIC}

Return ONLY valid JSON with this exact schema:
{{
  "groundedness": <integer 1-5>,
  "completeness": <integer 1-5>,
  "on_topic": <integer 1-5>,
  "rationale": {{
    "groundedness": "<one sentence>",
    "completeness": "<one sentence>",
    "on_topic": "<one sentence>"
  }}
}}

Question: {question}
Answer: {sut_answer}
Retrieved context:
{context_block}
"""

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()

    try:
        data = json.loads(raw)
        scores = {k: data[k] for k in ("groundedness", "completeness", "on_topic")}
        composite = sum(scores.values()) / len(scores)
        print(f"Composite: {composite:.1f}/5.0")
        for criterion, score in scores.items():
            rationale = data.get("rationale", {}).get(criterion, "")
            print(f"  {criterion:<14} [{score}/5]: {rationale}")
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"  Could not parse judge response ({exc}): {raw}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    judge = MockJudge()
    run_single_scoring(judge)
    run_pairwise_bias_demo(judge)
    run_mitigation_demo(judge)
    run_real_judge()
