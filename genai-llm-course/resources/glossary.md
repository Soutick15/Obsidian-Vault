# Glossary — Core GenAI / LLM Terms

Definitions are intentionally concise (one line each). For deeper coverage, see the curriculum day linked in parentheses.

---

| Term | Definition |
|------|------------|
| **token** | The atomic unit of text a model processes — roughly 0.75 words in English; text is split into tokens before any computation. *(Day 1)* |
| **tokenization** | The process of converting raw text into a sequence of integer token IDs using a vocabulary learned during pre-training. *(Day 1)* |
| **embedding** | A dense, fixed-length floating-point vector that represents the semantic meaning of a token, word, sentence, or document in high-dimensional space. *(Day 1, Day 6)* |
| **attention** | The mechanism that lets each token in a sequence dynamically weight how much it "looks at" every other token when computing its representation. *(Day 2)* |
| **self-attention** | Attention applied within a single sequence so the model can relate every position to every other position in one pass. *(Day 2)* |
| **transformer** | The neural network architecture (encoder, decoder, or both) built around stacked self-attention and feed-forward layers; the foundation of all major LLMs. *(Day 2)* |
| **context window** | The maximum number of tokens a model can process in a single forward pass (input + output combined). *(Day 1)* |
| **temperature** | A sampling parameter (0 – 2) that scales token probability distributions; higher values produce more varied/creative output, lower values more deterministic. *(Day 3)* |
| **top-p (nucleus sampling)** | A decoding strategy that samples from the smallest set of tokens whose cumulative probability exceeds p, dynamically adjusting vocabulary size per step. *(Day 3)* |
| **top-k** | A decoding strategy that restricts sampling to the k highest-probability tokens at each step. *(Day 3)* |
| **RAG (Retrieval-Augmented Generation)** | A pattern that retrieves relevant documents from an external store at inference time and injects them into the prompt so the model can answer with up-to-date, grounded information. *(Day 7)* |
| **chunking** | Splitting a document into smaller overlapping or non-overlapping segments before embedding, so retrieval can surface precise passages rather than whole documents. *(Day 7)* |
| **re-ranking** | A post-retrieval step that applies a more expensive cross-encoder model to reorder candidate passages by relevance before passing them to the LLM. *(Day 8)* |
| **vector database** | A data store optimised for approximate nearest-neighbour search over high-dimensional embedding vectors (examples: Chroma, FAISS, Pinecone, Weaviate). *(Day 6)* |
| **agent** | An LLM-powered system that iteratively decides which tools to call and what to do next in order to complete a multi-step goal autonomously. *(Day 9)* |
| **tool / function calling** | A structured API feature that lets the LLM request execution of a named function with typed arguments, enabling it to take actions and receive external data. *(Day 5, Day 9)* |
| **ReAct** | A prompting/agent pattern interleaving Reasoning steps and Action steps (tool calls), making the chain of thought explicit and auditable. *(Day 9)* |
| **MCP (Model Context Protocol)** | An open protocol for connecting LLMs to external context sources and tools in a standardised, composable way. *(Day 9)* |
| **LoRA (Low-Rank Adaptation)** | A parameter-efficient fine-tuning method that inserts small trainable rank-decomposition matrices into frozen model layers, drastically reducing trainable parameters. *(Day 11)* |
| **QLoRA** | LoRA applied to a quantized (4-bit or 8-bit) base model, enabling fine-tuning of large models on consumer GPUs with minimal quality loss. *(Day 11)* |
| **PEFT (Parameter-Efficient Fine-Tuning)** | A family of techniques (LoRA, prefix tuning, adapters, etc.) that adapt a pre-trained model for a new task by training only a small fraction of its parameters. *(Day 11)* |
| **quantization** | Reducing the numerical precision of model weights (e.g., float32 → int8 or int4) to shrink model size and speed up inference at the cost of small accuracy drops. *(Day 11)* |
| **fine-tuning** | Continued training of a pre-trained model on a task-specific dataset to adapt its behaviour, style, or knowledge for a narrow domain. *(Day 11)* |
| **hallucination** | A model confidently generating factually incorrect, fabricated, or contextually unsupported output. *(Day 12)* |
| **evaluation** | The set of methods (automated metrics, human review, LLM-as-judge) used to measure whether an LLM system produces correct, relevant, and safe outputs. *(Day 12)* |
| **LLM-as-judge** | Using a capable LLM to automatically score or compare the outputs of another LLM or pipeline against rubric criteria. *(Day 12)* |
| **guardrail** | A layer (code rule, classifier, or secondary LLM call) that detects and blocks unsafe, off-topic, or policy-violating inputs and outputs at inference time. *(Day 13)* |
| **prompt injection** | An attack where malicious text in user input or retrieved content attempts to override system-level instructions and hijack model behaviour. *(Day 13)* |
| **jailbreak** | An adversarial technique that attempts to bypass a model's safety training and guardrails, typically via role-play, encoding tricks, or indirect instruction. *(Day 13)* |
| **RLHF (Reinforcement Learning from Human Feedback)** | A training paradigm that fine-tunes a base model using human preference rankings to align output style, helpfulness, and safety. *(Day 11)* |
| **system prompt** | A privileged instruction block supplied to the model before the user conversation that sets persona, rules, output format, and constraints. *(Day 4)* |
| **evaluation harness** | A repeatable automated pipeline that feeds known inputs to a system under test, scores outputs against defined metrics, and produces a structured pass/fail report. *(Day 8)* |
| **golden dataset** | A versioned set of ground-truth input/expected-output pairs used to score a system under test; the authoritative reference for automated evaluation. *(Day 8)* |
| **faithfulness** | The degree to which an LLM's stated claims are supported by (grounded in) the retrieved context documents — distinct from factual correctness in the real world. *(Day 8)* |
| **groundedness** | Synonym for faithfulness in RAG evaluation; measures whether every claim in the answer can be traced back to retrieved source material. *(Day 8)* |
| **context precision** | A RAG eval metric measuring what fraction of retrieved context chunks are actually relevant to the question (precision of the retrieval set). *(Day 8)* |
| **context recall** | A RAG eval metric measuring what fraction of the ground-truth answer is supported by the retrieved context (recall of the retrieval set). *(Day 8)* |
| **regression delta** | The change in an eval metric's pass rate between the current version and a stored baseline; used in CI gates to detect quality regressions before merge. *(Day 8)* |
| **promptfoo** | An open-source, provider-agnostic CLI tool for evaluating LLM prompts via declarative YAML test cases and assertions; CI-ready; joined OpenAI in 2025. *(Day 8)* |
| **deepeval** | A Python framework that brings LLM evaluation into the pytest ecosystem with metric classes (faithfulness, relevancy, etc.) scored by an LLM judge. *(Day 8)* |
| **Ragas** | An open-source Python library providing reference-free RAG evaluation metrics including faithfulness, answer relevancy, context precision, and context recall. *(Day 8, Day 10)* |
| **Langfuse** | An open-source LLM observability and tracing platform for logging traces, evaluating outputs, and monitoring production AI applications. *(Day 11, DevOps Day 11)* |
| **OpenTelemetry** | A vendor-neutral observability framework providing APIs, SDKs, and collectors for generating and exporting traces, metrics, and logs from LLM applications. *(DevOps Day 11)* |
| **Prometheus** | An open-source time-series monitoring system that scrapes metrics endpoints and enables alerting; used to track LLM serving metrics like latency and error rates. *(DevOps Day 11)* |
| **vLLM** | A high-throughput LLM inference engine using PagedAttention for efficient KV-cache management, enabling fast and memory-efficient model serving. *(DevOps Day 7)* |
| **TGI (Text Generation Inference)** | Hugging Face's production-grade LLM serving toolkit with continuous batching, quantization support, and a REST API. *(DevOps Day 7)* |
| **Ollama** | A local LLM runtime that packages models with a Docker-like CLI, enabling offline inference on laptops and developer machines. *(DevOps Day 7)* |
| **Kubernetes** | An open-source container orchestration system used to deploy, scale, and manage containerised LLM workloads across clusters. *(DevOps Day 8)* |
| **HPA (Horizontal Pod Autoscaler)** | A Kubernetes controller that automatically scales the number of pod replicas based on CPU, memory, or custom metrics such as GPU utilisation. *(DevOps Day 8)* |
| **circuit breaker** | A resilience pattern that temporarily stops sending requests to a failing downstream service after a threshold of errors, allowing it to recover. *(DevOps Day 12)* |
| **exponential backoff** | A retry strategy that doubles the wait time between successive retry attempts to reduce load on a struggling service and avoid thundering-herd effects. *(DevOps Day 12)* |
| **SLO/SLI (Service Level Objective / Indicator)** | SLI is a measured metric (e.g., p95 latency); SLO is the target value for that metric; together they define and track acceptable service reliability. *(DevOps Day 12)* |
| **error budget** | The allowable amount of unreliability (1 − SLO) over a time window; when exhausted, changes are frozen and reliability work takes priority. *(DevOps Day 12)* |
| **semantic cache** | A cache layer that stores LLM responses keyed by embedding similarity rather than exact string match, returning cached answers for semantically equivalent queries. *(DevOps Day 10)* |
| **LiteLLM** | A Python library providing a unified OpenAI-compatible interface for 100+ LLM providers, plus load balancing, cost tracking, and fallback routing. *(DevOps Day 10)* |
| **Vault (HashiCorp)** | A secrets management tool that stores, rotates, and audits access to API keys and credentials; used to secure LLM API keys in production. *(DevOps Day 13)* |
| **IaC (Infrastructure as Code)** | The practice of managing and provisioning infrastructure through machine-readable config files (e.g., Terraform, Pulumi) rather than manual processes. *(DevOps Day 14)* |
| **Terraform** | An open-source IaC tool that declaratively provisions and manages cloud infrastructure using HCL config files and a plan/apply workflow. *(DevOps Day 14)* |
| **canary deploy** | A release strategy that routes a small percentage of traffic to a new model or service version before a full rollout, limiting blast radius of regressions. *(DevOps Day 14)* |
| **blue/green deploy** | A release strategy maintaining two identical production environments (blue = live, green = new); traffic switches atomically, enabling instant rollback. *(DevOps Day 14)* |
| **drift** | In ML/LLM contexts: statistical shift between training/baseline data distribution and live production inputs or model outputs over time. *(QA Day 14)* |
| **idempotent ingestion** | A pipeline property where re-running produces the same index state as a single run; implemented via deterministic chunk IDs and `upsert`. *(Day 9)* |
| **HNSW (Hierarchical Navigable Small World)** | The dominant approximate-nearest-neighbour algorithm in vector databases; key params are `M` (graph connectivity), `ef_construction` (build recall), and `ef_search` (query recall). *(Day 9)* |
| **incremental re-index** | Re-embedding only documents whose content hash has changed since the last ingestion run, reducing pipeline cost from O(corpus) to O(changed_docs). *(Day 9)* |
| **content hash** | An MD5 or SHA-256 digest of a document's text stored as metadata alongside each chunk; used to detect document changes between ingestion runs. *(Day 9)* |
| **blue/green collection migration** | A vector store migration pattern that builds the new index in parallel with the live collection, switches traffic atomically, and keeps the old collection as a rollback target — enabling zero-downtime embedding model upgrades. *(Day 9)* |
