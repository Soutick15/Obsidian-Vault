#!/usr/bin/env python3
"""
Day 14 Lab — Starter
CI Eval Gate: runs an eval harness, computes a score,
exits non-zero if below threshold (CI fails).
Also demonstrates baseline snapshot comparison and drift detection.

Usage:
    python starter.py
    python starter.py --threshold 0.99   # forces failure (score < threshold)
    python starter.py --save-baseline    # saves current score as baseline
"""

import sys
import pathlib
import json
import argparse
import statistics
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
    tags: List[str] = field(default_factory=list)

@dataclass
class EvalResult:
    question: str
    passed: bool
    score: float          # 1.0 = pass, 0.0 = fail
    failure_reason: Optional[str] = None

# ─── TODO 1 ─────────────────────────────────────────────────────────────────
# Build the golden set.
# Include at least 8 items covering:
#   - The PTO regression question (expected_contains=["15"])
#   - Remote work policy
#   - Onboarding / benefits
#   - At least one question that should NOT contain a PII token
# Return a list of GoldenItem.
def build_golden_set() -> List[GoldenItem]:
    # TODO 1: return a list of GoldenItem instances
    raise NotImplementedError

# ─── TODO 2 ─────────────────────────────────────────────────────────────────
# Run a contains check.
# Return True if ALL strings in expected_contains appear in answer_text
# (case-insensitive). Return False with a reason string if any are missing.
def run_contains_check(answer_text: str, expected_contains: List[str]) -> tuple[bool, Optional[str]]:
    # TODO 2: implement
    raise NotImplementedError

# ─── TODO 3 ─────────────────────────────────────────────────────────────────
# Run a faithfulness check.
# Return True if each faithfulness_claim appears in at least one of the
# context strings (case-insensitive).
def run_faithfulness_check(contexts: List[str], faithfulness_claims: List[str]) -> tuple[bool, Optional[str]]:
    # TODO 3: implement
    raise NotImplementedError

# ─── TODO 4 ─────────────────────────────────────────────────────────────────
# Score a single golden item.
# Call answer(item.question), then run both checks.
# Return EvalResult(passed=True) only if both checks pass.
def score_item(item: GoldenItem) -> EvalResult:
    # TODO 4: implement
    raise NotImplementedError

# ─── TODO 5 ─────────────────────────────────────────────────────────────────
# Run the full harness over the golden set.
# Return a list of EvalResult and the overall pass rate (0.0–1.0).
def run_harness(golden_set: List[GoldenItem]) -> tuple[List[EvalResult], float]:
    # TODO 5: implement
    raise NotImplementedError

# ─── TODO 6 ─────────────────────────────────────────────────────────────────
# Baseline snapshot comparison.
# Load a previously saved baseline score from 'baseline.json' (if it exists).
# Compare the current score against it.
# Return (baseline_score_or_None, delta, passed_regression_check).
# Regression check passes if current_score >= baseline_score * 0.95 (5% tolerance).
BASELINE_PATH = pathlib.Path(__file__).parent / "baseline.json"

def compare_to_baseline(current_score: float) -> tuple[Optional[float], Optional[float], bool]:
    # TODO 6: load baseline.json, compare, return (baseline, delta, passed)
    raise NotImplementedError

def save_baseline(score: float):
    """Save current score as the new baseline."""
    # TODO: write score to baseline.json
    raise NotImplementedError

# ─── TODO 7 ─────────────────────────────────────────────────────────────────
# Simple drift detection.
# Given a list of per-item scores from two "windows" (current vs historical),
# compute the mean of each and flag drift if the mean dropped by > 0.10.
# This simulates comparing a rolling production metric against a baseline window.
def detect_drift(current_window: List[float], baseline_window: List[float]) -> dict:
    # TODO 7: compute means, compute delta, return {"current_mean", "baseline_mean", "delta", "drift_detected"}
    raise NotImplementedError

# ─── Main eval gate ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CI Eval Gate")
    parser.add_argument("--threshold", type=float, default=0.75,
                        help="Minimum pass rate to pass the gate (default: 0.75)")
    parser.add_argument("--save-baseline", action="store_true",
                        help="Save the current score as the new baseline")
    args = parser.parse_args()

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

    if args.save_baseline:
        save_baseline(score)
        print(f"\nBaseline saved to {BASELINE_PATH}")

    # Drift detection demo
    # Simulate two windows of scores (in a real system these come from a DB)
    current_window = [r.score for r in results]
    # Simulate a slightly better historical window
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

    # Gate decision
    gate_passed = score >= args.threshold and (baseline is None or regression_ok)
    print(f"\n{'='*60}")
    if gate_passed:
        print("GATE: PASSED")
        sys.exit(0)
    else:
        print("GATE: FAILED — build blocked")
        sys.exit(1)

if __name__ == "__main__":
    main()
