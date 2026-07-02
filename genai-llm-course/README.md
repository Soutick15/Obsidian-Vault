# 15-Day GenAI / LLM Training Program

A structured, hands-on 15-day program that builds practical, working knowledge of generative AI and LLMs — from fundamentals to building, testing, and operating real LLM systems.

---

## Who Is This For?

This program is designed for **developers, QA engineers, and DevOps engineers** who are comfortable in Python but have limited or no background in machine learning or large language models. By the end you will be able to:

- Architect, build, test, and operate production AI systems (RAG pipelines, agent systems, LLM-powered features).
- Explain how modern LLM systems work and reason about their tradeoffs with clarity and depth.
- Build, evaluate, and operate LLM applications hands-on, from first prototype to production-ready deployment.

---

## Prerequisites

- Python 3.11+
- A terminal / shell you can run Python in.
- **[5-Day Python Foundation](curriculum/python-foundation/README.md)** — an optional pre-course module that teaches exactly the Python used in the labs (venv/pip, `pathlib`, JSON, Pydantic, `httpx`, `pytest`, the `--selftest` pattern). Skip it if you already write Python comfortably. (As an external reference, the [official Python Tutorial](https://docs.python.org/3/tutorial/) is also excellent.)

See [setup/environment-setup.md](setup/environment-setup.md) for full installation instructions.

---

## Program Goals

1. **Practical system-building** — design, build, and deploy real AI features including RAG pipelines, agents, and LLM-powered APIs.
2. **Deep conceptual understanding** — articulate architecture decisions, trade-offs, and failure modes the way experienced practitioners do.
3. **Provider flexibility** — work across Anthropic Claude, OpenAI, and open-source/local models without being locked to one ecosystem.

---

## How This Program Works

**New to Python?** Start with the optional **[5-Day Python Foundation](curriculum/python-foundation/README.md)** (Week 0) — it teaches exactly the Python the labs use. Skip it if you already write Python comfortably.

**Everyone does Days 1–5 (common foundation).** These five days cover the core concepts every AI practitioner needs regardless of role.

**From Day 6 onward, each person follows ONE role track for Days 6–15.**

```
Week 0 (optional):  Python Foundation  (if Python is new to you)
Days 1–5:           Common Foundation  (all roles)
Days 6–15:          Role Track         (Developer | QA | DevOps)
                    ─────────────────────────────────────────
                    5 common days  +  10 track days  =  15 days total
```

---

## Pick Your Track

- **Developer** — You build AI-powered features and services. Your track focuses on RAG, agents, fine-tuning, structured outputs, security, and deployment.
- **QA Engineer** — You own quality and reliability of AI systems. Your track focuses on eval harnesses, LLM-as-judge, AI-assisted test automation, red-teaming, and CI/CD for LLM testing.
- **DevOps Engineer** — You operate and scale AI infrastructure. Your track focuses on model serving, Kubernetes/GPU orchestration, vector DB ops, FinOps, observability, reliability, and IaC.

---

## How to Use Each Day

Each curriculum day follows the same 7-section template:

1. **Learning objectives** — 3–5 concrete things you will know or be able to do.
2. **Concept reading** — explanation written for practitioners
3. **Hands-on lab** — a runnable Python exercise in `labs/common/day-NN/` (Days 1–5) or `labs/<track>/day-NN/` (Days 6–15).
4. **Self-check quiz** — 5–8 questions with answers; test yourself before moving on.
5. **Concept Deep-Dive Q&A** — 5–10 questions that test deeper, applied understanding, with model answers.
6. **Further reading** — curated links if you want to go deeper. (Researcher Docs are for Expert Only e.g: https://arxiv.org/abs/2201.11903)
7. **Key takeaways** — bullet summary to review before the next day.

**Workflow per day:**
```
Read concept section → Run the lab → Take the quiz → Review the Concept Deep-Dive Q&A → Skim key takeaways
```

---

## Week 0 — Python Foundation (Optional)

A self-contained 5-day primer that builds exactly the Python the labs use. **Skip it if you already write Python comfortably.** Full module: [curriculum/python-foundation/](curriculum/python-foundation/README.md).

| Day | Topic | Exercise focus | File |
|-----|-------|----------------|------|
| 1 | Running Python & the basics | Text-stats CLI script | [Day-01](curriculum/python-foundation/Day-01-running-python-and-basics.md) |
| 2 | Data structures & functions | Process employee records | [Day-02](curriculum/python-foundation/Day-02-data-structures-and-functions.md) |
| 3 | Files, JSON & modules | Read the corpus, extract, write JSON | [Day-03](curriculum/python-foundation/Day-03-files-json-and-modules.md) |
| 4 | Classes, type hints & Pydantic | Validate data with a Pydantic model | [Day-04](Day-04-OOPs-typing-and-pydantic.md) |
| 5 | APIs, async & testing | Module + pytest + `--selftest` CLI | [Day-05](curriculum/python-foundation/Day-05-apis-async-and-testing.md) |

---

## Common Foundation — Days 1–5 (All Roles)

| Day | Topic | Lab focus | Curriculum file |
|-----|-------|-----------|-----------------|
| 1 | LLM landscape, tokens & embeddings | Tokenise text; measure embedding similarity | [Day-01](curriculum/common/Day-01-foundations-llms-tokens.md) |
| 2 | Transformer architecture & attention | Visualise attention weights | [Day-02](curriculum/common/Day-02-transformers-attention.md) |
| 3 | Generation, decoding params & model selection | Compare temperature / top-p outputs | [Day-03](curriculum/common/Day-03-generation-decoding-models.md) |
| 4 | Prompt engineering | Few-shot, chain-of-thought, structured output | [Day-04](curriculum/common/Day-04-prompt-engineering.md) |
| 5 | The API in depth — messages, streaming & tools | Streaming completion + tool call round-trip | [Day-05](curriculum/common/Day-05-apis-streaming-tools.md) |

Labs: `labs/common/day-01` … `labs/common/day-05`

---

## Track: Developer — Days 6–15

| Day | Topic | Curriculum file |
|-----|-------|-----------------|
| 6 | Embeddings & vector search | [Day-06](curriculum/developer/Day-06-embeddings-vector-search.md) |
| 7 | RAG basics — build a pipeline | [Day-07](curriculum/developer/Day-07-rag-basics.md) |
| 8 | RAG advanced + evaluation | [Day-08](curriculum/developer/Day-08-rag-advanced-eval.md) |
| 9 | Agents & tool use | [Day-09](curriculum/developer/Day-09-agents-tool-use.md) |
| 10 | Multi-agent orchestration & memory | [Day-10](curriculum/developer/Day-10-multiagent-memory.md) |
| 11 | Fine-tuning — LoRA / QLoRA & quantization | [Day-11](curriculum/developer/Day-11-finetuning-lora-qlora.md) |
| 12 | Structured outputs & robust app patterns | [Day-12](curriculum/developer/Day-12-structured-outputs-app-patterns.md) |
| 13 | App security & guardrails | [Day-13](curriculum/developer/Day-13-security-guardrails.md) |
| 14 | Deployment (FastAPI / streaming) + capstone build | [Day-14](curriculum/developer/Day-14-deployment-fastapi-capstone.md) |
| 15 | Capstone completion & review | [Day-15](curriculum/developer/Day-15-capstone-completion.md) |

Labs: `labs/developer/day-06` … `labs/developer/day-15`

---

## Track: QA Engineer — Days 6–15

| Day | Topic | Curriculum file |
|-----|-------|-----------------|
| 6 | LLM systems under test | [Day-06](curriculum/qa/Day-06-llm-systems-under-test.md) |
| 7 | Testing non-deterministic systems | [Day-07](curriculum/qa/Day-07-testing-nondeterministic-systems.md) |
| 8 | Eval harnesses — promptfoo & deepeval | [Day-08](curriculum/qa/Day-08-eval-harnesses-promptfoo-deepeval.md) |
| 9 | LLM-as-judge & automated scoring | [Day-09](curriculum/qa/Day-09-llm-as-judge-scoring.md) |
| 10 | RAG & agent eval with Ragas | [Day-10](curriculum/qa/Day-10-rag-agent-eval-ragas.md) |
| 11 | AI-assisted test automation I — Playwright / Selenium & test generation | [Day-11](curriculum/qa/Day-11-ai-test-automation-playwright.md) |
| 12 | AI-assisted test automation II — agentic & exploratory testing | [Day-12](curriculum/qa/Day-12-ai-test-automation-agentic.md) |
| 13 | Safety & red-teaming | [Day-13](curriculum/qa/Day-13-safety-red-teaming.md) |
| 14 | CI/CD for LLM testing + regression & drift (GitHub Actions, Langfuse) + capstone build | [Day-14](curriculum/qa/Day-14-cicd-regression-drift-capstone.md) |
| 15 | Capstone completion & review | [Day-15](curriculum/qa/Day-15-capstone-completion.md) |

Labs: `labs/qa/day-06` … `labs/qa/day-15`

---

## Track: DevOps Engineer — Days 6–15

| Day | Topic | Curriculum file |
|-----|-------|-----------------|
| 6 | LLM systems to operate | [Day-06](curriculum/devops/Day-06-llm-systems-to-operate.md) |
| 7 | Serving — vLLM / TGI / Ollama & Docker | [Day-07](curriculum/devops/Day-07-serving-vllm-tgi-ollama-docker.md) |
| 8 | Orchestration & scaling — Kubernetes & GPU | [Day-08](curriculum/devops/Day-08-orchestration-kubernetes-gpu.md) |
| 9 | Vector DB & data-infra ops | [Day-09](curriculum/devops/Day-09-vector-db-data-infra-ops.md) |
| 10 | Cost / FinOps — caching & LiteLLM routing | [Day-10](curriculum/devops/Day-10-cost-finops-caching-litellm.md) |
| 11 | Observability — Langfuse, Prometheus & Grafana | [Day-11](curriculum/devops/Day-11-observability-langfuse-prometheus.md) |
| 12 | Reliability — retries, failover & SLOs | [Day-12](curriculum/devops/Day-12-reliability-retries-failover-slos.md) |
| 13 | Security & governance ops — Vault & audit | [Day-13](curriculum/devops/Day-13-security-governance-vault-audit.md) |
| 14 | CI/CD & IaC — GitHub Actions & Terraform + capstone build | [Day-14](curriculum/devops/Day-14-cicd-iac-github-terraform-capstone.md) |
| 15 | Capstone completion & review | [Day-15](curriculum/devops/Day-15-capstone-completion.md) |

Labs: `labs/devops/day-06` … `labs/devops/day-15`

---

## Capstone Project — Internal Knowledge Assistant

Each track culminates in building a **RAG + agent "internal knowledge assistant"** over a sample HR/recruitment corpus, tailored to the concerns of each role:

- **Developer** — build and deploy the assistant end-to-end with a FastAPI streaming API.
- **QA** — own the eval harness, red-team the assistant, and build a regression CI pipeline.
- **DevOps** — containerise, orchestrate, observe, and cost-optimise the assistant in production.

All tracks share the same domain: a corpus of HR policy documents and job description templates. The assistant answers natural-language questions with cited source passages via an agent reasoning layer.

Capstone starters and rubrics: [`capstone/developer/`](capstone/developer/), [`capstone/qa/`](capstone/qa/), [`capstone/devops/`](capstone/devops/)

---

## Directory Layout

```
AI_Training/
├── README.md                        ← this file
├── .gitignore
├── setup/
│   └── environment-setup.md         ← install guide + verification
├── curriculum/
│   ├── python-foundation/           ← Week 0 (optional) — 5-day Python primer + exercises/
│   ├── common/                      ← Days 1–5 (all roles)
│   ├── developer/                   ← Days 6–15 (Developer track)
│   ├── qa/                          ← Days 6–15 (QA track)
│   └── devops/                      ← Days 6–15 (DevOps track)
├── labs/
│   ├── common/                      ← day-01 … day-05
│   ├── developer/                   ← day-06 … day-14
│   ├── qa/                          ← day-06 … day-14 + _shared/
│   └── devops/                      ← day-06 … day-14 + _shared/
├── capstone/
│   ├── developer/
│   ├── qa/
│   └── devops/
├── data/
│   └── hr-corpus/                   ← shared corpus used by all capstone tracks
├── assessments/
│   └── deep-dive-qa-bank.md         ← consolidated Concept Deep-Dive Q&A bank
└── resources/
    ├── glossary.md                  ← 60+ term definitions
    ├── cheatsheets.md               ← API, prompting, RAG, agent quick-refs
    └── reading-list.md              ← curated papers, courses, docs
```

---

## Resources

- [Environment setup](setup/environment-setup.md)
- [Glossary](resources/glossary.md)
- [Cheatsheets](resources/cheatsheets.md)
- [Reading list](resources/reading-list.md)
- [Assessments & quizzes](assessments/)
- [Concept Deep-Dive Q&A Bank](assessments/deep-dive-qa-bank.md)

---

## Notes on Provider Flexibility

Every lab works with **Anthropic Claude OR OpenAI**. Set whichever key(s) you have in `.env`; the lab's `starter.py` will pick the right client. Where feasible, an open-source / local path (via `sentence-transformers`, `llama.cpp`, or Ollama) is documented so the exercise can be completed without spending any credits.

---

*Program maintained by the InspironLabs AI Practice. Questions: training@inspironlabs.com*
