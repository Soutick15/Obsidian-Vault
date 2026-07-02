# Day 7 Lab — Containerising the Acme HR Assistant

**Track:** DevOps with AI  
**Day:** 7 of 15  
**Time to complete:** ~75 minutes

---

## What You Will Build

A **containerisation package** for the shared Acme HR Assistant, including:

1. A production-grade `Dockerfile` with all six best practices: slim base, layer caching, non-root user, `.dockerignore`, `HEALTHCHECK`, and pinned versions.
2. A `docker-compose.yml` for single-command local bring-up.
3. A Python verification script that (a) runs the app via `TestClient` (no server required) and (b) lints/validates the `Dockerfile` against the best-practice checklist.

---

## Prerequisites

- Python 3.11+
- No API key required.
- Docker is **not** required to run the verification script — the Dockerfile is validated by parsing, not by building.

---

## Files

| File | Purpose |
|---|---|
| `Dockerfile` | Container definition — fill in TODOs in `starter.py` flow, or inspect the complete version |
| `.dockerignore` | Keeps the build context lean |
| `docker-compose.yml` | Local orchestration |
| `requirements.txt` | Lab Python dependencies |
| `starter.py` | Guided lab — complete the TODO sections |
| `solution.py` | Reference implementation — run to verify everything passes |

---

## Setup

```bash
# From the repo root
pip install -r labs/devops/day-07/requirements.txt
```

---

## Running the Lab

### Option 1 — Guided (starter)

```bash
python labs/devops/day-07/starter.py
```

Complete each `# TODO` block. The script will print a checklist of what passes and what still needs work.

### Option 2 — Reference solution

```bash
python labs/devops/day-07/solution.py
```

All checks should pass with exit code 0.

---

## Building and Running with Docker (optional, requires Docker)

```bash
# From the repo root — build context must be repo root so corpus data is accessible
docker build -f labs/devops/day-07/Dockerfile -t hr-assistant:day07 .

# Run the container
docker run --rm -p 8000:8000 hr-assistant:day07

# In another terminal — smoke test
curl http://localhost:8000/health
curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the PTO policy?"}'
```

### Using docker-compose

```bash
docker-compose -f labs/devops/day-07/docker-compose.yml up
```

---

## Reference: vLLM and Ollama Serve Commands

Once your app is containerised, you can swap the mock LLM for a real self-hosted model by setting environment variables. The app expects an OpenAI-compatible endpoint.

### vLLM (GPU required)

```bash
# Install
pip install vllm

# Serve a model — exposes /v1/chat/completions on port 8001
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --host 0.0.0.0 \
  --port 8001

# Then run your app pointing at vLLM
LLM_BASE_URL=http://localhost:8001/v1 \
LLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct \
docker run --rm -p 8000:8000 \
  -e LLM_BASE_URL \
  -e LLM_MODEL \
  hr-assistant:day07
```

### Ollama (CPU/Apple Silicon)

```bash
# Install (macOS)
brew install ollama

# Pull model and start server
ollama pull llama3.2
ollama serve  # listens on localhost:11434

# Run your app pointing at Ollama
LLM_BASE_URL=http://host.docker.internal:11434/v1 \
LLM_MODEL=llama3.2 \
docker run --rm -p 8000:8000 \
  -e LLM_BASE_URL \
  -e LLM_MODEL \
  hr-assistant:day07
```

### TGI (GPU required)

```bash
docker run --gpus all \
  -v $HOME/.cache/huggingface:/data \
  -p 8002:80 \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id mistralai/Mistral-7B-Instruct-v0.2

# Then point your app at TGI
LLM_BASE_URL=http://localhost:8002/v1 \
LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.2 \
docker run --rm -p 8000:8000 \
  -e LLM_BASE_URL \
  -e LLM_MODEL \
  hr-assistant:day07
```

---

## Checklist of Best Practices (the script validates these)

- [ ] `FROM` uses `python:3.11-slim` (not `python:3.11` or `python:3`)
- [ ] Non-root `USER` directive present
- [ ] `HEALTHCHECK` directive present
- [ ] `requirements.txt` is `COPY`'d before application source (layer caching)
- [ ] `--no-cache-dir` used in `pip install`
- [ ] `.dockerignore` exists and excludes `__pycache__`, `.env`, `.venv`
