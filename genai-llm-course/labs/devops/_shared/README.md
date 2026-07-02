# Acme HR Knowledge Assistant — Shared Service

This is the **system under operation (SUT)** for the AI Training DevOps track.
All labs (serving, scaling, observability, security, CI/CD) operate **this** service.
It is intentionally simple so you can focus on *running* it, not building it.

## What it does

A RAG-style HR question-answering API backed by the `data/hr-corpus/` markdown documents (12 files covering benefits, leave, compensation, onboarding, etc.). It uses lexical TF-IDF retrieval and a deterministic mock LLM — **no API key required, no GPU needed**.

---

## Run locally (no Docker)

```bash
# From the repo root
pip install -r labs/devops/_shared/requirements.txt

# Start the server
uvicorn labs.devops._shared.app:app --reload --port 8000

# Or run directly (non-reload mode)
python -m uvicorn labs.devops._shared.app:app --host 0.0.0.0 --port 8000
```

### Quick self-test (no running server needed)

```bash
python labs/devops/_shared/app.py --selftest
```

Hits `/health`, `/chat`, and `/metrics` in-process and exits 0 on success.

---

## Build & run with Docker

Build context must be the **repo root** so the corpus is available:

```bash
# From the repo root
docker build -f labs/devops/_shared/Dockerfile -t acme-hr-assistant:latest .

docker run --rm -p 8000:8000 acme-hr-assistant:latest
```

Override version at build time:

```bash
docker run --rm -p 8000:8000 -e APP_VERSION=1.2.3 acme-hr-assistant:latest
```

---

## Endpoints

| Method | Path       | Description                                      |
|--------|------------|--------------------------------------------------|
| `GET`  | `/health`  | Liveness check; returns status, version, corpus stats, uptime |
| `POST` | `/chat`    | Answer an HR question; returns answer + sources + context chunks |
| `GET`  | `/metrics` | In-process counters (requests, avg latency). Replace with Prometheus in observability labs. |
| `GET`  | `/docs`    | Auto-generated OpenAPI / Swagger UI              |

### Example: /chat

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How many days of annual leave do I get?", "k": 3}' | jq .
```

Response shape:
```json
{
  "answer": "...",
  "sources": ["leave-and-pto-policy.md"],
  "contexts": ["...raw retrieved chunks..."],
  "mock": true,
  "latency_ms": 12.4
}
```

---

## Environment variables

| Variable          | Default   | Description                                      |
|-------------------|-----------|--------------------------------------------------|
| `APP_VERSION`     | `0.1.0`   | Reported in `/health`                            |
| `LOG_LEVEL`       | `INFO`    | Python log level (`DEBUG`, `INFO`, `WARNING`, …) |
| `HOST`            | `0.0.0.0` | Bind address for uvicorn                         |
| `PORT`            | `8000`    | Listen port                                      |
| `DEFAULT_K`       | `3`       | Default number of retrieval chunks per query     |
| `ANTHROPIC_API_KEY` | *(unset)* | If set, uses Claude for generation instead of mock |
| `ANTHROPIC_MODEL` | `claude-3-haiku-20240307` | Which Claude model (if key present) |
| `OPENAI_API_KEY`  | *(unset)* | If set, uses OpenAI for generation instead of mock |
| `OPENAI_MODEL`    | `gpt-3.5-turbo` | Which OpenAI model (if key present)         |

The service **always starts and responds correctly with no keys set**.

---

## Lab usage notes

- **Serving lab** — containerise and reverse-proxy behind nginx/caddy.
- **Scaling lab** — run multiple replicas; observe `/metrics` diverge per instance.
- **Observability lab** — replace `/metrics` with a Prometheus exporter; add Grafana.
- **Security lab** — add auth middleware, rate limiting, secrets scanning in the image.
- **CI/CD lab** — add the `--selftest` invocation as a smoke-test step in your pipeline.

The corpus lives at `data/hr-corpus/` (repo root). Do not modify it during labs; it is shared across all tracks.
