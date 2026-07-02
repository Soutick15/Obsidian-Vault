# Day 15 — Capstone Completion & Course Review

**Track:** DevOps | **Module:** Capstone Wrap-Up | **Day:** 15 of 15

---

## 1. Learning Objectives

By the end of this session you will be able to:

1. **Complete and demonstrate** your DevOps capstone project end-to-end, from health checks through canary traffic and incident simulation.
2. **Consolidate the full DevOps track** (Days 6–14) by connecting every topic into a single coherent operational picture.
3. **Self-assess your deployment** against the capstone rubric, identifying strengths and gaps without external evaluation.
4. **Reflect deeply on design decisions** in your own system — scaling, secrets management, drift detection, SLOs, and cost controls.
5. **Plan a continued learning roadmap** across LLMOps, Kubernetes, advanced observability, FinOps, and infrastructure-as-code.

---

## 2. Capstone Completion & Demo

### 2.1 Finishing Checklist

The following checklist maps directly to the rubric categories in `capstone/devops/`. Work through it before your demo walkthrough.

#### Service Operability (Day 6 foundations)
- [ ] FastAPI (or equivalent) service exposes a `/health` liveness endpoint returning `{"status": "ok"}` with HTTP 200
- [ ] A `/ready` readiness endpoint reflects upstream dependencies (model provider, vector DB) before returning 200
- [ ] `/metrics` (Prometheus-format) endpoint is present and scrape-ready
- [ ] Service logs are structured JSON (not free-text), with `request_id`, `latency_ms`, `model`, and `status` fields minimum

#### Containerisation & Serving (Day 7)
- [ ] `Dockerfile` uses a slim base image, multi-stage build, non-root user, `.dockerignore`, and `HEALTHCHECK` directive
- [ ] 12-factor config: all secrets and environment values come from env vars, not hardcoded values
- [ ] `docker build` completes without errors; `docker run` starts the service and health check passes

#### Orchestration (Day 8)
- [ ] Kubernetes manifests (or equivalent) exist: `Deployment`, `Service`, `HorizontalPodAutoscaler`
- [ ] GPU resource requests/limits are present if GPU inference is used
- [ ] Liveness and readiness probes are wired into the pod spec

#### Vector DB / Data Infra (Day 9)
- [ ] Vector store is initialised and queryable (embedding model + index)
- [ ] Data pipeline (ingest → embed → upsert) is documented and reproducible
- [ ] Index health is checkable (document count, embedding dimension)

#### Cost & Caching (Day 10)
- [ ] Prompt/semantic cache is in place; cache hit rate is observable
- [ ] Per-request token cost is estimated and logged
- [ ] Monthly cost projection is documented with assumptions

#### Observability (Days 11–12)
- [ ] Prometheus metrics cover: request latency (histogram), token throughput, error rate, cache hit rate
- [ ] At least one Grafana dashboard (or equivalent) visualises the four golden signals (latency, traffic, errors, saturation)
- [ ] Alerts are defined for: p95 latency > threshold, error rate > threshold, cost anomaly

#### Deployment Strategy (Day 13)
- [ ] A canary or blue-green deployment script/manifest exists
- [ ] Traffic split is configurable (e.g., 10% canary / 90% stable)
- [ ] Automated rollback condition is defined (error rate or latency spike)

#### Incident Handling & Reliability (Day 14)
- [ ] Runbook exists for at least two failure scenarios (provider outage, OOM/GPU fault)
- [ ] Fallback path is implemented (e.g., degraded model, cached responses, circuit breaker)
- [ ] Post-incident template is present in the repo

---

### 2.2 How to Validate and Run the Deployed Service

**Step 1 — Start the service**
```bash
# From capstone/devops/ root
docker compose up -d          # or: kubectl apply -f manifests/
```

**Step 2 — Confirm health and readiness**
```bash
# Health (liveness)
curl -s http://localhost:8000/health | python3 -m json.tool
# Expected: {"status": "ok"}

# Readiness (upstream deps)
curl -s http://localhost:8000/ready | python3 -m json.tool
# Expected: {"status": "ready", "dependencies": {"vector_db": "ok", "model": "ok"}}
```

**Step 3 — Check metrics**
```bash
curl -s http://localhost:8000/metrics | grep -E "^(llm_|http_)"
# Should show: request_latency_seconds histogram, token_total counter, cache_hits_total
```

**Step 4 — Send a test inference request**
```bash
curl -s -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain what a readiness probe does.", "max_tokens": 100}'
```

**Step 5 — Trigger a canary deploy**
```bash
# Example: shift 10% traffic to the new image
kubectl set image deployment/llm-service-canary \
  app=myregistry/llm-service:v2 --record
# Verify split via Ingress or service mesh weight annotation
```

**Step 6 — Simulate an incident and test fallback**
```bash
# Kill the upstream model provider (simulate outage)
docker stop mock-model-provider   # or scale the stub pod to 0
# Send a request — expect fallback response or graceful degradation
curl -s -X POST http://localhost:8000/generate \
  -d '{"prompt": "test fallback", "max_tokens": 50}'
# Expected: degraded response with X-Fallback: true header, not a 500
```

**Step 7 — Present the Grafana dashboard** (or equivalent)
Open `http://localhost:3000` → dashboard `LLM Service Overview`. Walk through:
- Request rate (last 15 min)
- p50 / p95 / p99 latency
- Error rate
- Cache hit %
- Token throughput and estimated cost

---

## 3. Capstone Review & Reflection

These questions are for **your own reflection**. There are no grades here — the goal is to deepen your understanding of the trade-offs in the system *you* built.

---

### Q1 — Scaling strategy
**Q1. If your service needs to handle 10× its current load tomorrow, what exactly changes? Where is the first bottleneck?**

<details>
<summary>Show answer</summary>

**Model answer:**
The first bottleneck is almost always the inference layer (GPU compute or API rate limits). Horizontally scaling the FastAPI pods handles routing overhead but not model throughput. For a self-hosted model, you need more GPU replicas behind a load balancer, plus a batching queue (e.g., vLLM's continuous batching). For a hosted provider, you hit per-minute token quotas and need request queuing with back-pressure. The HPA only helps if the metric it tracks (CPU/custom) correctly reflects the actual bottleneck.

**What a strong understanding looks like:**
You name the specific component that saturates first (not just "scale up"), distinguish compute vs. network vs. API quota bottlenecks, and describe how the cache affects scaling (higher hit rate = less model load).

</details>

---

### Q2 — Secrets management
**Q2. Where exactly do your API keys and database credentials live in your deployed system? What happens if one is rotated?**

<details>
<summary>Show answer</summary>

**Model answer:**
Keys should live in Kubernetes Secrets (or an external secrets manager such as HashiCorp Vault or AWS Secrets Manager) mounted as env vars or volume files — never in container images or config files committed to the repo. On rotation: the Secret object is updated, the pod must restart (or use a sidecar/agent that reloads without restart). If the app reads secrets only at startup, a rolling restart is required. If it reads at request time, it can pick up the new value without downtime.

**What a strong understanding looks like:**
You describe the exact mechanism (env var vs. file mount), whether your app reads secrets once or on every request, and the exact steps needed to rotate without dropping traffic.

</details>

---

### Q3 — Drift detection
**Q3. How would you know if your deployed model's output quality has drifted from what it was when you first deployed?**

<details>
<summary>Show answer</summary>

**Model answer:**
Drift detection for LLMs typically requires: (1) logging a sample of request/response pairs, (2) running a lightweight judge or embedding-based similarity check against a "golden" reference set, (3) tracking scores over time as a metric. Simple proxies include user feedback signals (thumbs down), downstream task accuracy on a held-out eval set run nightly, or embedding cosine distance of outputs relative to baseline. A spike in this score is an alert trigger. Model-version pinning in the deployment manifest prevents silent drift from provider updates.

**What a strong understanding looks like:**
You identify both distribution shift (prompt patterns change) and model shift (weights change behind an API), propose a concrete measurement approach, and explain how your observability stack surfaces it.

</details>

---

### Q4 — SLO definition and burn rate
**Q4. What are the SLOs for your service? How long before your error budget is exhausted at current error rate?**

<details>
<summary>Show answer</summary>

**Model answer:**
Example: SLO = 99.5% of requests complete within 3 seconds (28-day rolling window). Error budget = 0.5% of requests = ~2,160 request-failures per day at 1 req/s load. If your current error rate is 2%, you're burning 4× budget and will exhaust it in 7 days instead of 28. The alert should fire when the burn rate exceeds 2× over a 1-hour window (fast burn alert) or 1× over a 6-hour window (slow burn alert).

**What a strong understanding looks like:**
You know your actual SLO numbers, can calculate the budget in concrete units (failures or minutes), and describe both fast-burn and slow-burn alerting strategies.

</details>

---

### Q5 — Failover and fallback hierarchy
**Q5. Walk through what happens when the primary model provider returns 503 for 2 minutes.**

<details>
<summary>Show answer</summary>

**Model answer:**
A well-designed fallback hierarchy: (1) Retry with exponential backoff for transient errors (2–3 attempts, ~10 s total). (2) If retries fail, serve from semantic cache if the request is cacheable. (3) If not in cache, route to a secondary provider (e.g., switch from Provider A to Provider B via LiteLLM router). (4) If no secondary, respond with a graceful degraded message (`X-Fallback: cached` or `X-Degraded: true` header) rather than a 500. (5) Circuit breaker opens after N consecutive failures, bypassing the provider entirely for a cooldown window. Runbook should document all five levels.

**What a strong understanding looks like:**
You describe a multi-level hierarchy (not just "retry"), know which level your system currently implements, and identify what you'd need to add.

</details>

---

### Q6 — Cost controls
**Q6. What guardrails prevent your service from generating an unexpectedly large bill in a single day?**

<details>
<summary>Show answer</summary>

**Model answer:**
Effective cost controls: (1) Per-request `max_tokens` cap enforced at the service layer before sending to the provider. (2) Rate limiting at the API gateway level (requests per minute per user/key). (3) A daily budget alert via cloud provider billing API or custom cost metric that pages when cumulative spend crosses a threshold. (4) Semantic caching to reduce redundant API calls. (5) Prompt length validator rejecting inputs above a token limit. (6) Least-privilege API keys scoped to specific models to prevent accidental use of expensive models.

**What a strong understanding looks like:**
You have at least three independent layers of cost control, not just one, and can explain how each would catch a different failure mode.

</details>

---

### Q7 — Observability gaps
**Q7. Looking at your current metrics and logs, what is the one blind spot you are most concerned about?**

<details>
<summary>Show answer</summary>

**Model answer (illustrative):**
Common gaps: (a) Tail latency of the embedding step is not separately tracked — only end-to-end latency is visible, making it hard to isolate vector DB vs. model slowdowns. (b) Cache eviction rate is unmonitored, so a full cache eviction goes unnoticed until latency spikes. (c) Token count per request is logged but not broken down by system prompt vs. user prompt, hiding prompt-bloat over time. There is no single "right" answer — the value is in identifying a real gap in *your* system.

**What a strong understanding looks like:**
You name a specific metric or log field that is missing, explain what failure mode it would miss, and describe what you'd add and why.

</details>

---

### Q8 — Infrastructure as code completeness
**Q8. Can a team member with only your repo and valid API keys reproduce the entire deployment from scratch? What would break?**

<details>
<summary>Show answer</summary>

**Model answer:**
A fully reproducible deployment requires: pinned image tags (not `latest`), IaC files (Terraform or Helm charts) for all cloud resources, a `secrets.example.env` listing every required variable without values, documented DNS/ingress setup, and a runbook step that seeds the vector index. Common gaps: the vector index is populated by a one-time script not in CI, TLS cert provisioning is manual, or the monitoring stack (Prometheus + Grafana) is assumed to pre-exist rather than being declared.

**What a strong understanding looks like:**
You can describe the exact steps from zero to live, name the specific manual steps that still exist, and have a plan to automate them.

</details>

---

### Q9 — Model version governance
**Q9. If your provider silently upgrades the underlying model version, how do you detect it and what do you do?**

<details>
<summary>Show answer</summary>

**Model answer:**
Detection: (1) Log the `model` field returned in every API response (some providers include version hashes). (2) Run a nightly canary eval against a fixed set of prompts and compare outputs using embedding similarity or a rubric-based judge. (3) Monitor output-length distribution as a cheap proxy — a model change often shifts mean output length. Response: if quality degrades, pin to a named version (e.g., `claude-3-5-sonnet-20241022` not `claude-3-5-sonnet-latest`), open a rollback PR, and evaluate the new version in staging before re-enabling.

**What a strong understanding looks like:**
You distinguish between provider-controlled versioning (often silent) and self-hosted versioning (explicit image tag), and have a concrete detection mechanism for each.

</details>

---

### Q10 — Security posture
**Q10. What is the most significant attack surface in your current deployment, and how is it mitigated?**

<details>
<summary>Show answer</summary>

**Model answer:**
For most LLM services, the top risks are: (1) **Prompt injection** — malicious user input hijacking system-prompt instructions. Mitigation: input sanitisation, system-prompt isolation, output validation. (2) **API key exposure** — leaked keys via logs or error responses. Mitigation: secrets scanning in CI, redacting key-like patterns from logs. (3) **Unauthenticated inference endpoint** — anyone can call the model at your cost. Mitigation: auth middleware (API key or JWT) on all inference routes. (4) **Supply-chain risk** — unverified base images or dependencies. Mitigation: pinned digest hashes for base images, `pip-audit` in CI.

**What a strong understanding looks like:**
You rank risks specific to *your* deployment (not a generic list), describe the mitigations already in place, and identify the one you'd tackle next.

</details>

---

## 4. Concept Deep-Dive Q&A — Full Track Consolidation (Days 6–14)

These questions span the entire DevOps track. Work through them to consolidate your understanding before moving on.

---

**Q1. What is the fundamental difference between a liveness probe and a readiness probe, and why does confusing them cause production outages?**

<details>
<summary>Show answer</summary>

A liveness probe answers "is this process still running?" — failure causes a restart. A readiness probe answers "is this process ready to serve traffic?" — failure removes the pod from the load balancer without restarting it. Confusing them causes outages because: if readiness logic is used as liveness, a temporarily overloaded pod gets killed and restarted (making the problem worse). If liveness logic is used as readiness, a pod that is alive but unable to serve (e.g., its upstream is down) continues to receive requests it will fail.

</details>

---

**Q2. Explain continuous batching in vLLM. Why is it more efficient than static batching for LLM inference?**

<details>
<summary>Show answer</summary>

Static batching fills a batch to a fixed size and waits until all requests in the batch complete before starting the next. This wastes GPU capacity when requests in a batch finish at different times (the GPU idles waiting for the slowest request). Continuous batching (also called iteration-level batching) inserts new requests into the batch as existing ones complete, keeping the GPU maximally utilised. For LLMs with variable-length generation, this yields 2–10× higher throughput at similar latency compared to static batching.

</details>

---

**Q3. What is PagedAttention and why does it matter for GPU memory management?**

<details>
<summary>Show answer</summary>

PagedAttention (introduced by vLLM) manages the KV cache using a paging scheme analogous to OS virtual memory. Instead of pre-allocating a contiguous block of GPU memory for each sequence's KV cache (which wastes memory on over-allocation), it allocates fixed-size "pages" on demand. This eliminates internal fragmentation, allows much larger effective batch sizes, and enables memory-efficient sharing of KV cache blocks across parallel sequences (e.g., in beam search). The practical result is that a GPU can serve significantly more concurrent requests.

</details>

---

**Q4. You have a FastAPI LLM service running in Kubernetes. CPU usage is low but p95 latency is high and HPA is not scaling up. What is likely happening?**

<details>
<summary>Show answer</summary>

HPA scales on CPU (or custom metrics) by default. If CPU is low, the HPA sees no trigger even though the service is slow. The likely cause is I/O-bound waiting: the service is blocked on the model provider's API (network latency, rate limiting, or provider-side queuing). Solutions: (1) Define a custom HPA metric based on request queue depth or p95 latency (via KEDA or Prometheus Adapter). (2) Add a request queue with back-pressure. (3) Investigate and address the upstream bottleneck (caching, retries, provider tier upgrade).

</details>

---

**Q5. Describe the semantic caching pattern. When does it fail or cause correctness problems?**

<details>
<summary>Show answer</summary>

Semantic caching returns a cached response when a new query is semantically similar (cosine similarity above a threshold) to a previously answered query, avoiding a model call. It fails when: (1) The similarity threshold is too low — different questions get the same answer (correctness bug). (2) The similarity threshold is too high — few cache hits, negligible cost savings. (3) The question is time-sensitive ("what is today's date?") and the cache serves a stale answer. (4) The embedding model treats semantically different prompts as similar due to surface-level overlap. Mitigation: exclude time-sensitive or personalised queries from the cache via a query classifier.

</details>

---

**Q6. What are the four golden signals, and give a concrete LLM-specific example metric for each?**

<details>
<summary>Show answer</summary>

| Signal | LLM-specific example metric |
|---|---|
| **Latency** | p95 time-to-first-token (ms) |
| **Traffic** | Requests per second to `/generate` |
| **Errors** | Rate of HTTP 5xx + provider API errors per minute |
| **Saturation** | GPU memory utilisation % or KV cache eviction rate |

</details>

---

**Q7. Explain the canary deployment pattern. What specific metrics should trigger an automatic rollback?**

<details>
<summary>Show answer</summary>

A canary release routes a small fraction of traffic (e.g., 5–10%) to the new version while the majority stays on the stable version. Both versions run simultaneously and their metrics are compared. Automatic rollback triggers should include: (1) Error rate on the canary exceeds stable error rate by a statistically significant margin (e.g., 2× for >5 minutes). (2) p95 latency on the canary is >20% higher than stable. (3) Output quality score (if an automated judge is in place) drops below threshold. The rollback is executed by shifting traffic weight back to 0% on the canary and flagging the release for investigation.

</details>

---

**Q8. What is a circuit breaker and how does it differ from a retry policy?**

<details>
<summary>Show answer</summary>

A retry policy retries a failed request immediately (with optional backoff), assuming the failure is transient. A circuit breaker tracks the failure rate over time and, after a threshold is exceeded, "opens" — meaning it stops sending requests to the failing dependency entirely for a cooldown period. This prevents cascading failures: retries under a sustained outage amplify load on an already-struggling service, whereas an open circuit breaker sheds load immediately. After the cooldown, the circuit enters a "half-open" state and allows a probe request; if it succeeds, the circuit closes again.

</details>

---

**Q9. What is the difference between a token budget and a cost budget in LLM FinOps?**

<details>
<summary>Show answer</summary>

A **token budget** is a per-request cap on input + output tokens (e.g., `max_tokens=500`). It controls individual request cost and latency but does not prevent high aggregate spend from many requests. A **cost budget** is an aggregate limit over a time period (e.g., $200/day), enforced by tracking cumulative spend and blocking or alerting when the limit is approached. Both are necessary: token budgets prevent runaway individual requests; cost budgets prevent runaway usage patterns. LiteLLM's budget manager and cloud provider billing alerts can enforce cost budgets; `max_tokens` and prompt length validators enforce token budgets.

</details>

---

**Q10. What does "infrastructure as code" mean in the context of an LLM deployment, and why is it operationally essential?**

<details>
<summary>Show answer</summary>

IaC means declaring all infrastructure (compute, networking, storage, secrets, monitoring) in version-controlled files (Terraform, Helm charts, Kubernetes manifests) rather than applying changes manually via console or CLI. Operationally essential because: (1) **Reproducibility** — any environment (staging, prod, DR) can be recreated identically. (2) **Auditability** — every change is a git commit with author and rationale. (3) **Drift detection** — `terraform plan` or `kubectl diff` reveals when live state diverges from declared state. (4) **Disaster recovery** — rebuild from scratch from the repo, not from memory. For LLM systems specifically, this includes the model-serving configuration, vector index provisioning, and monitoring stack — not just compute.

</details>

---

## 5. Common Pitfalls & Best Practices

Operational mistakes that recur in LLM system deployments:

### Pitfalls to Avoid

| Pitfall | Why It Happens | How to Prevent |
|---|---|---|
| **Hardcoded API keys in source** | Convenience during development | Secrets manager + CI secrets scanning from day one |
| **Using `latest` image tag in production** | Convenience; "latest is always best" assumption | Pin exact digest or version tags; enforce in admission controller |
| **No `max_tokens` cap on requests** | Forgetting that users can trigger very long completions | Enforce at the service layer before the provider call |
| **Liveness probe hitting a slow dependency** | Copying readiness probe logic without thinking | Liveness = local process only; readiness = include upstreams |
| **Single point of failure in the model provider** | Starting with one provider is fine; not planning for its outage | Add fallback provider in LiteLLM router before going to production |
| **Over-caching with low similarity threshold** | Wanting high cache hit rates | Tune threshold on a representative query set; monitor false-positive rate |
| **Unstructured logs** | Free-text logging is easier initially | JSON logging from day one; retrofit is expensive |
| **No runbook for on-call** | "The alert will explain itself" assumption | Write runbook entries when you build each alert, not after an incident |
| **Alert fatigue from low-urgency alerts** | Adding alerts without severity tiers | Use SLO burn-rate alerts; route only actionable alerts to pager |
| **Deploying directly to production without staging** | Speed; "it works locally" | Maintain staging environment that mirrors production topology |
| **Vector index rebuilt on every restart** | Simple startup script re-ingests all documents | Persist the index to a volume or managed service; ingest is idempotent |
| **No cost anomaly detection** | Cost is monitored monthly, not continuously | Set daily budget alerts; log per-request cost as a metric |

### Best Practices Summary

1. **Health before traffic** — ensure liveness + readiness probes are correct before adding the pod to any load balancer.
2. **Observe before you optimise** — instrument first, then tune. Guessing without data wastes time.
3. **One change at a time in production** — canary releases exist to isolate changes; don't batch unrelated changes in a single release.
4. **Fail fast, recover fast** — circuit breakers and fallbacks reduce blast radius; fast rollback reduces MTTR.
5. **Treat cost as a first-class metric** — track token spend per request in Prometheus alongside latency and errors.
6. **Document decisions, not just procedures** — runbooks should explain *why* a step is taken, not just *what* to do.
7. **Pin everything in production** — model versions, image tags, dependency versions. Reproducibility requires pinning.

---

## 6. Continued Learning Roadmap

### Immediate Next Steps (0–4 weeks)

| Topic | Resource |
|---|---|
| **LLMOps patterns** | "Patterns for Building LLM-based Systems & Products" — Eugene Yan (https://eugeneyan.com/writing/llm-patterns/) |
| **Kubernetes production hardening** | Kubernetes documentation: Production Best Practices (https://kubernetes.io/docs/setup/production-environment/) |
| **Prometheus & Grafana deep dive** | Prometheus docs: https://prometheus.io/docs/introduction/overview/ |
| **OpenTelemetry for LLMs** | OpenTelemetry Semantic Conventions for GenAI (https://opentelemetry.io/docs/specs/semconv/gen-ai/) |

### 1–3 Month Skills

| Area | Focus |
|---|---|
| **Advanced Kubernetes** | RBAC, NetworkPolicy, Pod Security Standards, Admission Webhooks |
| **Service mesh** | Istio or Linkerd for traffic splitting, mTLS, observability sidecar |
| **FinOps** | FinOps Foundation open standards (https://www.finops.org/); cloud cost attribution with labels/tags |
| **Infrastructure as Code** | Terraform fundamentals + Helm chart authoring; `terraform plan` as drift detection |
| **Chaos engineering** | Chaos Monkey / Chaos Mesh: controlled failure injection to validate resilience |

### 3–6 Month Depth

| Area | Focus |
|---|---|
| **MLOps / LLMOps platforms** | MLflow, Weights & Biases, Arize AI for model monitoring and experiment tracking |
| **Advanced caching** | Redis for distributed semantic cache; cache warming strategies |
| **Multi-region deployments** | Active-active vs. active-passive; latency-based routing; data residency |
| **SRE practices** | "Site Reliability Engineering" (Google SRE Book — free online); error budget policies |
| **Security hardening** | OWASP LLM Top 10 (https://genai.owasp.org/); supply-chain security with SLSA |

### Certification Paths (optional)
- **Certified Kubernetes Administrator (CKA)** — validates Kubernetes operations depth
- **Prometheus Certified Associate (PCA)** — observability fundamentals
- **FinOps Certified Practitioner (FOCP)** — cloud cost management

---

## 7. Key Takeaways

**From the DevOps track (Days 6–14):**

- **LLM systems are production systems** — they require the same operational rigour as any distributed service: health checks, structured logging, SLOs, runbooks, and incident procedures.
- **The six operational concerns** — latency, throughput, cost, reliability, security, and observability — are not independent. Optimising one without considering the others creates new problems.
- **Containerisation is the foundation** — a well-built Docker image with proper health checks, non-root user, and 12-factor config is the prerequisite for everything above it.
- **Kubernetes manages the fleet, not the application** — probes, resource requests, and autoscaling only work correctly when the application itself is designed to be observable and graceful.
- **Caching is an economic primitive** — a semantic cache does not just improve latency; it is the most direct lever on cost in a token-priced world.
- **Observability is not optional** — you cannot debug what you cannot measure. The four golden signals plus LLM-specific metrics (token throughput, cache hit rate, cost per request) give you a complete operational picture.
- **Canary releases make change safe** — the ability to roll back in minutes is as important as the ability to deploy in minutes. Both require automation.
- **Runbooks are on-call insurance** — written during calm, invaluable during incidents. A runbook should exist before an alert fires, not after.
- **Cost is always someone's concern** — in every production LLM deployment, there is a budget. Designing for cost observability and control from the start is professional practice.
- **IaC closes the loop** — every manual step in a deployment is a reliability risk. Infrastructure as code is how operational knowledge is preserved, shared, and audited.

---

**Congratulations on completing the DevOps track.** You have built and operated an LLM system from scratch — from a bare FastAPI service to a production-grade deployment with caching, observability, canary releases, and incident playbooks. The operational instincts developed here apply equally to the next system you build, regardless of which models or providers it uses.

---

*Capstone project files: `capstone/devops/` | Track: Days 6–15 | Prerequisite: Days 1–5 (GenAI Foundations)*
