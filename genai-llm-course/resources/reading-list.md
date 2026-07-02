# Reading List — Curated Resources by Week

Links are grouped by the week they become most relevant. All resources are freely accessible unless noted.

---

## Week 1 — Foundations

### Official Documentation
- [Anthropic Documentation](https://docs.anthropic.com) — Claude API reference, model overviews, prompt engineering guides.
- [OpenAI Documentation](https://platform.openai.com/docs) — Chat completions, embeddings, function calling, fine-tuning API.
- [Hugging Face LLM Course](https://huggingface.co/learn/nlp-course/en/chapter1/1) — Free course covering transformers, tokenizers, and fine-tuning from the ground up.

### Reference Repositories
- [KalyanKS-NLP/LLM-Interview-Questions-and-Answers-Hub](https://github.com/KalyanKS-NLP/LLM-Interview-Questions-and-Answers-Hub) — A large bank of LLM technical questions with answers — useful extra practice; review alongside each day's Concept Deep-Dive Q&A.
- [mlabonne/llm-course](https://github.com/mlabonne/llm-course) — Structured LLM course with notebooks covering foundations through fine-tuning.
- [huggingface/course](https://github.com/huggingface/course) — Source notebooks for the Hugging Face NLP course.

### Key Papers
- **Attention Is All You Need** (Vaswani et al., 2017) — The original transformer paper. Read the abstract and architecture section (§3). [arXiv:1706.03762](https://arxiv.org/abs/1706.03762)
- **Language Models are Few-Shot Learners** (Brown et al., 2020) — GPT-3 paper; motivates in-context learning and prompt engineering. [arXiv:2005.14165](https://arxiv.org/abs/2005.14165)

### Blog Posts & Guides
- [The Illustrated Transformer (Jay Alammar)](https://jalammar.github.io/illustrated-transformer/) — Visual walkthrough of the transformer architecture; pairs perfectly with Day 2.
- [Andrej Karpathy — "Let's build GPT from scratch"](https://www.youtube.com/watch?v=kCc8FmEb1nY) — 2-hour YouTube lecture building a miniature GPT in PyTorch.
- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) — Official prompting best practices (pairs with Day 4).
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering) — Comparable guide from OpenAI.

---

## Week 2 — Building

### RAG
- **Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks** (Lewis et al., 2020) — The original RAG paper. [arXiv:2005.11401](https://arxiv.org/abs/2005.11401)
- [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/) — Step-by-step guide using LangChain components.
- [LlamaIndex Documentation](https://docs.llamaindex.ai) — Alternative RAG framework with first-class retrieval abstractions.
### Embeddings & Vector Search
- [FAISS Documentation](https://faiss.ai) — Facebook AI Similarity Search; used in Day 6 lab.
- [Chroma Documentation](https://docs.trychroma.com) — Lightweight persistent vector store; used in Day 6 and Day 7 labs.
- [Sentence Transformers Documentation](https://www.sbert.net) — Free local embedding models used throughout the program.

### Agents
- **ReAct: Synergizing Reasoning and Acting in Language Models** (Yao et al., 2022) — Foundational agent pattern paper. [arXiv:2210.03629](https://arxiv.org/abs/2210.03629)
- [Anthropic Tool Use Guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) — Official function-calling reference for Claude.
- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling) — Equivalent for OpenAI.
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/) — Graph-based multi-agent orchestration (Day 10).

---

## Week 3 — Production + Capstone

### Fine-Tuning
- **LoRA: Low-Rank Adaptation of Large Language Models** (Hu et al., 2021) — The core LoRA paper. [arXiv:2106.09685](https://arxiv.org/abs/2106.09685)
- **QLoRA: Efficient Finetuning of Quantized LLMs** (Dettmers et al., 2023) — Extends LoRA to 4-bit quantized models. [arXiv:2305.14314](https://arxiv.org/abs/2305.14314)
- [Hugging Face PEFT Library](https://huggingface.co/docs/peft/en/index) — Official library implementing LoRA, prefix tuning, and more.
- [Unsloth](https://github.com/unslothai/unsloth) — Fast, memory-efficient QLoRA training; used in Day 11 lab's local path.

### Evaluation
- **RAGAS: Automated Evaluation of Retrieval Augmented Generation** (Es et al., 2023) — [arXiv:2309.15217](https://arxiv.org/abs/2309.15217)
- [Anthropic Evals Guide](https://docs.anthropic.com/en/docs/test-and-evaluate/eval-intro) — Evaluation best practices from Anthropic.
- [OpenAI Evals Framework](https://github.com/openai/evals) — Benchmark suite and evaluation tooling.
- [promptfoo Documentation](https://promptfoo.dev/docs/intro) — Declarative YAML eval suite with CI integration; supports all major providers *(Day 8)*.
- [deepeval Documentation](https://docs.confident-ai.com/) — pytest-style LLM evaluation with faithfulness, relevancy, and other metric classes *(Day 8)*.
- [RAGAS Documentation](https://docs.ragas.io/) — Reference-free RAG evaluation metrics: faithfulness, answer relevancy, context precision *(Day 8)*.
- [LangSmith Evaluation Guide](https://docs.smith.langchain.com/evaluation) — Production eval, dataset management, and LLM-as-judge tracing *(Day 8, Day 14)*.
- [Databricks LLM Auto-Eval Best Practices for RAG](https://www.databricks.com/blog/LLM-auto-eval-best-practices-RAG) — Practical comparison of automated eval approaches for RAG pipelines *(Day 8)*.
- [HELM Benchmark (Stanford CRFM)](https://crfm.stanford.edu/helm/latest/) — Holistic LLM evaluation methodology covering accuracy, calibration, robustness, and fairness *(Day 8)*.

### Vector DB & Data Infrastructure Ops

- [Chroma Documentation](https://docs.trychroma.com) — Persistent client, `upsert`, custom embedding functions, metadata filtering *(Day 9)*.
- [Qdrant Documentation](https://qdrant.tech/documentation) — HNSW parameter reference, snapshot API, capacity planning *(Day 9)*.
- [pgvector README](https://github.com/pgvector/pgvector) — IVFFlat vs. HNSW options in PostgreSQL *(Day 9)*.
- **"Efficient and Robust Approximate Nearest Neighbor Search Using HNSW Graphs"** (Malkov & Yashunin, 2018) — Algorithm paper covering `M`, `ef_construction`, and `ef_search` tradeoffs. [arXiv:1603.09320](https://arxiv.org/abs/1603.09320) *(Day 9)*

### Production, Security & LLMOps
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — Security risks including prompt injection (Day 13).
- [Guardrails AI](https://www.guardrailsai.com/docs) — Open-source guardrail framework.
- [LangSmith Documentation](https://docs.smith.langchain.com) — LLM observability and tracing (Day 14).
- [Weights & Biases Prompts](https://docs.wandb.ai/guides/prompts) — Alternative LLMOps observability tool.

---

## Ongoing / Reference

- [Papers With Code — LLM section](https://paperswithcode.com/methods/category/language-models) — Track state-of-the-art results.
- [The Gradient Newsletter](https://thegradient.pub) — Accessible AI research commentary.
- [Lilian Weng's Blog](https://lilianweng.github.io) — Deep technical posts on LLMs, agents, and alignment.
- [Simon Willison's Weblog](https://simonwillison.net) — Practical LLM engineering notes and experiments.
