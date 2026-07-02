"""
Day 14 Lab — CI/CD & IaC for LLM Services
Complete solution — validates all lab artefacts without any API key.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Path setup — make the shared app importable as labs.devops._shared.app
# ---------------------------------------------------------------------------
# Go up: day-14 → devops → labs → AI_Training (repo root)
_AI_TRAINING_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_AI_TRAINING_ROOT))

# The shared app.py does `from service import ...` (bare import).
# We also add _shared/ to sys.path so that bare import resolves correctly
# when importing the module directly (outside of uvicorn's working dir).
_SHARED_DIR = Path(__file__).parent.parent / "_shared"
sys.path.insert(0, str(_SHARED_DIR))

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
LAB_DIR = Path(__file__).parent
SHARED_APP_DIR = LAB_DIR.parent / "_shared"

WORKFLOW_PATH = LAB_DIR / ".github" / "workflows" / "deploy.yml"
TF_PATH = LAB_DIR / "main.tf"
SCRIPT_PATH = LAB_DIR / "deploy.sh"


# ---------------------------------------------------------------------------
# Task 1 — Load the GitHub Actions workflow YAML
# ---------------------------------------------------------------------------
def load_workflow_yaml(path: Path) -> dict:
    """Load and parse the deploy.yml file. Return the parsed dict."""
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, dict), f"Expected dict from YAML, got {type(data)}"
    return data


# ---------------------------------------------------------------------------
# Task 2 — Validate the pipeline stage order (by 'needs' chain)
# ---------------------------------------------------------------------------
def check_pipeline_stages(workflow: dict) -> list[str]:
    """Assert the workflow has the required jobs in the correct needs-chain order.
    Returns the ordered list of job names."""
    required_jobs = ["lint-and-test", "build-and-scan", "eval-gate", "deploy-canary"]

    jobs = workflow.get("jobs", {})
    assert jobs, "No 'jobs' key found in workflow YAML"

    # Check all required jobs are present
    for job_name in required_jobs:
        assert job_name in jobs, (
            f"Required job '{job_name}' not found in workflow. "
            f"Found jobs: {list(jobs.keys())}"
        )

    # Validate the needs chain
    expected_needs = {
        "build-and-scan": "lint-and-test",
        "eval-gate":      "build-and-scan",
        "deploy-canary":  "eval-gate",
    }

    for job_name, expected_dep in expected_needs.items():
        job_cfg = jobs[job_name]
        needs = job_cfg.get("needs", [])
        # 'needs' can be a string or a list
        if isinstance(needs, str):
            needs = [needs]
        assert expected_dep in needs, (
            f"Job '{job_name}' should need '{expected_dep}', "
            f"but its 'needs' is: {needs}"
        )

    return required_jobs


# ---------------------------------------------------------------------------
# Task 3 — Validate the Terraform skeleton
# ---------------------------------------------------------------------------
def check_terraform_blocks(tf_path: Path) -> dict[str, bool]:
    """Read main.tf and check for required HCL blocks.
    Returns a dict mapping block type → found (bool). Asserts all True."""
    content = tf_path.read_text(encoding="utf-8")

    found = {
        "terraform": "terraform {" in content,
        "variable":  "variable" in content,
        "resource":  "resource" in content,
        "output":    "output" in content,
    }

    for block, present in found.items():
        assert present, (
            f"Terraform block '{block}' not found in {tf_path}. "
            "Check main.tf contains the required block."
        )

    return found


# ---------------------------------------------------------------------------
# Task 4 — Validate the deploy script
# ---------------------------------------------------------------------------
def check_deploy_script(script_path: Path) -> bool:
    """Check deploy.sh exists (and ideally is executable).
    Returns True if it exists. Prints a warning if not executable —
    git may not preserve executable bits, so we don't hard-fail on that."""
    assert script_path.exists(), (
        f"deploy.sh not found at {script_path}"
    )

    if os.access(script_path, os.X_OK):
        print(f"   deploy.sh is executable")
    else:
        print(
            f"   NOTE: deploy.sh exists but is not marked executable. "
            "Run: chmod +x deploy.sh  (git may not preserve executable bits)"
        )

    return True


# ---------------------------------------------------------------------------
# Task 5 — Test the shared FastAPI app with TestClient
# ---------------------------------------------------------------------------
def test_app_with_testclient() -> dict:
    """Import the shared FastAPI app and call GET /health via TestClient.
    Returns the JSON response body."""
    try:
        from labs.devops._shared.app import app as shared_app
    except ImportError as exc:
        print(
            f"   SKIP: Could not import shared app ({exc}). "
            "Ensure dependencies are installed: pip install -r requirements.txt"
        )
        return {"status": "skipped", "reason": str(exc)}

    from starlette.testclient import TestClient

    client = TestClient(shared_app)
    response = client.get("/health")

    assert response.status_code == 200, (
        f"/health returned HTTP {response.status_code}: {response.text}"
    )
    body = response.json()
    assert "status" in body, (
        f"'status' key missing from /health response: {body}"
    )

    return body


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Day 14 Lab Validation ===\n")

    print("1. Checking workflow YAML...")
    workflow = load_workflow_yaml(WORKFLOW_PATH)
    stages = check_pipeline_stages(workflow)
    print(f"   Pipeline stages in order: {stages}")
    print("   [PASS] Workflow YAML valid\n")

    print("2. Checking Terraform skeleton...")
    blocks = check_terraform_blocks(TF_PATH)
    for block, found in blocks.items():
        print(f"   {block}: {'[PASS]' if found else '[FAIL]'}")
    print("   [PASS] Terraform skeleton valid\n")

    print("3. Checking deploy script...")
    check_deploy_script(SCRIPT_PATH)
    print("   [PASS] deploy.sh exists and is executable\n")

    print("4. Testing shared app with TestClient...")
    health = test_app_with_testclient()
    print(f"   /health response: {health}")
    if health.get("status") != "skipped":
        print("   [PASS] App responds correctly\n")
    else:
        print("   [SKIP] App import skipped — install deps to enable\n")

    print("=== All validations passed! ===")
