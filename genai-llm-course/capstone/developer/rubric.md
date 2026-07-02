# Developer Capstone Rubric — Acme HR Knowledge Assistant

Total: **100 points**

---

## 1. Retrieval Quality (20 pts)

| Criterion | Points |
|---|---|
| Corpus correctly chunked and embedded into vector store | 5 |
| `retrieve()` returns semantically relevant chunks for HR queries | 8 |
| Retrieval eval (`eval.py` or notebook) reports MRR or Hit@k on ≥ 5 queries | 7 |

**Full marks**: eval shows Hit@3 ≥ 0.6 on the provided test queries, or a justified explanation of why the score differs.

---

## 2. Agent & Tool Use (20 pts)

| Criterion | Points |
|---|---|
| Agent loop correctly calls `search_hr_docs`, `calculator`, and `get_today` | 8 |
| Multi-step reasoning demonstrated (e.g. retrieve PTO days → calculate hours) | 7 |
| Mock path runs with zero API key; real-LLM path works when key is set | 5 |

**Full marks**: a two-tool query (retrieve + calculate) produces the correct answer in both mock and real-LLM modes.

---

## 3. Structured Output & Validation (15 pts)

| Criterion | Points |
|---|---|
| `AgentResponse` Pydantic model with `answer`, `sources`, `tool_calls_made` fields | 6 |
| Response validated before being returned by the API | 5 |
| Validation errors produce a meaningful HTTP 422 or logged warning | 4 |

---

## 4. Guardrails (15 pts)

| Criterion | Points |
|---|---|
| Input guardrail blocks off-topic or clearly harmful questions | 7 |
| Output guardrail flags or redacts PII-like patterns | 5 |
| Guardrails are unit-testable independently of the API | 3 |

**Full marks**: at least one test that shows the guardrail blocking a specific bad input.

---

## 5. API & Deployment (20 pts)

| Criterion | Points |
|---|---|
| `GET /health` returns `{"status": "ok"}` with no auth | 4 |
| `POST /chat` streams SSE correctly (parseable `data:` lines, `[DONE]` sentinel) | 6 |
| Bearer-token auth enforced; missing/wrong key returns 401/403 | 4 |
| All secrets from environment variables; no hardcoded keys | 4 |
| Dockerfile present and syntactically valid (bonus: actually builds) | 2 |

---

## 6. Code Quality (10 pts)

| Criterion | Points |
|---|---|
| Modules are importable and launchable in mock mode without errors | 4 |
| Clear separation of concerns (ingest / retrieve / agent / guardrails / API) | 3 |
| At least one automated test (pytest or `--selftest`) passes | 3 |

---

## Scoring Bands

| Score | Band |
|---|---|
| 90-100 | Distinction — ready to ship as an internal tool |
| 75-89 | Pass with Merit — strong foundation, minor gaps |
| 60-74 | Pass — core features work, needs polish |
| < 60 | Needs revision — revisit the relevant day labs |
