# Day 1 — LLM Landscape, Tokens & Embeddings

> **Program:** 15-Day GenAI/LLM Training | **Week 1 — Foundations**
> **Maintained by:** InspironLabs AI Practice · training@inspironlabs.com

---

## 1. Learning Objectives

By the end of Day 1 you will be able to:

- Explain the AI → ML → Deep Learning → Generative AI → LLM hierarchy and where each layer sits.
- Describe what an LLM actually is at a mechanical level: a next-token predictor trained on large text corpora.
- Define *token*, explain Byte-Pair Encoding (BPE) at an intuitive level, and estimate token counts for a piece of text.
- Explain what embeddings are, why they are vectors, and how cosine similarity measures semantic closeness.
- Define *context window* and explain why it constrains what you can send to a model.

---

## 2. Concept Reading

### 2.1 The Nesting Hierarchy: AI → ML → DL → GenAI → LLM

Software developers often hear these terms used interchangeably. They are not the same. Think of them as concentric circles:

```
┌──────────────────────────────────────────────────────────┐
│  Artificial Intelligence (AI)                            │
│  Any technique making machines exhibit intelligent       │
│  behaviour (rules-based, search, ML, etc.)               │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Machine Learning (ML)                             │  │
│  │  Systems that learn patterns from data instead     │  │
│  │  of following hand-written rules                   │  │
│  │                                                    │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  Deep Learning (DL)                          │  │  │
│  │  │  ML using multi-layer neural networks;       │  │  │
│  │  │  excel at images, speech, text               │  │  │
│  │  │                                              │  │  │
│  │  │  ┌────────────────────────────────────────┐  │  │  │
│  │  │  │  Generative AI (GenAI)                 │  │  │  │
│  │  │  │  DL models that *generate* new content  │  │  │  │
│  │  │  │  (text, images, audio, code, video)     │  │  │  │
│  │  │  │                                        │  │  │  │
│  │  │  │  ┌──────────────────────────────────┐  │  │  │  │
│  │  │  │  │  LLM                             │  │  │  │  │
│  │  │  │  │  GenAI model specialised for     │  │  │  │  │
│  │  │  │  │  text; trained on internet-      │  │  │  │  │
│  │  │  │  │  scale corpora                   │  │  │  │  │
│  │  │  │  └──────────────────────────────────┘  │  │  │  │
│  │  │  └────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

**Key distinctions:**

| Term | What it adds over the parent |
|------|------------------------------|
| ML | Learning from data (vs. hard-coded rules) |
| Deep Learning | Multi-layer neural nets — automatic feature extraction |
| Generative AI | Produces *new* content; not just classification/regression |
| LLM | Generative AI operating on token sequences; trained on massive text |

---

### 2.2 What an LLM Actually Is

**One-sentence definition:** An LLM is a probability distribution over the next token given all previous tokens.

At every step the model does:

```
P(next_token | token_1, token_2, ..., token_n)  →  sample one token  →  append  →  repeat
```

That's it. Everything else — answering questions, writing code, following instructions — is an emergent behaviour of training that distribution on enormous, diverse text.

Generative : Generate next sequence. 
#### What this implies for developers

| Implication               | Why it matters                                                                                                                                                                     |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Non-determinism**       | Sampling means the same prompt can return different outputs. Use `temperature=0` for near-deterministic output; exact reproducibility is NOT guaranteed across providers/hardware. |
| **No persistent memory**  | The model has no state between API calls. Everything it "knows" about your session must be in the current prompt.                                                                  |
| **Can hallucinate**       | If the most probable next token continues a plausible but wrong sentence, the model does it. It has no external fact-checker.                                                      |
| **Patterns, not logic**   | LLMs are very good at mimicking the *form* of reasoning they saw in training data. They are not running a symbolic solver.                                                         |
| **Context is everything** | The model only sees what you put in the prompt. Richer context = better output.                                                                                                    |

#### What LLMs can and cannot do

```
CAN DO well                          CANNOT DO reliably
────────────────────────────────     ────────────────────────────────────
Summarisation & extraction           Precise arithmetic (unless tool-use)
Paraphrasing & rewriting             Real-time / up-to-date information
Code generation & explanation        Deterministic exact-match logic
Instruction following (with care)    Count characters/tokens in own output
Language translation                 Access external URLs / APIs (without tools)
Chain-of-thought reasoning           Guarantee factual correctness
Classification & sentiment           Recall every training fact accurately
```

---

### 2.3 Tokens & Tokenisation

#### What is a token?

A **token** is the basic unit a model processes — not a character, not a word. Modern LLMs use sub-word tokenisers.

Rule of thumb (English text):

```
1 token ≈ 4 characters  ≈  0.75 words
```

Examples with GPT-style BPE:
```
"Hello"          → ["Hello"]                          1 token
"Hello, world!"  → ["Hello", ",", " world", "!"]      4 tokens
"unbelievable"   → ["un", "bel", "iev", "able"]       4 tokens
"2024-06-17"     → ["2024", "-", "06", "-", "17"]     5 tokens
```

Non-English text, code, or rare words cost more tokens per character.

#### Byte-Pair Encoding (BPE) — intuition

BPE builds a vocabulary by iteratively merging the most frequent adjacent byte pairs in the training corpus:

```
Step 0 (characters): h e l l o   w o r l d
Step 1 (most common pair merged): h e l l o   w o r ld      ← "rl"->"rl" merged as "rld"... 
                                                                (simplified; actual merges differ)
...
After N merges: common words → single tokens
               rare words   → several sub-word tokens
```

**Why does this matter to you as a developer?**

- **API cost** scales with tokens, not characters. 1 million tokens ≠ 1 million words.
- **Context limits** are measured in tokens. Knowing `~4 chars/token` lets you estimate fit.
- **Prompt design** — avoid excessive punctuation, whitespace, or non-standard characters; they inflate token counts.

#### Context Window

The **context window** is the maximum number of tokens a model can process in a single forward pass. It includes both **input** (your prompt + conversation history) and **output** (the model's response).

```
┌───────────────────────────────────────────────────────┐
│                    Context Window (e.g. 128 k tokens) │
│  ┌──────────────────────────┐  ┌─────────────────────┐│
│  │     INPUT tokens         │  │   OUTPUT tokens      ││
│  │  system prompt +         │  │   model completion   ││
│  │  conversation history +  │  │   (max_tokens)       ││
│  │  user message +          │  │                      ││
│  │  retrieved docs (RAG)    │  │                      ││
│  └──────────────────────────┘  └─────────────────────┘│
└───────────────────────────────────────────────────────┘
         input_tokens + output_tokens ≤ context_limit
```

**Common context limits (approximate, check current docs):**

| Model | Context Window |
|-------|---------------|
| GPT-5.5 | 1M tokens |
| Claude Opus 4.8 | 1M tokens |
| Gemini 3.1 Pro | 1M tokens |
| Llama 4 Scout | 10M tokens |
| DeepSeek V4 Pro | 1M tokens |
| Grok 4 | 2M tokens |

Exceeding the context window raises an error. Strategies to handle large inputs: chunking, summarisation, RAG (covered in later days).

---

### 2.4 Embeddings

#### Text → vectors

An **embedding** is a fixed-length numerical vector that represents the *meaning* of text. LLM-derived embeddings place semantically similar text close together in vector space.

```
"The cat sat on the mat"   →  [0.12, -0.34, 0.88, ..., 0.05]   (384 floats)
"A kitten rested on a rug" →  [0.11, -0.31, 0.85, ..., 0.07]   (384 floats, similar!)
"The stock market crashed"  →  [-0.55, 0.72, -0.12, ..., 0.91]  (384 floats, different)
```

#### Cosine similarity

The standard metric for comparing embeddings. It measures the *angle* between two vectors, independent of their magnitude:

```
           A · B
cos(θ) = ─────────
          |A| × |B|

Range: -1.0 (opposite) to +1.0 (identical)
Practical threshold: >0.85 = very similar; 0.5–0.85 = related; <0.5 = unrelated
```

ASCII illustration:

```
     B (kitten on rug)
    /
   / ← small angle → high cosine similarity
  /θ
 A────────────────────────── (cat on mat)

 C (stock market)             ← large angle, low cosine similarity
  \
   \
    \
     (far from A and B in vector space)
```

#### Why embeddings matter for AI projects

- **Semantic search** — find documents by meaning, not keywords.
- **RAG (Retrieval-Augmented Generation)** — retrieve relevant chunks to put into LLM context.
- **Clustering & classification** — group similar documents without labels.
- **Duplicate detection** — high cosine similarity flags near-duplicates.

The embedding model you use today (`all-MiniLM-L6-v2`) is a sentence-transformer that runs fully locally — no API key, no cost, 384-dimensional vectors.

---

## 3. Hands-on Lab

**Location:** `labs/common/day-01/`

**What you will do:**
1. Tokenise several text samples with **tiktoken** and observe how token counts vary.
2. Embed five sentences with **sentence-transformers** (`all-MiniLM-L6-v2`) and compute a cosine-similarity matrix.
3. Confirm that semantically related sentences score higher — *without* any API key.

**Setup:**
```bash
cd labs/common/day-01
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Run the starter file (with TODOs):**
```bash
python starter.py
```

**Run the complete solution:**
```bash
python solution.py
```

**What to observe:**
- Token counts differ from word counts — watch the ratio.
- The similarity matrix diagonal is always 1.0 (a sentence vs. itself).
- Sentence pairs about the same topic (e.g., both about cats) score 0.8–0.95.
- Unrelated pairs (cat sentence vs. finance sentence) score 0.1–0.4.

See `labs/common/day-01/README.md` for full instructions and expected output.

---

## 4. Self-Check Quiz

*Answer in your head or on paper first, then reveal the answers.*

**Q1.** Name the hierarchy from broadest to narrowest: AI / Deep Learning / Generative AI / LLM / Machine Learning.

<details>
<summary>Show answer</summary>

Broadest to narrowest: AI → Machine Learning → Deep Learning → Generative AI → LLM.

</details>

**Q2.** An LLM is often described as a "next-token predictor." What does this mean in plain English?

<details>
<summary>Show answer</summary>

Given the sequence of tokens seen so far, the model outputs a probability distribution over every possible next token, then samples (or argmax-selects) one. This is repeated token-by-token until a stop condition.

</details>

**Q3.** A user's message is 320 characters of English. Roughly how many tokens is that?

<details>
<summary>Show answer</summary>

320 characters ÷ 4 ≈ **80 tokens** (rule of thumb: ~4 chars per token for English).

</details>

**Q4.** Why does a rare or non-English word tend to cost more tokens than a common English word?

<details>
<summary>Show answer</summary>

BPE builds its vocabulary from the most frequent byte-pair merges in the training corpus (mostly English web text). Rare or non-English words did not appear frequently enough to earn a single merged token, so they are split into many sub-word or even character-level tokens.

</details>

**Q5.** What is the context window, and what happens if you exceed it?

<details>
<summary>Show answer</summary>

The context window is the maximum total number of tokens (input + output) that a model can process in one call. Exceeding it causes an API error; common mitigations include chunking, summarisation, or retrieval-augmented generation.

</details>

**Q6.** You have two sentences with a cosine similarity of 0.92 and two others with 0.18. What does each score indicate?

<details>
<summary>Show answer</summary>

0.92 = the sentences are semantically very similar (nearly the same meaning). 0.18 = the sentences are largely unrelated in meaning.

</details>

**Q7.** Give two concrete reasons why an LLM might produce a factually wrong answer.

<details>
<summary>Show answer</summary>

Any two of: (1) the most-probable next token continues a plausible-sounding but incorrect sentence; (2) the model's training data contained incorrect or outdated information; (3) the model has no external fact-checking mechanism; (4) stochastic sampling introduces variation.

</details>

**Q8.** Name three downstream tasks that use embeddings.

<details>
<summary>Show answer</summary>

Any three of: semantic search, RAG chunk retrieval, document clustering, duplicate/near-duplicate detection, recommendation systems, classification with nearest-neighbour lookup.

</details>

---

## 5. Concept Deep-Dive Q&A

*These questions test deeper, applied understanding of the day's concepts. Read the question, draft your own answer, then compare.*

---

**Q1. "Can you explain what a large language model is to a non-technical stakeholder?"**

<details>
<summary>Show answer</summary>

An LLM is a software system trained on enormous amounts of text — think most of the internet — to predict what word (more precisely, what token) comes next in a sequence. Through that training it learns grammar, facts, reasoning patterns, and writing styles. When you send it a prompt, it generates a continuation token by token. Despite this simple mechanism, well-trained models exhibit surprisingly powerful language abilities, which is why we can use them for tasks like summarisation, Q&A, code generation, and customer support.

</details>

---

**Q2. "What is a token, and why does it matter for cost estimation?"**

<details>
<summary>Show answer</summary>

A token is the sub-word unit that LLMs operate on — not a character, not a word. Tokenisation is handled by an algorithm like BPE that merges common byte sequences into single tokens. As a rule of thumb, one token ≈ 4 English characters or 0.75 words. Cost and context limits are both measured in tokens, so understanding tokenisation lets you estimate API cost, check whether a document fits in the context window, and optimise prompts for efficiency.

</details>

---

**Q3. "What is a context window, and how does it affect how you design a system?"**

<details>
<summary>Show answer</summary>

The context window is the maximum number of tokens — input plus output combined — that a model can process in a single API call. Everything the model "knows" about the current task must fit inside it. This drives several architectural decisions: for long documents you chunk them and retrieve only the relevant chunks (RAG); for long conversations you summarise or trim history; for very large code bases you index the codebase and surface only relevant files. Choosing a model with a larger context window can simplify design but increases cost per call.

</details>

---

**Q4. "Why are LLMs non-deterministic, and when would you want deterministic output?"**

<details>
<summary>Show answer</summary>

LLMs sample from a probability distribution over the vocabulary at each token step. Even with the same prompt, different samples produce different completions. You control this with the `temperature` parameter: `temperature=0` makes the model always pick the highest-probability token, producing near-deterministic output — but exact reproducibility is NOT guaranteed across providers or hardware due to floating-point and batching differences. You want near-deterministic output for testing, compliance outputs, or structured data extraction where repeatability matters. For creative tasks you want higher temperature to get diverse outputs.

</details>

---

**Q5. "What is an embedding, and how is it used in a RAG pipeline?"**

<details>
<summary>Show answer</summary>

An embedding is a dense numerical vector (typically hundreds to thousands of floats) produced by a model to represent the semantic content of a piece of text. Semantically similar text produces vectors that are close in the vector space, measured by cosine similarity. In a RAG pipeline, you pre-embed your knowledge-base documents and store them in a vector database. At query time, you embed the user's question and retrieve the top-K most similar document chunks. Those chunks are inserted into the LLM's context window, giving it grounded, relevant information to answer from.

</details>

---

**Q6. "What is cosine similarity and why is it preferred over Euclidean distance for embeddings?"**

<details>
<summary>Show answer</summary>

Cosine similarity measures the cosine of the angle between two vectors — equivalently, their dot product divided by the product of their magnitudes. It ranges from -1 to 1, where 1 means identical direction. It is preferred for embeddings because embedding models are trained to encode meaning in the *direction* of vectors, not their magnitude. Two sentences can have very different magnitudes (due to length or encoding choices) but the same meaning; cosine similarity captures this correctly where Euclidean distance would be misled by magnitude differences.

</details>

---

**Q7. "What are LLM hallucinations and how do you mitigate them?"**

<details>
<summary>Show answer</summary>

Hallucinations are when an LLM outputs fluent, confident-sounding content that is factually incorrect or entirely fabricated. They arise because the model is optimising for probable next tokens, not for factual accuracy. Common mitigations: (1) RAG — ground the model's answer in retrieved, verified documents; (2) tool use — let the model call APIs or databases for facts rather than recalling from parameters; (3) output validation — use structured output schemas and post-process/verify critical fields; (4) chain-of-thought prompting — asking the model to reason step-by-step reduces but does not eliminate hallucinations; (5) human-in-the-loop review for high-stakes outputs.

</details>

---

**Q8. "How does BPE tokenisation handle a word it has never seen before?"**

<details>
<summary>Show answer</summary>

BPE cannot produce a single token for an unseen word because that word was never frequent enough in training to get its own merged entry in the vocabulary. Instead, BPE falls back to smaller sub-word pieces — potentially down to individual bytes or characters — that are always in the vocabulary. So an invented word like "grokkinomics" might be tokenised as ["gr", "ok", "kin", "om", "ics"], costing five tokens instead of one. This graceful degradation means BPE never produces an unknown-token error, but rare words and non-English text cost more tokens per unit of meaning.

</details>

---

## 6. Further Reading : 

*Ordered from most accessible to most technical.*

| Resource | What you will get |
|----------|------------------|
| [Andrej Karpathy — "Intro to Large Language Models" (YouTube, 1 hr)](https://www.youtube.com/watch?v=zjkBMFhNj_g) | Best single video overview of how LLMs work; assumes coding background |
| [OpenAI Tokenizer playground](https://platform.openai.com/tokenizer) | Interactive: paste text, see token boundaries coloured live |
| [Hugging Face — "The Illustrated Word2Vec"](https://jalammar.github.io/illustrated-word2vec/) | Visual intuition for word embeddings (precursor to modern embeddings) |
| [Lilian Weng — "The Transformer Family Version 2.0"](https://lilianweng.github.io/posts/2023-01-27-the-transformer-family-v2/) | Deep dive into transformer architecture (Day 2 prep) |
| [BPE original paper — Sennrich et al. 2016](https://arxiv.org/pdf/1508.07909) | 6 pages; approachable; the original BPE-for-NLP paper |
| [Hugging Face `sentence-transformers` docs](https://www.sbert.net/) | Library documentation for the embeddings model used in the lab |
| [OpenAI — "Embeddings" guide](https://platform.openai.com/docs/guides/embeddings) | Practical guide including use cases and cost |

---

## 7. Key Takeaways

- **The hierarchy**: AI ⊃ ML ⊃ Deep Learning ⊃ Generative AI ⊃ LLM. Each layer narrows the technique.
- **LLMs are next-token predictors** — powerful emergent behaviour from a simple training objective on massive text.
- **LLMs are non-deterministic** by default (sampling); use `temperature=0` for near-deterministic output — exact reproducibility is NOT guaranteed across providers or hardware due to floating-point and batching effects.
- **Hallucinations are structural**, not bugs — the model predicts probable text, not verified facts. Plan for mitigation (RAG, tool use, validation).
- **Token ≠ word**: ~4 chars or ~0.75 words per token in English. Rare words and non-English text cost more.
- **Context window** = total tokens in + out per API call. Design your system around this limit.
- **Embeddings** are dense semantic vectors. Cosine similarity measures meaning-closeness. Foundation of semantic search and RAG.
- **No API key needed** for embeddings — `sentence-transformers` runs fully locally. Use this for cost-free exploration.

---

*Next: [Day 2 — Transformer Architecture & Attention](Day-02-transformers-attention.md)*
