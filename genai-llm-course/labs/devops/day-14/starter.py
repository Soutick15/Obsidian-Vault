"""
Day 14 Lab — CI/CD & IaC for LLM Services
Starter file: fill in the TODOs, then run solution.py to validate.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import yaml

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
    """TODO: Load and parse the deploy.yml file. Return the parsed dict."""
    raise NotImplementedError("TODO: load the YAML file")


# ---------------------------------------------------------------------------
# Task 2 — Validate the pipeline stage order
# ---------------------------------------------------------------------------
def check_pipeline_stages(workflow: dict) -> list[str]:
    """TODO: Assert that the workflow has jobs: lint-and-test, build-and-scan,
    eval-gate, deploy-canary IN ORDER (check 'needs' chain).
    Return list of job names in order."""
    raise NotImplementedError("TODO: extract and order jobs by needs chain")


# ---------------------------------------------------------------------------
# Task 3 — Validate the Terraform skeleton
# ---------------------------------------------------------------------------
def check_terraform_blocks(tf_path: Path) -> dict[str, bool]:
    """TODO: Read main.tf and assert it contains:
    'terraform {', 'variable', 'resource', 'output'.
    Return dict of found blocks."""
    raise NotImplementedError("TODO: check terraform file")


# ---------------------------------------------------------------------------
# Task 4 — Validate the deploy script
# ---------------------------------------------------------------------------
def check_deploy_script(script_path: Path) -> bool:
    """TODO: Assert deploy.sh exists and is executable. Return True/False."""
    raise NotImplementedError("TODO: check deploy script")


# ---------------------------------------------------------------------------
# Task 5 — Test the shared FastAPI app with TestClient
# ---------------------------------------------------------------------------
def test_app_with_testclient() -> dict:
    """TODO: Import the shared app and use TestClient to GET /health.
    Assert status 200 and that 'status' is in the response JSON.
    Return response.json()."""
    raise NotImplementedError("TODO: use TestClient on the shared app")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Run solution.py to validate — fill in the TODOs first!")
