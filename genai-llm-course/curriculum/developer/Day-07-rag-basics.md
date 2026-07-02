# Day 7 — RAG Basics: Retrieve, Augment, Generate

**Track:** Developer | **Week:** 2 | **Day:** 7 of 15

---

## 1. Objectives

By the end of Day 7 you will be able to:

- Explain the three-stage RAG pipeline (Retrieve → Augment → Generate) and why it matters
- Describe the four-stage ingestion pipeline (Load → Chunk → Embed → Store) and compare chunking strategies (fixed-size, overlap, recursive/structural) to choose the right one for a given corpus
- Build an augmented prompt that grounds the model's answer in retrieved context and elicits source citations
- Run a complete end-to-end RAG system over the shared HR corpus, fully offline with a mock generator
- Articulate when to use RAG vs fine-tuning vs long-context approaches

---

## 2. Concept Reading

### 2.1 Why RAG? The Core Problem

Large language models have a hard cutoff in their training data and zero access to private documents. Ask a model about Acme Corp's 2026 holiday calendar and it will either hallucinate confidently or refuse. This is not a model quality problem — it is a knowledge access problem.

**Retrieval-Augmented Generation (RAG)** solves it by injecting relevant, authoritative text into the context window at inference time. The model is not re-trained; it is given the right documents to reason over, just-in-time.

Benefits of RAG:

| Benefit | Mechanism |
|---|---|
| **Grounding** | Model's answer must be derivable from the injected text |
| **Fresh / private data** | Corpus can be updated independently of the model |
| **Reduced hallucination** | Model is instructed to stay within the provided context |
| **Citable answers** | Chunk metadata (source file, page) is returned alongside text |

### 2.2 The Retrieve → Augment → Generate Loop

```
User question
      │
      ▼
 ┌─────────────────────────────────┐
 │  RETRIEVE                       │
 │  • Embed the question           │
 │  • ANN search in vector store   │
 │  • Return top-k chunks + meta   │
 └─────────────┬───────────────────┘
               │ top-k chunks
               ▼
 ┌─────────────────────────────────┐
 │  AUGMENT                        │
 │  • Build prompt:                │
 │    [System instruction]         │
 │    [Context block — chunks]     │
 │    [User question]              │
 └─────────────┬───────────────────┘
               │ augmented prompt
               ▼
 ┌─────────────────────────────────┐
 │  GENERATE                       │
 │  • LLM produces grounded answer │
 │  • Cites source filenames       │
 └─────────────────────────────────┘
```

The retriever and the generator are **decoupled**: you can swap out the vector store, the embedding model, or the generator without rebuilding the whole pipeline.

### 2.3 The Ingestion Pipeline

Before you can retrieve anything, you must build the index. This is a one-time (or periodic) offline step:

```
Raw documents
      │
      ▼
   LOAD          Read files from disk, web, database, etc.
      │
      ▼
   CHUNK         Split into search-granularity pieces (see 2.4)
      │
      ▼
   EMBED         Convert each chunk to a dense vector
      │
      ▼
   STORE         Write vectors + metadata to a vector database
```

The "right" granularity for a chunk is one that:
- Contains a complete, self-contained thought
- Is small enough that it is not polluted by unrelated content
- Is large enough that the model has enough context to understand it

### 2.4 Chunking Strategies

#### Fixed-size / token-window
Split every N tokens (or characters) regardless of sentence boundaries.

- **Pro:** Simple, predictable chunk count, easy to size for context window limits
- **Con:** Can cut sentences mid-thought; no semantic awareness
- **When to use:** Uniform-density prose where sentence boundaries are not critical

#### Fixed-size with overlap
Same as above but adjacent chunks share M tokens of overlap (typically 10–20% of chunk size).

- **Pro:** Ensures that sentences near a boundary appear in at least one full chunk
- **Con:** Slight storage and compute overhead
- **When to use:** Most practical RAG systems; the overlap is almost always worth it

#### Recursive / structural splitting
Split first on paragraph breaks, then on sentence breaks, then on character count — preferring natural boundaries.

- **Pro:** Produces semantically coherent chunks
- **Con:** Chunk sizes vary; harder to predict retrieval coverage
- **When to use:** Well-structured documents (policies, manuals, reports)

#### Semantic chunking
Embed each sentence; group sentences whose embeddings are similar; cut on embedding-distance spikes.

- **Pro:** Chunks align with topic shifts rather than arbitrary token counts
- **Con:** Expensive at ingestion time (one embedding per sentence); requires tuning the similarity threshold
- **When to use:** Long documents with clear topic shifts (research papers, transcripts)

**Day 7 lab** uses fixed-size with overlap — the sweet spot for a first RAG system.

### 2.5 Building the Augmented Prompt

A well-designed RAG prompt has three parts:

```
SYSTEM:
You are Acme Corp's internal HR assistant.
Answer ONLY from the provided context.
If the context does not contain enough information, say exactly:
"I don't know based on the available documents."
Always cite the source file(s) at the end of your answer.

CONTEXT:
[chunk 1 text]
Source: leave-and-pto-policy.md

[chunk 2 text]
Source: benefits-and-insurance.md

QUESTION:
How many PTO days do new employees get in their first year?
```

Key design choices:
- **Explicit "answer only from context"** — prevents the model from mixing in training-set knowledge
- **"I don't know" escape hatch** — prevents confident hallucination on questions outside the corpus
- **Source metadata in the context block** — makes citation automatic rather than inferred

### 2.6 Handling "I Don't Know"

A RAG system must handle three failure modes gracefully:

| Failure mode | Cause | Solution |
|---|---|---|
| No relevant chunks retrieved | Query too narrow or corpus gap | Return "I don't know" + suggest rephrasing |
| Chunks retrieved but insufficient | Document exists but is incomplete | Return partial answer, cite source, flag uncertainty |
| Model ignores context | Prompt does not force grounding | Strengthen system instruction; lower temperature |

### 2.7 RAG vs Fine-Tuning vs Long-Context

| Dimension | RAG | Fine-Tuning | Long-Context |
|---|---|---|---|
| **Knowledge update** | Update the corpus | Retrain the model | Update the context window |
| **Cost to update** | Low (re-index) | High (GPU + data) | Zero (just paste) |
| **Max knowledge size** | Unlimited (indexed) | Baked into weights | Limited by context window |
| **Latency** | +retrieval step (~100 ms) | Same as base | Scales with token count |
| **Hallucination risk** | Low (grounded) | Medium (memorised) | Low (in-window) |
| **Best for** | Large, frequently updated corpora | Style / task adaptation | Small, stable document sets |
| **Interpretability** | High (citations) | Low | Medium |

**Rule of thumb:** If your knowledge base is larger than fits in a context window, or changes more than monthly, use RAG. If you need to change the model's tone or task behaviour, fine-tune. If your whole corpus fits in a single context window and never changes, long-context may be simpler.

---

## 3. Hands-on Lab

**Location:** `labs/developer/day-07/`

**Goal:** Build an end-to-end RAG system over the Acme Corp HR corpus. Chunk documents with overlap, embed locally with `sentence-transformers`, store in Chroma, retrieve top-k for a question, build a grounded prompt, and generate a cited answer. Runs fully offline via a mock generator when no API key is present.

### Quick Start

```bash
cd /path/to/AI_Training
pip install -r labs/developer/day-07/requirements.txt
python labs/developer/day-07/solution.py        # offline mock — no key needed
ANTHROPIC_API_KEY=sk-... python labs/developer/day-07/solution.py  # live Claude
```

See `labs/developer/day-07/README.md` for full instructions.

### Lab Milestones

1. **Step 1 — Load:** Read all `.md` files from `data/hr-corpus/` (skip `README.md`)
2. **Step 2 — Chunk:** Split each document into fixed-size chunks with overlap
3. **Step 3 — Embed:** Embed all chunks with `sentence-transformers`
4. **Step 4 — Store:** Persist in a Chroma collection
5. **Step 5 — Retrieve:** Embed a question and fetch top-k chunks
6. **Step 6 — Augment:** Build the grounded prompt with context blocks + source metadata
7. **Step 7 — Generate:** Call the generator (Claude / OpenAI / Mock) and print the cited answer

---

## 4. Self-Check Quiz

**Instructions:** Answer from memory, then check below.

**Q1.** What three stages does the name "RAG" refer to?

<details>
<summary>Show answer</summary>

Retrieve → Augment → Generate.

</details>

---

**Q2.** Name two concrete benefits of using RAG over relying on an LLM's training data alone.

<details>
<summary>Show answer</summary>

Any two of: (a) grounding — answers are backed by specific documents; (b) freshness — corpus can be updated independently of the model; (c) reduced hallucination — model is instructed to stay within provided context; (d) citations — chunk metadata provides citable sources.

</details>

---

**Q3.** In a fixed-size chunking strategy with overlap, what does the overlap parameter achieve and what is a typical overlap size relative to chunk size?

<details>
<summary>Show answer</summary>

Overlap ensures that sentences near a chunk boundary appear fully in at least one adjacent chunk, avoiding mid-thought cuts. A typical overlap is 10–20% of the chunk size (e.g., 50–100 tokens overlap on a 512-token chunk).

</details>

---

**Q4.** What is the difference between the *ingestion pipeline* and the *inference pipeline* in a RAG system?

<details>
<summary>Show answer</summary>

The ingestion pipeline (Load → Chunk → Embed → Store) is an offline, one-time (or periodic) batch process that builds the vector index. The inference pipeline (Retrieve → Augment → Generate) runs at query time for each user question.

</details>

---

**Q5.** Why should a RAG system prompt include an explicit "I don't know" instruction?

<details>
<summary>Show answer</summary>

Without this instruction the model may use training-data knowledge to fabricate a plausible but ungrounded answer, defeating the purpose of RAG. The "I don't know" path forces the model to signal when the corpus does not contain sufficient information.

</details>

---

**Q6.** You have a corpus of 50,000 internal wiki articles that is updated weekly. Compare RAG vs fine-tuning vs long-context and recommend one.

<details>
<summary>Show answer</summary>

Recommend **RAG**: 50,000 articles vastly exceeds any context window; weekly updates would make fine-tuning prohibitively expensive; RAG re-indexes updated documents at low cost. Fine-tuning is unsuitable for rapidly changing factual knowledge. Long-context cannot hold 50,000 articles.

</details>

---

**Q7.** In the augmented prompt, why is source metadata (e.g., the filename) placed *inside* the context block rather than appended after the model's response?

<details>
<summary>Show answer</summary>

Placing the filename inside the context block means the model can read and reference the source while generating its answer. If the metadata were appended post-generation, the model could not include it in a coherent citation sentence.

</details>

---

**Q8.** What embedding model does Day 7's lab use, and why does this choice allow the lab to run without any API key?

<details>
<summary>Show answer</summary>

The lab uses `all-MiniLM-L6-v2` from `sentence-transformers`, which is an open-weights model that runs locally on CPU. Because no API call is needed for embedding, the entire ingestion and retrieval pipeline is free and offline.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1. Why does chunking matter so much for retrieval quality?**

<details>
<summary>Show answer</summary>

Retrieval works by computing the cosine similarity between the query embedding and each chunk embedding. If a chunk is too large, its embedding is a blend of many topics and will have a mediocre similarity to any single query. If a chunk is too small, it may not contain enough context for the model to produce a useful answer. The chunk size sets the granularity of the retrieval signal: think of it as the resolution of the search.

</details>

---

**Q2. What is "semantic drift" in chunking and how does it relate to embedding quality?**

<details>
<summary>Show answer</summary>

Semantic drift occurs when a fixed-size window spans a topic boundary — the beginning of the chunk discusses Topic A and the end discusses Topic B. The resulting embedding is a semantic average of both topics. Neither query about A nor queries about B will score highly, so the chunk becomes effectively invisible to retrieval. Structural and semantic chunking strategies exist specifically to cut on topic boundaries rather than arbitrary token positions, eliminating drift.

</details>

---

**Q3. How does top-k selection affect the quality vs cost tradeoff in RAG?**

<details>
<summary>Show answer</summary>

Increasing k retrieves more context, which raises the probability of including the relevant passage but also: (a) consumes more context-window tokens, increasing LLM cost per query; (b) introduces more off-topic text that the model must ignore, which can lower answer precision; (c) increases the likelihood the model conflates information from multiple sources. In practice, k=3–5 works well for focused factual queries; k=8–10 is used for multi-hop questions requiring synthesis across documents.

</details>

---

**Q4. What is the difference between sparse retrieval (BM25) and dense retrieval (vector search), and when would you combine them?**

<details>
<summary>Show answer</summary>

BM25 is a keyword-frequency algorithm that scores documents by exact term overlap with the query. Dense retrieval embeds both query and documents into a shared vector space and scores by cosine similarity, capturing semantic equivalence (e.g., "vacation days" matches "PTO allowance"). BM25 is better for rare named entities and precise identifiers; dense retrieval is better for paraphrase and intent matching. **Hybrid retrieval** (combining both via reciprocal rank fusion or a linear score blend) consistently outperforms either alone and is the approach used by most production RAG systems.

</details>

---

**Q5. How does metadata filtering complement vector search?**

<details>
<summary>Show answer</summary>

Vector search alone returns the top-k globally most similar chunks. Metadata filters allow you to pre-restrict the candidate set before or after retrieval — for example, "only search the `leave-and-pto-policy.md` document" or "only chunks from documents tagged `benefits`". This reduces noise when the user's intent implies a specific document category. Chroma, Pinecone, and Weaviate all support pre-filtering on metadata fields alongside the vector score.

</details>

---

**Q6. Why is the "I don't know" instruction critical for production RAG, and what are common failure modes if it is omitted?**

<details>
<summary>Show answer</summary>

Without an explicit refusal instruction, models tend to: (a) extrapolate from retrieved chunks to answer questions the chunks do not actually support; (b) blend in training-data knowledge, making the answer un-citable and potentially incorrect for the specific organisation; (c) confidently answer questions outside the corpus domain. In a production HR assistant, a confident wrong answer about policy entitlements can have legal or compliance consequences, making this instruction non-negotiable.

</details>

---

**Q7. What is "context stuffing" and why is it an anti-pattern?**

<details>
<summary>Show answer</summary>

Context stuffing is the practice of inserting every retrieved chunk (or even the entire corpus) into the prompt to avoid retrieval entirely, relying on the model to find the relevant passage within its context window. Problems: (a) token cost scales linearly with corpus size; (b) models exhibit "lost in the middle" behaviour — accuracy drops for information placed in the middle of a long context; (c) latency increases. Proper retrieval keeps the context window focused on the 3–10 most relevant chunks, giving the model a high signal-to-noise ratio.

</details>

---

**Q8. How does RAG interact with long-context models (e.g., 200k token windows)?**

<details>
<summary>Show answer</summary>

Long-context models reduce but do not eliminate the need for RAG. Even a 200k-token window cannot hold an enterprise's full document corpus (millions of documents). More importantly, RAG's retrieval step acts as a semantic filter, not just a size limiter — it presents the model with only the most relevant content, which improves answer precision even when the corpus technically fits. The practical combination is to use RAG for large corpora and reserve long-context for the final "read the full retrieved set" step.

</details>

---

**Q9. What is re-ranking and when should you add it to your RAG pipeline?**

<details>
<summary>Show answer</summary>

After vector search returns top-k chunks, a **cross-encoder re-ranker** (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`) scores each (query, chunk) pair jointly — not independently — yielding much more accurate relevance scores than cosine similarity alone. The pipeline becomes: retrieve top-20 by vector search → re-rank → pass top-5 to the generator. Re-ranking typically gives a 10–20% accuracy lift at the cost of k × cross-encoder inference calls. Add it when your retrieval precision is the bottleneck.

</details>

---

**Q10. If your RAG system gives wrong answers, how do you systematically diagnose whether the problem is in retrieval or generation?**

<details>
<summary>Show answer</summary>

Use a two-phase debug process. First, isolate retrieval: for a failing question, print the top-k retrieved chunks and check manually whether the correct passage is present. If it is not → retrieval failure (chunking, embedding model, or k too small). If the correct passage is present → generation failure (prompt instruction, model, or context order). This "retrieval oracle" test — where you inject the ground-truth chunk directly into the prompt and ask the model again — isolates the generation component definitively. Tools like RAGAS provide automated metrics for both retrieval (recall@k) and generation (faithfulness, answer relevance).

</details>

---

## 6. Further Reading

> Note to maintainers: add these entries to `resources/reading-list.md` under a "RAG" heading.

| Title | URL | Why relevant |
|---|---|---|
| *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* (Lewis et al., 2020) | https://arxiv.org/abs/2005.11401 | Original RAG paper; introduces the dense retriever + generator architecture |
| *RAGAS: Automated Evaluation of Retrieval Augmented Generation* | https://arxiv.org/abs/2309.15217 | Metrics for evaluating RAG pipelines end-to-end |
| Chroma documentation | https://docs.trychroma.com | Practical reference for the vector store used in all track labs |
| *Chunking Strategies for LLM Applications* (Pinecone blog) | https://www.pinecone.io/learn/chunking-strategies/ | Practical comparison of chunking methods with benchmarks |
| *Lost in the Middle: How Language Models Use Long Contexts* | https://arxiv.org/abs/2307.03172 | Explains why context placement matters for retrieval quality |
| sentence-transformers model hub | https://www.sbert.net/docs/pretrained_models.html | All-MiniLM-L6-v2 and other free local embedding models |

**Suggested glossary terms to add to `resources/glossary.md`:**
- RAG (Retrieval-Augmented Generation)
- Ingestion pipeline
- Chunking / chunk overlap
- Dense retrieval
- Sparse retrieval (BM25)
- Hybrid retrieval
- Re-ranking / cross-encoder
- Grounding
- Context stuffing (anti-pattern)
- RAGAS

---

## 7. Key Takeaways

- **RAG solves the knowledge gap**: LLMs have fixed training data; RAG injects fresh, private, authoritative text at inference time without retraining.
- **Two pipelines**: ingestion (offline, batch: Load → Chunk → Embed → Store) and inference (online, per-query: Retrieve → Augment → Generate).
- **Chunk size is a precision dial**: too large → embedding drift; too small → insufficient context. Overlap is almost always worth the overhead.
- **Prompt design determines grounding**: an explicit "answer only from context" + "I don't know" instruction is the single highest-leverage line in a RAG system.
- **Citations are a first-class feature**: put source metadata inside the context block so the model can cite while it answers.
- **RAG vs fine-tuning vs long-context**: RAG wins for large, dynamic, private corpora; fine-tuning wins for style/task adaptation; long-context wins for small stable document sets.
- **Retrieval and generation fail independently**: debug them separately using the retrieval oracle test.
