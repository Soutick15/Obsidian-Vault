# Day 15 — Capstone Completion & Course Review

**Track:** Developer | **Position in course:** 15 of 15 (Final Day)
**Prerequisites:** Days 1–14 completed; capstone project substantially complete

---

## 1. Learning Objectives

By the end of Day 15 you will be able to:

1. Complete and demonstrate the Acme HR Knowledge Assistant against every rubric criterion.
2. Consolidate your understanding of every major topic from Days 1–14 through self-review.
3. Self-assess your architectural decisions — RAG vs. fine-tuning, chunking strategy, guardrails, cost model — with concrete tradeoffs rather than hand-wavy justifications.
4. Demonstrate breadth across the full 14-day curriculum through the Concept Deep-Dive Q&A spanning tokens, transformers, RAG, agents, fine-tuning, security, and LLMOps.
5. Plan your continued learning roadmap beyond this course.

---

## 2. Capstone Completion & Demo

### 2.1 What to Reference

All capstone materials live in `capstone/developer/`:
- `project-brief.md` — full requirements for the Acme HR Knowledge Assistant
- `rubric.md` — the scoring rubric

If those files are not yet on your machine, ask your program lead for the latest versions before proceeding with self-assessment.

### 2.2 Finishing Checklist

Work through each item below. Tick it off only when you can demonstrate it running, not just when it exists in code.

#### Retrieval & Knowledge Base
- [ ] Documents ingested, chunked, and embedded (verify chunk count and embedding dimensionality in your vector store)
- [ ] Semantic search returns sensible top-k results for at least 5 representative HR queries
- [ ] Metadata filtering (department, document type, date range) is functional
- [ ] Hybrid search (BM25 + semantic) or re-ranking is implemented if required by the brief

#### Generation & Grounding
- [ ] LLM call is conditioned only on retrieved context (no hallucinated HR policy details)
- [ ] Citations or source references are surfaced to the user
- [ ] System prompt clearly scopes the assistant to HR topics only
- [ ] Answers that fall outside the knowledge base are gracefully refused, not invented

#### Guardrails & Safety
- [ ] Input guard catches prompt injection and off-topic abuse
- [ ] Output guard validates citations are real and flags low-confidence responses
- [ ] PII handling policy is documented (redaction or passthrough with justification)

#### Agents & Tool Use (if implemented)
- [ ] Tool definitions are correctly typed and validated
- [ ] The agent does not loop indefinitely on ambiguous queries
- [ ] Tool call history is logged for auditability

#### Evaluation
- [ ] RAGAS (or equivalent) scores computed: faithfulness, answer relevance, context recall
- [ ] A baseline "no-RAG" comparison exists to show retrieval benefit
- [ ] Eval dataset of ≥20 question-answer pairs documented

#### Production Readiness
- [ ] Latency measured end-to-end under realistic load (at least synthetic)
- [ ] Token cost per query estimated and documented
- [ ] Secrets (API keys) managed via environment variables, not hardcoded
- [ ] Observability: at least one tracing/logging integration (LangSmith, W&B, or custom)

#### Code Quality
- [ ] README explains how to run the system end-to-end
- [ ] Requirements pinned (`requirements.txt` or `pyproject.toml`)
- [ ] No dead code, commented-out secrets, or placeholder TODOs left in main paths

### 2.3 Self-Assessment Against the Rubric

For each rubric dimension in `capstone/developer/rubric.md`:

1. **Read the criterion** — what does "Meets Expectations" look like?
2. **Find your evidence** — point to a specific file, function, or test result that demonstrates it.
3. **Score yourself honestly** — use the rubric's own language. "It kind of works" is not evidence.
4. **Log gaps** — anything you score below "Meets" needs a fix or a documented justification for why the scope was consciously reduced.

Use this table during self-assessment:

| Rubric Dimension | Your Evidence | Self-Score (1–4) | Gap / Action |
|---|---|---|---|
| Retrieval Quality | | | |
| Agent & Tool Use | | | |
| Structured Output & Validation | | | |
| Guardrails | | | |
| API & Deployment | | | |
| Code Quality | | | |

### 2.4 Recording a Demo Walkthrough

A 5–8 minute screen recording is the most tangible artifact you can produce from this course. Follow this structure:

1. **00:00–00:30 — Context** — one sentence on what the system does and who the user is.
2. **00:30–02:00 — Happy path** — a realistic HR query that returns a cited, grounded answer.
3. **02:00–03:30 — Edge cases** — (a) a question outside the knowledge base, (b) a borderline policy question with low confidence, (c) a short prompt-injection attempt. Show how each is handled.
4. **03:30–05:00 — Architecture walk** — screen-share the key files: ingestion pipeline, retrieval function, system prompt, guardrail hooks.
5. **05:00–06:30 — Eval results** — show your RAGAS (or equivalent) scores and explain what they mean.
6. **06:30–end — What you would do differently** — one honest reflection; reviewers reward self-awareness.

**Tools:** OBS Studio (free), macOS QuickTime screen recording, or Loom. Export at 1080p. Keep the file under 500 MB.

---

## 3. Capstone Review & Reflection

Use this section to deepen your understanding of the system you built. For each question below, write or speak a brief answer from memory, then compare it to the model answer. The goal is not to recite a script — it is to consolidate your own reasoning about the choices you made.

---

**Q1. Why did you choose RAG over fine-tuning for this system?**




RAG is the right default for a knowledge-retrieval use case where the source material changes frequently (HR policies update quarterly), where factual grounding and citation are required, and where the budget doesn't support a full fine-tuning pipeline. Fine-tuning encodes knowledge into weights, making it expensive to update and prone to hallucination when the model's "memory" diverges from current policy. RAG keeps knowledge in a versioned document store: update the PDFs, re-embed, done. Fine-tuning would be appropriate if we needed the model to adopt a very specific response *style* or handle a specialized domain vocabulary that the base model cannot handle — neither applies here.

*What a strong understanding looks like:* Clear decision criteria (update frequency, grounding requirement, cost), not a blanket "RAG is always better." Mentions the failure mode of stale fine-tuned weights. Acknowledges when fine-tuning would be the right choice.



---

**Q2. Walk through your chunking strategy. Why those chunk sizes?**




We use recursive character splitting at 512 tokens with a 64-token overlap. 512 tokens fits comfortably within the embedding model's optimal input range (most sentence-transformer models degrade above 256–512 tokens) while still capturing enough context for a coherent passage. The 64-token overlap prevents losing information at chunk boundaries — if a policy clause spans a split point, the overlap ensures at least one chunk contains it whole. We experimented with 256-token chunks and found recall improved for multi-sentence queries with 512. For long-form documents (employee handbooks), we also apply a semantic splitter as a secondary pass to avoid cutting mid-paragraph.

*What a strong understanding looks like:* Empirical justification (tested alternatives), awareness of embedding model limits, explains the overlap purpose, and mentions document-type variation.



---

**Q3. How do you handle hallucination? What is your guardrail architecture?**




Two layers. First, the system prompt instructs the model to answer *only* from the retrieved context and to say "I don't have information on that in the HR knowledge base" if context is insufficient — this is the cheapest guardrail and works for the majority of out-of-scope queries. Second, we apply a post-generation faithfulness check using RAGAS's faithfulness metric (or an NLI-based classifier) that flags responses where claims cannot be traced to retrieved passages. Flagged responses are either blocked or returned with a low-confidence label. We do not rely solely on the LLM's own epistemic humility because models will confabulate politely when prompted to be helpful.

*What a strong understanding looks like:* Explains why a single guardrail is insufficient. Distinguishes pre-generation (prompt-based) from post-generation (output-based) controls. Shows scepticism about model self-reporting.



---

**Q4. What is your cost model? If this goes to 10,000 employees, what does it cost per month?**




A rough model: average query retrieves 5 chunks × 300 tokens each = 1,500 context tokens. With a 200-token system prompt and a 150-token question, total input ≈ 1,850 tokens. Output ≈ 300 tokens. At GPT-4o pricing (~$2.50/M input, ~$10/M output), that's roughly $0.005 per query. At 10,000 employees × 5 queries/day × 20 working days = 1M queries/month, that's ~$5,000/month in generation costs alone. Embedding costs for query-time are negligible (~$0.02/M tokens with `text-embedding-3-small`). Ingestion re-embedding is a one-time + quarterly cost. If that number is too high, the lever is model choice: switching to a smaller model like Claude Haiku or gpt-5-mini drops generation cost by ~10×.

*What a strong understanding looks like:* Shows the ability to build a back-of-envelope cost model, names the main cost drivers, identifies the lever (model selection), and gives a concrete recommendation.



---

**Q5. Why did you pick your vector store? What are its limitations?**




Chroma was the right choice for this project because it's zero-infrastructure for development (embedded mode), Python-native, and supports metadata filtering out of the box. The limitation is operational: Chroma's distributed server mode is not production-hardened for high-QPS workloads, and you'd want to migrate to pgvector (if you're already on Postgres) or Pinecone/Weaviate for a production deployment at scale. For a first deployment under 500 concurrent users, Chroma with a persistent client is fine. For 10,000 employees at peak morning usage, pgvector co-locates with existing HR database infrastructure and eliminates an extra service to manage.

*What a strong understanding looks like:* Distinguishes dev vs. production suitability, references the surrounding infrastructure context, and gives a concrete migration path rather than just listing alternatives.



---

**Q6. How would you evaluate whether the system is actually improving HR productivity?**




Two levels. Technical: RAGAS scores (faithfulness, answer relevance, context recall) over a curated eval set give an automated signal. We'd track these on every deployment. Business: we'd instrument session analytics — query completion rate (did the user rephrase multiple times?), escalation rate (did they abandon the assistant and call HR?), and resolution time compared to a baseline of email-based HR queries. The gold standard is A/B testing: deploy to a pilot group, measure escalation and resolution time vs. the control group using the old HR portal. This is how you connect technical metrics to business value.

*What a strong understanding looks like:* Connects technical eval (RAGAS) to outcome metrics, mentions instrumentation, names A/B testing as the rigorous approach.



---

**Q7. What security risks did you assess, and how did you mitigate them?**




Three main risks. (1) Prompt injection: a user could embed instructions in their query to override the system prompt. Mitigation: input guard strips or refuses queries containing injection patterns; the system prompt uses delimiters to structurally separate instructions from user input. (2) Data leakage: the knowledge base contains sensitive HR documents; a crafted query could extract verbatim passages. Mitigation: we surface citations but limit raw chunk passthrough; the LLM synthesizes rather than quotes directly. (3) Access control: not all employees should see all HR data (executive compensation, disciplinary records). Mitigation: metadata-based access control at retrieval time — each user's session token is mapped to a permission tier that filters the vector store query. This is architecturally the most important: the LLM can't leak what retrieval never surfaces.

*What a strong understanding looks like:* Uses OWASP LLM Top 10 framing implicitly, identifies risks at different layers (input, output, retrieval), and focuses on the architectural mitigation (access control at retrieval) rather than trying to train the model to refuse.



---

**Q8. What are the biggest failure modes you observed during testing, and how did you address them?**




Three real ones. First, chunk boundary failures: a policy that spans two chunks was retrieved incompletely, and the model gave a partial answer. Fixed with overlap and a semantic splitter. Second, re-ranker over-filtering: an aggressive re-ranker occasionally dropped the most relevant chunk because the query phrasing didn't match the passage vocabulary. Fixed by tuning the top-n before re-ranking from 5 to 10. Third, confident wrong answers on rare policy edge cases: the model synthesized an answer from two unrelated retrieved passages that happened to sound coherent. Fixed by adding a faithfulness post-check and a fallback message when faithfulness score drops below 0.7.

*What a strong understanding looks like:* Specific, evidence-based failure modes rather than generic "the model sometimes hallucinates." Shows iteration and threshold tuning.



---

**Q9. How would you handle a request to add support for multiple languages (French, Spanish)?**




Two options depending on the document language. If the source HR documents are English-only, we'd use a multilingual embedding model (e.g., `paraphrase-multilingual-mpnet-base-v2`) so that a French query can still retrieve English documents by semantic similarity, then instruct the LLM to respond in the user's language. If documents are also multilingual, we embed each document in its source language and tag with a `language` metadata field, then filter at query time. The second option is more precise but requires maintaining parallel document stores. For a first iteration, the multilingual embedding + English corpus approach is the pragmatic choice.

*What a strong understanding looks like:* Distinguishes document language from query language, names a real multilingual embedding model, and gives a practical phased recommendation.



---

**Q10. If you had three more weeks, what would you improve first?**




Prioritized: (1) Access control at retrieval — currently all employees see all documents; this is a compliance risk. (2) Richer evaluation suite — 20 eval pairs is a floor; production needs 200+ with adversarial examples. (3) Streaming responses — current UX is blocking; users perceive the assistant as slow. After those, I'd investigate query routing: a classifier that routes simple factual queries to a lighter model and complex policy interpretation to the full model, cutting cost by ~40%.

*What a strong understanding looks like:* Prioritizes a real risk (access control, compliance) over a cosmetic improvement. Shows cost-awareness with query routing. Doesn't try to say "everything" — makes a clear prioritized list.



---

**Q11. What would you do differently if you were starting this project from scratch?**




I'd invest more time upfront in the eval dataset — it's the compass for every other decision. Without 50–100 labelled Q&A pairs from real subject-matter experts before building, you're optimizing blind. I'd also co-locate the vector store with the existing application database (pgvector) from day one rather than starting with Chroma and migrating. And I'd instrument tracing (LangSmith or similar) from the first prototype, not as an afterthought — the cost of retroactively adding observability is higher than building it in.

*What a strong understanding looks like:* Self-aware retrospective. Mentions evals-first as a workflow discipline, not a feature.



---

**Q12. How confident are you that this system won't give an employee incorrect HR policy information that could cause a legal or compliance issue?**




Not 100% — and I'd be worried about anyone who claims otherwise for any generative AI system. The mitigations we have: (1) grounding via RAG limits the model to citing real documents, (2) faithfulness checking flags unsupported claims, and (3) the UI displays the source document and page so the employee can verify. The recommended deployment posture for HR policy questions is "assistant with human review for high-stakes decisions" — the system should help employees find the right policy, not replace an HR professional for disciplinary or legal interpretation. Any deployment should include a disclaimer and an escalation path.

*What a strong understanding looks like:* Honest about limitations, doesn't oversell. Defines appropriate use boundary (assistant vs. decision-maker). Proactively raises the need for a disclaimer — shows professional maturity.



---

## 4. Concept Deep-Dive Q&A

These questions consolidate the full Developer track (Days 1–14). Work through them independently before reading the model answers.

---

**Q1. A model with a 128k context window can hold your entire knowledge base in a single prompt. Why would you still use RAG?**




Several reasons. (1) **Cost and latency**: stuffing 128k tokens per query is 10–100× more expensive than retrieving 1,500 relevant tokens. At scale, this is prohibitive. (2) **Accuracy degrades mid-context**: research (Lost in the Middle, Liu et al. 2023) shows models perform worse on information buried in the middle of very long contexts. RAG surfaces only the relevant passages. (3) **Staleness**: a context-stuffed approach still needs to refresh the entire window when any document changes. RAG allows incremental updates to the vector store. (4) **Attribution**: RAG produces structured chunk references; raw long-context prompting does not. Long context is a useful fallback and useful for small corpora, but it doesn't replace RAG for production-scale retrieval.



---

**Q2. What is the difference between cosine similarity and dot product similarity for vector search? When would you choose each?**




Cosine similarity normalizes vectors to unit length before computing the dot product, making it sensitive only to the *direction* (angle) between vectors, not their magnitude. Dot product measures both direction and magnitude. For most embedding models trained with cosine as the loss objective (e.g., `sentence-transformers`), cosine similarity is the correct metric. Use raw dot product when: (a) your embedding model was trained with dot product (e.g., OpenAI `text-embedding-3` optimized for dot product with normalized vectors — which is equivalent to cosine), or (b) magnitude carries semantic information (rare). FAISS's `IndexFlatIP` computes inner product; for cosine, normalize vectors first. Euclidean distance is equivalent to cosine on unit-normalized vectors up to a monotone transformation, so all three converge if you normalize — but always check your embedding model's documentation.



---

**Q3. Explain the difference between zero-shot, few-shot, and chain-of-thought prompting. When is each appropriate?**




Zero-shot gives the model only the task instruction with no examples — appropriate for simple, well-defined tasks that the model has strong prior knowledge of (classification, summarization). Few-shot adds 2–8 worked examples in the prompt to steer format and style — appropriate when the output format is non-standard or when the task requires a specific persona or tone. Chain-of-thought (CoT) asks the model to reason step-by-step before producing the final answer, which improves accuracy on multi-step logical, mathematical, or planning tasks. CoT requires a model large enough to actually reason (≥7B parameters; small models produce plausible-looking but incorrect chains). For the HR assistant, few-shot with 2–3 policy-answer examples improves citation formatting; CoT is useful for eligibility calculation queries ("Am I eligible for 12 weeks of leave?").



---

**Q4. What is RAGAS and what do faithfulness, answer relevance, and context recall each measure?**




RAGAS (Retrieval Augmented Generation Assessment) is a reference-free evaluation framework for RAG pipelines. **Faithfulness** measures whether every claim in the generated answer is supported by the retrieved context — a hallucination detector. Score: 0–1, where 1 = every claim traceable to context. **Answer relevance** measures whether the answer actually addresses the user's question — a non-answer or tangential response scores low. **Context recall** measures whether the retrieved context contains all the information needed to answer the question — a low score means retrieval missed something, not that generation failed. High context recall + low faithfulness = retrieval found the right docs but the model ignored them. High faithfulness + low context recall = model is faithful to the (wrong) context. You need both.



---

**Q5. What is LoRA and why does it make fine-tuning practical on a single GPU?**




LoRA (Low-Rank Adaptation) freezes the pre-trained model weights and inserts small trainable rank-decomposition matrices (A and B, where rank r << d) into each attention layer. Instead of updating all 7B parameters (for a 7B model), you update only ~1–50M parameters depending on rank and target layers. This reduces GPU memory from ~14 GB (full fine-tune in fp16 for a 7B model) to ~2–4 GB with QLoRA (LoRA + 4-bit quantization of the frozen weights). The tradeoff: LoRA may not fully capture distributional shifts that full fine-tuning would; and at very low rank (r=4), expressive capacity is limited. For style adaptation and domain vocabulary injection it's highly effective; for teaching entirely new reasoning patterns, full fine-tuning or continued pre-training may be needed.



---

**Q6. A developer proposes replacing the entire RAG pipeline with a single "just ask the model" API call because GPT-5 is very smart. How do you respond?**




It's a reasonable hypothesis to test, but there are structural reasons it won't fully replace RAG. (1) Knowledge cutoff: any base model has a training cutoff; HR policies updated after that date won't be known. (2) Factual grounding: even the best models confabulate confidently on specific organizational policies they were never trained on. (3) Auditability: "the model said so" is not a defensible citation for an employee dispute. (4) Cost: a single smart API call may be fine for 10 queries; at 1M queries/month the cost difference is material. The pragmatic answer is: test it against your eval set — but for any system where policy accuracy and attribution matter, RAG is a necessary architectural component, not an optimization.



---

**Q7. What is the ReAct pattern for agents, and what problem does it solve compared to a simple tool-call loop?**




ReAct (Reason + Act) interleaves explicit reasoning steps (Thought: …) with action steps (Action: call_tool(…)) and observations (Observation: result). The key insight is that making reasoning explicit improves the model's ability to decide *which* tool to call next and *when* to stop. A naive tool-call loop just sequences tools; the model can't reflect on intermediate results. ReAct allows the agent to notice "the search returned no results, so I should try a different query" rather than blindly proceeding. It also makes the chain of thought auditable — you can inspect the Thought steps to understand why the agent made a decision. The tradeoff: more tokens per step (reasoning adds overhead), and poorly calibrated models produce plausible-sounding but incorrect thoughts.



---

**Q8. How do you protect a RAG system against prompt injection, and why is it harder than it looks?**




Prompt injection occurs when user input (or retrieved document content) contains instructions that the model interprets as system commands. Defenses: (1) Structural delimiters — separate system instructions from user input with XML-style tags that the model is trained to treat as boundaries. (2) Input sanitization — detect and reject or escape common injection patterns ("Ignore all previous instructions…"). (3) Indirect injection defense — documents in the knowledge base could themselves contain injected instructions; mitigation is to treat retrieved content as untrusted data and instruct the model explicitly not to follow instructions embedded in retrieved passages. Why it's hard: there is no purely syntactic solution — the model is trained to follow instructions, and the boundary between "instruction" and "content" is semantic. Defense in depth (all three layers) is required, and red-team testing is essential.



---

**Q9. What is token budget management and why does it matter at production scale?**




Token budget management is the practice of explicitly accounting for all token sources in a prompt — system prompt, retrieved chunks, conversation history, few-shot examples, reserved output space — to ensure total tokens stay within the context window and within cost limits. At dev time with 2 users it's invisible. At production scale with 10,000 users: (1) a system prompt that's 2,000 tokens instead of 500 tokens costs $3,000 more per month at 1M queries; (2) a retrieval step that returns 10 chunks instead of 5 doubles context cost; (3) conversation history that grows unbounded eventually hits the context window and causes failures. Practical mitigations: compress history (summarize old turns), truncate low-scoring retrieved chunks, profile system prompt token count and optimize it.



---

**Q10. Describe the LLMOps monitoring you would put in place for the HR assistant in production.**




Three tiers. (1) **Request-level tracing**: every query logs model, token counts, latency, retrieved chunk IDs, and cost. Tool: LangSmith, W&B, or a custom OpenTelemetry span. (2) **Quality metrics**: faithfulness and answer relevance computed on a sampled 5% of production traffic using an LLM-as-judge evaluator. Alerts if faithfulness drops below threshold (signals knowledge base drift or retrieval degradation). (3) **Business metrics**: escalation rate (user clicked "Talk to HR instead"), satisfaction (thumbs up/down), query volume by topic cluster (surfacing emerging employee questions). Dashboards in Grafana or your BI tool. Additionally: track embedding model version and re-embedding events; maintain a changelog of knowledge base updates with timestamps so you can correlate quality drops with document changes.



---

## 5. Common Pitfalls & Best Practices

A recap of the most important mistakes to avoid when building LLM applications, drawn from all 14 days of the course.

| Pitfall | Why it matters | What to do instead |
|---|---|---|
| "The AI will learn over time" | LLMs don't update weights from conversations; this implies a misunderstanding of how the system works | Update the knowledge base (RAG) or retrain; make the distinction explicit in your design docs |
| "It's 95% accurate" without specifying the eval | 95% on what? With what baseline? | Define the eval set, the metric, and the baseline before quoting a number |
| Claiming hallucination is "solved" | No current system fully eliminates hallucination | Say "mitigated via grounding and guardrails" and quantify with faithfulness scores |
| Promising real-time learning / auto-updating | RAG can update the knowledge base; the model itself cannot self-update at inference | Design a clear knowledge base update pipeline with version tracking |
| "Fine-tuning will make it smarter" | Fine-tuning changes style and domain adaptation; it does not add new knowledge reliably | Use RAG for knowledge; use fine-tuning for style, format, or domain tone |
| Recommending the most expensive model by default | Dramatically increases cost at scale | Present a cost-tiered model recommendation and test cheaper models against your eval set first |
| Skipping access control in the design | For any system handling sensitive data, this is a compliance issue, not a backlog item | Enforce access control at retrieval, not generation — the model can't protect what it can already see |
| Building without an eval suite | You have no way to know if changes make things better or worse | Build your eval dataset before (or alongside) your pipeline |
| Skipping observability until "later" | Retroactively adding tracing is far more expensive than building it in | Add request-level tracing from the first prototype |

---

## 6. Continued-Learning Roadmap

You have covered the full stack from tokens to production. Here is where to go deeper, prioritized by practical impact.

### 6.1 Immediate Next Steps (0–4 weeks)

| Topic | Why It Matters | Resource |
|---|---|---|
| **Structured outputs / JSON mode** | Production systems need reliable schema-constrained responses | [Anthropic structured outputs docs](https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/increase-consistency) |
| **Advanced eval: LLM-as-judge** | Automate eval at scale without reference labels | [G-Eval (Liu et al., 2023)](https://arxiv.org/abs/2303.16634); [Anthropic Evals Guide](https://docs.anthropic.com/en/docs/test-and-evaluate/eval-intro) |
| **Streaming & UX patterns** | First-token latency is the dominant UX factor; streaming is non-optional at scale | [OpenAI streaming docs](https://platform.openai.com/docs/api-reference/streaming); [Anthropic streaming](https://docs.anthropic.com/en/api/messages-streaming) |
| **Caching (prompt + semantic)** | Cut cost 30–60% on repeated queries | [GPTCache](https://github.com/zilliztech/GPTCache); [Anthropic prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) |

### 6.2 Medium Term (1–3 months)

| Topic | Why It Matters | Resource |
|---|---|---|
| **Advanced agent patterns** | Plan-and-execute, hierarchical agents, reflection loops | [LangGraph documentation](https://langchain-ai.github.io/langgraph/); [AutoGen](https://microsoft.github.io/autogen/) |
| **Fine-tuning for style alignment** | When base model output format is structurally wrong for your use case | [Hugging Face TRL docs](https://huggingface.co/docs/trl); [PEFT library](https://huggingface.co/docs/peft) |
| **Multimodal RAG** | Documents with charts, diagrams, and tables; vision-language models | [GPT-4V](https://platform.openai.com/docs/guides/vision); [Claude claude-opus-4-5 vision](https://docs.anthropic.com/en/docs/build-with-claude/vision) |
| **Agentic evals (trajectories)** | Evaluating multi-step agent behavior, not just final answers | [Langchain agent evaluation](https://docs.smith.langchain.com/concepts/evaluators); [ToolBench](https://arxiv.org/abs/2307.16789) |
| **Security: red-teaming LLMs** | Formal adversarial testing of your system | [Garak (LLM vulnerability scanner)](https://github.com/NVIDIA/garak); [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/) |

### 6.3 Advanced (3–6 months)

| Topic | Why It Matters | Resource |
|---|---|---|
| **Reasoning models (o1-style, chain-of-thought distillation)** | Long-horizon reasoning tasks; math and code; audit chains | [DeepSeek-R1](https://arxiv.org/abs/2501.12948); [OpenAI o1 system card](https://openai.com/index/openai-o1-system-card/) |
| **Constitutional AI / RLHF fundamentals** | Understanding how alignment is achieved in production models | [Anthropic Constitutional AI paper](https://arxiv.org/abs/2212.08073) |
| **Knowledge graph + RAG hybrid** | Structured relationship traversal + semantic search | [Microsoft GraphRAG](https://github.com/microsoft/graphrag) |
| **LLM benchmarking & capability evaluation** | Choosing and comparing models for new tasks rigorously | [HELM](https://crfm.stanford.edu/helm/); [MMLU](https://arxiv.org/abs/2009.03300); [LMSYS Chatbot Arena](https://chat.lmsys.org/) |
| **On-device / edge inference** | Privacy-preserving deployment, offline capability | [llama.cpp](https://github.com/ggerganov/llama.cpp); [MLX (Apple Silicon)](https://github.com/ml-explore/mlx) |

### 6.4 Communities & Staying Current

- **Papers**: [arXiv cs.CL](https://arxiv.org/list/cs.CL/recent) and [cs.AI](https://arxiv.org/list/cs.AI/recent) — follow weekly
- **Applied practitioner writing**: [Eugene Yan's blog](https://eugeneyan.com), [Hamel Husain's blog](https://hamel.dev), [LangChain blog](https://blog.langchain.dev)
- **Benchmarks & model releases**: [Hugging Face Open LLM Leaderboard](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard)
- **Security**: [OWASP LLM working group](https://owasp.org/www-project-top-10-for-large-language-model-applications/) updates quarterly

---

## 7. Key Takeaways

1. **The capstone is a working system you've built and understand.** A working, evaluated, documented system you can demo and explain is the most meaningful outcome of this course.

2. **Tradeoffs beat enthusiasm.** The most credible technical practitioners don't advocate for a single approach — they map decision criteria to choices and defend them with evidence.

3. **Evaluation is infrastructure, not afterthought.** The teams that ship reliable GenAI systems are the ones who built their eval suites before (or alongside) their pipelines.

4. **Cost awareness is a professional competency.** Every architectural decision has a cost implication. Knowing the $/query model and where the levers are is table stakes.

5. **Guardrails are layered, not solved.** Prompt-based, retrieval-based, and output-based controls complement each other; no single layer is sufficient.

6. **GenAI is fast-moving — your mental models matter more than specific tool knowledge.** The specific libraries and APIs will change. Knowing *why* RAG works, *why* LoRA reduces memory, and *why* faithfulness checking is necessary will transfer to every new tool you encounter.

7. **You have built a complete, production-aware GenAI system.** From tokenization to tracing, from retrieval to red-teaming — you now have the vocabulary, the architecture patterns, and the hands-on experience to contribute meaningfully to real AI projects. Use it.

---

*End of Developer Track — Day 15*

*Reference: `capstone/developer/project-brief.md` | `capstone/developer/rubric.md`*
