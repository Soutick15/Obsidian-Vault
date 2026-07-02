# DevOps Capstone Rubric — Acme HR Knowledge Assistant

**Total: 100 points**

> **Grading note:** Full marks in each section require working code, not just stubs. Partial credit applies when the pattern is correct but implementation is incomplete. A correct design with a non-functional stub earns approximately half the points for that criterion.

---

## 1. Containerization (12 pts)

### 1.1 Multi-stage Dockerfile present and syntactically valid (4 pts)

| Score | Criteria |
|-------|----------|
| 4 | `Dockerfile` present; uses `FROM ... AS builder` + final stage; passes `docker build --no-cache` without error |
| 3 | Multi-stage structure present but minor syntax issue; builds with trivial fix |
| 2 | Single-stage Dockerfile only; builds successfully |
| 1 | Dockerfile present but does not build |
| 0 | No Dockerfile |

### 1.2 Image builds successfully (4 pts)

| Score | Criteria |
|-------|----------|
| 4 | `docker build -t acme-hr:capstone .` completes without error; image layers are cached correctly across stages |
| 2 | Builds with warnings or requires manual flag adjustments |
| 0 | Build fails |

### 1.3 Non-root user, minimal base image, health check instruction (4 pts)

| Score | Criteria |
|-------|----------|
| 4 | All three present: `USER nonroot` (or equivalent non-root UID), slim/alpine base image in final stage, `HEALTHCHECK` instruction pointing to `/health` |
| 3 | Two of three present |
| 1–2 | One of three present |
| 0 | None present |

---

## 2. Kubernetes & Scaling (15 pts)

### 2.1 Deployment manifest with correct spec (5 pts)

| Score | Criteria |
|-------|----------|
| 5 | `k8s/deployment.yaml` present; valid YAML; correct `spec.replicas`, `spec.template.spec.containers[*].image`, and environment config via `envFrom` or `env`; resource requests/limits set |
| 3–4 | Deployment present and valid but missing resource limits or env wiring |
| 1–2 | Deployment present but significant spec errors |
| 0 | No deployment manifest |

### 2.2 Service manifest (3 pts)

| Score | Criteria |
|-------|----------|
| 3 | `k8s/service.yaml` present; correct `selector` matching deployment labels; appropriate `type` (ClusterIP or LoadBalancer); port mapping correct |
| 2 | Present but selector or port mapping incorrect |
| 1 | Present but non-functional spec |
| 0 | Missing |

### 2.3 HPA configured with CPU/memory targets (4 pts)

| Score | Criteria |
|-------|----------|
| 4 | `k8s/hpa.yaml` present; references correct deployment; `minReplicas`, `maxReplicas`, and at least one metric (CPU utilization %) configured correctly |
| 2–3 | HPA present but missing memory metric or min/max bounds |
| 1 | HPA present but misconfigured `scaleTargetRef` |
| 0 | Missing |

### 2.4 ConfigMap or Secret for configuration (3 pts)

| Score | Criteria |
|-------|----------|
| 3 | `k8s/configmap.yaml` (or Secret) present; non-secret config (e.g., log level, provider name, cache TTL) stored there and referenced in Deployment |
| 2 | ConfigMap present but not referenced in Deployment |
| 1 | Config values hardcoded in Deployment only |
| 0 | Missing |

---

## 3. Observability (15 pts)

### 3.1 `/metrics` endpoint returns Prometheus-formatted counters (5 pts)

| Score | Criteria |
|-------|----------|
| 5 | `observability.py` exports a `/metrics` endpoint; response contains valid Prometheus text format (`# HELP`, `# TYPE`, counter/gauge lines); at minimum: request count, error count, latency histogram |
| 3–4 | Metrics endpoint present and returns Prometheus format but missing one of the required metric types |
| 1–2 | Metrics endpoint present but returns non-standard format or minimal data |
| 0 | No metrics endpoint |

### 3.2 Structured JSON logging with request_id, endpoint, latency (5 pts)

| Score | Criteria |
|-------|----------|
| 5 | Every request produces a JSON log line containing at minimum: `request_id`, `endpoint`, `latency_ms`, `status_code`, `timestamp` |
| 3–4 | JSON logging present; missing one or two required fields |
| 1–2 | Logging present but plain text or missing most structured fields |
| 0 | No structured logging |

### 3.3 Tracing: trace_id propagated through request (5 pts — bonus/optional)

| Score | Criteria |
|-------|----------|
| 5 | `trace_id` generated or propagated from `X-Trace-ID` header; included in log lines and response headers; optional Jaeger/OTLP export configured |
| 3–4 | `trace_id` propagated in logs but not in response headers, or export not configured |
| 1–2 | `trace_id` present in some but not all log events |
| 0 | No tracing |

> This section is optional bonus. Students who do not implement tracing are not penalized; the overall rubric totals remain at 100 points without it.

---

## 4. Reliability (12 pts)

### 4.1 Circuit breaker wrapper (5 pts)

| Score | Criteria |
|-------|----------|
| 5 | `reliability.py` implements a circuit breaker: transitions CLOSED → OPEN after N consecutive failures; rejects calls fast when OPEN; transitions OPEN → HALF-OPEN → CLOSED on recovery; state is observable |
| 3–4 | Circuit breaker present; transitions work but recovery logic incomplete |
| 1–2 | Stub present with correct interface but no state machine logic |
| 0 | Missing |

### 4.2 Retry with exponential backoff + jitter (4 pts)

| Score | Criteria |
|-------|----------|
| 4 | Retry decorator/wrapper in `reliability.py`; exponential delay (`base * 2^attempt`); jitter applied (random offset); configurable max attempts and max delay |
| 3 | Retry present; exponential backoff correct but no jitter |
| 1–2 | Fixed-delay retry only; or retry present but not wired to application calls |
| 0 | Missing |

### 4.3 Graceful degradation (3 pts)

| Score | Criteria |
|-------|----------|
| 3 | When circuit is OPEN (or all retries exhausted), a meaningful fallback response is returned to the caller rather than an unhandled exception; fallback is logged |
| 2 | Fallback present but not logged, or only returns HTTP 503 with no body |
| 1 | Exception propagated to caller with no fallback |
| 0 | Missing |

---

## 5. Security & Governance (14 pts)

### 5.1 All secrets via environment variables, none hardcoded (4 pts)

| Score | Criteria |
|-------|----------|
| 4 | Grep of codebase shows zero hardcoded API keys, passwords, or tokens; all secrets read from `os.environ` or equivalent; `.env.example` provided with placeholder values |
| 3 | No hardcoded secrets in Python files; Dockerfile or YAML contains a non-sensitive default that should be externalized |
| 1–2 | One or more secrets hardcoded in non-production path |
| 0 | API key or password present in committed code |

### 5.2 Audit log entry per request (4 pts)

| Score | Criteria |
|-------|----------|
| 4 | Every request to `/query` produces an audit log entry containing: caller identifier (user/IP), query text (truncated), timestamp, response status, and token count |
| 3 | Audit log present; missing one required field |
| 1–2 | Audit log present but only on errors, or missing most fields |
| 0 | No audit logging |

### 5.3 Input guardrail blocks off-topic or harmful queries (4 pts)

| Score | Criteria |
|-------|----------|
| 4 | `security.py` implements `InputGuardrail` class; blocks queries outside HR domain (e.g., requests for stock tips, harmful content); returns a clear, user-friendly rejection message; guardrail logic is testable without an API key |
| 3 | Guardrail present and functional; rejection message generic or not user-friendly |
| 1–2 | Guardrail stub present but logic always passes or always blocks |
| 0 | No guardrail |

### 5.4 Secrets rotation pattern documented (2 pts)

| Score | Criteria |
|-------|----------|
| 2 | README or inline comments describe a concrete secrets rotation pattern: how to update the secret, restart pods without downtime (rolling restart), and verify the new secret is active |
| 1 | Rotation mentioned but no concrete steps |
| 0 | Not mentioned |

---

## 6. CI/CD Pipeline & IaC (18 pts)

### 6.1 GitHub Actions workflow with lint → test → eval-gate → deploy stages (6 pts)

| Score | Criteria |
|-------|----------|
| 6 | `.github/workflows/deploy.yml` present and valid YAML; four distinct jobs or steps: (1) lint with `ruff`/`flake8`, (2) unit tests with `pytest`, (3) eval gate, (4) canary deploy; jobs use `needs:` to enforce order; secrets referenced via `${{ secrets.* }}` |
| 4–5 | Workflow present and valid; missing one stage or `needs:` ordering |
| 2–3 | Workflow present; two or more stages missing or misordered |
| 1 | Workflow present but non-functional YAML |
| 0 | Missing |

### 6.2 Eval gate script that fails pipeline if quality score < threshold (5 pts)

| Score | Criteria |
|-------|----------|
| 5 | `eval_gate.py` (or equivalent) runs a set of test queries against the app; computes a quality score (e.g., keyword match, response length, latency); exits with non-zero code when score < configurable threshold; threshold is documented |
| 3–4 | Eval gate present; quality scoring logic correct but threshold not configurable or exit code not used correctly |
| 1–2 | Eval gate stub always passes or score computation missing |
| 0 | Missing |

### 6.3 Terraform skeleton with provider, variables, resource, output blocks (4 pts)

| Score | Criteria |
|-------|----------|
| 4 | `main.tf` present; passes `terraform validate`; contains: `terraform {}` block with provider requirement, at least one `variable` block, at least one `resource` block (can be a null_resource or illustrative cloud resource), at least one `output` block |
| 3 | Present and validates; missing one of the four required block types |
| 1–2 | Present but does not pass `terraform validate` |
| 0 | Missing |

### 6.4 Canary deploy script with rollback capability (3 pts)

| Score | Criteria |
|-------|----------|
| 3 | `deploy.sh` implements both `--canary-weight N` (patch Service/Ingress weights or use kubectl rollout) and `--rollback` (reverts to previous revision via `kubectl rollout undo`); dry-run mode present |
| 2 | Deploy script present; canary or rollback works but not both |
| 1 | Script present but no canary/rollback logic |
| 0 | Missing |

---

## 7. Cost Controls (8 pts)

### 7.1 Token counter per request (3 pts)

| Score | Criteria |
|-------|----------|
| 3 | Token count (prompt + completion) recorded per request; surfaced in structured log output and in the `/metrics` endpoint as a counter or histogram |
| 2 | Token count logged but not in metrics |
| 1 | Token count stub returns a fixed value |
| 0 | Missing |

### 7.2 Budget guard (3 pts)

| Score | Criteria |
|-------|----------|
| 3 | Daily token or cost accumulator tracked (in-memory or Redis); when daily budget exceeded, requests are rejected with a clear message or downgraded to cached-only mode; budget limit is configurable via environment variable |
| 2 | Budget guard present; rejects requests when exceeded but limit not configurable |
| 1 | Budget guard stub; accumulator not implemented |
| 0 | Missing |

### 7.3 Cache hit rate tracked in metrics (2 pts)

| Score | Criteria |
|-------|----------|
| 2 | `cache_hits_total` and `cache_misses_total` counters present in `/metrics`; ratio computable from these counters |
| 1 | Cache hit/miss counted in logs but not in Prometheus metrics |
| 0 | Missing |

---

## 8. Documentation & Demo (6 pts)

### 8.1 README covers: run in mock mode, run with Docker, how to demo (3 pts)

| Score | Criteria |
|-------|----------|
| 3 | `README.md` present; contains working commands for all three scenarios: (1) mock/local Python run, (2) Docker build + run, (3) demo walkthrough or link to demo script |
| 2 | README present; covers two of three scenarios |
| 1 | README present but commands are incomplete or incorrect |
| 0 | No README |

### 8.2 5-minute demo script or walkthrough documented (3 pts)

| Score | Criteria |
|-------|----------|
| 3 | A step-by-step demo script is present (in README or a separate `DEMO.md`/`demo.sh`); covers at minimum: build, validate, deploy, observe metrics, trigger rollback; each step has the exact command to run |
| 2 | Demo walkthrough present but missing one or two steps |
| 1 | Demo mentioned but no concrete commands |
| 0 | Missing |

---

## Score Summary

| Section | Max Points |
|---------|-----------|
| 1. Containerization | 12 |
| 2. Kubernetes & Scaling | 15 |
| 3. Observability | 15 |
| 4. Reliability | 12 |
| 5. Security & Governance | 14 |
| 6. CI/CD Pipeline & IaC | 18 |
| 7. Cost Controls | 8 |
| 8. Documentation & Demo | 6 |
| **Total** | **100** |

> **Partial credit policy:** When the pattern is architecturally correct and the code structure demonstrates understanding of the concept, award at least 50% of the points for that criterion even if the implementation is incomplete. Reserve 0 scores for missing files or stubs that show no engagement with the concept.
