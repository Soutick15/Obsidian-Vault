# Day 13 — Security & Governance for LLM Systems

**Track:** DevOps | **Day:** 13 of 15 | **Prerequisites:** Days 6–12

---

## 1. Objectives

By the end of this day you will be able to:

- Explain the hierarchy of secrets management — env vars → cloud secret stores → dedicated vaults (HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager) — and state when each tier is appropriate.
- Implement a **secrets provider abstraction** that loads credentials from the environment (or a mock vault) without ever touching source code, container images, or log streams.
- Design and emit **tamper-evident audit log** records (who, what question-hash, decision, timestamp) with PII redacted before persistence.
- Apply **gateway-level guardrails**: prompt-injection detection and PII redaction at the infrastructure boundary rather than inside application logic.
- Enforce a simple **API-key authz check** and distinguish authentication from authorisation in the LLM-system context.
- Describe egress-control patterns (allowlisting model-provider endpoints, denying unexpected outbound connections) and why they matter for supply-chain integrity.
- Articulate data-residency obligations (GDPR, SOC 2 Type II) and how they constrain model-provider selection and log retention.

---

## 2. Concept Reading

### 2.1 Secrets & Key Management

#### The Secrets Hierarchy

Every LLM deployment handles at least one secret: the API key for the model provider. At scale the list grows quickly — database passwords, vector-store credentials, internal service tokens, TLS private keys. Managing secrets safely requires a layered strategy:

| Tier | Mechanism | Appropriate for |
|---|---|---|
| **Tier 0 — Code / Image** | Hardcoded strings, baked into Dockerfile | **Never** — immediately exposed via source control or image registry |
| **Tier 1 — Environment variables** | `os.environ["ANTHROPIC_API_KEY"]` | Local dev, simple CI pipelines |
| **Tier 2 — Cloud secret stores** | AWS Secrets Manager, GCP Secret Manager, Azure Key Vault | Cloud-native deployments; automatic rotation; fine-grained IAM |
| **Tier 3 — Dedicated vault** | HashiCorp Vault, CyberArk | Hybrid infra, dynamic short-lived credentials, policy-as-code |

The progression is not about complexity for its own sake — it is about **rotation without redeployment** and **audit trail**. When a key is compromised, Tier 0 requires a code change + rebuild + redeploy. Tier 2–3 requires a single API call to rotate and an automatic notification to dependent services.

#### Hardcoded Secrets Anti-patterns to Detect

Hardcoded secrets appear in four common places. Each requires a different detection control:

| Location | Detection control |
|---|---|
| **Source code / commits** | `git-secrets`, `trufflehog`, `gitleaks` in CI pre-commit hooks |
| **Container images** | Image scanners (Trivy, Snyk) in the build pipeline |
| **Log output** | Structured-logging middleware that scrubs known patterns (Bearer tokens, UUIDs matching secret format) |
| **Environment dumps** | Restrict which env vars appear in debug endpoints; never expose raw `os.environ` |

#### Rotation

Rotation means replacing a secret on a schedule (or on-demand after a suspected leak) without downtime. The canonical pattern:

1. Generate new credential at the provider.
2. Update the secret store with the new value.
3. Services reload the secret at next access (or are signalled to refresh).
4. Revoke the old credential after a grace period.

In Python, a secrets provider abstraction (a class with a `get(key)` method) makes rotation transparent to application code — the call site never changes.

```python
# Application code — provider-agnostic
from secrets_provider import SecretsProvider

secrets = SecretsProvider()
api_key = secrets.get("ANTHROPIC_API_KEY")
```

---

### 2.2 Gateway-Level Guardrails & Prompt-Injection Mitigation

#### Why the Infrastructure Layer?

Application-level guardrails (inside the model-calling code) protect one service. **Infrastructure-layer guardrails** — deployed as a reverse proxy, API gateway plugin, or sidecar — protect every LLM call made by every service in the cluster without requiring each team to re-implement checks.

Typical gateway responsibilities:

| Responsibility | What it does |
|---|---|
| **Prompt-injection detection** | Pattern-match or classify incoming text for known injection signals before forwarding to the model |
| **PII redaction (input)** | Strip emails, phone numbers, SSNs, credit-card numbers from the prompt |
| **PII redaction (output)** | Strip any PII that leaked into the model's response before returning it to the caller |
| **Content policy enforcement** | Block categories of requests (e.g., requests for code that calls internal APIs) |
| **Rate limiting** | Per-principal or per-IP token-rate limits |
| **Response sanitisation** | Remove control characters, very long outputs, or output that matches internal data patterns |

#### Prompt-Injection Patterns

Prompt injection is an attempt by user-supplied text to override the system prompt or extract model context. Infrastructure-level signals to detect:

- Phrases like `"ignore previous instructions"`, `"forget your rules"`, `"you are now"`, `"DAN mode"`.
- Instruction-formatted text (numbered lists of directives) embedded in a user query.
- Base64 or hex-encoded payloads (attempts to smuggle instructions past keyword filters).
- Unusual Unicode characters used to break tokenization.

Regex and keyword detection is a **heuristic starting point**, not a complete security control — a determined attacker can encode, paraphrase, or obfuscate injection payloads to evade pattern matching. No single filter is complete. The practical approach is **defence in depth**: detect obvious patterns at the gateway, constrain the model with a tightly scoped system prompt, and treat model output as untrusted data that passes through an output sanitiser before reaching downstream systems.

---

### 2.3 PII Handling, Data Residency & Compliance

#### PII in LLM Systems

PII enters LLM systems through user queries ("what is Alice's salary?"), retrieved context (documents that contain employee records), and model outputs (the model summarises or quotes PII from context). Each path requires a control:

| PII path | Control |
|---|---|
| **User query** | Gateway input redaction; replace with pseudonyms before forwarding to model |
| **Retrieved context** | Role-based access control on the document store; return only documents the principal is authorised to see |
| **Model output** | Gateway output redaction; log only redacted version |
| **Audit logs** | Never log raw PII; log a hash or token |

#### GDPR Awareness (for DevOps Engineers)

GDPR affects infrastructure decisions in concrete ways:

- **Data residency**: Personal data of EU residents must not leave the EU without adequate safeguards (Standard Contractual Clauses or equivalent). This constrains which model-provider regions you can use and prohibits sending EU employee data to a model endpoint in a non-approved region.
- **Right to erasure**: If personal data is stored in vector stores or fine-tuning datasets, you must be able to delete it on request. Design data pipelines with deletion in mind from the start.
- **Data minimisation**: Do not send more PII to the model than required for the task. Strip unnecessary fields before constructing the prompt.
- **Logging retention**: Access logs that contain personal identifiers must have a defined retention period (commonly 90 days for operational logs, shorter for audit logs containing PII).

#### SOC 2 Type II Awareness

SOC 2 Type II auditors look for:

- Evidence that access to production secrets is logged and access is least-privilege.
- Evidence that audit logs are tamper-evident and retained for the audit period.
- Evidence that secrets are rotated and access is reviewed periodically.
- Automated alerts for anomalous access patterns.

DevOps engineers are responsible for the infrastructure controls that produce this evidence. The audit log design in §2.4 is directly connected to SOC 2 requirements.

---

### 2.4 Audit Logging

#### What Makes a Good Audit Log?

Audit logs differ from application logs. An application log records what happened for debugging. An audit log records **who did what, when, and what decision was made** — for accountability and forensics.

Minimum fields per audit record:

| Field | Type | Notes |
|---|---|---|
| `event_id` | UUID | Unique identifier for the record |
| `timestamp` | ISO-8601 UTC | Use `datetime.utcnow().isoformat() + "Z"` |
| `principal` | string | Authenticated caller identity (never raw password/token) |
| `action` | string | e.g., `"chat_request"`, `"secret_access"` |
| `question_hash` | hex string | SHA-256 of the original question — links records without storing PII |
| `decision` | string | `"allowed"`, `"blocked"`, `"redacted"` |
| `reason` | string | Why the decision was made (useful for SOC 2 evidence) |
| `metadata` | dict | Extensible; never include raw secrets or full PII here |

#### Tamper-Evidence

A tamper-evident log makes it detectable if a record is modified or deleted after the fact. Approaches in increasing rigour:

1. **Append-only file or stream** — process lacks write permission to existing records (minimal).
2. **Hash chaining** — each record contains the SHA-256 of the previous record; any modification breaks the chain.
3. **Write-once object storage** — S3 Object Lock, GCS Object Hold (cloud-native).
4. **Dedicated audit log service** — AWS CloudTrail, GCP Audit Logs, Datadog Audit Trail.

For the purposes of this lab we implement hash chaining in Python to make the concept concrete before reaching for a managed service. Note: a file-based hash chain deters casual tampering but needs OS-level write protection (e.g., append-only file permissions) or a managed write-once store (S3 Object Lock, GCS Object Hold) to resist a privileged attacker who can overwrite the file and recompute the chain.

#### PII Redaction in Logs

Log exactly this pattern:

```python
import hashlib, re

# Redact before logging — never log raw PII
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")

def redact_pii(text: str) -> str:
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _PHONE_RE.sub("[PHONE]", text)
    return text

def question_hash(question: str) -> str:
    return hashlib.sha256(question.encode()).hexdigest()[:16]
```

---

### 2.5 Access Control — AuthN and AuthZ for LLM Services

**Authentication (AuthN)** — who is calling? Verify identity via API key, JWT, mTLS, or OIDC token. The LLM gateway must reject unauthenticated callers before forwarding any request.

**Authorisation (AuthZ)** — what is the caller allowed to do? After identity is established, enforce policies:

| Policy type | Example |
|---|---|
| **Action-level** | Only `hr-bot-service` may call the `/chat` endpoint |
| **Data-level** | A caller with `role=employee` may not retrieve documents tagged `classification=confidential` |
| **Rate / quota** | A caller may make at most 100 requests per minute |
| **Time-based** | Service accounts may only call during business hours |

For the infra layer, the simplest implementation is an **API-key registry** — a mapping of hashed key → principal, roles, and rate-limit tier. The gateway looks up the key on every request and attaches the principal identity to the audit log.

```python
# Never store raw keys — store their SHA-256 hash
API_KEY_REGISTRY: dict[str, dict] = {
    hashlib.sha256(b"svc-hr-prod-key").hexdigest(): {
        "principal": "hr-bot-service",
        "roles": ["chat"],
        "rate_limit_rpm": 100,
    }
}
```

---

### 2.6 Network Isolation & Egress Control

#### Why Egress Control Matters

An LLM deployment that can make arbitrary outbound connections is a risk: a compromised dependency, a malicious retrieved document, or a model that hallucinates a URL can all trigger unexpected outbound calls. Egress control limits blast radius.

Typical egress allowlist for an LLM service:

```
# Allow only model provider endpoints + internal services
ALLOW api.anthropic.com:443
ALLOW api.openai.com:443
ALLOW <internal-vector-store>:6333
DENY *
```

Implementation options by layer:

| Layer | Mechanism |
|---|---|
| **Network policy** | Kubernetes `NetworkPolicy` (Calico, Cilium) — drop packets at L3/L4 |
| **Service mesh** | Istio/Linkerd egress gateway — L7-aware, logs by hostname |
| **Firewall** | AWS Security Groups, GCP VPC firewall rules |
| **DNS-based** | CoreDNS RPZ, Unbound local-zone — block resolution of disallowed domains |

#### Dependency Supply-Chain Integrity

Every Python package in `requirements.txt` is a potential supply-chain vector. Controls:

| Control | Mechanism |
|---|---|
| **Pin exact versions** | `anthropic==0.40.0` not `anthropic>=0.30` |
| **Lock file** | `pip-compile` generates `requirements.lock` with hashes |
| **Hash verification** | `pip install --require-hashes -r requirements.lock` |
| **Image scanning** | Trivy or Grype scan the container image for CVEs and known-malicious packages |
| **Private registry** | Pull only from an internal mirror that has already been scanned |

---

## 3. Hands-on Lab

See `labs/devops/day-13/` for the complete lab.

**What you will build:**

| Component | Description |
|---|---|
| `SecretsProvider` | Abstraction that loads secrets from env / mock vault; asserts no secret is hardcoded or logged |
| `AuditLogger` | Append-only, hash-chained log with PII redaction; logs every gateway decision |
| `SecurityGateway` | Validates authz (API key), detects prompt injection, redacts PII in inputs and outputs |
| Demo script | Shows an allowed request (audited), a blocked injection attempt (audited), and PII redaction end-to-end |

**Run the lab:**

```bash
# No API key required
python labs/devops/day-13/solution.py
```

---

## 4. Self-Check Quiz

Answer these questions without referring to your notes. Review any you cannot answer confidently.

**Q1. List four locations where a hardcoded API key can appear, and name a detection control for each.**

<details>
<summary>Show answer</summary>

Source code/commits (`git-secrets`, `trufflehog`, `gitleaks` in CI pre-commit hooks), container images (Trivy/Snyk image scanners in the build pipeline), log output (structured-logging middleware that scrubs known patterns), and environment dumps (restrict which env vars appear in debug endpoints; never expose raw `os.environ`).

</details>

**Q2. A GDPR audit finds that EU employee emails appear in your LLM service's CloudWatch logs. What three immediate remediation steps would you take?**

<details>
<summary>Show answer</summary>

(1) Immediately apply PII redaction middleware to the logging pipeline to stop new raw PII from being written. (2) Delete or pseudonymise the existing log records containing PII (exercising the right to erasure obligation). (3) Review the data-residency configuration to confirm logs are stored only in approved regions, and add automated scanning to detect future PII leakage in logs.

</details>

**Q3. Your audit log shows record N has a `prev_hash` field that does not match SHA-256 of record N-1. What does this indicate, and what do you do next?**

<details>
<summary>Show answer</summary>

A hash-chain mismatch indicates that one or more records between N-1 and N have been modified, deleted, or inserted after the fact — the log has been tampered with or corrupted. Next steps: preserve the log as evidence, isolate the system, investigate who had write access around the time of the mismatch, and trigger your incident response process.

</details>

**Q4. Explain the difference between prompt injection at the application layer versus at the infrastructure gateway layer. Why might you want both?**

<details>
<summary>Show answer</summary>

Application-layer detection runs inside the service that calls the model; it protects only that one service and must be re-implemented per service. Infrastructure-layer (gateway) detection runs as a reverse proxy or sidecar and protects every LLM call in the cluster without per-service changes. You want both for defence in depth: the gateway catches known patterns centrally, while application-layer checks can enforce domain-specific rules the generic gateway cannot know about.

</details>

**Q5. A developer argues that `ANTHROPIC_API_KEY=...` in a `.env` file committed to Git is fine because the repo is private. Provide three specific counter-arguments.**

<details>
<summary>Show answer</summary>

(1) Private repos can become public by accident (settings change, fork, migration), instantly exposing the key. (2) Every developer with repo access can see the key — violating least-privilege; a single compromised developer account leaks the key. (3) Git history is permanent; even if the key is removed in a later commit, it remains in history and must be rotated, whereas a secret store allows rotation without touching the repo at all.

</details>

**Q6. You need to enforce that only the `hr-bot-service` principal can call `/chat` while `analytics-service` can only call `/metrics`. What mechanism would you use, and where in the stack would you place it?**

<details>
<summary>Show answer</summary>

Use an API-key registry (or an identity-provider policy) that maps each authenticated principal to a set of allowed actions/routes. Place this authorisation check at the LLM gateway layer (before requests reach backend services), so it is enforced uniformly and the downstream services do not need to re-implement access control.

</details>

**Q7. Define "tamper-evident" in the context of audit logs and describe the hash-chaining approach.**

<details>
<summary>Show answer</summary>

Tamper-evident means that any modification, deletion, or insertion of a log record after it is written is detectable. Hash chaining achieves this by including in each record a `prev_hash` field containing the SHA-256 of the previous record. Any alteration to a record changes its hash, breaking the chain from that point forward; a verifier re-computes hashes sequentially and flags any mismatch.

</details>

**Q8. What is egress control, and what concrete risk does it mitigate in an LLM deployment?**

<details>
<summary>Show answer</summary>

Egress control restricts which outbound network destinations a service is permitted to reach. In an LLM deployment it mitigates the risk that a compromised dependency, a malicious retrieved document, or a hallucinated URL causes the service to exfiltrate data or beacon to an attacker-controlled server. An allowlist permitting only model-provider endpoints and internal services — with a default-deny rule — limits the blast radius of such an attack.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1. HashiCorp Vault looks complex. For a small team, is it overkill?**

<details>
<summary>Show answer</summary>

For a team of 2–5 engineers deploying a single LLM service on a cloud provider, Vault is often overkill. Start with your cloud provider's native secret store (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault): they offer rotation, versioning, access policies, and audit trail out of the box, and billing is negligible at small scale. Introduce Vault when you have hybrid infrastructure (some workloads on-prem, some in cloud), when you need dynamic short-lived credentials (e.g., database passwords that expire after 1 hour), or when policy-as-code governance is required across teams. The key architectural decision is the **secrets provider abstraction** — if your application code only ever calls `secrets.get("KEY")`, swapping the backend from env vars to Secrets Manager to Vault is a one-line config change.

</details>

**Q2. What is the difference between prompt injection and jailbreaking?**

<details>
<summary>Show answer</summary>

They are related but distinct attack classes. **Prompt injection** is an attacker embedding instructions in user-controlled input (a query, a retrieved document, a form field) that attempt to override the system prompt or extract model context. It is an **input-side** attack and is detectable at the gateway by pattern matching. **Jailbreaking** is a technique to elicit content that a model's safety training is supposed to prevent — it requires the attacker to interact with the model directly. At the infrastructure layer, jailbreaks are harder to block because they often look like legitimate text; the primary defence is the model provider's own safety training plus output content classification. For DevOps engineers, the practical difference is: prompt injection is an infra-layer problem (guard the input); jailbreaking is a model-selection and output-classification problem.

</details>

**Q3. Should I redact PII before or after the model call?**

<details>
<summary>Show answer</summary>

Both, for defence in depth. Redact **before** the call to prevent PII from reaching the model provider (relevant for GDPR data-residency requirements — if you are not permitted to send EU personal data to a US-hosted model, you must strip it before the API call). Redact **after** the call because the model may reproduce PII from its context window in the response, even if you did not explicitly ask for it. In the gateway pattern, input redaction is a pre-filter step and output redaction is a post-filter step, both implemented in the same gateway component. For logging, always apply redaction before writing the log record — never log the raw pre-redaction input and then redact later.

</details>

**Q4. How does SOC 2 Type II actually verify audit log tamper-evidence in practice?**

<details>
<summary>Show answer</summary>

SOC 2 auditors do not typically re-implement your hash-chain verification; they look for two things: (1) **evidence of design** — architecture diagrams, runbooks, or code reviews showing that logs are append-only and hash-chained (or stored in a write-once system), and (2) **evidence of operation** — a sample of audit log records from the audit period showing consistent `prev_hash` fields and an automated alerting rule that fires if the chain breaks. If you use a managed service like AWS CloudTrail with S3 Object Lock, the auditor accepts the provider's own compliance attestation (SOC 2, ISO 27001) as evidence. The practical recommendation: use a managed write-once log store for production and implement hash chaining in code for environments where the managed service is not available, so engineers understand the underlying mechanism.

</details>

**Q5. What does "pinning dependencies" actually protect against?**

<details>
<summary>Show answer</summary>

Three distinct threats. First, **typosquatting** — a malicious package with a name similar to a legitimate one (`anthropi` vs `anthropic`); pinning the exact name and version reduces the attack surface but does not eliminate it. Second, **version substitution** — a maintainer pushes a malicious update to a legitimate package; pinning to a specific version + hash (`--require-hashes`) means `pip` will refuse to install a different binary even if the version number matches. Third, **transitive dependency confusion** — a dependency of your dependency is compromised; a lock file generated by `pip-compile` pins the full transitive closure, not just your direct dependencies. Image scanning (Trivy, Grype) catches known CVEs in pinned packages — pinning and scanning are complementary, not alternatives.

</details>

**Q6. Is API-key auth enough for an internal LLM gateway?**

<details>
<summary>Show answer</summary>

API-key auth establishes identity cheaply and is sufficient for many internal services, but it has weaknesses: keys are long-lived (rotation is often neglected), they travel in HTTP headers (logged by default in many systems, creating a PII/secret leak vector), and they offer no cryptographic proof of the caller's identity. For higher-assurance requirements, prefer **mTLS** (mutual TLS, where both server and client present certificates — common in service meshes like Istio) or **short-lived tokens** from an identity provider (OIDC/OAuth2 with a 15-minute expiry). The gateway abstraction in the lab uses API keys because they are simple enough to implement without external dependencies; in production you would replace the `_verify_api_key()` function with a call to your identity provider while keeping the rest of the gateway logic unchanged.

</details>

---

## 6. Further Exploration

The topics below are intentionally not required for the lab. Pursue them based on your team's immediate needs.

### Hands-on Practice

- Deploy HashiCorp Vault in dev mode (`vault server -dev`) locally and update the lab's `SecretsProvider` to call the Vault HTTP API.
- Add Kubernetes `NetworkPolicy` manifests to the day-9 vector-store deployment to enforce egress restrictions.
- Integrate `trufflehog` into a local `pre-commit` hook and verify it catches a test secret before a commit is made.
- Replace the lab's flat-file audit log with SQLite using `apsw` in WAL mode and verify append-only behaviour.

### Architecture Patterns to Study

- **Open Policy Agent (OPA)**: policy-as-code engine for fine-grained AuthZ — study the Rego language basics and how OPA integrates with Kubernetes admission controllers.
- **SPIFFE/SPIRE**: workload identity framework for zero-trust networking — produces short-lived X.509 SVIDs used in place of static API keys.
- **Sigstore / cosign**: container image signing to establish a chain of trust from source code to running container.

### Standards & Frameworks

- OWASP LLM Top 10 (2025 edition) — `owasp.org/www-project-top-10-for-large-language-model-applications/`
- NIST AI Risk Management Framework (AI RMF 1.0) — `nist.gov/artificial-intelligence`
- GDPR full text, Articles 5, 17, 25, 32 — data minimisation, erasure, privacy by design, security.
- CIS Benchmarks for Kubernetes — baseline security hardening aligned with SOC 2 / ISO 27001.

---

## 7. Day Summary

| Theme | Key takeaway |
|---|---|
| **Secrets hierarchy** | Never in code or images; use env vars locally, cloud secret stores in production, Vault for hybrid/dynamic creds |
| **Gateway guardrails** | Prompt-injection detection and PII redaction belong at the infra boundary, protecting all services uniformly |
| **Audit logging** | Record who/what/when with hash chaining for tamper-evidence; redact PII before writing |
| **AuthN vs AuthZ** | Establish identity first (API key / mTLS / OIDC), then enforce least-privilege access policies |
| **Egress control** | Allowlist model-provider endpoints; deny all other outbound — limits blast radius of supply-chain attacks |
| **Compliance posture** | GDPR constrains data residency and log retention; SOC 2 requires evidence of all the above |

**Next up — Day 14:** Observability & Incident Response — structured logging, distributed tracing, alerting pipelines, and runbooks for LLM-specific failure modes.
