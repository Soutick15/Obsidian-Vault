# Day 14 — CI/CD, IaC, and the DevOps Capstone

**Track:** DevOps | **Day:** 14 of 15 | **Prerequisites:** Days 6–13

---

## 1. Objectives

By the end of this day you will be able to:

- Explain why LLM services require a specialised CI/CD pipeline with an **eval gate** stage in addition to conventional lint/test/build stages.
- Write a working **GitHub Actions** workflow and an equivalent **GitLab CI** pipeline that model the four key stages: lint/test → build & image scan → eval gate → deploy.
- Apply **semantic versioning to prompts** and model configurations using manifest files checked into version control.
- Describe the mechanics and trade-offs of **canary deployments** vs. **blue/green deployments**, including rollback strategies for each.
- Read and write basic **Terraform HCL**: define providers, resource blocks, input variables, and understand what Terraform state represents and why it is sensitive.
- Explain the **dev → staging → prod promotion pattern** and the gates that should exist at each boundary.
- Navigate the DevOps capstone materials in `capstone/devops/` and understand what is expected of you.

---

## 2. Concept Reading

### 2.1 Why LLM Services Need Specialised CI/CD

Traditional CI/CD pipelines assume deterministic software: if all unit tests pass, the build is good. LLM services violate this assumption in at least two ways:

1. **Non-determinism.** The same input can produce outputs that vary in quality, tone, and factual accuracy across model versions, prompt edits, or even temperature shifts. A unit test asserting `response == "John Smith"` will fail intermittently and tell you nothing about *overall* answer quality.

2. **Silent quality regression.** A change to a system prompt, a model version bump, or a retrieval config change can silently degrade answer faithfulness — all while unit tests stay green, the HTTP endpoint returns 200, and latency is unchanged. Without a quality gate in the pipeline, regressions reach production undetected.

The solution is an **eval gate**: a pipeline stage that runs a scored evaluation harness against a representative golden dataset before the deployment step is allowed to proceed. The gate blocks deployment if the score falls below a defined threshold.

**Comparison: traditional vs. LLM CI/CD**

| Stage | Traditional software | LLM service |
|---|---|---|
| Lint / unit test | Function logic, types | Same, plus prompt schema validation |
| Integration test | API contract | Same, plus retrieval pipeline smoke test |
| **Eval gate** | Not present | Run eval harness; gate on score ≥ threshold |
| Image build / scan | Same | Same |
| Deploy | If tests pass | If tests pass **and** eval gate passes |
| Rollback trigger | Error rate / crash | Error rate, latency, **and** eval score drift |

The key insight is that the eval gate is not a replacement for unit tests — it is an additional layer that catches the category of failures that unit tests cannot see.

---

### 2.2 Pipeline Architecture: Stages and What Each Does

A well-structured LLM CI/CD pipeline has four stages, executed in order. Later stages do not run if an earlier stage fails.

```
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 1: lint-and-test                                              │
│  • ruff / flake8 — style and static analysis                         │
│  • mypy — type checking                                              │
│  • pytest unit tests (mocked LLM, no API key needed)                │
│  • Validate prompt manifest schema (JSON Schema or Pydantic)         │
│  Fail fast: blocks all subsequent stages                             │
└─────────────────┬───────────────────────────────────────────────────┘
                  │ passes
┌─────────────────▼───────────────────────────────────────────────────┐
│  STAGE 2: build-and-scan                                             │
│  • docker build — produce container image                            │
│  • trivy / grype / snyk — scan image for CVEs                        │
│  • Push image to registry with content-addressed tag (git SHA)       │
│  • Fail if HIGH or CRITICAL vulnerabilities found                    │
└─────────────────┬───────────────────────────────────────────────────┘
                  │ passes
┌─────────────────▼───────────────────────────────────────────────────┐
│  STAGE 3: eval-gate                                                  │
│  • Pull golden dataset from version-controlled fixtures/             │
│  • Run eval harness against the newly built image (or mock endpoint) │
│  • Compute: faithfulness %, answer relevance %, safety pass rate     │
│  • Compare scores to baseline stored in eval-baseline.json           │
│  • Fail (block deploy) if score drops more than allowed delta        │
└─────────────────┬───────────────────────────────────────────────────┘
                  │ passes
┌─────────────────▼───────────────────────────────────────────────────┐
│  STAGE 4: deploy                                                     │
│  • Update image tag in deployment manifest / Helm values             │
│  • Apply canary weight (e.g., 10% traffic to new version)            │
│  • Monitor metrics; promote or rollback automatically                │
└─────────────────────────────────────────────────────────────────────┘
```

Each stage produces an **artifact** (test report, SBOM, eval report, deploy log) that is retained for audit purposes. This is especially important for AI governance (see Day 13).

---

### 2.3 GitHub Actions Syntax and GitLab CI Comparison

Both platforms use YAML pipeline definitions checked into the repository alongside the application code. The mental models are similar but the vocabulary differs.

#### 2.3.1 Core Vocabulary

| Concept | GitHub Actions term | GitLab CI term |
|---|---|---|
| Pipeline definition file | `.github/workflows/<name>.yml` | `.gitlab-ci.yml` |
| Top-level pipeline run | **workflow** | **pipeline** |
| A unit of work | **job** | **job** |
| A step inside a job | **step** | **script line / before_script** |
| Group of jobs | — | **stage** |
| Re-usable action/component | **action** (`uses:`) | **include** / **extends** |
| Trigger events | `on: [push, pull_request]` | `rules:` / `only:` / `except:` |
| Shared data between jobs | **artifacts** (`upload-artifact` / `download-artifact`) | **artifacts** (`artifacts: paths:`) |
| Secrets / env vars | `secrets` context (`${{ secrets.X }}`) | CI/CD Variables (masked) |

#### 2.3.2 GitHub Actions Example

The following workflow implements all four pipeline stages for the Acme HR Knowledge Assistant. Note that the eval gate uses a mocked LLM — no real API key is required.

```yaml
# .github/workflows/deploy.yml
name: LLM Service CI/CD

on:
  push:
    branches: [main, "release/**"]
  pull_request:
    branches: [main]

env:
  IMAGE_NAME: acme-hr-assistant
  REGISTRY: ghcr.io/${{ github.repository_owner }}

jobs:
  lint-and-test:
    name: Lint & Unit Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: pip install -r labs/devops/day-14/requirements.txt

      - name: Lint
        run: |
          ruff check .
          mypy labs/devops/_shared/app.py --ignore-missing-imports

      - name: Validate prompt manifest
        run: python -c "
          import json, jsonschema, pathlib
          manifest = json.loads(pathlib.Path('prompt-manifest.json').read_text())
          schema = json.loads(pathlib.Path('prompt-manifest.schema.json').read_text())
          jsonschema.validate(manifest, schema)
          print('Prompt manifest valid')
        "

      - name: Unit tests
        run: pytest labs/devops/day-14/tests/ -v --tb=short
        env:
          MOCK_LLM: "true"  # no API key needed

  build-and-scan:
    name: Build & Scan Image
    runs-on: ubuntu-latest
    needs: lint-and-test
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4

      - name: Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=sha-

      - name: Build image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: ${{ steps.meta.outputs.tags }}
          load: true

      - name: Scan image for CVEs
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.meta.outputs.tags }}
          format: table
          exit-code: "1"
          severity: HIGH,CRITICAL

  eval-gate:
    name: Eval Gate
    runs-on: ubuntu-latest
    needs: build-and-scan
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: pip install -r labs/devops/day-14/requirements.txt

      - name: Run eval harness
        run: |
          python labs/devops/day-14/eval_gate.py \
            --golden-dataset labs/devops/day-14/fixtures/golden.jsonl \
            --baseline labs/devops/day-14/fixtures/eval-baseline.json \
            --threshold-delta 0.05
        env:
          MOCK_LLM: "true"

      - name: Upload eval report
        uses: actions/upload-artifact@v4
        with:
          name: eval-report
          path: eval-report.json

  deploy:
    name: Deploy (Canary)
    runs-on: ubuntu-latest
    needs: eval-gate
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Update image tag in manifest
        run: |
          sed -i "s|image: .*acme-hr-assistant.*|image: ${{ needs.build-and-scan.outputs.image-tag }}|g" \
            deploy/kubernetes/deployment.yaml

      - name: Apply canary deployment
        run: bash deploy/deploy.sh --env=staging --canary-weight=10

      - name: Commit manifest update
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add deploy/kubernetes/deployment.yaml
          git commit -m "chore: bump image to ${{ github.sha }} [skip ci]"
          git push
```

#### 2.3.3 Equivalent GitLab CI Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - lint-and-test
  - build-and-scan
  - eval-gate
  - deploy

variables:
  IMAGE_NAME: acme-hr-assistant
  REGISTRY: $CI_REGISTRY_IMAGE
  MOCK_LLM: "true"

.python-setup: &python-setup
  image: python:3.11-slim
  before_script:
    - pip install -r labs/devops/day-14/requirements.txt

lint-and-test:
  stage: lint-and-test
  <<: *python-setup
  script:
    - ruff check .
    - mypy labs/devops/_shared/app.py --ignore-missing-imports
    - python -c "
        import json, jsonschema, pathlib;
        manifest = json.loads(pathlib.Path('prompt-manifest.json').read_text());
        schema = json.loads(pathlib.Path('prompt-manifest.schema.json').read_text());
        jsonschema.validate(manifest, schema);
        print('Prompt manifest valid')"
    - pytest labs/devops/day-14/tests/ -v --tb=short

build-and-scan:
  stage: build-and-scan
  image: docker:24
  services:
    - docker:24-dind
  needs: [lint-and-test]
  script:
    - docker build -t $REGISTRY/$IMAGE_NAME:$CI_COMMIT_SHORT_SHA .
    - |
      docker run --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        aquasec/trivy:latest image \
        --exit-code 1 --severity HIGH,CRITICAL \
        $REGISTRY/$IMAGE_NAME:$CI_COMMIT_SHORT_SHA
  artifacts:
    paths:
      - trivy-report.json
    expire_in: 30 days

eval-gate:
  stage: eval-gate
  <<: *python-setup
  needs: [build-and-scan]
  script:
    - python labs/devops/day-14/eval_gate.py
        --golden-dataset labs/devops/day-14/fixtures/golden.jsonl
        --baseline labs/devops/day-14/fixtures/eval-baseline.json
        --threshold-delta 0.05
  artifacts:
    paths:
      - eval-report.json
    reports:
      junit: eval-junit.xml
    expire_in: 90 days

deploy-staging:
  stage: deploy
  needs: [eval-gate]
  environment:
    name: staging
    url: https://staging.acme-hr.internal
  script:
    - bash deploy/deploy.sh --env=staging --canary-weight=10
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

deploy-production:
  stage: deploy
  needs: [eval-gate]
  environment:
    name: production
    url: https://hr.acme.internal
  script:
    - bash deploy/deploy.sh --env=production --canary-weight=10
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  when: manual  # require human approval for production
```

#### 2.3.4 Side-by-Side Syntax Comparison

| Concern | GitHub Actions | GitLab CI |
|---|---|---|
| Job dependency | `needs: [job-name]` | `needs: [job-name]` (same) |
| Conditional run | `if: github.ref == 'refs/heads/main'` | `rules: - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH` |
| Reusable config | Composite actions in `.github/actions/` | `extends:` keyword or `!reference` tags |
| Manual gate | `environment: protection rules` in GitHub UI | `when: manual` on the job |
| Secrets | `${{ secrets.MY_SECRET }}` | `$MY_SECRET` (CI/CD variables, masked) |
| Cache | `actions/cache@v4` with a key | `cache: key: paths:` block |
| Matrix builds | `strategy.matrix` | `parallel: matrix:` |

---

### 2.4 Prompt and Model Versioning

Source code versioning is well-understood, but prompts and model configurations are often left unversioned — a serious operational risk. A prompt change that silently degrades output quality is indistinguishable from a code bug if there is no version history.

#### 2.4.1 The Prompt Manifest Pattern

Store prompt metadata in a machine-readable **manifest file** alongside the application code. Check this file into version control. The CI/CD pipeline validates it on every commit.

```json
// prompt-manifest.json
{
  "schema_version": "1.0",
  "prompts": {
    "hr_answer": {
      "version": "2.4.1",
      "file": "prompts/hr_answer_v2.txt",
      "sha256": "a3f1b2c4d5e6...",
      "model": {
        "provider": "anthropic",
        "model_id": "claude-sonnet-4-5",
        "temperature": 0.3,
        "max_tokens": 1024
      },
      "eval_baseline": "eval-baselines/hr_answer_v2.4.1.json",
      "changelog": "v2.4.1: tightened citation format; reduced hallucination on edge cases"
    },
    "safety_classifier": {
      "version": "1.1.0",
      "file": "prompts/safety_v1.txt",
      "sha256": "b7c8d9e0f1a2...",
      "model": {
        "provider": "openai",
        "model_id": "gpt-5-mini",
        "temperature": 0.0,
        "max_tokens": 64
      },
      "eval_baseline": "eval-baselines/safety_v1.1.0.json",
      "changelog": "v1.1.0: added PII detection criteria"
    }
  }
}
```

#### 2.4.2 Semantic Versioning for Prompts

Apply **SemVer** (`MAJOR.MINOR.PATCH`) to prompts with a defined interpretation:

| Version bump | When to use | Example |
|---|---|---|
| **PATCH** (x.y.**Z**) | Whitespace, typos, wording that doesn't change meaning | `2.4.0 → 2.4.1` |
| **MINOR** (x.**Y**.0) | Adds capability, changes output format, adds instructions | `2.3.0 → 2.4.0` |
| **MAJOR** (**X**.0.0) | Breaking change: output schema change, persona pivot, model swap | `1.x.x → 2.0.0` |

A MINOR or MAJOR bump **must** trigger a new eval baseline. The CI/CD pipeline can enforce this: if the manifest version changed and no new baseline file exists at the expected path, the eval-gate stage fails.

#### 2.4.3 Model Pinning

Pin model identifiers to specific versioned strings — never use mutable aliases like `"latest"` or `"gpt-4"` in production. Example:

```python
# Bad — resolves to a different model each time the provider updates
MODEL = "gpt-4"

# Good — pinned to a specific snapshot
MODEL = "gpt-4o-2024-08-06"

# Also good — pinned through the manifest
MODEL = prompt_manifest["prompts"]["hr_answer"]["model"]["model_id"]
```

Store the pinned model ID in the prompt manifest. When you intentionally upgrade the model, bump the prompt version accordingly and update the baseline.

---

### 2.5 Progressive Delivery: Canary and Blue/Green

"Deploy everything at once" is the highest-risk deployment strategy. Progressive delivery reduces blast radius by routing only a fraction of traffic to the new version, observing real metrics, and promoting or rolling back based on evidence.

#### 2.5.1 Blue/Green Deployments

Maintain **two identical environments** (blue = current production, green = new version). Traffic is switched atomically from blue to green using a load balancer or DNS update.

```
                       ┌───────────────────────┐
Users ──► Load         │  Blue (v2.4.0) — LIVE │ ◄── 100% traffic
         Balancer ─►   └───────────────────────┘

Deploy new version:

                       ┌───────────────────────┐
Users ──► Load         │  Blue (v2.4.0) — IDLE │  0% traffic (kept warm)
         Balancer ─►   └───────────────────────┘
                       ┌───────────────────────┐
                       │  Green (v2.5.0) — LIVE│ ◄── 100% traffic
                       └───────────────────────┘
```

**Rollback:** Switch traffic back to blue instantly. Blue is kept warm until green is validated.

**Strengths:** Zero-downtime switch; instant rollback; simple traffic model.

**Weaknesses:** Requires 2× compute; database schema changes that are not backward-compatible are dangerous (both versions share the DB).

#### 2.5.2 Canary Deployments

Route a small percentage of real traffic to the new version while the majority continues on the stable version. Gradually increase the canary weight as confidence grows.

```
Users ──► Load Balancer ──► Stable v2.4.0   (90% of requests)
                       └──► Canary v2.5.0   (10% of requests)
                                │
                          monitor metrics
                         (error rate, latency,
                          eval score samples)
                                │
                    ┌──────────┴──────────┐
                    │ metrics healthy?    │
                   YES                   NO
                    │                    │
              increase weight         rollback:
              to 25% → 50%            set canary
              → 100%                  weight to 0%
```

**Rollback:** Set canary weight to 0% — takes seconds and only a fraction of users were affected.

**Strengths:** Real traffic validation with bounded blast radius; gradual ramp reduces risk.

**Weaknesses:** Requires traffic-splitting infrastructure; both versions run simultaneously (state/DB compatibility required).

#### 2.5.3 LLM-Specific Rollback Signals

In addition to standard signals (HTTP error rate, p99 latency), LLM services should monitor:

| Signal | How to collect | Rollback threshold example |
|---|---|---|
| Eval score (sampled) | Run eval harness on 5% of canary responses | Score drops > 5% vs. baseline |
| User thumbs-down rate | UI feedback, logged and aggregated | Rate > 3× stable average |
| Safety classifier fail rate | Run classifier on all canary outputs | Any increase above stable baseline |
| Hallucination marker rate | Keyword heuristics or LLM-as-judge spot check | Absolute rate > 2% |

---

### 2.6 Terraform IaC Basics

**Infrastructure as Code (IaC)** means defining cloud infrastructure in declarative configuration files that are version-controlled and applied by a tool — just as application code is compiled and deployed. **Terraform** (by HashiCorp) is the dominant open-source IaC tool for multi-cloud infrastructure.

#### 2.6.1 Core Concepts

| Concept | Description |
|---|---|
| **Provider** | Plugin that translates Terraform config into API calls for a specific platform (AWS, GCP, Azure, Kubernetes, Docker, etc.) |
| **Resource** | A manageable infrastructure object: a VM, a container service, a database, a load balancer |
| **Data source** | Read-only reference to existing infrastructure not managed by this Terraform config |
| **Variable** | Input parameter; allows the same config to be reused across environments |
| **Output** | Value exported from the config (e.g., the endpoint URL of the created service) |
| **State** | JSON file that records the current known state of all managed resources — the source of truth for `plan` and `apply` |
| **Module** | Reusable grouping of resources published and consumed like a library |

#### 2.6.2 Workflow

```
terraform init       # download providers and modules
terraform plan       # show what would change (diff vs. state)
terraform apply      # create/update/delete resources to match config
terraform destroy    # tear down all managed resources
```

#### 2.6.3 Illustrative HCL Example

The following provisions a container-based compute service (provider-flexible — substitute your cloud provider's equivalent resource type):

```hcl
# main.tf — Acme HR Assistant infrastructure (illustrative)

terraform {
  required_version = ">= 1.6"
  required_providers {
    # Replace with your cloud provider block, e.g.:
    # aws = { source = "hashicorp/aws", version = "~> 5.0" }
    # google = { source = "hashicorp/google", version = "~> 5.0" }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }

  # Remote state backend (recommended for teams):
  # backend "s3" {
  #   bucket = "acme-tf-state"
  #   key    = "hr-assistant/terraform.tfstate"
  #   region = "us-east-1"
  #   encrypt = true
  # }
}

# ── Variables ──────────────────────────────────────────────────────────

variable "environment" {
  description = "Deployment environment: dev, staging, or production"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be dev, staging, or production."
  }
}

variable "image_tag" {
  description = "Container image tag to deploy (e.g., sha-abc1234)"
  type        = string
}

variable "replica_count" {
  description = "Number of service replicas"
  type        = number
  default     = 2
}

variable "llm_model_id" {
  description = "Pinned LLM model identifier from prompt-manifest.json"
  type        = string
}

# ── Locals ─────────────────────────────────────────────────────────────

locals {
  service_name = "acme-hr-assistant-${var.environment}"
  image_uri    = "ghcr.io/acme-corp/acme-hr-assistant:${var.image_tag}"

  common_labels = {
    app         = "acme-hr-assistant"
    environment = var.environment
    managed_by  = "terraform"
  }
}

# ── Resources ──────────────────────────────────────────────────────────

# Illustrative: a Docker container resource (works locally with docker provider)
# In a real cloud deployment, replace with:
#   aws_ecs_service / aws_ecs_task_definition  (AWS ECS)
#   google_cloud_run_v2_service                (GCP Cloud Run)
#   azurerm_container_group                    (Azure ACI)
#   kubernetes_deployment                      (any K8s cluster)

resource "docker_image" "hr_assistant" {
  name         = local.image_uri
  keep_locally = true
}

resource "docker_container" "hr_assistant" {
  count = var.replica_count
  name  = "${local.service_name}-${count.index}"
  image = docker_image.hr_assistant.image_id

  ports {
    internal = 8000
    external = 8000 + count.index
  }

  env = [
    "ENVIRONMENT=${var.environment}",
    "LLM_MODEL_ID=${var.llm_model_id}",
    "LOG_LEVEL=${var.environment == "production" ? "WARNING" : "DEBUG"}",
    "MOCK_LLM=${var.environment == "dev" ? "true" : "false"}",
  ]

  labels {
    label = "app"
    value = "acme-hr-assistant"
  }
  labels {
    label = "environment"
    value = var.environment
  }

  restart = "unless-stopped"
}

# ── Outputs ────────────────────────────────────────────────────────────

output "service_name" {
  description = "Name of the deployed service"
  value       = local.service_name
}

output "container_ids" {
  description = "IDs of the running containers"
  value       = [for c in docker_container.hr_assistant : c.id]
}
```

#### 2.6.4 Terraform State: What It Is and Why It Is Sensitive

Terraform writes a **state file** (`terraform.tfstate`) after every `apply`. This JSON file records:

- The current configuration of every managed resource.
- IDs, ARNs, connection strings, IP addresses, and resource attributes.
- Cross-resource relationships and dependency order.

**Why it is sensitive:**

1. The state file contains **plaintext secrets** — database passwords, API keys, and private keys passed as resource attributes are stored unencrypted by default.
2. It maps your **entire infrastructure topology**, making it a high-value target for attackers who want to understand your blast radius or enumerate attack surfaces.
3. **Drift detection** requires the state file to be accurate. If the state is lost or corrupted, Terraform cannot safely manage resources and may try to recreate existing infrastructure.

**Best practices:**

- Store state in an **encrypted remote backend** (cloud storage bucket with server-side encryption) — never commit `terraform.tfstate` to version control.
- Enable **state locking** (DynamoDB for AWS, GCS object locking for GCP) to prevent concurrent `apply` operations from corrupting state.
- Treat state files with the same access controls as production database credentials.

---

### 2.7 Environment Promotion Patterns

A **promotion pattern** defines how a change moves from development through staging to production, what gates must be passed at each boundary, and who can approve the promotion.

#### 2.7.1 The Three-Environment Model

```
 ┌──────────────────────────────────────────────────────────────────────┐
 │  dev                                                                  │
 │  • Any push to a feature branch                                       │
 │  • MOCK_LLM=true (no real API calls)                                  │
 │  • Single replica, no HA                                              │
 │  • Rapid iteration; no approval gate                                  │
 └─────────────────────────┬────────────────────────────────────────────┘
                           │ PR merged to main
                           │ Gate: lint + unit tests + eval gate pass
                           ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  staging                                                              │
 │  • Mirrors production config (real LLM, production-like data volume) │
 │  • Canary at 10% within staging (if multi-tenant staging)             │
 │  • Full eval suite runs nightly against golden dataset                │
 │  • Load test and latency SLA check                                    │
 │  • Gate: all checks pass + 24-hour soak period for stateful services  │
 └─────────────────────────┬────────────────────────────────────────────┘
                           │ Manual approval by tech lead or release manager
                           │ Gate: eval score ≥ baseline, load test pass,
                           │       security scan clean, change record open
                           ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  production                                                           │
 │  • Canary deploy: 10% → 25% → 50% → 100% with automated checks       │
 │  • Rollback trigger: any metric breaches threshold                    │
 │  • Post-deploy eval sample: 5% of live traffic scored asynchronously  │
 │  • Incident response runbook link in deploy job output               │
 └──────────────────────────────────────────────────────────────────────┘
```

#### 2.7.2 Promotion Gates Reference

| Boundary | Automated gate | Manual gate |
|---|---|---|
| Feature → dev | Lint, unit tests pass | Code review approval (PR) |
| dev → staging | Full CI pipeline (lint + build + scan + eval) | — |
| staging → production | Load test pass, eval ≥ baseline, security scan clean | Release manager sign-off; change record |
| Canary 10% → 100% | Error rate, latency, eval sample all within thresholds | Optional: SRE review at 50% |

#### 2.7.3 GitOps Promotion

A common pattern is to use **GitOps**: each environment has its own configuration branch or directory, and a promotion is a **pull request** that updates the image tag or Helm values. The CI/CD system watches the repository and applies changes automatically. This creates a full audit trail — every production change is a reviewed, approved, merged commit.

```
repos/
  hr-assistant/           ← application code
    .github/workflows/    ← pipeline definition
    prompt-manifest.json  ← versioned prompts

  hr-infra/               ← GitOps config repo
    envs/
      dev/
        values.yaml       ← image_tag: sha-abc1234
      staging/
        values.yaml       ← image_tag: sha-abc1234
      production/
        values.yaml       ← image_tag: sha-xyz5678  (promoted separately)
```

---

## 3. Hands-on Lab

**Lab directory:** `labs/devops/day-14/`

**Shared application:** `labs/devops/_shared/` — the Acme HR Knowledge Assistant FastAPI app used throughout Days 6–13. The lab builds CI/CD tooling around this application.

### Setup

```bash
pip install -r labs/devops/day-14/requirements.txt
```

### Lab Files

| File | Purpose |
|---|---|
| `labs/devops/day-14/starter.py` | Skeleton with `# TODO` markers — your starting point |
| `labs/devops/day-14/solution.py` | Complete working solution — use to validate your work |
| `labs/devops/day-14/requirements.txt` | Python dependencies (FastAPI, httpx, pytest, PyYAML, pydantic) |
| `labs/devops/day-14/fixtures/golden.jsonl` | Golden dataset for the eval gate |
| `labs/devops/day-14/fixtures/eval-baseline.json` | Baseline scores for the eval gate |
| `labs/devops/day-14/tests/test_pipeline.py` | Unit tests for pipeline validation logic |
| `.github/workflows/deploy.yml` | GitHub Actions workflow (you will parse and validate this) |
| `deploy/main.tf` | Terraform config (you will parse and validate this) |
| `deploy/deploy.sh` | Deployment script (you will check it exists and is executable) |
| `prompt-manifest.json` | Prompt manifest (you will load and validate this) |
| `prompt-manifest.schema.json` | JSON Schema for the manifest |

### What You Will Build in `starter.py`

Work through each `# TODO` in order:

1. **TODO 1 — Parse the GitHub Actions workflow.** Load `.github/workflows/deploy.yml` and extract the job names in dependency order. Assert that the four required stages are present: `lint-and-test`, `build-and-scan`, `eval-gate`, `deploy`.

2. **TODO 2 — Validate stage ordering.** Assert that `build-and-scan` depends on `lint-and-test`, `eval-gate` depends on `build-and-scan`, and `deploy` depends on `eval-gate`. The `needs:` field encodes this.

3. **TODO 3 — Parse the Terraform config.** Load `deploy/main.tf` and assert that it contains: a `terraform` block, at least one `variable` block, at least one `resource` block, and at least one `output` block.

4. **TODO 4 — Check the deploy script.** Assert that `deploy/deploy.sh` exists and is executable (`os.access(path, os.X_OK)`).

5. **TODO 5 — Load and validate the prompt manifest.** Load `prompt-manifest.json`, validate it against `prompt-manifest.schema.json` using `jsonschema`, and assert that every prompt entry has a `version` field following SemVer (`MAJOR.MINOR.PATCH`).

6. **TODO 6 — Smoke-test the app via TestClient.** Import the FastAPI app from `labs/devops/_shared/app.py`, create a `TestClient`, send a `POST /ask` request with a sample HR question, and assert that the response is HTTP 200 with a non-empty `answer` field. Set `MOCK_LLM=true` in the environment so no API key is required.

### Validate

```bash
python labs/devops/day-14/solution.py
```

The solution script runs all six checks and prints a report. Expected output:

```
[PASS] Workflow: 4 stages found and correctly ordered
[PASS] Terraform: required blocks present (terraform, variable, resource, output)
[PASS] deploy.sh: exists and is executable
[PASS] Prompt manifest: valid JSON Schema; 2 prompts with valid SemVer versions
[PASS] App smoke test: POST /ask → 200 OK, answer field present
[PASS] All 5 checks passed. Day 14 lab complete.
```

No real cloud account, Kubernetes cluster, or LLM API key is required.

---

## 4. Self-Check Quiz

Answer each question before revealing the answer.

**Q1.** A team adds a new system prompt to the Acme HR assistant and runs the CI pipeline. All unit tests pass and the image builds cleanly. The eval gate runs and reports a faithfulness score of 0.71, down from a baseline of 0.82 — a drop of 11 percentage points. The pipeline is configured with `--threshold-delta 0.05`. What happens and why?

<details>
<summary>Show answer</summary>

The eval gate fails and blocks the deploy stage from running. The observed score drop (0.11) exceeds the allowed delta (0.05). This is the correct behaviour: the new system prompt degraded answer faithfulness, and the eval gate caught the regression before it reached production. The unit tests could not catch this because they test code logic (routing, schema validation, error handling), not answer quality. The team must revise the prompt, re-run the eval gate, and only proceed when the faithfulness score is within the allowed delta of the baseline.

</details>

---

**Q2.** You are versioning the `hr_answer` prompt. The current version is `2.4.1`. You make the following changes:
- Fix a typo in the word "benefits" (was "benfits").
- Add a new instruction: "Always cite the specific policy section number."
- Change the output format from a paragraph to a structured JSON object.

What is the correct new version, and why?

<details>
<summary>Show answer</summary>

The new version is **3.0.0** (a MAJOR bump). The output format change from a paragraph to a structured JSON object is a breaking change — any consumer of the API that parses the response as plain text will break. The new instruction (cite policy section) is a MINOR change, and the typo fix is a PATCH change. When multiple changes occur together, you apply the **highest-severity** version bump. Because there is a breaking change, the version must be bumped to a new MAJOR. A MAJOR bump also requires creating a new eval baseline at `eval-baselines/hr_answer_v3.0.0.json` before the CI pipeline will accept the change.

</details>

---

**Q3.** Your team is choosing between blue/green and canary for the next production deployment of the HR assistant. The deployment includes a database schema migration that is **not backward-compatible** (a column is renamed). Which strategy is safer, and what additional step is required?

<details>
<summary>Show answer</summary>

Neither strategy is safe as described — a non-backward-compatible schema change is the most dangerous class of deployment because both blue/green and canary require both versions to coexist during the transition period. The additional required step is to **decouple the schema migration from the application deployment** using an expand/contract pattern:

1. **Expand**: Deploy a database migration that adds the new column alongside the old one (both exist). Deploy app version N+1 that writes to both columns and reads from the new one.
2. **Contract**: After all traffic is on version N+1 and no rollback is needed, run a second migration that drops the old column.

With this pattern, blue/green becomes safe: blue uses the old column, green uses both, and if you roll back to blue the old column still exists. Never rename a column in a single migration when zero-downtime deployment is required.

</details>

---

**Q4.** Where is Terraform state stored by default, and what is the problem with that default for a team of three engineers all running `terraform apply`?

<details>
<summary>Show answer</summary>

By default, Terraform writes state to a local file `terraform.tfstate` in the working directory. For a team, this creates three problems:

1. **No sharing**: Each engineer has their own local state file, so each engineer's view of infrastructure differs. Engineer A may not know that Engineer B already created the database.
2. **No locking**: If two engineers run `terraform apply` simultaneously, both read the same state and both try to modify infrastructure. This causes race conditions and can corrupt the state or create duplicate resources.
3. **No backup**: A local file is lost if the engineer's machine fails.

The solution is a **remote state backend** (e.g., S3 + DynamoDB for locking on AWS, GCS + object locking on GCP, Terraform Cloud). The remote backend centralises state, provides locking, and encrypts the file at rest.

</details>

---

**Q5.** A canary deployment of the HR assistant is at 10% traffic. After 20 minutes you observe: error rate on canary is 0.3% (stable: 0.2%), p99 latency is 420 ms (stable: 380 ms), and the async eval sample score is 0.79 (baseline: 0.82, delta threshold: 0.05). Should you promote to 25%, hold, or rollback? Justify each metric.

<details>
<summary>Show answer</summary>

**Recommendation: hold (do not promote yet; do not rollback yet).**

- **Error rate (0.3% vs. 0.2%)**: A 50% relative increase, but both values are very low in absolute terms. Not an automatic rollback trigger, but worth monitoring. Set an alert if canary error rate exceeds 0.5%.
- **p99 latency (420 ms vs. 380 ms)**: A 10% increase. If the SLA is 500 ms this is within bounds, but a consistent latency increase warrants investigation before promoting. Check whether the new version is doing extra work (e.g., a new retrieval call).
- **Eval score (0.79 vs. 0.82 baseline, delta = 0.03)**: The drop of 0.03 is **within** the 0.05 threshold. This is not a rollback trigger. However, the score is trending below baseline.

With all three metrics showing mild degradation, the safest action is to **hold at 10%** for another 30–60 minutes and collect more data. If any metric breaches its threshold during the hold period, rollback. If all metrics stabilise within bounds, promote to 25%. Do not rollback on current data alone — the sample sizes at 10% traffic may be too small for statistical significance.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1: Why include an eval gate in CI/CD rather than relying on unit tests and integration tests?**

<details>
<summary>Show answer</summary>

Unit tests verify **code correctness**: does the function return the right type, does the router call the right endpoint, does error handling work? They are fast, deterministic, and excellent at what they test. Integration tests verify that **services connect correctly**: does the FastAPI app start, does the retrieval pipeline return results, do requests flow end-to-end?

Neither category can detect **output quality regression** because LLM output quality is not a property of code logic — it is an emergent property of the combination of prompt, model version, retrieval configuration, and input distribution. A typo in a system prompt, a model version bump, or a temperature change can silently degrade faithfulness, safety, or relevance while all unit and integration tests continue to pass.

The eval gate operates in a different semantic space: it runs a **scored evaluation** over a representative golden dataset and compares the score to a stored baseline. If the score drops beyond a threshold, the gate blocks the deploy. This is the only CI/CD mechanism that can catch quality regressions before they reach users. The three layers are complementary, not substitutes: unit tests catch logic bugs (fast, cheap), integration tests catch wiring bugs (medium cost), and the eval gate catches quality regressions (slower, more expensive — but catches what the others miss).

</details>

---

**Q2: How do canary and blue/green differ in rollback risk, and when should you choose each?**

<details>
<summary>Show answer</summary>

The key difference is **blast radius during the exposure window**.

In a **blue/green** deployment, the switch is atomic: 0% of users see the new version until you flip the load balancer, then 100% of users see it. Rollback is instant (flip back), but if the new version has a defect, **100% of users are affected** from the moment of promotion until the rollback completes (typically seconds to minutes). Blue/green is best for changes where you have very high confidence in the new version (comprehensive staging tests, identical staging and production environments) and where the deployment is simple to validate quickly.

In a **canary** deployment, the new version receives a small traffic percentage (e.g., 10%) while 90% of users remain on the stable version. If the canary has a defect, only 10% of users are affected — the rollback involves routing that 10% back to stable. The trade-off is that the exposure window is longer (you need time to collect meaningful metrics at each weight tier), and you need traffic-splitting infrastructure. Canary is preferred for high-traffic, high-stakes services where even a brief 100% exposure to a defective version would have significant user or revenue impact, and for LLM services where you want to validate eval scores against **real production traffic** (not just golden datasets).

For LLM services, canary is generally preferred because eval scores on golden datasets may not reflect the actual diversity of production queries.

</details>

---

**Q3: What does Terraform state represent, and why is it sensitive?**

<details>
<summary>Show answer</summary>

Terraform state is a **JSON snapshot of the last-known configuration of every infrastructure resource** that Terraform manages. After each `terraform apply`, Terraform writes the state file with the current resource IDs, attributes, connection strings, and dependency graph. On the next run, Terraform computes a **diff between the state file and the desired configuration** to determine what to create, update, or destroy.

State is sensitive for three reasons. First, it contains **plaintext secrets**: any value passed to a resource block (database password, API key, private key) is stored unencrypted in the state file by default. Even if the Terraform code uses a secrets manager reference, the resolved value at apply time may appear in state. Second, it is a **complete map of your infrastructure**: an attacker who obtains the state file knows every resource you run, their IDs, their network configuration, and their relationships — a significant reconnaissance advantage. Third, **corrupted or lost state breaks Terraform's ability to manage infrastructure**: without accurate state, Terraform cannot safely plan changes and may attempt to recreate existing resources (potentially causing data loss or outages).

The standard mitigations are: store state in an encrypted remote backend with access controls, enable state locking to prevent concurrent modification, restrict who can read the state backend, and never commit `terraform.tfstate` to version control.

</details>

---

**Q4: How do you version a prompt in a CI/CD pipeline, and what does the pipeline validate?**

<details>
<summary>Show answer</summary>

Prompt versioning in CI/CD has three components: the **manifest file**, the **validation step**, and the **baseline coupling**.

The **prompt manifest** (`prompt-manifest.json`) is a machine-readable file checked into the repository alongside the application code. It records, for each named prompt: the semantic version, the file path to the prompt text, a SHA-256 hash of the prompt file, the pinned model ID and parameters, and the path to the eval baseline JSON for that version.

The **validation step** in Stage 1 (lint-and-test) loads the manifest and checks: (a) the JSON is valid against the manifest JSON Schema, (b) every version string follows SemVer `MAJOR.MINOR.PATCH`, (c) the SHA-256 hash of each prompt file matches the hash recorded in the manifest (catches accidental edits without version bumps), and (d) the referenced baseline file exists at the expected path.

The **baseline coupling** rule is enforced in the eval gate: if the prompt version has changed since the last pipeline run (detectable via git diff on the manifest), the pipeline checks that a new baseline file exists for the new version. If someone bumped the version but did not generate a new baseline, the eval gate has nothing to compare against and fails.

This combination means that every prompt change must be intentional (version bumped, SHA updated), validated (schema check, hash check), and accompanied by a quality measurement (new baseline), before the pipeline allows a deploy.

</details>

---

**Q5: What makes LLM CI/CD fundamentally different from traditional software CI/CD?**

<details>
<summary>Show answer</summary>

Several properties of LLM services have no equivalent in traditional software:

**Non-determinism.** Running the same test input twice may produce different outputs. Traditional test assertions (`assert output == expected`) are unreliable. LLM CI/CD requires **scoring** rather than exact matching, and statistical aggregation over a dataset rather than individual test cases.

**Quality as an emergent property.** Traditional software quality is fully determined by code logic. LLM service quality is jointly determined by prompt text, model version, retrieval configuration, temperature, and input distribution. A code change that doesn't touch any of these can still change output quality if, for example, a dependency update changes tokenisation.

**Artefacts that aren't code.** Prompts, model weights, golden datasets, and eval baselines are first-class artefacts that must be versioned, validated, and stored — but traditional CI/CD tooling has no built-in concept of them. The manifest pattern is a workaround for this gap.

**Slow and expensive quality tests.** Running an eval harness over 500 golden examples with a real LLM takes minutes and costs money. Traditional test suites run in seconds. This drives trade-offs: use mocked LLMs in fast unit tests, use real LLMs only in the eval gate (or sample a subset in CI, run the full set nightly).

**Model providers as external dependencies.** A model API is an external service that can change behaviour through silent model updates, rate limits, or outages. Traditional CI/CD has no analogue to a dependency that can "drift" in quality without any version change on your side.

</details>

---

**Q6: How do you promote safely from staging to production for an LLM service?**

<details>
<summary>Show answer</summary>

Safe promotion requires automated gates and a structured human decision point.

**Automated gates that must pass in staging:**
- Full eval suite score ≥ baseline for all prompt versions deployed.
- Load test: p95 latency within SLA under peak-traffic simulation.
- Security scan: no new HIGH or CRITICAL CVEs in the image.
- Safety classifier pass rate: no regression vs. production baseline.
- Soak period: service runs for at least the required duration (e.g., 24 hours for stateful services) without alerts firing.

**Human decision gate:** A release manager or tech lead reviews the automated gate report and the change record (what changed, why, risk assessment) before approving the production promotion. This gate exists because automated checks cannot evaluate business context — a change that is technically safe may be operationally risky (e.g., a major prompt overhaul during peak business hours).

**Production deployment itself is progressive (canary):** start at 10%, collect 30 minutes of real-traffic metrics (error rate, latency, async eval sample), promote to 25%, repeat, promote to 50% and 100%. Each step is automated but can be paused or rolled back by the on-call engineer.

**Post-deploy:** Run an async eval sample on 5% of live production traffic for 24 hours after full promotion. If the eval score trends below baseline, initiate an automatic rollback review. This closes the loop between production behaviour and the CI/CD quality gate.

</details>

---

**Q7: Your Terraform `plan` shows that changing a single variable will destroy and recreate a production database. How do you handle this safely?**

<details>
<summary>Show answer</summary>

Terraform's plan is deterministic: if a resource attribute that requires replacement (marked `# forces replacement` in the plan output) changes, Terraform will destroy the old resource and create a new one. For a production database this is catastrophic if executed naively.

**Safe handling approach:**

1. **Understand why replacement is required.** Some attributes (e.g., RDS `engine_version` for a major version jump, `subnet_group_name`) cannot be changed in-place. Others can be changed without replacement if applied differently (e.g., via a snapshot + restore).

2. **Use `lifecycle { prevent_destroy = true }`.** Adding this to the database resource causes `terraform plan` to error rather than show a destroy — a hard guardrail that prevents accidental destruction.

3. **Use `terraform state mv` or `terraform import` to restructure state** without destroying the resource. If you are renaming a resource in HCL (e.g., `aws_db_instance.old` → `aws_db_instance.new`), move it in state first so Terraform sees it as the same resource.

4. **Decouple the change.** Instead of changing the variable directly, provision the new database alongside the old one, migrate data, update the application connection string, verify, then decommission the old database. Terraform manages both resources during the transition.

5. **Never run `terraform apply` on production without a peer-reviewed plan file** (`terraform plan -out=tfplan` → review → `terraform apply tfplan`). The plan file is cryptographically bound to the state at plan time, preventing surprises from concurrent changes.

</details>

---

## 6. Further Reading

| Resource | URL | Why read it |
|---|---|---|
| GitHub Actions documentation — Workflow syntax | https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions | Complete reference for `on:`, `jobs:`, `steps:`, `needs:`, `env:`, `secrets`, and matrix builds |
| GitLab CI/CD documentation — Pipeline configuration reference | https://docs.gitlab.com/ee/ci/yaml/ | Authoritative reference for `.gitlab-ci.yml`: `stages:`, `rules:`, `extends:`, `artifacts:`, `cache:`, and `include:` |
| Terraform documentation — Language overview | https://developer.hashicorp.com/terraform/language | Covers providers, resources, variables, outputs, locals, modules, and state management |
| Terraform — State and backends | https://developer.hashicorp.com/terraform/language/state | Explains state file format, remote backends, locking, and security considerations |
| Argo Rollouts — Progressive Delivery concepts | https://argoproj.github.io/argo-rollouts/ | Kubernetes-native canary and blue/green controller; explains weight-based traffic splitting and automated analysis |
| OpenTelemetry — LLM observability semantic conventions | https://opentelemetry.io/docs/specs/semconv/gen-ai/ | Standard attribute names for tracing LLM calls — important for eval sampling in production |

---

## 7. What's Next

**Day 15 — DevOps Capstone** is the final day of the track. You will apply everything from Days 6–14 to build, evaluate, and operate a production-grade LLM service end-to-end.

**Capstone materials are in `capstone/devops/`.**

The capstone covers:
- Packaging the Acme HR Knowledge Assistant with a complete CI/CD pipeline (GitHub Actions or GitLab CI — your choice).
- Writing Terraform configuration to provision the compute and networking infrastructure for the service.
- Implementing canary deployment logic in the deploy script.
- Running the full eval gate against a provided golden dataset and demonstrating that it blocks a deliberately broken prompt.
- Producing a deployment runbook documenting your pipeline stages, promotion gates, and rollback procedure.

Before Day 15:
- Make sure you can run `python labs/devops/day-14/solution.py` cleanly.
- Review the capstone `README.md` in `capstone/devops/` for the full task list and acceptance criteria.
- Skim your Day 11 (observability) and Day 13 (security/governance) notes — both feed directly into the capstone's pipeline and runbook requirements.

> **Key takeaways from Day 14:**
> - The eval gate is the CI/CD stage that catches quality regressions that unit tests cannot see. It is not optional for LLM services in production.
> - Prompt versioning via a manifest file makes prompt changes auditable, reviewable, and blockable by the pipeline — just like code changes.
> - Canary deployments are preferred for LLM services because they bound the blast radius and allow eval scoring on real production traffic before full promotion.
> - Terraform state is the authoritative record of your infrastructure; protect it like a production database credential.
> - Every promotion boundary (dev → staging → production) must have automated gates and, for the final production promotion, a human decision point.
