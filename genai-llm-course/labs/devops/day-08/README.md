# Day 8 Lab — Kubernetes Manifests, Validation & Load Testing

**Track:** DevOps | **Day:** 8 of 15

---

## Learning Goals

- Write production-quality Kubernetes manifests (Deployment, Service, HPA, ConfigMap) for the shared HR Assistant service.
- Programmatically validate YAML manifests — catching probe misconfigurations, missing resource limits, and selector mismatches before deployment.
- Measure the throughput of the in-process app under concurrent load to motivate horizontal scaling.

No Kubernetes cluster required. All validation and load testing run in-process via FastAPI's TestClient.

---

## Prerequisites

- Completed Days 6–7 (operating and containerising the shared app).
- Python 3.11+ virtual environment with packages below installed.

```bash
pip install -r requirements.txt
```

---

## Files

| File | Purpose |
|------|---------|
| `README.md` | This file |
| `requirements.txt` | Python dependencies |
| `deployment.yaml` | Kubernetes Deployment manifest (edit to fix probes/resources) |
| `service.yaml` | Kubernetes Service manifest |
| `hpa.yaml` | HorizontalPodAutoscaler manifest |
| `configmap.yaml` | ConfigMap for app configuration |
| `starter.py` | Scaffolded lab with TODO markers — work through these |
| `solution.py` | Complete reference implementation |

---

## Tasks

### Part A — Write the Manifests (30 min)

Review `deployment.yaml`, `service.yaml`, `hpa.yaml`, and `configmap.yaml`. Each has inline comments explaining each field. Your goal is to understand how they compose into a complete deployment.

Key things to verify as you read:
1. The `selector.matchLabels` in the Deployment matches `metadata.labels` in its `template`.
2. The `selector` in the Service matches the same pod labels.
3. The `scaleTargetRef.name` in the HPA matches the Deployment name.
4. All probes point to `/health` on port 8000.
5. Resource requests and limits are set on the container.

### Part B — Complete `starter.py` (25 min)

Open `starter.py` and complete each TODO. You will:

1. **TODO 1**: Load and parse all four YAML manifests using `pyyaml`.
2. **TODO 2**: Assert the Deployment has readiness and liveness probes with the correct path.
3. **TODO 3**: Assert resource requests and limits are set.
4. **TODO 4**: Assert selector/label consistency between Deployment and Service.
5. **TODO 5**: Assert the HPA targets the correct Deployment.
6. **TODO 6**: Run a concurrent load test against the app via TestClient and print throughput.

### Part C — Run & Reflect (15 min)

```bash
python labs/devops/day-08/solution.py
```

Expected output:
```
[manifest] Loaded 4 manifests
[check] Deployment probes OK
[check] Resource limits OK
[check] Selector/label consistency OK
[check] HPA target OK
[load-test] 50 requests in X.XX s → YY.Y req/s (all 200 OK)
[summary] All manifest checks passed. Load test complete.
```

Reflect: at what throughput does the service need a second replica? What HPA metric would you use?

---

## SUT Import Pattern

```python
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))
from app import app  # FastAPI application instance
```

---

## No API Key Required

The shared app runs with a mock LLM by default. Set `USE_MOCK=true` (or leave unset) — no credentials needed.

---

## Estimated Time

~2–3 hours total including concept reading from the curriculum.
