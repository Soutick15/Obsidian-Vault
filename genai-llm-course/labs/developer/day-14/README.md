# Day 14 Lab — Wrapping the HR Assistant in a FastAPI Service

## Goal

Build a FastAPI service that exposes the HR Knowledge Assistant (RAG + agent from Days 7-9) via:

- `POST /chat` — streaming SSE endpoint (yields tokens as they arrive)
- `GET /health` — liveness check

The service includes Pydantic models, bearer-token auth, an in-memory rate limiter, and environment-variable config. It runs **with no API key** using the mock LLM path.

## Prerequisites

```bash
pip install -r labs/developer/day-14/requirements.txt
```

## Run the Self-Test (no server, no API key)

```bash
python labs/developer/day-14/solution.py --selftest
```

Expected output:
```
[selftest] GET /health -> 200 {"status": "ok", ...}
[selftest] POST /chat  -> 200 streaming SSE received N chunks
[selftest] PASSED
```

## Start the Server

```bash
cd labs/developer/day-14
uvicorn solution:app --reload --port 8000
```

Or equivalently from the repo root (using `--app-dir`):
```bash
APP_API_KEY=secret123 uvicorn --app-dir labs/developer/day-14 solution:app --port 8000
```

> **Note:** The directory name `day-14` contains a hyphen, so a dotted Python module path like `labs.developer.day_14.solution` will not resolve correctly. Always use the `cd` or `--app-dir` form shown above.

## Call the API

### Health check (curl)
```bash
curl http://localhost:8000/health
```

### Streaming chat (curl)
```bash
curl -N -H "Authorization: Bearer changeme" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the PTO policy?"}' \
     http://localhost:8000/chat
```

### Streaming chat (httpie)
```bash
http --stream POST http://localhost:8000/chat \
     Authorization:"Bearer changeme" \
     question="What is the PTO policy?"
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_API_KEY` | `changeme` | Bearer token required on `/chat` |
| `LLM_PROVIDER` | `mock` | `mock` / `anthropic` / `openai` |
| `ANTHROPIC_API_KEY` | *(none)* | Required only when `LLM_PROVIDER=anthropic` |
| `OPENAI_API_KEY` | *(none)* | Required only when `LLM_PROVIDER=openai` |
| `CORPUS_DIR` | `data/hr-corpus` | Path to HR corpus text files |
| `APP_VERSION` | `dev` | Reported by `/health` |
| `RATE_LIMIT` | `10` | Max requests per client per 60 s |

## Run Standalone Tests

```bash
pytest labs/developer/day-14/test_client.py -v
```

Or run directly:
```bash
python labs/developer/day-14/test_client.py
```
