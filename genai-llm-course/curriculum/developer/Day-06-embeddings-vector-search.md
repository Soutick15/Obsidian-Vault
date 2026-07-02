# Day 6 — Embeddings & Vector Search

**Track:** Developer | **Position in course:** 6 of 15  
**Prerequisites:** Days 1–5 (LLM basics, tokens/embeddings intro, transformers, decoding/model selection, prompting, APIs/streaming/tools)

---

## 1. Learning Objectives

By the end of Day 6 you will be able to:

1. Explain the difference between semantic search and keyword (lexical) search and choose the right approach for a given use case.
2. Select an appropriate embedding model (local `sentence-transformers` vs. API-hosted) based on latency, cost, privacy, and dimensionality requirements.
3. Describe how vector databases (Chroma, FAISS, pgvector) store and retrieve embeddings, and choose between them.
4. Apply and compare similarity metrics — cosine, dot product, Euclidean — and understand when each is appropriate.
5. Explain approximate nearest-neighbor (ANN) algorithms (HNSW, IVF) and articulate the speed/recall tradeoff they manage.

---

## 2. Concept Reading

### 2.1 Keyword Search vs. Semantic Search

**Keyword (lexical) search** — systems like Elasticsearch or `LIKE` in SQL — match documents that contain the exact query terms. They are fast, interpretable, and great when users know the precise vocabulary. They fail when a document uses synonyms or paraphrases the concept differently.

**Semantic search** works on meaning. A query like *"What is the parental leave policy?"* can match a document that says *"secondary caregiver leave is 6 weeks paid"* even with zero shared words, because both are encoded as nearby vectors in embedding space.

The tradeoff: keyword search is deterministic and explainable; semantic search handles vocabulary mismatch but can surface plausible-sounding but wrong matches. Production systems often combine both — a technique called **hybrid search**.

---

### 2.2 Embedding Models

An **embedding model** is a neural network that maps a piece of text to a fixed-length vector (a list of floating-point numbers) such that semantically similar texts are close together in that space.

#### Local models — `sentence-transformers`

The `sentence-transformers` library (built on Hugging Face Transformers) lets you run embedding models entirely on your machine. The most common general-purpose model is:

| Model | Dimensions | Size | Best for |
|---|---|---|---|
| `all-MiniLM-L6-v2` | 384 | ~22 MB | Fast, English, general |
| `all-mpnet-base-v2` | 768 | ~420 MB | Higher quality, slower |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | ~118 MB | Multilingual |

**When to use local models:**
- No API key required — zero cost at inference time.
- Data stays on-premises (privacy/compliance).
- Low latency for batch ingestion of thousands of documents.
- Good enough for most internal knowledge-base tasks.

#### API-hosted embeddings

Cloud providers (Anthropic via third-party partners, OpenAI `text-embedding-3-small/large`, Cohere `embed-v3`) offer higher-dimensional, more capable models (up to 3072 dimensions) but require network round-trips and charge per token.

**When to use API embeddings:**
- You need state-of-the-art quality and can tolerate cost/latency.
- You are already calling the API for other tasks.
- You need multi-modal embeddings (text + image).

**Dimensions matter:** Higher dimensions capture richer meaning but cost more memory and compute. A 1536-dim vector takes 4× the storage of a 384-dim vector. Unless you have evidence of quality gains, start with a smaller local model.

---

### 2.3 Vector Databases

A vector database stores embedding vectors alongside metadata and provides an **approximate nearest-neighbor (ANN)** index so you can find the top-k most similar vectors to a query vector very quickly — without scanning every document.

#### Chroma

- Embedded (runs in-process) or client-server mode.
- Persists to disk with a single path argument.
- Native Python API; great for prototyping and small-to-medium corpora (<10 M vectors).
- Supports metadata filtering, hybrid queries.

#### FAISS (Facebook AI Similarity Search)

- Library (not a full database) written in C++ with Python bindings.
- Extremely fast; runs entirely in memory by default.
- Needs custom serialization (`faiss.write_index`) for persistence.
- No built-in metadata filtering — you manage a parallel document store yourself.
- Best for: pure similarity search at scale when you control the full stack.

#### pgvector

- PostgreSQL extension; adds a `vector` column type and ANN operators.
- Lets you filter, join, and sort using full SQL alongside semantic search.
- Excellent for production when you already operate Postgres and need metadata-rich queries.
- Requires a running Postgres instance.

---

### 2.4 Similarity Metrics

Given two vectors **a** and **b**:

| Metric | Formula (intuition) | When to use |
|---|---|---|
| **Cosine similarity** | `dot(a,b) / (‖a‖ · ‖b‖)` | Magnitude-invariant; use for semantic search where length of text varies; range [−1, 1] |

> **Note:** In practice, sentence-transformer models produce non-negative activations, so cosine similarities between their outputs typically fall in **[0, 1]** rather than the full [−1, 1] theoretical range.
| **Dot product** | `sum(a_i · b_i)` | Fast; rewards both direction *and* magnitude; use when vectors are pre-normalised (cosine ≡ dot on unit vectors) |
| **Euclidean distance** | `sqrt(sum((a_i − b_i)²))` | Geometric distance; sensitive to magnitude; common in image similarity; smaller = more similar |

For typical NLP embedding search, **cosine similarity** is the standard default because it ignores vector magnitude (which can vary with document length or embedding norm) and focuses on direction (meaning).

---

### 2.5 Approximate Nearest Neighbor (ANN) — HNSW and IVF

Brute-force nearest-neighbor search requires comparing the query vector against every stored vector — O(n·d) operations. With millions of documents and 768-dim vectors this is too slow.

**ANN algorithms** trade a small amount of recall for massive speed gains.

#### HNSW (Hierarchical Navigable Small World)

Builds a multi-layer proximity graph during indexing. Each node connects to its nearest neighbours; upper layers are sparse (fast navigation), lower layers are dense (fine-grained search).

- **Search:** Start at top layer, greedily walk to nodes closer to the query, descend layers until the bottom.
- **Speed:** Sub-millisecond queries even at millions of vectors.
- **Recall:** Typically 95–99 % at good parameter settings (`ef_construction`, `M`).
- **Downside:** Index lives in RAM; can be memory-intensive for very large corpora.

#### IVF (Inverted File Index) + PQ (Product Quantization)

Divides the embedding space into `n_lists` clusters (via k-means). At query time, only the nearest `n_probe` cluster centroids are searched.

- **Speed:** Fast when `n_probe` is small.
- **Recall:** Lower recall if the query falls near a cluster boundary.
- **Downside:** Requires a training step (clustering) before indexing.
- **IVF + PQ** compresses vectors further (4–32× smaller), enabling billion-scale search on commodity hardware.

#### Speed / Recall Tradeoff

Every ANN algorithm has parameters that let you slide along the speed-recall curve:

```
High recall  ←────────────────────→  High speed
 (brute-force)                         (fewer probes/hops)
```

For a production knowledge base, recall@10 ≥ 95 % at < 10 ms latency per query is a typical starting target.

---

### 2.6 Metadata Filtering

Raw semantic search ranks by similarity alone. **Metadata filtering** lets you pre- or post-filter on structured fields stored alongside each vector:

```python
# Chroma example: only search within the "HR" category
results = collection.query(
    query_embeddings=[query_vec],
    n_results=5,
    where={"category": "HR"}
)
```

Common metadata fields: document source file, author, date, department, language. Pre-filtering (before ANN) reduces the search space; post-filtering (after ANN) is simpler but may return fewer than k results.

---

### 2.7 Chunking's Effect on Retrieval (RAG Preview)

Embedding an entire 10-page document as one vector averages out all the meaning — the resulting vector is a blurry summary. **Chunking** splits documents into smaller passages (e.g., 200–500 tokens) before embedding, so each vector represents a focused idea.

The chunk size directly affects retrieval quality:

| Chunk size | Effect |
|---|---|
| Too small (e.g., 50 tokens) | Vectors lack context; matching is noisy |
| Optimal (200–500 tokens) | Good semantic density; matches focused on one concept |
| Too large (e.g., 2000 tokens) | Diluted meaning; misses specific facts |

In Day 8 (RAG) you will build a full pipeline. Today's lab uses paragraph-level chunks to preview this idea.

---

## 3. Hands-on Lab

**Location:** `labs/developer/day-06/`

**Goal:** Ingest the shared Acme Corp HR corpus, embed it with a local sentence-transformer model, store it in Chroma, and run semantic queries with metadata filtering.

**No API key required.** All computation is local.

### Files

| File | Purpose |
|---|---|
| `README.md` | Lab overview and run instructions |
| `requirements.txt` | Python dependencies |
| `starter.py` | Skeleton with `TODO` comments — work through these |
| `solution.py` | Complete reference implementation |

### Run the solution

```bash
# From the repo root
python labs/developer/day-06/solution.py
```

### What you'll build

1. Load all 12 HR markdown documents from `data/hr-corpus/`.
2. Split each document into paragraph-level chunks; attach source-filename metadata.
3. Embed chunks locally with `all-MiniLM-L6-v2`.
4. Persist to a Chroma collection at `labs/developer/day-06/.chroma_db/`.
5. Run 5 semantic queries and print top-3 results with similarity scores.
6. Demonstrate metadata filtering (restrict query to a specific source document).

---

## 4. Self-Check Quiz

**Instructions:** Answer from memory, then check the answers below.

**Q1.** A user searches for *"paternity leave"* but the policy document only uses the phrase *"secondary caregiver leave."* Which search approach will find it — keyword or semantic? Why?

<details>
<summary>Show answer</summary>

Semantic search. Both phrases occupy nearby positions in embedding space because they describe the same concept, even though they share no words. Keyword search would return zero results since the exact term is absent.

</details>

---

**Q2.** `all-MiniLM-L6-v2` produces 384-dimensional vectors. A 768-dim model doubles the dimensions. How much more memory does the 768-dim version require to store 1 million vectors (float32)?

<details>
<summary>Show answer</summary>

1M × 384 × 4 bytes = 1.54 GB vs 1M × 768 × 4 bytes = 3.07 GB — exactly 2× more. Dimensions scale memory linearly.

</details>

---

**Q3.** You have unit-normalized embedding vectors. Is cosine similarity equivalent to dot product in this case? Why?

<details>
<summary>Show answer</summary>

Yes. Cosine similarity = dot(a,b) / (‖a‖·‖b‖). When both vectors have ‖a‖ = ‖b‖ = 1, the denominator is 1, so cosine = dot. Chroma normalizes by default, which is why both metrics give identical ranking on its collections.

</details>

---

**Q4.** What is the main difference between HNSW and IVF-based ANN indexes?

<details>
<summary>Show answer</summary>

HNSW builds a graph of proximity connections and navigates it at query time — no training step needed, high recall, memory-resident. IVF partitions the space into clusters via k-means (requires training) and at query time searches only the nearest clusters — better for very large indexes where memory is constrained, but recall depends on `n_probe`.

</details>

---

**Q5.** Why is chunking important before embedding long documents?

<details>
<summary>Show answer</summary>

Embedding a long document averages its meaning into one vector, which is too diffuse to match specific query terms. Chunking into 200–500-token passages gives each vector a focused semantic meaning, enabling precise retrieval of the exact passage that answers a query.

</details>

---

**Q6.** A metadata filter narrows Chroma search to `{"department": "engineering"}`. The collection has 50,000 vectors total but only 2,000 in engineering. What is the practical benefit?

<details>
<summary>Show answer</summary>

The ANN search is effectively over 2,000 vectors instead of 50,000, improving speed and reducing irrelevant results. Even if Chroma still evaluates all candidates and post-filters, the user gets results restricted to the relevant department, improving precision.

</details>

---

**Q7.** When would you choose pgvector over Chroma or FAISS?

<details>
<summary>Show answer</summary>

When you already run PostgreSQL in production and need to combine semantic similarity with SQL — for example, filtering by date range, joining with a users table, or enforcing row-level security. pgvector avoids running a separate vector database service.

</details>

---

**Q8.** Euclidean distance and cosine similarity can give different rankings for the same query. Give an example scenario where this matters.

<details>
<summary>Show answer</summary>

If two documents discuss the same topic but one is much longer (resulting in a higher-magnitude embedding in un-normalized space), Euclidean distance would rank the shorter document as more distant even though it's on the same topic. Cosine similarity ignores magnitude, so it correctly ranks both as equally relevant. Always normalize embeddings before using Euclidean distance for semantic search.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1. Why does cosine similarity outperform Euclidean distance for most text embedding tasks, even though Euclidean is the more "natural" notion of distance?**

<details>
<summary>Show answer</summary>

Text embedding models learn to encode meaning in the *direction* of a vector, not its magnitude. The magnitude can vary with sequence length, padding artifacts, or the model's internal scaling. Euclidean distance penalizes magnitude differences regardless of whether they carry semantic information. Cosine similarity projects both vectors onto the unit sphere first, removing the confounding magnitude factor and comparing pure direction. Additionally, embedding spaces are high-dimensional (128–3072 dims): in high dimensions, Euclidean distances between random points concentrate around the same value (the "curse of dimensionality"), making them poorly discriminative. The angular separation cosine measures remains meaningful in high dimensions.

</details>

---

**Q2. HNSW claims 95–99 % recall. What causes the missing 1–5 %, and how do you tune it away?**

<details>
<summary>Show answer</summary>

HNSW performs a greedy graph walk — it follows edges toward the query but can get trapped in local minima if the graph does not have enough long-range edges. The parameter `M` (number of bidirectional links per node) controls graph connectivity: higher M means more edges, fewer local minima, but more memory and slower indexing. The parameter `ef_construction` controls how many candidates are evaluated *during* index build: higher values improve recall at the cost of longer build time. At query time, `ef` (or `ef_search`) controls how many candidates are explored per hop: increase it for better recall at the cost of slower search. Typical production settings: M=16–48, ef_construction=200–400, ef=100–200 for 99 %+ recall.

</details>

---

**Q3. What is the difference between a vector *library* (FAISS) and a vector *database* (Chroma, pgvector)? When does the distinction matter?**

<details>
<summary>Show answer</summary>

A library like FAISS provides the core indexing and search algorithms as a C++ library with Python bindings. It does not manage persistence, metadata, multi-tenancy, access control, or CRUD updates — you are responsible for all of that. A vector database wraps an ANN library with a storage layer (SQLite, RocksDB, Postgres), a metadata store, an API (REST or Python client), and often replication/sharding. The distinction matters in production: if you need to add/remove/update documents, filter by metadata, handle concurrent readers, or manage schema migrations, a database is far simpler. FAISS shines in batch offline pipelines where you rebuild the index from scratch periodically and don't need any of those services.

</details>

---

**Q4. How does chunk size affect retrieval precision vs. recall, and what chunking strategy would you recommend for a corpus of HR policy documents?**

<details>
<summary>Show answer</summary>

Smaller chunks increase *precision* — each retrieved passage is tightly focused on one idea, minimising noise. Larger chunks increase *recall* — more context is present in each chunk, reducing the chance of splitting an answer across two chunks. The optimal size depends on the query pattern. For HR policy documents, which tend to be structured with clear headings and numbered lists, a good strategy is: (1) chunk by paragraph or list-item boundary rather than a fixed token count, so you don't split mid-sentence; (2) target 150–300 tokens per chunk; (3) add a 20–50 token overlap between adjacent chunks so that answers straddling a boundary are still retrievable. Also embed the section heading as a prefix to every chunk's text so the query context is preserved.

</details>

---

**Q5. Explain the concept of "semantic drift" when using metadata filters. How might filtering on `source_file` reduce recall even when it seems like it should help?**

<details>
<summary>Show answer</summary>

Metadata filtering restricts the search space to a subset of vectors. If the policy you are looking for is cross-referenced across multiple documents — for example, parental leave appears in both `leave-and-pto-policy.md` and `benefits-and-insurance.md` — filtering to only the first file misses the second document's perspective. More subtly, a user may not know which file contains the answer. Forcing them to specify the source defeats the purpose of semantic search. A better pattern: use metadata filters as an optional *refinement* (e.g., filter by date or language) rather than a mandatory scope constraint. For navigation ("I know this is in the PTO doc"), filtering is appropriate; for open-ended Q&A it often hurts recall.

</details>

---

**Q6. Why do high-dimensional embeddings from API providers (1536 or 3072 dims) not always outperform small local models (384 dims) on domain-specific retrieval tasks?**

<details>
<summary>Show answer</summary>

Large-dimensional API models are trained on broad corpora to achieve high scores on general benchmarks (MTEB/BEIR). Domain-specific corpora — like internal HR documents — use jargon, acronyms, and policy structures that may be underrepresented in that training data. A 384-dim model fine-tuned on similar HR/legal text can outperform a 3072-dim general model because it has learned the right similarity structure for that domain. Additionally, higher dimensions increase storage cost, retrieval latency, and Chroma/FAISS index size, which matters when running on modest hardware. The practical advice: benchmark on a held-out sample of your actual corpus before assuming bigger = better.

</details>

---

**Q7. What is "hybrid search" and when should you implement it over pure semantic search?**

<details>
<summary>Show answer</summary>

Hybrid search combines a lexical score (BM25 or TF-IDF from a keyword index) with a semantic score (cosine similarity from a vector index), usually via reciprocal rank fusion (RRF) or weighted linear combination. It is particularly valuable when: (1) users search with exact product codes, names, or IDs that embeddings blur together semantically; (2) the corpus contains short, keyword-rich entries (FAQs, table rows) where semantic context is thin; (3) you need to support both power users who write precise queries and casual users who describe concepts vaguely. Most production search stacks (Elasticsearch 8.x `knn` + BM25, Weaviate hybrid, Chroma + rank fusion layer) implement hybrid search for exactly this reason.

</details>

---

**Q8. A Chroma collection is queried with `n_results=5` but only 3 results are returned. What are the likely causes?**

<details>
<summary>Show answer</summary>

Three causes: (1) the collection contains fewer than 5 documents/chunks total; (2) a metadata `where` filter eliminates all but 3 matching records; (3) the collection is using a distance threshold and only 3 vectors fall within the maximum allowed distance. Chroma will silently return fewer than `n_results` rather than raise an error in all three cases. To debug: print `collection.count()` before querying, remove filters to test without them, and check whether a `where_document` or distance cutoff is applied.

</details>

---

**Q9. Explain the IVF training step. Why does it exist, and what goes wrong if you skip it or train on too little data?**

<details>
<summary>Show answer</summary>

IVF partitions embedding space into `n_lists` Voronoi cells using k-means clustering on a representative sample of your data. The centroids of those cells are the "posting list" entries — at query time you find the nearest centroids and only search those cells. The training step is necessary because the partition must reflect the actual distribution of your data; centroids computed on random data would cluster poorly for your domain's embedding distribution. If you train on too few samples (rule of thumb: at least 39× `n_lists` samples, ideally much more), the clusters are unrepresentative, cells are unevenly populated, and recall drops significantly. FAISS raises a warning if the training set is too small. HNSW avoids this issue entirely by building its graph incrementally as documents are added.

</details>

---

**Q10. What privacy and compliance considerations should guide the choice between local embedding models and API-hosted embeddings for an internal HR corpus?**

<details>
<summary>Show answer</summary>

HR documents often contain sensitive personal data: salary ranges, performance ratings, medical leave, disciplinary records. Sending this data to a third-party API creates several concerns: (1) **data residency** — the API provider may process or cache data in jurisdictions not covered by your data-processing agreements; (2) **GDPR/CCPA** — employee data may be subject to subject-access or deletion rights, which are harder to enforce once data has left your control; (3) **contract risk** — most API providers use your queries to improve their models unless you explicitly opt out (and even opt-out policies can change); (4) **breach surface** — a network call is another attack surface. Local models like `sentence-transformers` keep all data on-premises, eliminate network latency, and cost nothing per query. For internal HR corpora, local embeddings are the strongly recommended default unless you have evaluated and mitigated all of the above risks.

</details>

---

## 6. Further Reading

| Resource | Why read it |
|---|---|
| [SBERT: Sentence-BERT paper (Reimers & Gurevych, 2019)](https://arxiv.org/abs/1908.10084) | Original paper behind `sentence-transformers`; explains the siamese fine-tuning approach |
| [HNSW paper (Malkov & Yashunin, 2018)](https://arxiv.org/abs/1603.09320) | The algorithm behind Chroma's default index; explains the layered graph construction |
| [BEIR benchmark](https://github.com/beir-cellar/beir) | Heterogeneous retrieval benchmark for comparing embedding models on real tasks |
| [Chroma docs — Getting Started](https://docs.trychroma.com/getting-started) | Official quickstart for collections, queries, metadata filtering |
| [FAISS wiki](https://github.com/facebookresearch/faiss/wiki) | Comprehensive guide to IVF, PQ, HNSW configurations and index factory strings |
| [pgvector README](https://github.com/pgvector/pgvector) | SQL-native vector search — operators, indexing options, performance tips |
| [Pinecone "What is a Vector Database?" guide](https://www.pinecone.io/learn/vector-database/) | Accessible visual explainer of ANN concepts (vendor-neutral content) |
| [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) | Compare embedding models across retrieval, clustering, classification tasks |

---

## 7. Key Takeaways

1. **Semantic search matches meaning, not words** — it handles synonyms and paraphrases that break keyword search.
2. **Local models (`all-MiniLM-L6-v2`) are fast, free, and private** — start there; only move to API embeddings when you have evidence of quality gains.
3. **Vector databases (Chroma, FAISS, pgvector) differ in their operational model** — choose Chroma for prototyping, FAISS for high-throughput batch search, pgvector when you already run Postgres.
4. **Cosine similarity is the default metric** for text — it ignores magnitude and focuses on direction (meaning).
5. **ANN algorithms (HNSW, IVF) trade a small amount of recall for orders-of-magnitude speed** — tune `M`, `ef`, and `n_probe` to slide along the tradeoff curve.
6. **Chunk your documents before embedding** — 200–500 tokens per chunk gives focused, retrievable units of meaning; too large blurs the signal.
7. **Metadata filtering is a precision tool** — useful for scoped queries but can hurt recall for open-ended questions.
8. **Day 8 (RAG) builds directly on today** — today you built the retrieval half; next week you add the generation half.
