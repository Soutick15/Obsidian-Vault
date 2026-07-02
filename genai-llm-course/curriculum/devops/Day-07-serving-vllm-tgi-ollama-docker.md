# Day 7 — Serving LLM Applications: vLLM, TGI, Ollama, and Docker

**Track:** DevOps with AI  
**Day:** 7 of 15  
**Prerequisites:** Days 1–6 (LLM fundamentals, tokens, prompting, APIs, and Day 6 shared HR app + operational concerns)

---

## 1. Objectives

By the end of this day you will be able to:

1. Explain the purpose of a model-serving layer and why it exists between raw model weights and an application.
2. Compare vLLM, TGI, and Ollama — their architecture, strengths, and appropriate use cases.
3. Define **continuous batching** and explain why it dramatically improves GPU utilisation versus static batching.
4. Write a production-grade `Dockerfile` for a FastAPI LLM service, applying best practices: slim base, layer caching, multi-stage builds, non-root user, `.dockerignore`, and `HEALTHCHECK`.
5. Describe the trade-offs between self-hosting a model versus using a hosted provider API.
6. Apply 12-factor config principles to containerised LLM services.

---

## 2. Concept Reading

### 2.1 The Serving Stack: Why Another Layer?

When a model finishes training it is a set of weights on disk — a `.safetensors` or `.gguf` file. To serve inference requests you need:

```
Client (HTTP)
      │
      ▼
┌─────────────────────┐
│  Application Layer  │  FastAPI / your product code
│  (business logic)   │
└──────────┬──────────┘
           │ LLM calls
           ▼
┌─────────────────────┐
│  Model Serving Layer│  vLLM / TGI / Ollama
│  (inference engine) │  — batching, KV-cache, scheduling
└──────────┬──────────┘
           │ GPU kernels
           ▼
┌─────────────────────┐
│  Hardware           │  GPU(s) / CPU
└─────────────────────┘
```

The **model serving layer** handles the hard parts of inference at scale: scheduling concurrent requests, managing the GPU memory (KV-cache), and exposing a standard HTTP API. Your application code calls that API as if it were any other microservice.

### 2.2 FastAPI as the Application Layer (Recap)

The shared Acme HR app (`labs/devops/_shared/app.py`) already wraps its LLM call inside a FastAPI endpoint:

```
POST /chat  →  retrieve context  →  call answer()  →  return JSON
```

That `answer()` function today calls a mock or a hosted provider. In a self-hosted scenario it would call `http://localhost:8000/v1/chat/completions` — the **OpenAI-compatible endpoint** that vLLM, TGI, and Ollama all expose.

This compatibility matters: your application code does not change when you switch serving backends. Only the `base_url` environment variable changes.

### 2.3 vLLM

**What it is:** An open-source, high-throughput LLM inference and serving library from UC Berkeley, designed for production GPU deployments.

**Key capabilities:**
- **PagedAttention** — manages KV-cache memory like OS virtual memory (paging), eliminating KV-cache fragmentation and enabling much larger effective batch sizes.
- **Continuous batching** (see §2.5) — fully implemented; best-in-class throughput benchmarks.
- **OpenAI-compatible REST API** — drop-in replacement for `openai.OpenAI(base_url=...)`.
- Supports tensor parallelism across multiple GPUs.
- Serves models from Hugging Face Hub or local paths.

**When to use vLLM:**
- You have one or more NVIDIA GPUs (A100, H100, L40S, etc.).
- You need high throughput — many requests per second.
- You want the OpenAI API surface without the hosted cost.
- Models: Llama-3, Mistral, Mixtral, Qwen, Gemma, etc.

**Quick reference:**
```bash
# Install
pip install vllm

# Start an OpenAI-compatible server
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --host 0.0.0.0 \
  --port 8001

# Call from Python (no code change in your app beyond base_url)
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8001/v1", api_key="ignored")
response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    messages=[{"role": "user", "content": "What is PTO policy?"}]
)
```

### 2.4 TGI — Text Generation Inference

**What it is:** Hugging Face's production inference server, written in Rust with Python bindings. The backend that powers Hugging Face Inference Endpoints.

**Key capabilities:**
- **Continuous batching** with a Rust scheduler — very low latency at moderate batch sizes.
- **Flash Attention 2** and other kernel optimisations baked in.
- OpenAI-compatible endpoint (`/v1/chat/completions`).
- Built-in token streaming (SSE).
- Model quantisation: GPTQ, AWQ, bitsandbytes out of the box.
- Docker-first: Hugging Face publishes an official `ghcr.io/huggingface/text-generation-inference` image.

**When to use TGI:**
- You are already in the Hugging Face ecosystem.
- You need quantised models with minimal setup.
- You want a battle-tested production image from a major vendor.

**Quick reference:**
```bash
# Run via Docker (GPU)
docker run --gpus all \
  -v $HOME/.cache/huggingface:/data \
  -p 8002:80 \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id mistralai/Mistral-7B-Instruct-v0.2
```

### 2.5 Continuous Batching — Why It Matters

Traditional **static batching** groups requests into a fixed batch, waits for every request to finish, then starts the next batch. Requests that finish early sit idle waiting for the slowest request:

```
Static batch (4 requests):
  Req A ██████████████████ (18 tokens)
  Req B █████              (5 tokens)  ← waits 13 token-steps idle
  Req C ████████████       (12 tokens) ← waits 6 token-steps idle
  Req D ██                 (2 tokens)  ← waits 16 token-steps idle
  Time ─────────────────────────────►
```

**Continuous batching** (also called iteration-level scheduling) finishes each sequence at its own pace and immediately slots in the next waiting request at each forward pass:

```
Continuous batch:
  Step 1-2:  A B C D
  Step 3:    A   C   → D finishes, E enters
  Step 4:    A   C E → ...
  GPU stays near 100% utilisation throughout
```

**Impact:** 10-20x throughput improvement for mixed-length workloads compared to static batching. All three engines (vLLM, TGI, Ollama) implement variants of this.

### 2.6 Ollama

**What it is:** A local-first LLM runner designed for developer workstations and CPU-only machines. Uses `llama.cpp` under the hood with a clean CLI and REST API.

**Key capabilities:**
- Runs on CPU (or Apple Silicon MPS/Metal) — no GPU required.
- One-line model downloads: `ollama pull llama3.2`.
- OpenAI-compatible API at `http://localhost:11434/v1`.
- Model library with quantised GGUF files (4-bit, 8-bit).
- `Modelfile` concept for model customisation/system-prompt baking.

**When to use Ollama:**
- Local development without a GPU.
- Air-gapped or laptop environments.
- Rapid prototyping where throughput is not critical.
- Testing that your app integrates with an OpenAI-compatible server before moving to vLLM/TGI.

**Quick reference:**
```bash
# Install (macOS)
brew install ollama

# Pull and run a model
ollama pull llama3.2
ollama serve  # starts API at localhost:11434

# Call from Python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
response = client.chat.completions.create(
    model="llama3.2",
    messages=[{"role": "user", "content": "What is PTO policy?"}]
)
```

### 2.7 Self-Host vs Hosted API — Decision Framework

| Dimension | Self-Hosted (vLLM/TGI/Ollama) | Hosted API (Anthropic, OpenAI) |
|---|---|---|
| **Cost at scale** | GPU hourly rate; breaks even at ~$X/M tokens | Per-token pricing; cost grows linearly |
| **Latency** | Low (local network), but depends on hardware | Variable (network + provider load) |
| **Data privacy** | Data never leaves your infra | Data sent to provider |
| **Model choice** | Any open-weight model | Provider's catalogue only |
| **Ops burden** | High — GPU infra, scaling, upgrades | None |
| **Model quality** | Open models catching up; frontier still hosted | Frontier models (GPT-4o, Claude) |
| **Best for** | High-volume, privacy-sensitive, cost-optimised | Rapid development, best-quality output |

**Rule of thumb:** Start with a hosted API. Switch to self-hosting when monthly token cost exceeds ~$2,000–5,000 or data residency requirements demand it.

### 2.8 Docker Containerisation for LLM Services

#### Why containerise?

A container packages your application code, runtime, and dependencies into a single reproducible unit. It runs identically on a developer laptop, a CI pipeline, and a production Kubernetes cluster.

#### Dockerfile Best Practices for LLM Services

**1. Slim base image**

```dockerfile
# Bad — full image, ~1.2 GB
FROM python:3.11

# Good — slim variant, ~125 MB
FROM python:3.11-slim
```

The `slim` variant omits compilers, documentation, and other tools you don't need at runtime. For further reduction, `python:3.11-alpine` exists but often causes issues with compiled Python packages (numpy, scikit-learn) that expect glibc.

**2. Layer caching — dependencies before code**

Docker re-executes only the layers that changed and everything after them. Put slow-changing layers first:

```dockerfile
WORKDIR /app

# COPY requirements first — this layer is cached as long as requirements.txt doesn't change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# COPY source code last — changes here don't invalidate the pip layer
COPY . .
```

**3. Multi-stage builds — keep the final image lean**

For applications that need a build step (compiling extensions, bundling assets):

```dockerfile
# Stage 1: builder — installs build tools
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: runtime — no build tools, much smaller
FROM python:3.11-slim
COPY --from=builder /install /usr/local
WORKDIR /app
COPY . .
```

**4. Non-root user**

Running as root inside a container is a security risk — if an attacker escapes the container, they have root on the host. Create a dedicated user:

```dockerfile
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser
```

**5. `.dockerignore`**

Prevents large or sensitive files from being sent to the Docker build context:

```
__pycache__/
*.pyc
.env
.venv/
*.egg-info/
.git/
tests/
*.md
```

A bloated build context slows down every `docker build` even if those files are never `COPY`'d into the image.

**6. `HEALTHCHECK`**

Tells the Docker daemon (and orchestrators like Kubernetes) whether the container is healthy. Without it, a container that started but whose app crashed appears "running":

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
```

**7. Pinned versions**

```dockerfile
# Bad — unpredictable, breaks on new releases
FROM python:3

# Good — reproducible builds
FROM python:3.11-slim
```

Pin `FROM` tags and pin packages in `requirements.txt` (e.g. `fastapi==0.111.0`).

**8. Expose and configure via environment**

```dockerfile
EXPOSE 8000
# All config comes from environment variables — 12-factor
ENV APP_VERSION=0.1.0
```

### 2.9 12-Factor Config for LLM Services

The [12-factor app](https://12factor.net/config) principle: **store config in the environment, never in code**.

For an LLM service the critical env vars are:

| Variable | Purpose |
|---|---|
| `LLM_BASE_URL` | Where to send inference calls (hosted API or local vLLM/TGI) |
| `LLM_MODEL` | Model identifier (`claude-haiku-4-5`, `llama3.2`, etc.) |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | Credentials — **never bake into image** |
| `APP_VERSION` | Passed into health/metrics responses |
| `LOG_LEVEL` | `INFO` in prod, `DEBUG` in dev |
| `PORT` | Defaults to 8000; override per environment |

Your `docker-compose.yml` or Kubernetes `Deployment` injects these at runtime from secrets or a `.env` file. The image itself contains no credentials.

### 2.10 Image Size and Startup Considerations

LLM service images can become large due to ML dependencies (scikit-learn, torch, transformers). Strategies:

| Strategy | Typical saving |
|---|---|
| `slim` base vs full | ~1 GB |
| `--no-cache-dir` in pip | ~200 MB |
| Multi-stage build (no dev tools in final) | ~300 MB |
| `.dockerignore` corpus/test data from context | Varies |
| Pre-download model weights to a volume (not in image) | Huge — don't bake weights into images |

**Startup time:** FastAPI apps with scikit-learn start in 1–3 seconds. An app that loads model weights at startup can take 30–120 seconds — use the `--start-period` on `HEALTHCHECK` to prevent premature health failures.

---

## 3. Worked Example

The lab walks through containerising the Acme HR Assistant. Here is the target `Dockerfile` structure you will produce:

```
labs/devops/day-07/
├── Dockerfile          ← well-formed, all best practices
├── .dockerignore       ← keeps context lean
├── docker-compose.yml  ← single-command local run
├── requirements.txt    ← pinned lab deps
├── README.md
├── starter.py          ← TODOs for you to complete
└── solution.py         ← reference implementation
```

The Python verification script (`solution.py`) does two things without needing Docker installed:

1. **Application verification** — uses FastAPI's `TestClient` to call the app in-process and assert correct responses.
2. **Dockerfile linting** — parses `Dockerfile` and asserts the six best-practice rules.

---

## 4. Self-Check Quiz

Answer these without looking back. Check yourself against the concept reading.

**Q1. What does **continuous batching** allow that static batching does not?**

<details>
<summary>Show answer</summary>

Process new requests without waiting for in-flight ones to finish.

</details>

**Q2. Which of vLLM / TGI / Ollama is best suited for a CPU-only developer laptop?**

<details>
<summary>Show answer</summary>

Ollama.

</details>

**Q3. Name three Dockerfile best practices introduced in this day.**

<details>
<summary>Show answer</summary>

Any three of: slim base image, pinned dependencies, layer caching (deps before code), non-root user, `.dockerignore`, `HEALTHCHECK`.

</details>

**Q4. Why should model weights never be baked into a Docker image?**

<details>
<summary>Show answer</summary>

Weights are large (GBs), change rarely, and should be fetched at runtime (volume mount or object storage) to keep images small and immutable.

</details>

**Q5. Your `requirements.txt` lists `fastapi` without a version pin. What risk does this introduce?**

<details>
<summary>Show answer</summary>

The next `pip install` may pull a breaking version, causing non-reproducible builds.

</details>

**Q6. A container starts successfully but the app inside crashes 5 seconds later. What Docker directive would surface this to an orchestrator?**

<details>
<summary>Show answer</summary>

`HEALTHCHECK`.

</details>

**Q7. Where should an `ANTHROPIC_API_KEY` be stored in a containerised deployment?**

<details>
<summary>Show answer</summary>

Environment variables injected at runtime (from a secret store or `.env` file).

</details>

**Q8. What does the `.dockerignore` file affect — the image contents, the build context, or both?**

<details>
<summary>Show answer</summary>

The build context (what is sent to the Docker daemon) — which indirectly affects image contents if ignored files would otherwise be `COPY`-ed.

</details>

**Q9. Which API endpoint do vLLM, TGI, and Ollama all expose for compatibility?**

<details>
<summary>Show answer</summary>

`/v1/chat/completions`.

</details>

**Q10. At what monthly spend does self-hosting typically start to make economic sense over hosted APIs?**

<details>
<summary>Show answer</summary>

Roughly $10K–$20K/month (varies by model size and traffic pattern).

</details>

**Q11. A developer on a MacBook Pro (Apple Silicon, no NVIDIA GPU) wants to run a local LLM for integration testing. Which engine should they choose, and why can't they use vLLM or TGI in their default configuration?**

<details>
<summary>Show answer</summary>

**Ollama** — it runs on CPU and Apple Silicon MPS/Metal via `llama.cpp` and requires no NVIDIA GPU. vLLM and TGI in their default configurations require CUDA-capable NVIDIA GPUs; running them on CPU-only or Apple Silicon hardware is either unsupported or requires non-trivial workarounds.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1. vLLM's PagedAttention is described as "like OS virtual memory." What exactly is being paged?**

<details>
<summary>Show answer</summary>

During autoregressive generation the model maintains a **KV-cache** — the key/value tensors from the attention layers for every token generated so far. Without paging, you pre-allocate contiguous GPU memory for the maximum possible sequence length for each request in the batch. Most requests are much shorter, so most of that memory is wasted (internal fragmentation), and no two requests can share the same memory block (external fragmentation). PagedAttention divides the KV-cache into fixed-size **pages** (blocks), allocates pages on demand as a sequence grows, and maps logical sequence positions to physical pages via a block table — exactly like an OS maps virtual addresses to physical memory pages. This eliminates both types of fragmentation and allows sequences to share prefix pages (e.g., when many users share the same system prompt).

</details>

**Q2. TGI is written in Rust but serves Python models. How does that work?**

<details>
<summary>Show answer</summary>

TGI has a layered architecture. The HTTP server, scheduler, and batching logic are implemented in Rust for low-latency request handling. When a batch is ready to execute, TGI calls into Python (PyTorch) via a subprocess router that loads the Hugging Face model and runs the forward pass. The Rust layer handles the IO-bound scheduling work; Python handles the compute-bound forward pass on GPU. The result is low scheduling overhead (Rust) combined with the full Hugging Face model ecosystem (Python/PyTorch).

</details>

**Q3. If vLLM, TGI, and Ollama all expose `/v1/chat/completions`, are they fully interchangeable?**

<details>
<summary>Show answer</summary>

In practice they are compatible for most use cases but have divergences. Token-count fields, finish reasons, and some parameter names behave slightly differently. Streaming SSE framing is consistent. Not all models support all parameters (e.g., `tool_choice`, `response_format`) on all backends. For production use, run your integration test suite against each backend before switching. The key benefit is that the **core interface** — model, messages, temperature, max_tokens — works identically, so you can prototype with Ollama locally and deploy against vLLM without rewriting your application.

One important historical caveat: **older TGI versions (pre-1.4) exposed a non-standard `/generate` endpoint** and did not support `/v1/chat/completions` at all — that endpoint was added later. If you are pinning TGI to an older version for stability, verify which API surface is available; code written against the OpenAI-compatible endpoint will not work against the old `/generate` API without changes. This is a concrete reason why **pinning dependency versions matters**: switching TGI versions can silently change the API surface your application depends on.

</details>

**Q4. Why does the `slim` variant sometimes cause failures with packages like numpy?**

<details>
<summary>Show answer</summary>

`python:3.11-slim` strips most system libraries but retains glibc. Packages like numpy, scikit-learn, and Pillow ship as pre-compiled wheels on PyPI that link against glibc — these work fine on `slim`. Problems arise with `python:3.11-alpine`, which uses musl libc instead of glibc. PyPI wheels compiled against glibc are not compatible, so Alpine forces Alpine to compile from source, which requires build tools and often fails due to missing headers. For ML workloads: use `slim`, not `alpine`.

</details>

**Q5. A `HEALTHCHECK` is defined in the Dockerfile but Kubernetes doesn't seem to use it. Why?**

<details>
<summary>Show answer</summary>

Kubernetes has its own `livenessProbe` and `readinessProbe` configuration in the Pod spec. It does **not** read the Docker `HEALTHCHECK` instruction — that is a Docker-native concept used by `docker run` and `docker-compose`. When deploying to Kubernetes you must define `livenessProbe` / `readinessProbe` in your Deployment YAML separately. The `HEALTHCHECK` in the Dockerfile is still useful for `docker-compose`-based local development and for documentation purposes.

Importantly, **Docker Compose *does* honour `HEALTHCHECK`**: when you specify `depends_on: condition: service_healthy` in a `docker-compose.yml`, Compose waits for the container's `HEALTHCHECK` to pass before starting the dependent service. This is directly relevant to this lab's `docker-compose.yml` — the `HEALTHCHECK` defined in the Dockerfile is what makes `depends_on: condition: service_healthy` functional in local development.

</details>

**Q6. What is the difference between `EXPOSE` and publishing a port with `-p` in `docker run`?**

<details>
<summary>Show answer</summary>

`EXPOSE` is documentation — it tells readers (and tools) which port the container's application listens on, but it does **not** open that port on the host. Publishing a port (`-p 8000:8000` in `docker run`, or `ports:` in `docker-compose.yml`) maps a host port to the container port and makes the service reachable from outside the container. You can run a container without `-p` and it still works for container-to-container traffic on the same Docker network.

</details>

---

## 6. Summary and What's Next

**What you covered today:**

- The three-tier serving stack: hardware → model server → application layer.
- vLLM (GPU, high throughput, PagedAttention), TGI (Hugging Face ecosystem, Rust scheduler), and Ollama (CPU/local, developer-friendly).
- Continuous batching and why it matters for GPU utilisation.
- Six Dockerfile best practices: slim base, layer caching, multi-stage builds, non-root user, `.dockerignore`, `HEALTHCHECK`.
- Self-host vs hosted API trade-offs.
- 12-factor config for secrets and environment-specific configuration.

**Day 8 preview:** Kubernetes basics for LLM workloads — Deployments, Services, ConfigMaps, resource requests/limits, and rolling updates for the Acme HR service.

---

## 7. References

*Links and glossary additions are listed in the course report.*

| Topic | Where to look |
|---|---|
| vLLM documentation | https://docs.vllm.ai |
| TGI documentation | https://huggingface.co/docs/text-generation-inference |
| Ollama | https://ollama.com |
| PagedAttention paper | Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention," SOSP 2023 |
| 12-factor app | https://12factor.net |
| Docker best practices | https://docs.docker.com/build/building/best-practices/ |
| Continuous batching blog | https://www.anyscale.com/blog/continuous-batching-llm-inference |
