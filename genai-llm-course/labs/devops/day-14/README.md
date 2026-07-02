# Day 14 Lab — CI/CD & IaC for LLM Services

Design and validate a production-grade CI/CD pipeline and Infrastructure-as-Code skeleton for the Acme HR Knowledge Assistant (FastAPI RAG service).

## Prerequisites

- Python 3.10+
- `pip install -r requirements.txt` (from this directory)
- No API key required — the shared app runs fully in mock mode

## What You'll Build

| File | Purpose |
|------|---------|
| `.github/workflows/deploy.yml` | 4-stage GitHub Actions pipeline (lint → build → eval gate → canary) |
| `main.tf` | Illustrative Terraform skeleton with variables, resource, and output blocks |
| `deploy.sh` | Canary deploy/rollback bash script |
| `starter.py` | Fill in the TODOs to validate the files above |

## Pipeline Stages (deploy.yml)

```
lint-and-test  →  build-and-scan  →  eval-gate  →  deploy-canary
```

1. **lint-and-test** — flake8 + pytest
2. **build-and-scan** — Docker build + Trivy image scan
3. **eval-gate** — runs Python eval script; fails if quality score < 0.7
4. **deploy-canary** — routes 10% traffic, smoke tests, then promotes or rolls back

## How to Run

```bash
# Fill in starter.py TODOs, then validate:
python starter.py

# Or run the complete solution directly:
python solution.py
```

## Expected Output

```
=== Day 14 Lab Validation ===

1. Checking workflow YAML...
   Pipeline stages in order: ['lint-and-test', 'build-and-scan', 'eval-gate', 'deploy-canary']
   [PASS] Workflow YAML valid

2. Checking Terraform skeleton...
   terraform: [PASS]
   variable: [PASS]
   resource: [PASS]
   output: [PASS]
   [PASS] Terraform skeleton valid

3. Checking deploy script...
   [PASS] deploy.sh exists and is executable

4. Testing shared app with TestClient...
   /health response: {'status': 'ok', ...}
   [PASS] App responds correctly

=== All validations passed! ===
```
