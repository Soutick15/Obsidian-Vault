#!/usr/bin/env python3
"""
Capstone CI Gate — integrates all evaluation modules and exits non-zero if quality is below threshold.

Usage:
    python ci_gate.py
    python ci_gate.py --threshold 0.9
    python ci_gate.py --skip-judge      # skip judge (faster)
    python ci_gate.py --skip-redteam    # skip red-team (faster)
"""
import sys
import pathlib
import argparse

_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "labs" / "qa" / "_shared"))

# TODO 1: Import from the other capstone modules.
#
# Use a try/except block for EACH import so that a partially-complete capstone can still
# run the modules that are finished. Set a boolean flag when each import succeeds.
#
# Pattern to follow for each module:
#
#   try:
#       from eval_harness import build_golden_set, run_harness, print_report
#       EVAL_AVAILABLE = True
#   except (ImportError, NotImplementedError):
#       EVAL_AVAILABLE = False
#
# Do this for: eval_harness, judge, rag_metrics, redteam
# Flag names: EVAL_AVAILABLE, JUDGE_AVAILABLE, RAG_AVAILABLE, REDTEAM_AVAILABLE

EVAL_AVAILABLE = False
JUDGE_AVAILABLE = False
RAG_AVAILABLE = False
REDTEAM_AVAILABLE = False


# TODO 2: Run all available components and collect scores.
#
# Implement run_all_components(args) that:
#   - Runs eval_harness if EVAL_AVAILABLE and not already failed
#   - Runs judge if JUDGE_AVAILABLE and not args.skip_judge
#   - Runs rag_metrics if RAG_AVAILABLE
#   - Runs redteam if REDTEAM_AVAILABLE and not args.skip_redteam
#   - For each module, wraps execution in try/except NotImplementedError and prints a helpful message
#   - Returns a dict with keys: "eval_pass_rate", "judge_avg_helpfulness", "judge_avg_faithfulness",
#     "rag_avg_precision", "vuln_count", "total_probes"
#   - Uses sensible defaults when a module is skipped or raises NotImplementedError:
#       eval_pass_rate = 0.0
#       judge_avg_helpfulness = 0.0, judge_avg_faithfulness = 0.0
#       rag_avg_precision = 0.0
#       vuln_count = 0, total_probes = 1   (avoid division by zero)
#
# Print section headers like:
#   print("\n--- Eval Harness ---")
# before each module's output so the report is readable.
def run_all_components(args) -> dict:
    scores = {
        "eval_pass_rate": 0.0,
        "judge_avg_helpfulness": 0.0,
        "judge_avg_faithfulness": 0.0,
        "rag_avg_precision": 0.0,
        "vuln_count": 0,
        "total_probes": 1,
    }
    raise NotImplementedError("TODO 2: Implement run_all_components")


# TODO 3: Compute the gate score and decide pass/fail.
#
# Gate score formula (weighted average):
#
#   gate_score = (
#       eval_pass_rate                                   * 0.40
#     + (judge_avg_helpfulness / 5.0)                   * 0.25
#     + rag_avg_precision                                * 0.15
#     + (1.0 - vuln_count / max(total_probes, 1))       * 0.20
#   )
#
# Print the gate score and whether the run PASSED or FAILED relative to the threshold.
# Use sys.exit(0) for PASS, sys.exit(1) for FAIL.
#
# Example output:
#   ============================================================
#   GATE SCORE: 0.712
#   Threshold:  0.600
#   Result:     PASSED
#   ============================================================
def compute_gate_and_exit(scores: dict, threshold: float):
    raise NotImplementedError("TODO 3: Implement compute_gate_and_exit")


def main():
    parser = argparse.ArgumentParser(description="QA Capstone CI Gate")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.60,
        help="Minimum gate score to pass (0.0–1.0, default: 0.60)",
    )
    parser.add_argument(
        "--skip-judge",
        action="store_true",
        help="Skip the LLM-as-judge module (faster run)",
    )
    parser.add_argument(
        "--skip-redteam",
        action="store_true",
        help="Skip the red-team module (faster run)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("QA CAPSTONE CI GATE")
    print("=" * 60)
    print(f"Threshold: {args.threshold:.2f}")
    print(f"Skip judge: {args.skip_judge}  |  Skip red-team: {args.skip_redteam}")

    try:
        scores = run_all_components(args)
        compute_gate_and_exit(scores, args.threshold)
    except NotImplementedError as e:
        print("\n[INFO] Some modules are not yet implemented.")
        print("       Fill in the TODOs in each starter file and re-run.")
        print(f"       First unimplemented TODO: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
