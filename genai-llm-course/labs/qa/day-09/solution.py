"""
Day 9 Lab — LLM-as-Judge Scorer  (solution.py)
================================================
Complete reference implementation.  Run with:
    python labs/qa/day-09/solution.py

No API key required — the MockJudge is fully deterministic.
Optional: set ANTHROPIC_API_KEY in your environment (or .env) to activate
the claude-haiku-4-5 real-judge path.
"""

from __future__ import annotations

import json
import os
import sys
import pathlib
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Load .env if python-dotenv is available (graceful fallback)
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # no dotenv — rely on environment variables set manually

# ---------------------------------------------------------------------------
# SUT import
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
        if not self.criteria:
            return 0.0
        return sum(c.score for c in self.criteria) / len(self.criteria)


@dataclass
class PairwiseResult:
    """Result from a single pairwise comparison run."""
    question: str
    winner: str          # "A", "B", or "tie"
    rationale: str
    order: str           # e.g. "AB" or "BA" — which label was presented first


# ---------------------------------------------------------------------------
# RUBRIC (shared by mock and real judge)
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
# MockJudge — deterministic, no API key required
# ---------------------------------------------------------------------------

class MockJudge:
    """
    Deterministic judge implementing rubric scoring via keyword heuristics.

    Key behaviours:
    - Detects the HR assistant's seeded PTO hallucination (states 20 days when
      the corpus says 15 days for 0-2 year employees) → groundedness = 2.
    - In pairwise comparison, when scores are tied the mock ALWAYS picks the
      first-presented answer — deliberately demonstrating position bias.
    """

    _HALLUCINATION_SIGNALS = [
        ("20 days", "15 days"),
    ]

    # ------------------------------------------------------------------ #
    # Single-output scoring                                                #
    # ------------------------------------------------------------------ #

    def score_single(self, question: str, sut_answer: str, context: list[str]) -> JudgeResult:
        """Score one SUT answer against the rubric."""
        context_text = " ".join(context).lower()
        answer_lower = sut_answer.lower()

        # -- groundedness --
        grounded_score = 5
        grounded_rationale = "All claims appear traceable to retrieved context."
        for (hallucinated, actual) in self._HALLUCINATION_SIGNALS:
            if hallucinated in sut_answer and actual in context_text:
                grounded_score = 2
                grounded_rationale = (
                    f"Answer states '{hallucinated}' but context shows '{actual}' for "
                    "new employees — factual mismatch, partially grounded."
                )
                break

        # -- completeness --
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

        # -- on_topic --
        stop_words = {"what", "how", "is", "the", "a", "an", "do", "does", "many",
                      "are", "get", "can", "i", "we", "?", "our"}
        question_words = set(question.lower().split()) - stop_words
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

    # ------------------------------------------------------------------ #
    # Pairwise comparison (with deliberate position bias)                  #
    # ------------------------------------------------------------------ #

    def compare_pairwise(
        self,
        question: str,
        answer_first: str,
        answer_second: str,
        label_first: str = "A",
        label_second: str = "B",
    ) -> PairwiseResult:
        """
        Compare two answers.  Position bias is deliberately present:
        when scores are tied (within 0.5), the first-presented answer wins.
        """
        result_first = self.score_single(question, answer_first, [])
        result_second = self.score_single(question, answer_second, [])

        s1 = result_first.composite_score
        s2 = result_second.composite_score
        margin = s1 - s2

        if margin > 0.5:
            winner = label_first
            rationale = (
                f"{label_first} scores {s1:.1f} vs {label_second} {s2:.1f} "
                f"— clear winner on rubric."
            )
        elif margin < -0.5:
            winner = label_second
            rationale = (
                f"{label_second} scores {s2:.1f} vs {label_first} {s1:.1f} "
                f"— clear winner on rubric."
            )
        else:
            # Tie on scores → position bias: pick whoever was listed first
            winner = label_first
            rationale = (
                f"Scores nearly equal ({s1:.1f} vs {s2:.1f}). "
                f"Defaulting to {label_first} (presented first) — POSITION BIAS."
            )

        return PairwiseResult(
            question=question,
            winner=winner,
            rationale=rationale,
            order=f"{label_first}{label_second}",
        )


# ---------------------------------------------------------------------------
# Agreement-based position-bias mitigation
# ---------------------------------------------------------------------------

def mitigate_position_bias(
    judge: MockJudge,
    question: str,
    answer_a: str,
    answer_b: str,
) -> tuple[str, PairwiseResult, PairwiseResult]:
    """
    Run pairwise comparison in both orderings and require agreement.

    Returns (verdict, result_ab, result_ba) where verdict is "A", "B", or "tie".
    """
    # Order 1: A presented first
    result_ab = judge.compare_pairwise(question, answer_a, answer_b, "A", "B")
    # Order 2: B presented first (labels swapped so result is still in A/B space)
    result_ba = judge.compare_pairwise(question, answer_b, answer_a, "B", "A")

    winner_ab = result_ab.winner  # "A" or "B"
    winner_ba = result_ba.winner  # "B" or "A" — in original label space

    if winner_ab == "A" and winner_ba == "A":
        verdict = "A"
    elif winner_ab == "B" and winner_ba == "B":
        verdict = "B"
    else:
        # Judges disagreed across orderings — position bias detected → tie
        verdict = "tie"

    return verdict, result_ab, result_ba


# ---------------------------------------------------------------------------
# Demo runners
# ---------------------------------------------------------------------------

def run_single_scoring(judge: MockJudge) -> None:
    """Score the SUT on the PTO question — exposes the faithfulness bug."""
    print("\n" + "=" * 60)
    print("SINGLE-OUTPUT SCORING")
    print("=" * 60)

    question = "How many PTO days do new employees get?"
    sut_result = answer(question)
    sut_answer = sut_result["answer"]
    contexts = sut_result.get("contexts", [])

    result = judge.score_single(question, sut_answer, contexts)

    print(f"Question : {question}")
    print(f"SUT Answer: {sut_answer}")
    print(f"\nComposite Score: {result.composite_score:.1f}/5.0")
    print("Criterion breakdown:")
    for c in result.criteria:
        print(f"  {c.name:<14} [{c.score}/5]: {c.rationale}")


def run_pairwise_bias_demo(judge: MockJudge) -> None:
    """
    Demonstrate position bias by swapping A/B order.

    Two scenarios:
    (a) Very different quality  → clear winner both ways, no bias.
    (b) Nearly equal quality    → mock judge flips on order swap, bias detected.
    """
    print("\n" + "=" * 60)
    print("PAIRWISE COMPARISON — POSITION BIAS DEMO")
    print("=" * 60)

    question = "What is the PTO policy for new employees?"

    # ------------------------------------------------------------------ #
    # Scenario (a): clearly different answers — expect consistent result   #
    # ------------------------------------------------------------------ #
    print("\n-- Scenario (a): clearly different answers --")
    answer_good = (
        "New employees with 0–2 years of service accrue 15 days of PTO per year. "
        "The entitlement increases to 20 days at year 3 and 25 days at year 6, "
        "following the tiered accrual schedule."
    )
    answer_bad = "Employees get some paid time off."

    result_ab = judge.compare_pairwise(question, answer_good, answer_bad, "A", "B")
    print(f"Order A→B (good first):   winner = {result_ab.winner}")
    print(f"  {result_ab.rationale}")

    result_ba = judge.compare_pairwise(question, answer_bad, answer_good, "B", "A")
    print(f"Order B→A (bad first):    winner = {result_ba.winner}")
    print(f"  {result_ba.rationale}")

    if result_ab.winner != result_ba.winner:
        print("  *** POSITION BIAS DETECTED (unexpected in this scenario) ***")
    else:
        print("  Consistent: large quality gap → same winner regardless of order.")

    # ------------------------------------------------------------------ #
    # Scenario (b): similar-quality answers → position bias triggers       #
    # Both answers are partially wrong (state 20 days), similar wording.  #
    # ------------------------------------------------------------------ #
    print("\n-- Scenario (b): similar-quality answers (both partially wrong) --")
    answer_x = (
        "According to company policy, employees receive 20 days of PTO annually "
        "starting from their first year."
    )
    answer_y = (
        "The company provides 20 paid vacation days per year to all employees "
        "beginning on their start date."
    )

    result_xy = judge.compare_pairwise(question, answer_x, answer_y, "X", "Y")
    print(f"Order X→Y (X first):      winner = {result_xy.winner}")
    print(f"  {result_xy.rationale}")

    result_yx = judge.compare_pairwise(question, answer_y, answer_x, "Y", "X")
    print(f"Order Y→X (Y first):      winner = {result_yx.winner}")
    print(f"  {result_yx.rationale}")

    if result_xy.winner != result_yx.winner:
        print("  *** POSITION BIAS DETECTED: winner flipped on order swap ***")
        print("  Mitigation: run both orderings and require agreement (see next section).")
    else:
        print("  Consistent result (check MockJudge heuristics if bias not shown).")


def run_mitigation_demo(judge: MockJudge) -> None:
    """Demonstrate agreement-based mitigation of position bias."""
    print("\n" + "=" * 60)
    print("POSITION BIAS MITIGATION — AGREEMENT-BASED")
    print("=" * 60)

    question = "What is the PTO policy for new employees?"
    answer_a = (
        "New employees (0–2 years of service) accrue 15 days of PTO per year "
        "according to the tiered schedule. The rate increases to 20 days at year 3."
    )
    answer_b = "Employees get some paid time off."

    verdict, result_ab, result_ba = mitigate_position_bias(judge, question, answer_a, answer_b)

    print(f"\nOrder A→B result : winner = {result_ab.winner}")
    print(f"Order B→A result : winner = {result_ba.winner}")
    print(f"\nFinal verdict (agreement-based): {verdict}")

    if verdict == "tie":
        print(
            "  Judges disagreed across orderings — position bias detected.\n"
            "  Calling it a tie; escalate to human review if needed."
        )
    else:
        print(f"  Both orderings agreed: {verdict} is the better answer.")


# ---------------------------------------------------------------------------
# Optional real judge — claude-haiku-4-5
# ---------------------------------------------------------------------------

def run_real_judge() -> None:
    """
    Uses claude-haiku-4-5 as the judge when ANTHROPIC_API_KEY is set.
    Secrets are loaded from environment only (never hard-coded).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    print("\n" + "=" * 60)
    print("REAL JUDGE — claude-haiku-4-5 (optional)")
    print("=" * 60)

    if not api_key:
        print("  Skipped — ANTHROPIC_API_KEY not set.")
        print("  Export the key to activate this path:")
        print("    export ANTHROPIC_API_KEY=sk-ant-...")
        return

    try:
        import anthropic
    except ImportError:
        print("  Skipped — anthropic package not installed.")
        print("  Uncomment 'anthropic>=0.40.0' in requirements.txt and pip install.")
        return

    question = "How many PTO days do new employees get?"
    sut_result = answer(question)
    sut_answer = sut_result["answer"]
    contexts = sut_result.get("contexts", [])
    context_block = "\n".join(f"- {c}" for c in contexts) if contexts else "(no context retrieved)"

    prompt = f"""You are evaluating an AI assistant's answer to a user question.

{RUBRIC}

Return ONLY valid JSON with this exact schema (no markdown fences, no extra keys):
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
        print(f"\nQuestion : {question}")
        print(f"SUT Answer: {sut_answer}")
        print(f"\nComposite (real judge): {composite:.1f}/5.0")
        for criterion, score in scores.items():
            rationale = data.get("rationale", {}).get(criterion, "")
            print(f"  {criterion:<14} [{score}/5]: {rationale}")
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"  Could not parse judge response ({exc}).")
        print(f"  Raw response: {raw}")


# ---------------------------------------------------------------------------
# Pairwise real-judge demo (with order-swap mitigation)
# ---------------------------------------------------------------------------

def run_real_judge_pairwise() -> None:
    """
    Pairwise comparison using claude-haiku-4-5.
    Demonstrates that a real judge also exhibits position bias,
    and shows how the mitigation handles it.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return  # already reported above

    try:
        import anthropic
    except ImportError:
        return

    print("\n--- Real judge pairwise (order-swap mitigation) ---")

    question = "What is the PTO policy for new employees?"
    answer_a = (
        "New employees with 0–2 years of service accrue 15 days of PTO per year. "
        "The entitlement rises to 20 days at 3 years and 25 days at 6 years."
    )
    answer_b = "Employees get some paid time off."

    def _pairwise_call(q: str, first: str, second: str, lf: str, ls: str) -> str:
        prompt = f"""You are comparing two AI assistant answers. Choose the better one.

Criteria: groundedness (factual accuracy), completeness, and relevance to the question.
Length alone does NOT indicate quality.

Return ONLY valid JSON: {{"winner": "{lf}", "rationale": "<one sentence>"}}
or {{"winner": "{ls}", "rationale": "<one sentence>"}}
or {{"winner": "tie", "rationale": "<one sentence>"}}

Question: {q}
Answer {lf}: {first}
Answer {ls}: {second}
"""
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        try:
            data = json.loads(raw)
            return data.get("winner", "tie")
        except json.JSONDecodeError:
            return "tie"

    winner_ab = _pairwise_call(question, answer_a, answer_b, "A", "B")
    winner_ba = _pairwise_call(question, answer_b, answer_a, "B", "A")

    print(f"  Order A→B: winner = {winner_ab}")
    print(f"  Order B→A: winner = {winner_ba}")

    if winner_ab == winner_ba:
        final = winner_ab
        print(f"  Agreement: final verdict = {final}")
    else:
        final = "tie"
        print(f"  Disagreement detected — final verdict = tie (position bias mitigation)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    judge = MockJudge()

    run_single_scoring(judge)
    run_pairwise_bias_demo(judge)
    run_mitigation_demo(judge)
    run_real_judge()
    run_real_judge_pairwise()

    print("\n" + "=" * 60)
    print("Day 9 lab complete.")
    print("=" * 60)
