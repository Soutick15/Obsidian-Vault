# Day 8 — Advanced RAG: Hybrid Search, Re-Ranking, Query Transformation & Evaluation

**Track:** Developer | **Week:** 2 | **Prerequisites:** Day 7 (Basic RAG with Chroma)

---

## 1. Objectives

By the end of Day 8 you will be able to:

- Explain *why* naive dense-only retrieval fails and quantify the gaps
- Implement **hybrid retrieval** by fusing dense (bi-encoder) and sparse (BM25) scores
- Add a **cross-encoder re-ranker** to improve result ordering after initial retrieval
- Describe query transformation strategies (rewriting, expansion, HyDE, multi-query) and when each helps
- Apply **metadata filtering** and better chunking to reduce noise
- Name the core RAG failure modes and map them to mitigations
- Compute **Hit@k** to compare naive vs. improved retrieval pipelines

---

## 2. Concept Reading

### 2.1 Why Naive RAG Underperforms

Basic RAG (Day 7) encodes queries and documents with a **bi-encoder** and retrieves by cosine/dot-product similarity. This works reasonably well but breaks down when:

- **Lexical mismatch** — The query uses exact product codes, names, or acronyms the embedder has never linked to the document text.
- **Semantic drift** — Short queries give vague embeddings that rank semantically adjacent but irrelevant chunks highly.
- **Chunking artifacts** — Key facts straddle chunk boundaries; neither chunk alone is retrievable.
- **Missing context** — The top-k window is too small to include the relevant chunk (recall failure), or the right chunk exists but is buried (rank failure).

### 2.2 Hybrid Search: Dense + Sparse (BM25)

**Dense retrieval** (bi-encoders like `all-MiniLM-L6-v2`) captures semantic meaning.  
**Sparse retrieval** (BM25, TF-IDF) captures exact lexical overlap.

Neither alone dominates across all query types. **Hybrid search fuses both scores:**

```
hybrid_score(d, q) = α × dense_score(d, q) + (1 - α) × bm25_score(d, q)
```

Typical values: `α ∈ [0.4, 0.7]`. Tune on a dev set.

> **Important:** dense (cosine) and BM25 scores live on entirely different scales, so both lists must be normalised (e.g. min-max or softmax per list) before the weighted sum is meaningful; RRF (used in the lab) sidesteps this problem by operating on ranks rather than raw scores.

**Reciprocal Rank Fusion (RRF)** is an alternative that avoids score-scale mismatches:

```
rrf(d) = Σ  1 / (k + rank_i(d))
```

where the sum is over retrieval systems and `k ≈ 60` is a stability constant.

### 2.3 Re-Ranking with a Cross-Encoder

A **bi-encoder** independently embeds query and document — fast but less accurate.  
A **cross-encoder** takes `(query, document)` as a single concatenated input and scores their relevance jointly — slower but far more accurate.

**Two-stage retrieval:**
1. Retrieve top-`N` candidates (e.g. N=20) cheaply with the hybrid retriever.
2. Score all N pairs with the cross-encoder; re-sort; keep top-`k` (e.g. k=5).

Common cross-encoders: `cross-encoder/ms-marco-MiniLM-L-6-v2` (English, MS MARCO fine-tuned).

### 2.4 Query Transformations

| Technique | What it does | When it helps |
|---|---|---|
| **Query rewriting** | LLM reformulates the query for better retrieval | Vague or ambiguous user queries |
| **Query expansion** | Add synonyms / related terms before retrieval | Lexical mismatch, domain jargon |
| **HyDE** (Hypothetical Document Embeddings) | LLM generates a *hypothetical answer*; embed that instead of the query | Queries phrased as questions, not statements |
| **Multi-query** | Generate N paraphrases; retrieve for each; union results | Broad queries, multiple intents |

HyDE intuition: document corpora contain *statements of fact*, not questions — embedding a hypothetical answer shifts the query into the same semantic space as the corpus.

### 2.5 Metadata Filtering

Pair semantic retrieval with structured filters on document metadata (department, date, policy version, document type). This **shrinks the search space** before embedding similarity is computed, improving both speed and precision.

Example (Chroma syntax):
```python
results = collection.query(
    query_embeddings=[q_emb],
    where={"doc_type": "policy"},
    n_results=10,
)
```

### 2.6 Better Chunking Strategies

| Strategy | Description |
|---|---|
| Fixed-size with overlap | Simple; overlap prevents boundary misses |
| Sentence / paragraph boundary | Preserves grammatical units |
| Semantic chunking | Split when sentence embedding similarity drops |
| Hierarchical (parent-child) | Store small chunks for retrieval, return parent for context |
| Document-level summarization | Prepend a chunk with a doc summary for coarse retrieval |

For the HR corpus, paragraph-boundary chunking with a small overlap outperforms fixed-token chunking because facts are cleanly delimited by policy bullets.

### 2.7 RAG Failure Modes

| Failure Mode | Description | Mitigation |
|---|---|---|
| **Missed retrieval** | Correct chunk not in top-k | Increase N, use hybrid search |
| **Wrong chunk** | Irrelevant chunk retrieved instead of correct one | Re-ranking, metadata filters |
| **Lost-in-the-middle** | Correct chunk retrieved but buried in the context window | Re-rank to surface it; reduce context window size |
| **Hallucination despite context** | Model ignores retrieved context or fabricates details | Prompt engineering; faithfulness eval |
| **Stale context** | Retrieved doc is outdated version | Metadata date filtering; versioned ingestion |

### 2.8 Introduction to RAG Evaluation Metrics

*(The QA track covers this in depth. Here we introduce the vocabulary.)*

| Metric | Definition |
|---|---|
| **Faithfulness / Groundedness** | Fraction of answer claims that are supported by retrieved context |
| **Context Precision** | Fraction of retrieved chunks that are relevant to the question |
| **Context Recall** | Fraction of ground-truth relevant chunks that were retrieved |
| **Answer Relevance** | How well the generated answer addresses the question (regardless of grounding) |
| **Hit@k** | Binary: was the correct document/chunk in the top-k results? Avg over eval set. |

Day 8 lab focuses on **Hit@k** because it measures retrieval quality without requiring a generation step — we can evaluate entirely locally with no API key.

---

## 3. Hands-on Lab

**Directory:** `labs/developer/day-08/`

**Goal:** Extend Day-7 RAG to hybrid retrieval + cross-encoder re-ranking; evaluate naive vs. improved pipeline on the HR corpus using Hit@k.

### Setup

```bash
cd /path/to/AI_Training
pip install -r labs/developer/day-08/requirements.txt
```

### Run the starter (with TODOs)

```bash
python labs/developer/day-08/starter.py
```

### Run the complete solution

```bash
python labs/developer/day-08/solution.py
```

Expected output: a table comparing Naive Dense vs. Hybrid+Rerank retrieval across the labeled evaluation set (Hit@1, Hit@3, Hit@5).

See `labs/developer/day-08/README.md` for full instructions.

---

## 4. Self-Check Quiz

**Q1.** What is the fundamental limitation of a bi-encoder for ranking?

<details>
<summary>Show answer</summary>

It encodes query and document *independently*, so fine-grained token-level interactions between them are lost. A cross-encoder sees the full pair together and can model interactions at the cost of being O(N) per query.

</details>

---

**Q2.** In Reciprocal Rank Fusion, what does the constant `k` do?

<details>
<summary>Show answer</summary>

It dampens the advantage of rank-1 results and provides numerical stability. Higher `k` reduces the impact of top ranks; `k=60` is a common default.

</details>

---

**Q3.** Give one scenario where BM25 beats dense retrieval.

<details>
<summary>Show answer</summary>

Queries containing exact policy codes, employee IDs, or uncommon acronyms that the embedding model was not trained on. BM25 rewards exact lexical overlap regardless of whether the term was seen at training time.

</details>

---

**Q4.** What is HyDE, and why does it help?

<details>
<summary>Show answer</summary>

Hypothetical Document Embeddings: an LLM generates a hypothetical answer to the query; that answer is embedded instead of the raw query. It helps because corpus documents are *statements*, not questions — the hypothetical answer sits in the same embedding subspace as real documents.

</details>

---

**Q5.** What does Hit@3 measure?

<details>
<summary>Show answer</summary>

The proportion of queries in the evaluation set for which the correct document/chunk appears in the top-3 retrieved results.

</details>

---

**Q6.** Name two RAG failure modes and their mitigations.

<details>
<summary>Show answer</summary>

(a) *Missed retrieval* — correct chunk never retrieved; fix with hybrid search or larger N. (b) *Lost-in-the-middle* — correct chunk retrieved but buried; fix with re-ranking to surface it.

</details>

---

**Q7.** Why should you use a two-stage approach (retrieve-then-rerank) rather than running the cross-encoder over the entire corpus?

<details>
<summary>Show answer</summary>

Cross-encoders require O(N) forward passes — one per document. For a large corpus this is prohibitively slow at query time. Limiting to the top-N candidates from a fast retriever keeps latency acceptable.

</details>

---

**Q8.** What is the difference between context precision and context recall?

<details>
<summary>Show answer</summary>

Precision measures how many of the *retrieved* chunks are actually relevant (signal-to-noise). Recall measures how many of the *truly relevant* chunks were retrieved (coverage). Optimising only precision risks missing facts; optimising only recall floods the context window.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1: Why does naive RAG underperform on exact-match queries like policy codes or employee numbers?**

<details>
<summary>Show answer</summary>

Bi-encoders are trained to maximise cosine similarity between semantically related text. Exact tokens like `"Policy-IT-004"` may not appear in training pairs that teach the model this string is similar to queries asking about IT policies. BM25 uses inverted-index term frequencies and has no such blind spot — it will always rank a document containing the exact string above documents that do not.

</details>

---

**Q2: When fusing dense and BM25 scores, how do you handle the fact that their numeric ranges differ?**

<details>
<summary>Show answer</summary>

You have three options: (1) **Min-max normalise** each score list before weighting; (2) **Softmax normalise** each ranked list; (3) use **Reciprocal Rank Fusion** which operates purely on rank positions, bypassing score-scale issues entirely. RRF is the most robust in practice because it does not require hyperparameter tuning for scale.

</details>

---

**Q3: Can a cross-encoder hurt retrieval quality? Under what conditions?**

<details>
<summary>Show answer</summary>

Yes. If the initial candidate set (top-N from Stage 1) does not contain the correct chunk, re-ranking cannot recover it — the cross-encoder can only reorder what it was given. Also, cross-encoders fine-tuned on general web data (e.g. MS MARCO) may not handle domain-specific HR jargon well; a fine-tuned or in-domain model is preferable. Finally, if N is too small relative to corpus size, the cross-encoder may waste computation reranking irrelevant candidates.

</details>

---

**Q4: Explain the multi-query strategy and describe a failure mode it introduces.**

<details>
<summary>Show answer</summary>

Multi-query generates several paraphrases of the original query via an LLM, retrieves separately for each, then unions (or RRF-merges) results. The benefit is coverage across different wordings. The failure mode: if the LLM generates paraphrases that drift from the original intent — or that are nearly identical — you retrieve duplicates or off-topic chunks that dilute precision. Deduplication (e.g. by chunk ID) and a re-ranker help mitigate this.

</details>

---

**Q5: How does metadata filtering interact with chunk-level embedding retrieval?**

<details>
<summary>Show answer</summary>

Metadata filtering pre-prunes the search space to only chunks whose structured attributes (doc_type, date, department) match the query constraints. Embedding retrieval then runs on this smaller set. The interaction is important: filtering *before* embedding comparison improves both speed and precision, but over-filtering can exclude the correct chunk if metadata is incorrectly assigned or the filter is too strict. Pre-filtering is correct when metadata is reliable; otherwise use post-retrieval soft boosting.

</details>

---

**Q6: What does "lost-in-the-middle" mean, and why is it an LLM problem rather than a retrieval problem?**

<details>
<summary>Show answer</summary>

LLMs attend unevenly to a long context window — they are most reliable about information near the *beginning* and *end* of the window; material in the middle receives less attention weight. So even if the correct chunk is retrieved, placing it in the middle of a 10-chunk context causes the model to under-utilise it. The fix is to re-rank so the most relevant chunk surfaces to position 1, or to reduce the context window so there is no "middle" to get lost in.

</details>

---

**Q7: Why is Hit@k a practical starting point for RAG evaluation in a no-API-key environment?**

<details>
<summary>Show answer</summary>

Hit@k measures only whether the correct source document/chunk appeared in the top-k results. It requires a labeled set (query → expected document) but no generation step and no LLM-as-judge. It is deterministic, fast, free, and directly measures retrieval quality — the component we are improving today. Faithfulness and answer relevance metrics require generating answers, which needs a language model.

</details>

---

**Q8: What is the risk of evaluating RAG purely on answer quality rather than retrieval quality?**

<details>
<summary>Show answer</summary>

Answer quality conflates retrieval quality and generation quality. A pipeline with poor retrieval can still score well on answer quality if the LLM falls back on parametric knowledge (hallucination). Conversely, a pipeline with excellent retrieval can score poorly on answer quality if the generation model paraphrases poorly. Measuring retrieval separately (Hit@k, context recall) isolates the retrieval component so you can debug and improve it independently.

</details>

---

## 6. Further Reading

### Core Papers
- Robertson, S. & Zaragoza, H. (2009). *The Probabilistic Relevance Framework: BM25 and Beyond*. Foundations and Trends in Information Retrieval.
- Nogueira, R. & Cho, K. (2019). *Passage Re-ranking with BERT*. arXiv:1901.04085
- Ma, X. et al. (2023). *Zero-Shot Listwise Document Reranking with a Large Language Model*. arXiv:2305.02156
- Gao, L. et al. (2022). *Precise Zero-Shot Dense Retrieval without Relevance Labels* (HyDE). arXiv:2212.10496

### Documentation & Libraries
- [rank_bm25 on PyPI](https://pypi.org/project/rank-bm25/) — lightweight BM25 for Python
- [sentence-transformers CrossEncoder](https://www.sbert.net/docs/cross_encoder/usage/usage.html) — cross-encoder usage guide
- [Chroma metadata filtering](https://docs.trychroma.com/guides#filtering-by-metadata) — `where` clause reference
- [RAGAS framework](https://docs.ragas.io/) — automated RAG evaluation (faithfulness, context precision/recall)

### Glossary Additions
| Term | Definition |
|---|---|
| BM25 | Sparse retrieval algorithm scoring term frequency weighted by inverse document frequency with length normalization |
| Bi-encoder | Neural model that independently encodes query and document into fixed vectors; similarity via dot-product/cosine |
| Cross-encoder | Neural model that takes a (query, document) pair as single input; outputs a relevance score |
| Hybrid search | Retrieval combining dense and sparse signals, typically fused via weighted sum or RRF |
| HyDE | Hypothetical Document Embeddings: embed a generated hypothetical answer instead of the raw query |
| RRF | Reciprocal Rank Fusion — rank combination formula: `Σ 1/(k + rank_i)` |
| Hit@k | Proportion of eval queries where the correct item appears in the top-k results |
| Context Precision | Fraction of retrieved chunks relevant to the query |
| Context Recall | Fraction of relevant chunks that were actually retrieved |
| Faithfulness | Fraction of answer claims that are grounded in retrieved context |
| Lost-in-the-middle | LLM failure to attend to context placed in the middle of a long input window |

---

## 7. Key Takeaways

1. **Naive dense-only retrieval has known failure modes** — exact-match queries, domain jargon, and chunk-boundary splits all degrade recall.
2. **Hybrid search (dense + BM25)** gives complementary signals; fusing them with RRF or weighted averaging consistently improves recall at low engineering cost.
3. **Cross-encoder re-ranking** is cheap to add as a second stage — retrieve 20, rerank to 5 — and dramatically improves precision at the top of the ranked list.
4. **Query transformations** (rewriting, HyDE, multi-query) address semantic gaps between how users phrase questions and how facts are stated in documents.
5. **Metadata filtering** shrinks the search space before embedding comparison, improving both speed and precision when metadata is reliable.
6. **RAG evaluation starts with retrieval metrics** (Hit@k, context recall/precision) before you add generation, so you isolate retrieval problems independently.
7. **The QA track goes deeper on faithfulness and answer relevance** — today's focus is retrieval quality, which is the foundation everything else depends on.
