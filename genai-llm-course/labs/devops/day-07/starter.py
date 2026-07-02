"""
Day 7 Lab — Starter File
========================
Containerising the Acme HR Knowledge Assistant

Complete each TODO section. Run with:
    python labs/devops/day-07/starter.py

No API key required. Docker is NOT required to run this script.

What you will implement:
  PART A — Application verification via TestClient (in-process, no server)
  PART B — Dockerfile best-practice linting (parse + assert, no docker build)
"""

from __future__ import annotations

import pathlib
import sys

# ---------------------------------------------------------------------------
# Shared app import — do not modify this block
# ---------------------------------------------------------------------------
_HERE = pathlib.Path(__file__).resolve()
_SHARED = _HERE.parents[1] / "_shared"
sys.path.insert(0, str(_SHARED))

from app import app  # noqa: E402  (FastAPI application instance)

# ---------------------------------------------------------------------------
# PART A — Application Verification
# ---------------------------------------------------------------------------
# The TestClient wraps a FastAPI app for in-process HTTP testing.
# No uvicorn server needed.

# TODO A1: Import TestClient from fastapi.testclient
# from fastapi.testclient import TestClient


def verify_app() -> list[tuple[str, bool, str]]:
    """
    Run three checks against the shared app using TestClient.
    Returns a list of (check_name, passed, detail) tuples.
    """
    results: list[tuple[str, bool, str]] = []

    # TODO A2: Create a TestClient wrapping `app`
    # client = TestClient(app)

    # TODO A3: GET /health — assert status 200
    # Hint: client.get("/health")
    # results.append(("GET /health → 200", <condition>, <detail>))

    # TODO A4: GET /health — assert response JSON contains "status" key
    # results.append(("GET /health has 'status' field", <condition>, <detail>))

    # TODO A5: POST /chat with {"question": "What is the PTO policy?"}
    # Assert status 200 and that "answer" key is in the response JSON.
    # results.append(("POST /chat → 200 with answer", <condition>, <detail>))

    # TODO A6: GET /metrics — assert status 200
    # results.append(("GET /metrics → 200", <condition>, <detail>))

    return results


# ---------------------------------------------------------------------------
# PART B — Dockerfile Linting
# ---------------------------------------------------------------------------
# Parse the Dockerfile as plain text and assert best-practice rules.
# This validates the file without needing Docker installed.

_DOCKERFILE = _HERE.parent / "Dockerfile"


def lint_dockerfile() -> list[tuple[str, bool, str]]:
    """
    Parse the Dockerfile and assert six best-practice rules.
    Returns a list of (rule_name, passed, detail) tuples.
    """
    results: list[tuple[str, bool, str]] = []

    if not _DOCKERFILE.exists():
        results.append(("Dockerfile exists", False, str(_DOCKERFILE)))
        return results

    # TODO B1: Read the Dockerfile content
    # content = _DOCKERFILE.read_text()
    # lines = content.splitlines()

    # TODO B2: Rule — slim base image
    # Assert that the FROM line uses "python:3.11-slim" (not plain "python:3.11" or "python:3")
    # Hint: look for a line starting with "FROM" and check it contains "slim"
    # results.append(("FROM uses slim base", <condition>, <detail>))

    # TODO B3: Rule — non-root USER
    # Assert a line containing "USER" and a non-root username appears after RUN adduser
    # Hint: any line that starts with "USER" and does not end with "root"
    # results.append(("Non-root USER directive", <condition>, <detail>))

    # TODO B4: Rule — HEALTHCHECK present
    # Assert a HEALTHCHECK instruction exists
    # results.append(("HEALTHCHECK present", <condition>, <detail>))

    # TODO B5: Rule — requirements.txt COPY'd before source COPY
    # Assert "COPY" of requirements.txt appears before "COPY" of app source files
    # Hint: find line indexes for each COPY and compare positions
    # results.append(("requirements.txt COPY before source COPY", <condition>, <detail>))

    # TODO B6: Rule — --no-cache-dir in pip install
    # Assert the pip install RUN line includes --no-cache-dir
    # results.append(("pip install uses --no-cache-dir", <condition>, <detail>))

    # TODO B7: Rule — .dockerignore exists
    # Check that labs/devops/day-07/.dockerignore exists on disk
    # results.append((".dockerignore exists", <condition>, <detail>))

    return results


# ---------------------------------------------------------------------------
# Runner — do not modify below this line
# ---------------------------------------------------------------------------

def _print_results(section: str, results: list[tuple[str, bool, str]]) -> int:
    """Print a checklist and return number of failures."""
    print(f"\n{'='*60}")
    print(f"  {section}")
    print(f"{'='*60}")
    failures = 0
    for name, passed, detail in results:
        icon = "[PASS]" if passed else "[FAIL]"
        print(f"  {icon}  {name}")
        if not passed:
            print(f"         Detail: {detail}")
            failures += 1
    return failures


def main() -> None:
    total_failures = 0

    app_results = verify_app()
    if app_results:
        total_failures += _print_results("PART A — Application Verification", app_results)
    else:
        print("\n[!] PART A: No results returned — complete the TODO sections in verify_app()")
        total_failures += 1

    df_results = lint_dockerfile()
    if df_results:
        total_failures += _print_results("PART B — Dockerfile Lint", df_results)
    else:
        print("\n[!] PART B: No results returned — complete the TODO sections in lint_dockerfile()")
        total_failures += 1

    print(f"\n{'='*60}")
    if total_failures == 0:
        print("  ALL CHECKS PASSED")
    else:
        print(f"  {total_failures} check(s) failed — see details above")
    print(f"{'='*60}\n")

    sys.exit(0 if total_failures == 0 else 1)


if __name__ == "__main__":
    main()
