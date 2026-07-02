"""
Day 7 Lab — Solution File
=========================
Containerising the Acme HR Knowledge Assistant

Run with:
    python labs/devops/day-07/solution.py

No API key required. Docker is NOT required.

Verification covers:
  PART A — Application verification via TestClient (in-process, no server)
  PART B — Dockerfile best-practice linting (parse + assert)
"""

from __future__ import annotations

import pathlib
import sys

# ---------------------------------------------------------------------------
# Shared app import
# ---------------------------------------------------------------------------
_HERE = pathlib.Path(__file__).resolve()
_SHARED = _HERE.parents[1] / "_shared"
sys.path.insert(0, str(_SHARED))

from app import app  # noqa: E402  (FastAPI application instance)
from fastapi.testclient import TestClient  # noqa: E402

# ---------------------------------------------------------------------------
# PART A — Application Verification via TestClient
# ---------------------------------------------------------------------------

def verify_app() -> list[tuple[str, bool, str]]:
    """
    Run four checks against the shared app using FastAPI's in-process TestClient.
    No server, no network, no API key required.
    """
    results: list[tuple[str, bool, str]] = []
    client = TestClient(app, raise_server_exceptions=False)

    # Check 1: GET /health → 200
    r = client.get("/health")
    results.append((
        "GET /health → 200",
        r.status_code == 200,
        f"status={r.status_code}",
    ))

    # Check 2: /health response contains "status" key
    try:
        body = r.json()
        has_status = "status" in body
        detail = str(list(body.keys()))
    except Exception as exc:
        has_status = False
        detail = str(exc)
    results.append(("GET /health has 'status' field", has_status, detail))

    # Check 3: POST /chat → 200 with "answer" key
    r2 = client.post("/chat", json={"question": "What is the PTO policy?"})
    try:
        body2 = r2.json()
        has_answer = r2.status_code == 200 and "answer" in body2
        detail2 = f"status={r2.status_code}, keys={list(body2.keys())}"
    except Exception as exc:
        has_answer = False
        detail2 = str(exc)
    results.append(("POST /chat → 200 with 'answer' field", has_answer, detail2))

    # Check 4: GET /metrics → 200
    r3 = client.get("/metrics")
    results.append((
        "GET /metrics → 200",
        r3.status_code == 200,
        f"status={r3.status_code}",
    ))

    return results


# ---------------------------------------------------------------------------
# PART B — Dockerfile Best-Practice Linting
# ---------------------------------------------------------------------------

_DOCKERFILE = _HERE.parent / "Dockerfile"
_DOCKERIGNORE = _HERE.parent / ".dockerignore"


def lint_dockerfile() -> list[tuple[str, bool, str]]:
    """
    Parse the Dockerfile as plain text and validate six best-practice rules.
    Does not require Docker to be installed.
    """
    results: list[tuple[str, bool, str]] = []

    # Rule 0: file must exist
    if not _DOCKERFILE.exists():
        results.append(("Dockerfile exists", False, str(_DOCKERFILE)))
        return results
    results.append(("Dockerfile exists", True, str(_DOCKERFILE)))

    content = _DOCKERFILE.read_text()
    lines = content.splitlines()

    # Strip comments and blank lines for analysis
    effective_lines = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]

    # Rule 1: slim base image
    from_lines = [ln for ln in effective_lines if ln.upper().startswith("FROM")]
    uses_slim = any("slim" in ln for ln in from_lines)
    results.append((
        "FROM uses slim base (python:3.11-slim)",
        uses_slim,
        from_lines[0] if from_lines else "no FROM found",
    ))

    # Rule 2: non-root USER directive
    # Must have a USER instruction that is not "root"
    user_lines = [ln for ln in effective_lines if ln.upper().startswith("USER")]
    non_root_user = any(
        ln.split()[-1].lower() not in ("root", "0")
        for ln in user_lines
    )
    results.append((
        "Non-root USER directive present",
        non_root_user,
        user_lines[0] if user_lines else "no USER directive found",
    ))

    # Rule 3: HEALTHCHECK present
    has_healthcheck = any(ln.upper().startswith("HEALTHCHECK") for ln in effective_lines)
    results.append((
        "HEALTHCHECK directive present",
        has_healthcheck,
        "found" if has_healthcheck else "missing — add HEALTHCHECK instruction",
    ))

    # Rule 4: requirements.txt COPY'd before application source COPY
    # Find index of first COPY that mentions "requirements" and first that mentions app source
    req_copy_idx: int | None = None
    src_copy_idx: int | None = None
    for idx, ln in enumerate(effective_lines):
        if not ln.upper().startswith("COPY"):
            continue
        if "requirements" in ln.lower():
            req_copy_idx = idx
        elif (".py" in ln or "app" in ln.lower() or "service" in ln.lower()):
            if src_copy_idx is None:
                src_copy_idx = idx

    if req_copy_idx is not None and src_copy_idx is not None:
        order_ok = req_copy_idx < src_copy_idx
        order_detail = f"requirements at line-pos {req_copy_idx}, source at {src_copy_idx}"
    elif req_copy_idx is not None:
        order_ok = True  # requirements present; no explicit source COPY detected
        order_detail = "requirements COPY found"
    else:
        order_ok = False
        order_detail = "no COPY of requirements.txt found"
    results.append((
        "requirements.txt COPY'd before source files",
        order_ok,
        order_detail,
    ))

    # Rule 5: --no-cache-dir in pip install
    pip_lines = [ln for ln in effective_lines if "pip install" in ln]
    no_cache = any("--no-cache-dir" in ln for ln in pip_lines)
    results.append((
        "pip install uses --no-cache-dir",
        no_cache,
        pip_lines[0] if pip_lines else "no pip install found",
    ))

    # Rule 6: .dockerignore exists and excludes key paths
    di_exists = _DOCKERIGNORE.exists()
    if di_exists:
        di_content = _DOCKERIGNORE.read_text()
        excludes_pycache = "__pycache__" in di_content
        excludes_env = ".env" in di_content
        excludes_venv = ".venv" in di_content or "venv/" in di_content
        di_detail = (
            f"__pycache__={'yes' if excludes_pycache else 'MISSING'}, "
            f".env={'yes' if excludes_env else 'MISSING'}, "
            f"venv={'yes' if excludes_venv else 'MISSING'}"
        )
        di_ok = excludes_pycache and excludes_env and excludes_venv
    else:
        di_ok = False
        di_detail = f"not found at {_DOCKERIGNORE}"
    results.append((
        ".dockerignore exists and excludes __pycache__, .env, venv",
        di_ok,
        di_detail,
    ))

    return results


# ---------------------------------------------------------------------------
# Runner
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
        if detail and (not passed or "--" in detail or "found" in detail.lower()):
            print(f"         {detail}")
        if not passed:
            failures += 1
    return failures


def main() -> None:
    print("\nDay 7 Lab — Verification")
    print("Running in-process checks (no Docker, no API key required)")

    total_failures = 0
    total_failures += _print_results("PART A — Application Verification", verify_app())
    total_failures += _print_results("PART B — Dockerfile Best-Practice Lint", lint_dockerfile())

    print(f"\n{'='*60}")
    if total_failures == 0:
        print("  ALL CHECKS PASSED")
    else:
        print(f"  {total_failures} check(s) failed — see details above")
    print(f"{'='*60}\n")

    sys.exit(0 if total_failures == 0 else 1)


if __name__ == "__main__":
    main()
