#!/usr/bin/env python3
"""
Day 14 Lab — Solution
CI Eval Gate: runs an eval harness, computes a score,
exits non-zero if below threshold (CI fails).
Also demonstrates baseline snapshot comparison and drift detection.

Usage:
    python solution.py
    python solution.py --threshold 0.99   # forces failure (score < threshold)
    python solution.py --save-baseline    # saves current score as baseline
    python solution.py --demo-fail        # convenience alias for --threshold 0.99
"""

import sys
import pathlib
import json
import argparse
import statistics
import re
from dataclasses import dataclass, field
from typing import List, Optional

# --- SUT import ---
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))
from hr_assistant import answer

# ─── Data structures ────────────────────────────────────────────────────────

@dataclass
class GoldenItem:
    question: str
    expected_contains: List[str]        # strings the answer must contain
    faithfulness_claims: List[str]      # strings that must appear in contexts
    forbidden_contains: List[str] = field(default_factory=list)  # strings the answer must NOT contain
    tags: List[str] = field(default_factory=list)

@dataclass
class EvalResult:
    question: str
    passed: bool
    score: float          # 1.0 = pass, 0.0 = fail
    failure_reason: Optional[str] = None

# ─── TODO 1: Golden set ─────────────────────────────────────────────────────

def build_golden_set() -> List[GoldenItem]:
    """
    Return 8 golden items covering PTO (regression), remote work, onboarding,
    benefits, code of conduct, expenses, performance reviews, and PII safety.

    NOTE: The PTO item uses expected_contains=["15"] because the HR corpus
    states new employees receive 15 days. The SUT has a seeded bug that returns
    "20 days". This item is *expected to fail* — that is the eval gate working
    correctly by surfacing a real defect.
    """
    return [
        # ── Regression canary: SUT bug states "20 days" but corpus says "15" ──
        # NOTE: the SUT appends its retrieved supporting context (which contains
        # the correct "15 days" accrual table) to the answer string, so a naive
        # expected_contains=["15"] check passes spuriously. The hallucination
        # lives in the SUT's *stated* answer ("20 days of PTO per year"), so we
        # use forbidden_contains to assert the wrong figure is NOT stated.
        GoldenItem(
            question="How many PTO days do new employees receive in their first year?",
            expected_contains=["15"],
            faithfulness_claims=["15"],
            forbidden_contains=["20 days of PTO"],
            tags=["pto", "regression", "bug"],
        ),
        # ── Remote work ──────────────────────────────────────────────────
        GoldenItem(
            question="What is the remote work policy for full-time employees?",
            expected_contains=["remote"],
            faithfulness_claims=["remote"],
            tags=["remote-work"],
        ),
        # ── Onboarding ───────────────────────────────────────────────────
        GoldenItem(
            question="How does the onboarding process work for new hires?",
            expected_contains=["onboard"],
            faithfulness_claims=["onboard"],
            tags=["onboarding"],
        ),
        # ── Benefits ─────────────────────────────────────────────────────
        GoldenItem(
            question="What health benefits are available to employees?",
            expected_contains=["health"],
            faithfulness_claims=["health"],
            tags=["benefits"],
        ),
        # ── Code of conduct ──────────────────────────────────────────────
        GoldenItem(
            question="What is the company code of conduct policy?",
            expected_contains=["conduct"],
            faithfulness_claims=["conduct"],
            tags=["policy"],
        ),
        # ── Expense reports ──────────────────────────────────────────────
        GoldenItem(
            question="How do employees submit expense reports for reimbursement?",
            expected_contains=["expense"],
            faithfulness_claims=["expense"],
            tags=["expenses"],
        ),
        # ── Performance reviews ──────────────────────────────────────────
        GoldenItem(
            question="How often are performance reviews conducted?",
            expected_contains=["review"],
            faithfulness_claims=["review"],
            tags=["performance"],
        ),
        # ── PII safety ───────────────────────────────────────────────────
        # The answer must NOT contain obvious PII patterns (SSN, raw email).
        # We repurpose expected_contains as a "must NOT contain" check via a
        # dedicated tag; faithfulness_claims are left empty since this is a
        # safety check, not a retrieval check. The score_item function handles
        # the "no_pii" tag specially.
        # This is a safety negative-test: the answer must not leak PII patterns
        # (SSN, email, phone). The contains check is kept loose ("employee") so
        # the item exercises the PII guard rather than a brittle phrase match.
        GoldenItem(
            question="What is the process for updating employee personal information?",
            expected_contains=["employee"],
            faithfulness_claims=[],
            tags=["pii-safety"],
        ),
    ]

# ─── TODO 2: Contains check ─────────────────────────────────────────────────

def run_contains_check(answer_text: str, expected_contains: List[str]) -> tuple[bool, Optional[str]]:
    """
    Return (True, None) if ALL strings in expected_contains appear in
    answer_text (case-insensitive).
    Return (False, reason) on the first missing string.
    """
    lower = answer_text.lower()
    for token in expected_contains:
        if token.lower() not in lower:
            return False, f'expected "{token}" in answer'
    return True, None

def run_forbidden_check(answer_text: str, forbidden_contains: List[str]) -> tuple[bool, Optional[str]]:
    """
    Return (True, None) if NONE of the forbidden strings appear in answer_text
    (case-insensitive). Return (False, reason) on the first forbidden string found.
    This catches hallucinated values even when the correct value also appears
    elsewhere (e.g. in an appended supporting-context block).
    """
    lower = answer_text.lower()
    for token in forbidden_contains:
        if token.lower() in lower:
            return False, f'forbidden value "{token}" present in answer (hallucination)'
    return True, None

# ─── TODO 3: Faithfulness check ─────────────────────────────────────────────

def run_faithfulness_check(contexts: List[str], faithfulness_claims: List[str]) -> tuple[bool, Optional[str]]:
    """
    Return (True, None) if each claim in faithfulness_claims appears in at
    least one of the context strings (case-insensitive).
    Return (False, reason) on the first ungrounded claim.
    """
    if not faithfulness_claims:
        return True, None  # no claims to check

    combined = " ".join(contexts).lower()
    for claim in faithfulness_claims:
        if claim.lower() not in combined:
            return False, f'claim "{claim}" not grounded in retrieved contexts'
    return True, None

# ─── PII safety helper ───────────────────────────────────────────────────────

_PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),          # SSN
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),  # email
    re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),  # phone
]

def _has_pii(text: str) -> bool:
    """Return True if any PII pattern is detected in text."""
    for pattern in _PII_PATTERNS:
        if pattern.search(text):
            return True
    return False

# ─── TODO 4: Score a single item ─────────────────────────────────────────────

def score_item(item: GoldenItem) -> EvalResult:
    """
    Call answer(), run contains + faithfulness checks, return EvalResult.
    Items tagged 'pii-safety' additionally fail if the answer contains PII.
    """
    try:
        response = answer(item.question)
    except Exception as exc:
        return EvalResult(
            question=item.question,
            passed=False,
            score=0.0,
            failure_reason=f"SUT raised exception: {exc}",
        )

    answer_text = response.get("answer", "")
    contexts = response.get("contexts", [])

    # Contains check
    contains_ok, contains_reason = run_contains_check(answer_text, item.expected_contains)
    if not contains_ok:
        return EvalResult(
            question=item.question,
            passed=False,
            score=0.0,
            failure_reason=contains_reason,
        )

    # Forbidden check (catches hallucinated values)
    forbidden_ok, forbidden_reason = run_forbidden_check(answer_text, item.forbidden_contains)
    if not forbidden_ok:
        return EvalResult(
            question=item.question,
            passed=False,
            score=0.0,
            failure_reason=forbidden_reason,
        )

    # Faithfulness check
    faith_ok, faith_reason = run_faithfulness_check(contexts, item.faithfulness_claims)
    if not faith_ok:
        return EvalResult(
            question=item.question,
            passed=False,
            score=0.0,
            failure_reason=faith_reason,
        )

    # PII safety check (only for tagged items)
    if "pii-safety" in item.tags and _has_pii(answer_text):
        return EvalResult(
            question=item.question,
            passed=False,
            score=0.0,
            failure_reason="PII detected in answer",
        )

    return EvalResult(
        question=item.question,
        passed=True,
        score=1.0,
    )

# ─── TODO 5: Full harness ────────────────────────────────────────────────────

def run_harness(golden_set: List[GoldenItem]) -> tuple[List[EvalResult], float]:
    """
    Score every item in the golden set.
    Return (results, pass_rate) where pass_rate is between 0.0 and 1.0.
    """
    results = [score_item(item) for item in golden_set]
    if not results:
        return results, 0.0
    pass_rate = sum(r.score for r in results) / len(results)
    return results, pass_rate

# ─── TODO 6: Baseline comparison ─────────────────────────────────────────────

BASELINE_PATH = pathlib.Path(__file__).parent / "baseline.json"

def compare_to_baseline(current_score: float) -> tuple[Optional[float], Optional[float], bool]:
    """
    Load baseline.json (if present) and compare current_score against it.

    Returns:
        (baseline_score, delta, regression_ok)
        - baseline_score: float from file, or None if no baseline exists
        - delta: current_score - baseline_score, or None if no baseline
        - regression_ok: True if current_score >= baseline_score * 0.95
    """
    if not BASELINE_PATH.exists():
        return None, None, True  # no baseline yet — first run

    try:
        data = json.loads(BASELINE_PATH.read_text())
        baseline_score = float(data["score"])
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"  [WARN] Could not parse baseline.json: {exc}")
        return None, None, True

    delta = current_score - baseline_score
    regression_ok = current_score >= baseline_score * 0.95
    return baseline_score, delta, regression_ok

def save_baseline(score: float):
    """Persist the current score as the new baseline snapshot."""
    BASELINE_PATH.write_text(json.dumps({"score": score}, indent=2))

# ─── TODO 7: Drift detection ─────────────────────────────────────────────────

def detect_drift(current_window: List[float], baseline_window: List[float]) -> dict:
    """
    Compare the mean of two score windows.
    Drift is flagged when the current mean has dropped more than 0.10 (10 pp)
    below the baseline mean.

    Returns a dict with keys:
        current_mean, baseline_mean, delta, drift_detected
    """
    current_mean = statistics.mean(current_window) if current_window else 0.0
    baseline_mean = statistics.mean(baseline_window) if baseline_window else 0.0
    delta = current_mean - baseline_mean
    drift_detected = delta < -0.10  # dropped more than 10 percentage points
    return {
        "current_mean": current_mean,
        "baseline_mean": baseline_mean,
        "delta": delta,
        "drift_detected": drift_detected,
    }

# ─── Main eval gate ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CI Eval Gate")
    parser.add_argument("--threshold", type=float, default=0.75,
                        help="Minimum pass rate to pass the gate (default: 0.75)")
    parser.add_argument("--save-baseline", action="store_true",
                        help="Save the current score as the new baseline")
    parser.add_argument("--demo-fail", action="store_true",
                        help="Convenience alias: sets threshold=0.99, guaranteed to fail")
    args = parser.parse_args()

    # --demo-fail overrides threshold for easy classroom demonstration
    if args.demo_fail:
        args.threshold = 0.99

    print("=" * 60)
    print("CI EVAL GATE — Acme HR Assistant")
    print("=" * 60)

    golden_set = build_golden_set()
    results, score = run_harness(golden_set)

    print(f"\nResults ({len(results)} items):")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.question[:55]}")
        if r.failure_reason:
            print(f"         Reason: {r.failure_reason}")

    print(f"\nOverall score: {score:.2%}")
    print(f"Threshold:     {args.threshold:.2%}")

    # Baseline comparison
    baseline, delta, regression_ok = compare_to_baseline(score)
    if baseline is not None:
        print(f"\nBaseline:      {baseline:.2%}")
        print(f"Delta:         {delta:+.2%}")
        if not regression_ok:
            print("  [REGRESSION] Score dropped more than 5% from baseline!")
    else:
        print("\nBaseline:      (none — run with --save-baseline to create one)")

    if args.save_baseline:
        save_baseline(score)
        print(f"\nBaseline saved to {BASELINE_PATH}")

    # Drift detection demo
    # In production these windows come from a metrics store (e.g. BigQuery, Postgres).
    # Here we simulate a baseline_window that was 15 pp better than current.
    current_window = [r.score for r in results]
    baseline_window = [min(1.0, s + 0.15) for s in current_window]
    drift_report = detect_drift(current_window, baseline_window)

    print(f"\nDrift detection:")
    print(f"  Current window mean:  {drift_report['current_mean']:.2%}")
    print(f"  Baseline window mean: {drift_report['baseline_mean']:.2%}")
    print(f"  Delta:                {drift_report['delta']:+.2%}")
    if drift_report['drift_detected']:
        print("  [DRIFT DETECTED] Quality dropped > 10% from baseline window!")
    else:
        print("  [OK] No significant drift detected.")

    # Gate decision: score must clear threshold AND not regress vs saved baseline
    gate_passed = score >= args.threshold and (baseline is None or regression_ok)
    print(f"\n{'='*60}")
    if gate_passed:
        print("GATE: PASSED")
        sys.exit(0)
    else:
        reason_parts = []
        if score < args.threshold:
            reason_parts.append(
                f"score {score:.2%} is below threshold {args.threshold:.2%}"
            )
        if baseline is not None and not regression_ok:
            reason_parts.append(
                f"regression vs baseline ({baseline:.2%} → {score:.2%})"
            )
        print(f"GATE: FAILED — build blocked ({'; '.join(reason_parts)})")
        sys.exit(1)

if __name__ == "__main__":
    main()
