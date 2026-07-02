# Capstone Starter — Acme HR Knowledge Assistant

This skeleton is **importable and launchable in mock mode out of the box**.

```bash
# 1. Install deps
pip install -r capstone/developer/starter/requirements.txt

# 2. Ingest the corpus (first time only)
python capstone/developer/starter/ingest.py

# 3. Run mock self-test (no API key needed)
python capstone/developer/starter/app.py --selftest

# 4. Start the server
uvicorn capstone.developer.starter.app:app --port 8000
```

## Module Map

| File            | Responsibility                     | Status                        |
| --------------- | ---------------------------------- | ----------------------------- |
| `ingest.py`     | Chunk + embed corpus into ChromaDB | Skeleton — complete the TODOs |
| `retrieve.py`   | Semantic search over the index     | Skeleton — complete the TODOs |
| `agent.py`      | ReAct agent loop + tool dispatch   | Skeleton — complete the TODOs |
| `guardrails.py` | Input + output safety checks       | Skeleton — complete the TODOs |
| `app.py`        | FastAPI routes + streaming SSE     | Runnable in mock mode now     |

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `mock` | `mock` / `anthropic` / `openai` |
| `ANTHROPIC_API_KEY` | *(none)* | Required only for `anthropic` provider |
| `OPENAI_API_KEY` | *(none)* | Required only for `openai` provider |
| `APP_API_KEY` | `changeme` | Bearer token for `/chat` |
| `CORPUS_DIR` | `data/hr-corpus` | Path to document corpus |
| `CHROMA_DIR` | `.chroma_capstone` | ChromaDB persistence directory |

## Module Imports

The modules use relative imports and must be run from `capstone/developer/starter/` (e.g. `python app.py`) or via `app.py --selftest` which patches `sys.path` automatically; running individual modules from the repo root will raise `ImportError`.

## Swapping the Corpus

Set `CORPUS_DIR=/path/to/your/docs` and re-run `python ingest.py`. The pipeline is corpus-agnostic.
