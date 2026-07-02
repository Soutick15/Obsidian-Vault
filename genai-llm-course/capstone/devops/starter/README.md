# DevOps Capstone Starter — Acme HR Knowledge Assistant

## Overview

This is the starter scaffold for the DevOps capstone project. You will build a production-grade deployment of the Acme HR Knowledge Assistant — an LLM-powered RAG chatbot that answers employee questions about HR policies.

The shared FastAPI application lives at `labs/devops/_shared/app.py`. Your job is to wire it into an observable, reliable, and secure deployment pipeline using the modules in this directory.

## File Structure

```
capstone/devops/starter/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Multi-stage container build
├── observability.py             # Metrics, structured logging, trace IDs
├── reliability.py               # Circuit breaker, retry, fallback
├── security.py                  # Audit logging, guardrails, secrets validation
├── k8s/
│   ├── deployment.yaml          # Kubernetes Deployment (2 replicas, probes, HPA-ready)
│   ├── service.yaml             # ClusterIP Service
│   └── hpa.yaml                 # HorizontalPodAutoscaler (CPU + memory)
└── .github/
    └── workflows/
        └── deploy.yml           # CI/CD pipeline stub (lint → build → eval gate → canary)
```

## How to Run in Mock Mode

No API key required. All modules import cleanly with `LLM_PROVIDER=mock` (the default).

```bash
# Verify imports work
python -c "from capstone.devops.starter.observability import record_request; print('OK')"
python -c "from capstone.devops.starter.reliability import CircuitBreaker; print('OK')"
python -c "from capstone.devops.starter.security import audit_log; print('OK')"

# Run the shared app in mock mode
LLM_PROVIDER=mock uvicorn labs.devops._shared.app:app --reload
```

## How to Run with Docker

```bash
# Build
docker build -t acme-hr-assistant:dev capstone/devops/starter/

# Run in mock mode (no API key needed)
docker run -e LLM_PROVIDER=mock -p 8000:8000 acme-hr-assistant:dev

# Run with a real provider
docker run -e LLM_PROVIDER=anthropic -e ANTHROPIC_API_KEY=sk-... -p 8000:8000 acme-hr-assistant:dev
```

## How to Validate

Point the pipeline validator at the day-14 solution script:

```bash
python labs/devops/day-14/solution.py --validate capstone/devops/starter/
```

The validator checks:
- `/health` returns 200
- `/metrics` returns Prometheus-format text
- `/chat` returns `{"answer": ..., "sources": [...]}` shape
- Circuit breaker trips after `failure_threshold` failures
- Audit log entries are emitted for each request

## TODOs Guide

Each file has inline `TODO` comments. Here is a quick summary of what to implement:

| File | Key TODOs |
|------|-----------|
| `observability.py` | Wire Prometheus counters in `record_request()`; return `generate_latest()` from `get_metrics_text()` |
| `reliability.py` | Implement `CircuitBreaker.call()` state machine; implement `retry_with_backoff()` with exponential backoff + jitter |
| `security.py` | Add HR topic hint check in `check_input_guardrail()`; extend `REQUIRED_ENV_VARS` for non-mock mode |
| `Dockerfile` | Swap CMD to your entrypoint; add trivy scan step in CI |
| `k8s/deployment.yaml` | Replace `image:` with your registry path; add `imagePullSecrets` if needed |
| `.github/workflows/deploy.yml` | Fill in eval gate script; implement canary promote/rollback logic |

Stubs that raise `NotImplementedError` are intentional — replace them with your implementation.
