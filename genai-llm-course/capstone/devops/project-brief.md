# DevOps Capstone — Deploy & Operate the Acme HR Knowledge Assistant

## 1. Goal

Deploy and fully operationalize the **Acme HR Knowledge Assistant** as a production-ready containerized service. You will integrate every major concern covered in Days 6–14 into a single cohesive system:

- **Containerization** — multi-stage Docker image with security scanning
- **Kubernetes manifests** — Deployment, Service, HPA, ConfigMap
- **Redis caching** — semantic cache to reduce redundant LLM calls
- **Observability stack** — Prometheus metrics, structured logging, optional distributed tracing
- **Reliability wrapper** — circuit breaker, retry with backoff, graceful degradation
- **Security & governance** — secrets via env vars, audit logging, input guardrails
- **CI/CD pipeline** — GitHub Actions with lint → test → eval gate → canary deploy
- **Terraform IaC** — illustrative infrastructure provisioning skeleton

The shared application lives at `labs/devops/_shared/`. Your capstone deliverables wrap and deploy that application.

---

## 2. What You Are Building

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        CI/CD Pipeline                            │
│  GitHub Actions: lint → test → eval gate → canary → promote     │
└───────────────────────────────┬──────────────────────────────────┘
                                │ image push
                                ▼
                    ┌───────────────────────┐
                    │   Container Registry  │
                    │   (GHCR / ECR / GCR)  │
                    └───────────┬───────────┘
                                │ pull
                                ▼
         ┌──────────────────────────────────────────┐
         │              Kubernetes Cluster           │
         │                                          │
         │  ┌─────────────┐    ┌─────────────────┐  │
         │  │  Canary Pod │    │  Production Pods│  │
         │  │  (10% tfc)  │───▶│  (90% traffic)  │  │
         │  └─────────────┘    └────────┬────────┘  │
         │                             │            │
         │         ┌───────────────────┘            │
         │         │                                │
         │         ▼                                │
         │  ┌─────────────────────────────────────┐ │
         │  │       Acme HR Knowledge Assistant   │ │
         │  │  ┌──────────┐  ┌─────────────────┐  │ │
         │  │  │ Security │  │  Reliability    │  │ │
         │  │  │ Layer    │  │  Wrapper        │  │ │
         │  │  │(guardrail│  │ (circuit breaker│  │ │
         │  │  │ audit)   │  │  retry, backoff)│  │ │
         │  │  └──────────┘  └─────────────────┘  │ │
         │  │  ┌──────────┐  ┌─────────────────┐  │ │
         │  │  │ FastAPI  │  │  Observability  │  │ │
         │  │  │ App      │  │  (metrics, logs,│  │ │
         │  │  │(shared)  │  │   tracing)      │  │ │
         │  │  └──────────┘  └─────────────────┘  │ │
         │  └─────────────────────────────────────┘ │
         │         │                    │            │
         │         ▼                    ▼            │
         │  ┌────────────┐   ┌────────────────────┐  │
         │  │   Redis    │   │  Observability     │  │
         │  │  Semantic  │   │  Stack             │  │
         │  │  Cache     │   │  Prometheus        │  │
         │  └────────────┘   │  Grafana           │  │
         │                   │  Jaeger (optional) │  │
         │                   └────────────────────┘  │
         └──────────────────────────────────────────┘

                    ┌───────────────────────┐
                    │    Terraform IaC      │
                    │  (infra provisioning  │
                    │   skeleton)           │
                    └───────────────────────┘
```

---

## 3. Required Components

| Component | Day(s) | Description |
|-----------|--------|-------------|
| Containerization (Dockerfile, image build, scan) | Day 7 | Multi-stage Dockerfile; non-root user; health check; Trivy image scan in CI |
| Kubernetes manifests | Day 8 | Deployment, Service (ClusterIP/LoadBalancer), HPA with CPU/memory targets, ConfigMap |
| Caching layer | Day 10 | Redis semantic cache integration; cache hit/miss tracked in metrics |
| Observability | Day 11 | `/metrics` Prometheus endpoint; structured JSON logging with request_id, endpoint, latency; optional distributed tracing with trace_id propagation |
| Reliability wrapper | Day 12 | Circuit breaker (opens after N failures), retry with exponential backoff + jitter, graceful degradation fallback response |
| Security & governance | Day 13 | Secrets via environment variables only (none hardcoded); audit log per request; input guardrails blocking off-topic or harmful queries; secrets rotation pattern |
| CI/CD pipeline | Day 14 | GitHub Actions: lint → test → eval gate (quality threshold) → canary deploy → promote |
| Terraform IaC | Day 14 | Illustrative skeleton: provider, variables, resource (e.g., container cluster or VM), output blocks |
| Cost controls | Day 10 | Token counter per request; daily budget guard (reject/warn when exceeded); cache hit rate in metrics |

---

## 4. Deliverables

Your submission must include all of the following files under `capstone/devops/starter/` (or a directory of your choice):

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build; non-root user; health check instruction |
| `k8s/deployment.yaml` | Kubernetes Deployment manifest |
| `k8s/service.yaml` | Kubernetes Service manifest |
| `k8s/hpa.yaml` | HorizontalPodAutoscaler manifest |
| `k8s/configmap.yaml` | ConfigMap for non-secret configuration |
| `.github/workflows/deploy.yml` | CI/CD pipeline: lint → test → eval gate → canary deploy |
| `main.tf` | Terraform IaC skeleton |
| `observability.py` | Prometheus metrics endpoint, structured logging, optional tracing |
| `reliability.py` | Circuit breaker, retry with exponential backoff + jitter, health check |
| `security.py` | Input guardrails, audit logging, secrets handling pattern |
| `deploy.sh` | Canary deploy and rollback script |
| `README.md` | How to run in mock mode, with Docker, with Kubernetes; demo walkthrough |

---

## 5. How to Run / Validate / Demo

### Mock Mode (no API key, no cloud infra required)

All modules must be importable and runnable without credentials:

```bash
# Validate observability module
python -c "
import sys; sys.path.insert(0, '.')
from capstone.devops.starter.observability import MetricsCollector
m = MetricsCollector()
m.record_request(endpoint='/query', latency_ms=42, status=200)
print('observability OK')
"

# Validate reliability module
python -c "
import sys; sys.path.insert(0, '.')
from capstone.devops.starter.reliability import CircuitBreaker, retry_with_backoff
cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
print('circuit breaker state:', cb.state)
print('reliability OK')
"

# Validate security module
python -c "
import sys; sys.path.insert(0, '.')
from capstone.devops.starter.security import InputGuardrail, AuditLogger
g = InputGuardrail()
result = g.check('What is the vacation policy?')
print('guardrail check:', result)
print('security OK')
"
```

### Docker Build & Run

```bash
# Build the image
docker build -t acme-hr:capstone .

# Run locally (mock mode — no API key needed for startup)
docker run -p 8000:8000 \
  -e LLM_PROVIDER=mock \
  -e REDIS_URL=redis://localhost:6379 \
  acme-hr:capstone

# Verify health check
curl http://localhost:8000/health

# Verify metrics endpoint
curl http://localhost:8000/metrics
```

### Kubernetes (minikube)

```bash
# Start minikube (single-node local cluster)
minikube start

# Apply all manifests
kubectl apply -f k8s/

# Check pod status
kubectl get pods -l app=acme-hr

# Port-forward for local access
kubectl port-forward svc/acme-hr 8000:80

# Scale manually to test HPA behavior
kubectl scale deployment acme-hr --replicas=3
```

### Validate CI/CD Pipeline Logic

```bash
# Run the eval gate script standalone
python capstone/devops/starter/eval_gate.py

# Dry-run the canary deploy script
bash capstone/devops/starter/deploy.sh --dry-run --canary-weight 10
```

### Validate Terraform Syntax

```bash
# Initialize and validate (no cloud credentials needed for syntax check)
terraform init -backend=false
terraform validate
```

---

### 5-Step Demo Walkthrough

**Step 1 — Build & Scan**
```bash
docker build -t acme-hr:capstone .
# Show multi-stage layers, non-root user
docker inspect acme-hr:capstone | python -c "import sys,json; cfg=json.load(sys.stdin)[0]['Config']; print('User:', cfg.get('User')); print('Healthcheck:', cfg.get('Healthcheck'))"
```

**Step 2 — Validate All Modules**
```bash
python -m pytest capstone/devops/starter/tests/ -v
# Show: all reliability, security, observability unit tests pass
```

**Step 3 — Deploy to Kubernetes**
```bash
kubectl apply -f k8s/
kubectl rollout status deployment/acme-hr
# Show pod running, HPA active
```

**Step 4 — Observe**
```bash
# Send a request
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" \
     -d '{"question": "What is the vacation policy?"}'

# Check metrics
curl http://localhost:8000/metrics | grep acme_hr

# Show structured log output
kubectl logs deployment/acme-hr | python -c "import sys,json; [print(json.dumps(json.loads(l), indent=2)) for l in sys.stdin if l.strip()]" | head -40
```

**Step 5 — Rollback**
```bash
# Simulate a bad deploy, then rollback
bash capstone/devops/starter/deploy.sh --rollback
kubectl rollout history deployment/acme-hr
```

---

## 6. Capstone Scope Note

This is an integrative educational exercise. The emphasis is on **correctness of design patterns** and demonstrated understanding of each component's role — not on managing live cloud resources.

**Guidance on scope:**
- Use mock or stub implementations wherever real cloud infrastructure is unavailable. A `MockLLMClient`, `MockRedisCache`, or in-memory circuit breaker is perfectly valid as long as the pattern is correct.
- All Python modules must be importable and their core logic executable without API keys.
- Kubernetes manifests must be syntactically valid YAML but do not need to target a real cluster.
- Terraform must pass `terraform validate` but does not need real provider credentials.
- GitHub Actions workflow must be syntactically valid but does not need to run against a live repository.

The goal is a system where every layer is present, wired together, and demonstrably understood — not a production deployment to a live cloud provider.
