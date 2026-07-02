# Day 3 — Generation, Decoding Parameters & Model Selection

## 1. Objectives

By the end of Day 3 you will be able to:

- Explain the three-phase lifecycle that produces a deployable LLM: pretraining → supervised fine-tuning (SFT) → preference alignment (RLHF / DPO).
- Describe exactly what happens when an LLM generates text: probability distribution over the vocabulary, sampling vs. argmax.
- Tune and reason about every major decoding parameter: temperature, top-k, top-p (nucleus), max tokens, stop sequences, frequency penalty, presence penalty.
- Compare the major model families (Claude, GPT, Llama/Mistral/Qwen) on five practical dimensions: capability, cost, latency, context window, and hosting model.
- Estimate token-based API cost for a given workload and identify levers to reduce it.

---

## 2. Concept Reading

### 2.1 How LLMs Are Built — The Three-Phase Pipeline

Understanding where a model comes from helps you choose the right one and set realistic expectations.

#### Phase 1: Pretraining

The model is trained on a massive corpus (trillions of tokens from the web, books, code) with a simple objective: **predict the next token**. This phase is computationally expensive (weeks on thousands of GPUs) and produces a *base model* — a powerful pattern-matcher that can continue any text, but is not yet useful as an assistant.

Key intuitions:
- The model learns language structure, world knowledge, and reasoning patterns purely from statistical co-occurrence.
- It has no notion of "helpful" or "harmful" at this stage — it will complete a sentence about bomb-making just as readily as a recipe.
- Context window size and tokenisation scheme are fixed here.

#### Phase 2: Supervised Fine-Tuning (SFT)

Human annotators write (prompt, ideal-response) pairs. The base model is fine-tuned on these pairs to teach it the **instruction-following format** — how to behave as an assistant that answers questions rather than just continuing text.

After SFT, the model is usable but still imperfectly calibrated: it may be verbose, sycophantic, or occasionally harmful.

#### Phase 3: Preference Alignment — RLHF and DPO

**Reinforcement Learning from Human Feedback (RLHF):** Human raters compare pairs of model outputs and label which is better. A *reward model* is trained on these preferences. The LLM is then fine-tuned with reinforcement learning to maximise the reward model's score.

**Direct Preference Optimization (DPO):** A more recent and simpler alternative — skips the separate reward model and directly optimises the policy using preference pairs. Most current frontier models use some variant of DPO or hybrid approaches.

**Intuition:** RLHF/DPO teaches the model to be helpful, harmless, and honest. It is also where much of the model's "personality" is shaped.

> **Key point:** When asked "how is ChatGPT/Claude different from a raw GPT model?" — the answer is SFT + RLHF on top of pretraining.

---

### 2.2 How Generation Works

At inference time, the model processes the input tokens and produces a **logit vector** of size `|vocabulary|` (typically 32 000–128 000 tokens). Applying softmax converts logits to a **probability distribution** over the entire vocabulary.

The model then *samples* (or selects) the next token from this distribution, appends it to the context, and repeats — this is **autoregressive generation**.

```
Input tokens → Transformer → Logit vector (vocab size)
                                    ↓  softmax
                          Probability distribution
                                    ↓  sampling strategy
                             Next token selected
                                    ↓  append & repeat
```

The choice of *how* to pick the next token from the distribution is called the **decoding strategy**.

---

### 2.3 Decoding Strategies & Parameters

#### Greedy Decoding
Always pick the highest-probability token. Fast, deterministic, but often repetitive and suboptimal — it can paint itself into a corner by making a locally good choice that leads to a globally bad sequence.

#### Beam Search
Maintain `k` candidate sequences ("beams") simultaneously, expanding each at every step, and keep only the top-k by cumulative log-probability. Used in translation and summarisation where precision matters. Less used in chat — it's expensive and tends to produce "safe", generic text.

#### Temperature Sampling

Before applying softmax, divide all logits by a temperature `T`:

```
P(token_i) = softmax(logits / T)
```

| Temperature | Effect |
|-------------|--------|
| `T < 1.0` (e.g. 0.2) | Sharpens distribution — high-prob tokens become much more likely. More deterministic, focused. |
| `T = 1.0` | Raw model distribution unchanged. |
| `T > 1.0` (e.g. 1.5) | Flattens distribution — low-prob tokens become relatively more likely. More random, creative. |

Mathematically: divide the logits by T before softmax — `scaled = logits / T`. T<1 sharpens the distribution, T>1 flattens it, T→0 approaches greedy.

**When to use low temperature:** factual Q&A, code generation, structured output (JSON extraction).  
**When to use high temperature:** brainstorming, creative writing, diversity in generation.

#### Top-k Sampling

After temperature scaling, zero out all tokens except the top-k by probability, then re-normalise and sample. This prevents the model from choosing very low-probability "garbage" tokens.

Typical values: `k = 50` or `k = 40`. Setting `k = 1` is equivalent to greedy decoding.

#### Top-p (Nucleus) Sampling

Instead of a fixed k, keep the smallest set of tokens whose cumulative probability exceeds `p`, then re-normalise and sample. This is adaptive — when the model is confident (one token dominates), the nucleus is small; when uncertain, the nucleus is large.

Common value: `p = 0.95` or `p = 0.9`.

**Top-p vs top-k:** Top-p is generally preferred for chat and creative tasks because it adapts to the model's confidence. Top-k is simpler and useful when you know the vocabulary is well-behaved.

**Combining:** Many APIs apply temperature → top-k → top-p in sequence. Check your provider's docs.

#### Other Important Parameters

| Parameter | What it does | Typical range |
|-----------|-------------|---------------|
| `max_tokens` | Hard cap on output length. Prevents runaway responses; also controls cost. | 256–4096 |
| `stop` / `stop_sequences` | List of strings at which generation halts immediately (token is NOT included). Useful for structured output: `["```", "\n\n"]`. | List of strings |
| `frequency_penalty` | Reduces probability of tokens in proportion to how many times they have already appeared. Reduces repetition. | 0.0–2.0 (OpenAI) |
| `presence_penalty` | Flat penalty for any token that has already appeared at least once. Encourages topic diversity. | 0.0–2.0 (OpenAI) |

> **Note:** Claude's API (Anthropic) does not expose top-k or penalties directly. It uses `temperature` and `top_p`; Anthropic recommends using only one at a time. Other providers vary — always check the API reference.

---

### 2.4 Model Families & How to Choose

The LLM landscape in mid-2020s has consolidated into a few major families. You need to know how to recommend or choose a model — not just name-drop.

#### Major Families

**Claude (Anthropic)**
- Trained with Constitutional AI and RLHF for safety and instruction-following.
- Tiers: small/fast (Haiku class) → mid-range (Sonnet class) → large/capable (Opus class).
- Strong at long-context reasoning, code, and structured output.
- API-only; no self-hosted option for frontier models.

**GPT / o-series (OpenAI)**
- The originals that popularised the space. Very broad ecosystem (Azure, fine-tuning, assistants API).
- o-series models (o1, o3) use "thinking" / chain-of-thought at inference time — much slower but better at hard reasoning.
- Available via API and Azure OpenAI.

**Open-source / Open-weight**
- **Llama (Meta):** Most widely adopted open-weight family. Available in sizes from 1B to 405B+. Can run locally via Ollama, llama.cpp, or vLLM.
- **Mistral / Mixtral (Mistral AI):** Efficient mixture-of-experts models. Strong performance-per-parameter.
- **Qwen (Alibaba):** Strong multilingual performance, especially CJK languages. Growing ecosystem.
- **Gemma (Google):** Lightweight, open models designed for on-device/edge use.

#### Decision Framework: 5 Dimensions

| Dimension | Hosted (Claude/GPT) | Open-weight (Llama/Mistral) |
|-----------|--------------------|-----------------------------|
| **Capability** | Frontier-quality; regularly updated | Varies; large models (70B+) competitive; small models lag |
| **Cost** | Per-token pricing; predictable | Infrastructure cost; free if you have the hardware |
| **Latency** | Network + queue; ~1–5s TTFT | Local = hardware-dependent; can be <1s on GPU |
| **Context window** | 128K–1M tokens (current leaders) | Varies widely; often 4K–128K |
| **Hosting / compliance** | Provider's cloud; data leaves your infra | Full control; air-gap possible |

**Quick heuristics for common scenarios:**

- **Prototype / early build:** Claude Haiku or gpt-5-mini — cheap, fast, good enough to test the concept.
- **Production with data privacy:** Open-weight model self-hosted (Llama 3 70B on a GPU server).
- **Hard reasoning / math / code:** Claude Sonnet/Opus, OpenAI o3, or Llama with extended context.
- **Multilingual CJK:** Qwen is worth benchmarking.
- **Edge / mobile:** Llama 3.2 1B-3B, Gemma 2B.
- **Always benchmark on your data** — rankings change with every release.

---

### 2.5 Cost & Token Accounting

API pricing is always **per-token**, split into input and output. Output tokens cost more (they require a forward pass per token; input is processed in parallel).

**Rough estimation formula:**

```
estimated_cost = (input_tokens × input_price_per_1M) / 1_000_000
              + (output_tokens × output_price_per_1M) / 1_000_000
```

**Cost levers:**

1. **Reduce input tokens:** Shorter system prompts, fewer few-shot examples, tighter context windows in RAG.
2. **Reduce output tokens:** Set `max_tokens` tightly; request concise responses; use structured output (JSON is often shorter).
3. **Choose a smaller model:** A small/fast model is often 10–50× cheaper per token than a large one.
4. **Cache prompt prefixes:** Anthropic and OpenAI both offer prompt caching — repeated identical prefixes are billed at a fraction of the full input price.
5. **Batch API:** Both providers offer async batch processing at ~50% discount for non-latency-sensitive workloads.

**Token counting without making an API call:** Use provider token-counting utilities (e.g. Anthropic's `count_tokens` / OpenAI's `tiktoken`) to count tokens locally before sending.

> **Key point:** "How would you estimate and control LLM API cost in production?" — input/output token split, model tier choice, caching, and batching are the four pillars.

---

## 3. Hands-On Lab

**Lab location:** `labs/common/day-03/`

**Goal:** Make decoding parameters tangible through two exercises:

1. **Pure-numpy decoding visualiser** — given a toy probability distribution, apply temperature, top-k, and top-p and watch the distribution shift. No API needed.
2. **Provider-flexible LLM call** — sends the same prompt at temperature 0 and temperature 1 to show output variation. If no API key is set, a built-in mock runs the same logic.

**Setup:**
```bash
cd labs/common/day-03
pip install -r requirements.txt
python solution.py          # runs entirely with mock — no API key needed
```

**To use a real API (optional):**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python solution.py

# or with OpenAI:
export OPENAI_API_KEY=sk-...
python solution.py
```

See `labs/common/day-03/README.md` for full details and expected output.

---

## 4. Self-Check Quiz

**Instructions:** Answer each question before checking the answer below.

---

**Q1.** What is the purpose of the supervised fine-tuning (SFT) phase, and why isn't the base pretrained model sufficient for use as an assistant?

<details>
<summary>Show answer</summary>

The base model is trained only to predict the next token — it will complete any text, including harmful ones, and has no concept of instruction-following format. SFT teaches the model to behave as an assistant by training on (instruction, ideal-response) pairs, giving it the conversational format and basic instruction adherence needed for practical use.

</details>

**Q2.** You set `temperature=0` on a model call. What will you observe and why? What is the downside?

<details>
<summary>Show answer</summary>

With temperature 0, the model always picks the highest-probability token (greedy decoding). Output becomes deterministic and focused. The downside is repetitiveness and potential quality loss — greedy choices can be locally optimal but globally suboptimal, and you lose the diversity that sampling provides.

</details>

**Q3.** Explain top-p (nucleus) sampling in one sentence, and explain why it is preferred over top-k in most chat applications.

<details>
<summary>Show answer</summary>

Top-p keeps the smallest set of tokens whose cumulative probability reaches `p`, then samples from that set. It is preferred because it adapts to the model's confidence — when the model is sure, only a few tokens are in the nucleus; when uncertain, more are included — whereas top-k always keeps a fixed count regardless of how concentrated the distribution is.

</details>

**Q4.** A developer complains that their LLM responses repeat the same phrases constantly. Which two parameters could help, and how do they differ?

<details>
<summary>Show answer</summary>

`frequency_penalty` and `presence_penalty`. Frequency penalty reduces a token's probability proportionally to how many times it has already appeared (scales with count). Presence penalty applies a flat penalty to any token that has appeared at least once (binary — appeared or not). Frequency penalty is better for reducing repeated phrases; presence penalty is better for forcing topic diversity.

</details>

**Q5.** A client wants to process 500 000 customer support tickets overnight to extract structured JSON from each. They want the cheapest option with Anthropic. What two API features would you recommend?

<details>
<summary>Show answer</summary>

(1) **Batch API** — async processing at ~50% discount, ideal for non-latency-sensitive bulk workloads. (2) **Prompt caching** — the system prompt and schema instructions are identical across all 500K calls; caching the common prefix dramatically reduces input token costs. Also, choose the smallest model that achieves acceptable quality (Haiku class).

</details>

**Q6.** What is RLHF and what problem does it solve that SFT alone cannot?

<details>
<summary>Show answer</summary>

RLHF (Reinforcement Learning from Human Feedback) trains a reward model on human preference comparisons and then fine-tunes the LLM to maximise that reward. SFT alone teaches format but can produce verbose, sycophantic, or subtly harmful outputs — RLHF calibrates the model to produce responses that humans actually prefer, including being appropriately concise, honest, and safe.

</details>

**Q7.** You have a client in healthcare with strict data residency requirements (no data may leave their private cloud). They need a capable LLM for clinical note summarisation. What model architecture/hosting approach do you recommend and why?

<details>
<summary>Show answer</summary>

An open-weight model (e.g. Llama 3 70B or Mistral Large) self-hosted in their private cloud. This provides full data control — no tokens are sent to a third-party API. The tradeoff is infrastructure cost and maintenance burden, but it is the only approach compatible with strict data residency. Consider a GPU cluster with vLLM for inference efficiency.

</details>

**Q8.** In token-based pricing, why do output tokens typically cost more than input tokens?

<details>
<summary>Show answer</summary>

Input tokens can all be processed in parallel in a single forward pass (the attention mechanism processes the whole sequence simultaneously). Output tokens must each be generated sequentially — one forward pass per output token. This makes output generation more compute-intensive per token, hence the higher price.

</details>

---

## 5. Concept Deep-Dive Q&A

---

**Q1. "How does an LLM actually produce text — walk me through the mechanics."**

<details>
<summary>Show answer</summary>

At inference time, the model takes the input tokens, runs them through all transformer layers, and produces a vector of logits — one number per vocabulary token (often 32K–128K tokens). Softmax converts those logits into a probability distribution. We then sample one token from that distribution using our chosen strategy (greedy, top-p, etc.), append it to the sequence, and repeat. This autoregressive loop continues until a stop condition — a stop sequence or max token limit. The key insight is that the model never "thinks ahead" — it makes one token decision at a time, each conditioned on everything before it.

</details>

**Q2. "A stakeholder wants our AI feature to be 'more creative.' What do you actually change in the API call, and what are the risks?"**

<details>
<summary>Show answer</summary>

Increase `temperature` (e.g. from 0.7 to 1.0–1.2) and consider widening `top_p` slightly. Higher temperature flattens the probability distribution, making lower-probability tokens more likely — which produces more varied, surprising outputs. The risks are: outputs may become factually unreliable (hallucinations increase), structurally inconsistent (harder to parse as JSON), or occasionally incoherent. For a production feature I'd benchmark quality metrics at a few temperature values and pick the highest temperature that still meets accuracy/format requirements.

</details>

**Q3. "We're worried about LLM API costs scaling with our user base. How do you manage that?"**

<details>
<summary>Show answer</summary>

Four levers: (1) **Model tier** — use the smallest model that meets quality requirements; a 10× cost difference between small and large models is common. (2) **Prompt efficiency** — audit system prompt length, reduce redundant few-shot examples, tighten context in RAG pipelines. (3) **Caching** — both Anthropic and OpenAI offer prompt prefix caching; repeated system prompts cost a fraction of full price. (4) **Batching** — for non-real-time workloads, batch APIs offer ~50% discounts. Also set `max_tokens` tightly and count tokens before sending with `tiktoken` / `anthropic.count_tokens` to forecast cost before scaling.

</details>

**Q4. "Why would we choose an open-source model over Claude or GPT?"**

<details>
<summary>Show answer</summary>

The main reasons are: (1) **Data privacy / compliance** — data never leaves your infrastructure; important for healthcare, finance, and legal applications. (2) **Cost at scale** — at very high volume, hosting a GPU cluster can be cheaper than per-token API pricing. (3) **Customisation** — open-weight models can be fine-tuned on proprietary data without sending that data to a third party. (4) **Latency control** — no network round-trip; local inference on fast hardware can beat hosted APIs. The trade-offs are infrastructure complexity, the need for ML ops expertise, and typically lower out-of-the-box capability than frontier models at equivalent parameter counts.

</details>

**Q5. "What is RLHF and why does it matter for our production application?"**

<details>
<summary>Show answer</summary>

RLHF — Reinforcement Learning from Human Feedback — is the process that turns a raw language model into a helpful assistant. Human raters compare model outputs and label which is better; a reward model is trained on these preferences; then the LLM is fine-tuned to maximise the reward. For a production application, RLHF matters because it is what makes the model refuse harmful requests, follow instructions precisely, give concise answers, and maintain a consistent tone. If you use a base model without RLHF (which some open-source checkpoints are), you get a very capable text-completer that is unpredictable as an assistant.

</details>

**Q6. "How do you choose between Claude, GPT, and an open-source model for a new project?"**

<details>
<summary>Show answer</summary>

I evaluate five dimensions: (1) **Capability** — benchmark on a representative sample of the actual task; leaderboard rankings don't always translate to your specific domain. (2) **Cost** — estimate monthly token volume and compare per-token pricing vs. hosting cost. (3) **Latency** — check time-to-first-token and throughput SLAs against UX requirements. (4) **Context window** — if the task needs very long contexts (e.g. full document analysis), confirm the model handles it reliably, not just in theory. (5) **Data compliance** — if there are data residency or privacy requirements, open-weight self-hosted may be the only option. I typically prototype with a hosted model (cheapest iteration) and revisit hosting if cost or compliance forces it.

</details>

**Q7. "What are stop sequences and when would you use them?"**

<details>
<summary>Show answer</summary>

Stop sequences are strings that cause the model to halt generation immediately when produced — the stop string itself is not included in the output. They're useful for: structured output (stop at the closing `}` of a JSON object), multi-turn dialogue (stop at `\nHuman:` to prevent the model from role-playing the next turn), code extraction (stop at the closing code fence), and in RAG pipelines where you want exactly one answer before a delimiter. They're a lightweight, zero-cost way to enforce output boundaries without prompt complexity.

</details>

**Q8. "Explain the difference between frequency penalty and presence penalty."**

<details>
<summary>Show answer</summary>

Both discourage repetition, but the mechanism differs. Frequency penalty reduces a token's logit proportionally to how many times it has already appeared in the output — the more it's been used, the harder it's penalised. Presence penalty applies a flat, one-time penalty to any token that has appeared at all, regardless of count. In practice: use frequency penalty to suppress repeated phrases (e.g. a model that keeps saying "certainly!"); use presence penalty to encourage the model to explore new topics rather than circling back to ones it has already mentioned.

</details>

**Q9. "A client asks whether we can fine-tune Claude to speak in their brand voice. How do you answer?"**

<details>
<summary>Show answer</summary>

For Anthropic's Claude, fine-tuning is not publicly available — the model is accessed only through the API. To achieve brand voice, the practical approach is prompt engineering: a detailed system prompt that describes the tone, style, and example phrases, potentially with a few-shot examples of ideal responses. For clients where fine-tuning is a hard requirement, the path is open-weight models (Llama, Mistral) where you can run supervised fine-tuning on brand voice examples using tools like Hugging Face TRL or Axolotl. I'd always recommend validating whether prompt engineering is sufficient before committing to the complexity and cost of fine-tuning.

</details>

**Q10. "What is context window size and why does it matter practically?"**

<details>
<summary>Show answer</summary>

The context window is the maximum number of tokens the model can "see" at once — both input and output combined. It matters practically because it determines: (1) how long a document you can process in one call, (2) how much conversation history you can maintain in a chat, (3) how many retrieved chunks you can fit in a RAG prompt. Most current frontier models offer 128K–1M token windows, which is large enough for most tasks, but beware: performance often degrades on very long contexts (the model may miss information in the middle), and longer contexts cost more in input tokens. For tasks like full-book summarisation or very long code analysis, context window limits are a real architectural constraint.

</details>

---

## 6. Further Reading

| Resource | Why read it |
|----------|-------------|
| Hugging Face — [The Illustrated GPT-2](https://jalammar.github.io/illustrated-gpt2/) | Visual walkthrough of autoregressive generation — best mental model for how tokens are produced one at a time |
| Anthropic — [Model overview](https://docs.anthropic.com/en/docs/about-claude/models/overview) | Official model tier comparison; always check for current model IDs and pricing |
| OpenAI — [API reference: Chat completions](https://platform.openai.com/docs/api-reference/chat) | Parameter reference for temperature, top_p, penalties, stop sequences |
| Chip Huyen — *Designing Machine Learning Systems*, Ch. 11 | Deployment and cost considerations for ML/LLM in production |
| Lilian Weng — [Reinforcement Learning from Human Feedback](https://lilianweng.github.io/posts/2023-01-27-the-transformer-family-v2/) | Deep but accessible blog post on RLHF mechanics |
| geeksforgeeks — [Understanding LLM Sampling](https://www.geeksforgeeks.org/artificial-intelligence/graph-based-semi-supervised-learning/) | Practical guide to temperature, top-k, top-p with visualisations |
| Andrej Karpathy — [Let's build GPT](https://www.youtube.com/watch?v=kCc8FmEb1nY) | 2-hour video; builds a GPT from scratch — cements everything in Days 2–3 |
| Open LLM Leaderboard (Hugging Face) | Benchmark comparisons across open-weight models; update frequently |

---

## 7. Key Takeaways

1. **LLMs are built in three phases:** pretraining learns language from raw text; SFT teaches instruction-following format; RLHF/DPO aligns the model to human preferences for helpfulness, safety, and accuracy.

2. **Generation is sequential sampling:** the model outputs a probability distribution over the vocabulary at each step and samples one token. The decoding strategy controls how that sampling happens.

3. **Temperature is your primary creativity dial:** low (0–0.3) for factual/structured tasks, medium (0.5–0.8) for balanced chat, high (0.9–1.3) for creative tasks. Never set it and forget it — it should match the task.

4. **Top-p beats top-k for most chat tasks** because it adapts to the model's confidence. Use top-p 0.9–0.95 as a default starting point.

5. **Model selection is a trade-off across five dimensions:** capability, cost, latency, context window, and data compliance. No model wins on all five — match the model to the project's constraints.

6. **Cost scales with tokens, not calls:** the fastest ROI on cost reduction is model tier selection and prompt compression, not architecture changes.

7. **Stop sequences and max_tokens are underused:** they're zero-cost guardrails that prevent runaway outputs and make structured generation reliable.
