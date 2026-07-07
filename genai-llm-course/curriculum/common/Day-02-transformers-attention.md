# Day 2 — Transformer Architecture & Attention

**Week 1 — Foundations** | Prerequisite: Day 1 (LLM basics, tokens, embeddings)

---

## 1. Learning Objectives

By the end of Day 2 you will be able to:

1. Trace the data flow through a transformer block — from token IDs to output logits — and explain what each sub-layer does.
2. Explain the Query/Key/Value formulation of self-attention and articulate the intuition (not just the formula) behind why it captures context.
3. Distinguish multi-head attention from single-head attention and state why multiple heads help.
4. Compare decoder-only, encoder-only, and encoder-decoder architectures and choose the right one for a given task.
5. Explain the O(n²) cost of attention, why it limits context windows, and name at least two approaches used to extend them.

---
## 2. Concept Reading

### 2.1 The Big Picture — From Tokens to Logits

Almost every modern LLM (GPT, Llama, Gemini, Claude, Mistral, DeepSeek) is based on the **Transformer Architecture** introduced in the 2017 paper:

GPT - Generative pre-trained transformer. Transformer is a generative in nature based on pre-trained data.

On Day 1 you saw that text becomes tokens and tokens become embeddings. 


The transformer takes those embeddings and transforms them through a stack of identical blocks, ultimately producing a probability distribution over the vocabulary at each position.

```
Input text
	↓
[Tokeniser]          "The cat sat" → [464, 3797, 3332]
	↓
[Token Embedding] integer IDs → dense vectors  shape: (seq_len, d_model)
    +
[Positional Encoding] inject order information
	↓
┌────────────────────────────────────┐
│  Transformer Block × N             │
│  ┌──────────────────────────────┐  │
│  │  Multi-Head Self-Attention   │  │
│  │  + Layer Norm + Residual     │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Feed-Forward Network (FFN)  │  │
│  │  + Layer Norm + Residual     │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘
	↓
[Output Linear + Softmax]  → logits / probabilities over vocabulary
```

The model is "just" a function: given a sequence of token vectors, produce a new set of contextualised vectors (and ultimately a next-token prediction).

**Key design choices:**
- `d_model`: dimension of every embedding and hidden vector (e.g., 768 for GPT-2 base).
- `N`: number of stacked blocks (e.g., 12 for GPT-2 base).
- `d_ff`: inner dimension of the feed-forward layer (typically `4 × d_model`).



---

### 2.2 `Self-Attention` — The Core Idea


Imagine you read this sentence:

```text
The animal didn't cross the street because it was too tired.
```

Now to resolve what "it" refers to, you mentally scan back to "animal". 

Before Transformers, people used

- RNN
- LSTM
- GRU

for language processing. These models couldn't understand this relation between words. Earlier models (RNNs) had to remember everything sequentially. This problem is solved by self-attention

#### Self-Attention



Self-Attention is the mechanism of the Transformer. It is used by LLM models to figure out how words relate to each other in a sentence - every token can directly look at every other token in one pass, with learned weights it determines attention scores. 


To do this mathematically, the Transformer assigns three vectors Query, Key, Value (Q, K, V) to every single token .
#### Query, Key, Value (Q, K, V)

Think of a library system analogy:

- **Query (Q):** What word you're looking for e.g., The word "it". Query compares with every Key. In library analogy think like  ("I want books about neural networks"). 

- **Key (K):**  Based on the information the model have, it creates a word's identity label e.g., The word "dog" says: "I am an animal". In library analogy think like the label on each book's cover ("neural networks", "recipes", "history"). 

- **Value (V):** Based on the Query → the model Compare with all Keys  → Generate scores  →Pick important Values. The value is the actual _meaning_ of the word.  In library analogy : The actual content of the book you were looking for. 

The score between token i and j is `Qᵢ · Kⱼ`, and token i's output is a weighted sum of all Vⱼ values.

You compute a relevance score between your query and every key, convert those scores to weights (softmax), and return a weighted blend of the values.


#### Softmax : converts to percentages



In transformer self-attention : Every token simultaneously plays all three roles — it generates its own Q, K, and V vectors by multiplying its embedding by three learned weight matrices (W_Q, W_K, W_V).

**The Result:** The model matches the **Query** with the right **Key**, and blends the **Values** together. That's how the AI knows "it" means "dog."

Every word first becomes an embedding.

```
The → Embedding → [0.2, 0.5, ...] → (Query + Key + Value) 
```

```
Cat → Embedding → [0.7, 0.1, ...] → (Query + Key + Value) 
```

```
sat → Embedding → [0.9, 0.3, ...] → (Query + Key + Value) 
```

---

Enough theory, now we will see how the model actually processes this step-by-step:
#### The Formula

```
Attention(Q, K, V) = softmax( Q · Kᵀ / √dₖ ) · V
```

Step by step for a sequence of length `n` with key / query dimension `d_k` :

```
1. Linear projections:
   Q = X · W_Q     shape: (n, d_k) 
   K = X · W_K     shape: (n, d_k)
   V = X · W_V     shape: (n, d_v)

2. Raw scores (dot products):
   scores = Q · Kᵀ  shape: (n, n)
   scores[i][j] = "how much does token i attend to token j?"

3. Scale:
   scores = scores / sqrt(d_k)
   (prevents dot products from growing too large, keeping softmax gradients healthy)

4. (Optional mask — for decoder only-models)
   scores[i][j] = -inf  if j > i    (can't look at future tokens)

5. Softmax → attention weights:
   weights = softmax(scores, dim=-1)  shape: (n, n)
   Each row sums to 1.

6. Weighted sum of values:
   output = weights · V              shape: (n, d_v)
```

The output for token `i` is a context-aware blend of all token values, weighted by how relevant each was to token `i`'s query.

#### ASCII Attention Weight Matrix (3-token example)

Tokens: ["The", "cat", "sat"]

Row = source token. 
Column = target token.

```

             attends to →
             
            The   cat   sat

The         0.6   0.3   0.1

cat         0.2   0.7   0.1

sat         0.1   0.5   0.4

```

See the above matrix. in the cat row "cat" pays 70% attention to itself and 20% to "The".

These scores are scaled and passed through a Softmax function to obtain attention weights that sum to one. Finally, the weights are used to compute a weighted combination of the Value vectors, producing a new context-aware embedding for each token.

The model learns these weight patterns from data — no human labels required.

---

### 2.3 Why Scaling Matters

Without the `/ √d_k` divisor, dot products grow with `d_k`. For large d_k (e.g., 64), dot products can reach large magnitudes, pushing softmax into regions where gradients nearly vanish. Scaling by `1/√d_k` keeps the input variance to softmax stable at ~1.

---

### 2.4 `Multi-Head` Attention


If you only have one attention mechanism (a single "head"), The one attention head can only focus on one relationship at a time. It might notice that "it" connects to "animal," but miss that "animal" is connected to "cross" (the action).

But a single word can have multiple relationships at once. For example one head reading a sentence, another head focus on grammar, another notices emotion, all heads working simultaneously.

Interview Answer :

>**Multi-Head Attention** extends Self-Attention by running multiple attention mechanisms in parallel. 
>
>Each head has its own Query, Key, and Value projections and learns different types of relationships between tokens, such as syntax, semantics, or long-range dependencies. 
>
>The outputs from all heads are concatenated and passed through a linear layer to produce a richer, context-aware representation.

---

Multi-head attention runs `h` independent attention operations in parallel, then concatenates and projects:

```
head_i = Attention(Q·W_Qi, K·W_Ki, V·W_Vi)

MultiHead(Q, K, V) = Concat(head_1, ..., head_h) · W_O
```

**Why bother?**

Multiple "heads" mean multiple heads looking at the sentence to track different relationships simultaneously:
- Head 1 might track syntactic dependencies (subject → verb).
- Head 2 might track coreference ("it" → "animal").
- Head 3 might track proximity (adjacent words).

GPT-2 base uses `h=12` heads; GPT-3 uses `h=96` heads.

**Practical note:** The total computation is the same as one big head (since d_k_per_head = d_model / h), but the expressivity is dramatically higher. FLOPs are roughly equivalent to one large head, but multi-head adds an extra output projection W_O and its associated parameters.

---

### 2.5 Positional Encoding — Injecting Order

Without position, Self-attention treats a sentence like a random words (token). The model just sees the words even though it has different meaning.


Self-attention computes dot products between Q and K vectors —Self-attention is inherently permutation-invariant  — the same tokens in different orders would produce identical dot-product scores without positional information. 

If you shuffle the words _"Dog bites man"_ to _"Man bites dog"_, even though meaning changes, a pure attention layer sees the exact same mathematical relationships. It doesn't inherently understand word order. That's a problem — word order can change the meaning. 

The fix is Positional encoding, it adds a position-dependent signal to each token embedding before the first block.. Positional Encoding Tells the model the order of tokens

**Original (sinusoidal) positional encoding:**
```
PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
```

Here `i` ranges from 0 to d_model/2 − 1, producing d_model sinusoidal values per position. This encodes position as a unique pattern of sine and cosine waves at different frequencies. The model can learn to read this pattern.

**Modern approaches:**
- **Learned positional embeddings** (GPT-2, BERT): just another embedding table, trained end-to-end. Simpler, works well, but doesn't generalise to lengths beyond what was seen in training.
- **RoPE (Rotary Position Embeddings)** (LLaMA, Mistral, Gemma): encodes position as a rotation of the Q/K vectors. Generalises better to longer sequences; now widely used.
- **ALiBi** (MPT): adds a position-dependent bias to attention scores rather than modifying embeddings.



---
### 2.6 The Feed-Forward Network (FFN)

Attention collects information and Context. FFN process it. 
After attention, each position goes through an identical two-layer MLP independently:

```
FFN(x) = max(0, x · W1 + b1) · W2 + b2    (or GELU instead of ReLU)
```

This is often described as the "memory" layer — research shows factual associations ("Paris is the capital of France") are largely stored in FFN weights. Each block has its own W1 and W2.



> **The Feed-Forward Network (FFN)** is the second major component of every Transformer block. After the Multi-Head Attention layer gathers contextual information, the FFN processes each token independently through two linear layers separated by a non-linear activation function such as GELU or ReLU. This transforms the token into a richer representation while preserving its contextual information. Unlike Self-Attention, the FFN does not allow tokens to communicate with one another.

---

### 2.7 Residual Connections & Layer Norm

Both the attention and FFN sub-layers use the **Add & Norm** pattern:

```
x = LayerNorm(x + SubLayer(x))
```

- **Residual (skip) connection:** `x + SubLayer(x)` — lets gradients flow directly through the network, enabling training of very deep stacks.
- **Layer Norm:** normalises activations, stabilising training.



>A Residual Connection (or Skip Connection) adds the original input of a layer to its output. This preserves previously learned information and makes it easier to train very deep Transformer models by providing a direct path for information and gradients.


> Layer Normalization normalizes the values of each token's feature vector so they remain on a stable scale. This improves training stability, speeds up convergence, and prevents values from becoming excessively large or small.

---

### 2.8 Decoder-Only vs Encoder-Decoder vs Encoder-Only

The transformer architecture can be wired in three different ways:


| ENCODER-ONLY                                                                                            | DECODER-ONLY                                                                                                                                   | ENCODER-DECODER                                                                                                                    |
| ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Bidirectional attention -  every token sees all<br><br>                                                 | Causal/masked attention - each token sees only past.<br><br>While predicting the next word it can't see future words, can only see past words. | Encoder: bidirectional` `Decoder: causal + cross-att<br><br>One side reads and one side writes                                     |
| Best for: <br>- classification<br>- NER / token labelling<br>- Sentence embeddings<br>- Semantic search | Best for :<br>- Text generation<br>- Chat / instruction following<br>- Code generation<br>- Few-shot reasoning                                 | Best for:<br>- Translation (English - Bengali)<br>- Summarisation of long article<br>- Structured generation<br>- Seq-to-seq tasks |
| Example - BERT, RoBERTa                                                                                 | Example - GPT, Claude, Llama, Mistral                                                                                                          | Example - T5, mT5, BART                                                                                                            |

**Causal masking (decoder-only):** During training and inference, position `i` cannot attend to position `j > i`. This is enforced by setting those attention scores to `-inf` before softmax. This is what allows autoregressive generation — predict one token at a time.

**Cross-attention (encoder-decoder):** The decoder's Q comes from the decoder's own representation, but K and V come from the encoder's output. This lets the decoder "ask questions" of the encoded input.

**Developer rule of thumb:**
- Generating text or code? → Decoder-only (GPT/Claude/Llama-style).
- Classifying, extracting, or embedding? → Encoder-only (BERT-style), or use a dedicated embedding model.
- Translating or summarising with a separate input and output? → Encoder-decoder (T5/BART-style), though modern decoder-only models handle this too.

---

### 2.9 Why Context Windows Are Limited — O(n²) Attention

In standard Self-Attention, every token compares itself with every other token, producing an attention matrix of size **n × n**.

**The problem:** As the number of tokens increases, both computation and memory grow quadratically ` O(n²)` Big-O of n²

- **Memory increates:** O(n²) — For example a 128K-token context needs 128,000 × 128,000 entries.
- **Compute:** O(n²) — every pair must be computed.

At n = 128,000 tokens, that's ~16 billion scores per head per layer. Even with efficient implementations it's expensive.



To reduce this cost & extend context, researchers use these below techniques : 

| Technique                                                         | Idea                                                                                                                                           |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Sliding window / local attention** (Longformer, Mistral)        | Each token only looks at nearby tokens of its local window, not all others. O(n × window).                                                     |
| **Sparse attention** (BigBird)                                    | Combine local, global (CLS-like), and random attention patterns.<br>Each token looks at only a selected subset of tokens.                      |
| **FlashAttention**                                                | Algorithmic rewrite that is still O(n²) but dramatically reduces memory by computing in tiles — fits 4–8× longer contexts in the same GPU RAM. |
| **RoPE + fine-tuning on longer seqs** (LLaMA 2 Long, GPT-4 Turbo) | Extend position encoding to longer sequences and fine-tune.                                                                                    |
| **State-space models (Mamba)**                                    | Different architecture, O(n) scaling, but trade-offs vs attention quality.                                                                     |

---

## 3. Hands-On Lab

**Lab directory:** `labs/common/day-02/`

**Goal:** Make attention concrete by implementing scaled dot-product attention from scratch in NumPy, then visualise the resulting weight matrix.

**Setup:**
```bash
cd labs/common/day-02
pip install -r requirements.txt
```

**Run starter (complete the TODOs):**
```bash
python starter.py
```

**Run solution:**
```bash
python solution.py
```

**What you'll build:**
1. Compute Q, K, V from toy embedding vectors using random weight matrices.
2. Implement `scaled_dot_product_attention(Q, K, V)` step by step.
3. Print the attention weight matrix showing which tokens attend to which.
4. (Bonus) Load `distilgpt2` from HuggingFace with `output_attentions=True` and visualise a real attention head.

See `labs/common/day-02/README.md` for full instructions and expected output.

---

**Q2.** Why do we divide the dot-product scores by √d_k before applying softmax?


Show answer

As d_k grows, dot products have larger magnitude (their variance scales with d_k), pushing softmax into near-zero gradient regions (saturation). Dividing by √d_k keeps variance ~1 and softmax gradients healthy.



**Q3.** A decoder-only model uses causal masking. What is causal masking and why is it necessary?

Causal masking sets the attention score to -∞ (→ weight ≈ 0 after softmax) for any token j that appears after token i. This prevents each position from "seeing the future", which is required for autoregressive generation — the model must predict token n+1 having only seen tokens 1…n.




**Q5.** You need to build a semantic text search feature — users type a query and you return the most relevant paragraphs from a document set. Which transformer architecture family would you choose?

Encoder-only (e.g., `sentence-transformers` / BERT-style). These produce rich bidirectional contextualised embeddings ideal for similarity-based retrieval. Decoder-only models are generative and less suited (though embedding models derived from them exist).



**Q6.** What is the computational complexity of standard self-attention with respect to sequence length n? What does this imply for context window size?


O(n²) in both memory and compute. Doubling the context length quadruples the attention computation. A 128K context needs ~16B score values per head per layer, making very long contexts expensive without algorithmic changes (FlashAttention, sparse attention, etc.).





**Q8.** What does the feed-forward network (FFN) in each transformer block do, and is it applied per-token or across the whole sequence?


Show answer

The FFN applies the same two-layer MLP independently to each token position — it is a per-token (pointwise) operation. Research suggests FFN layers are where factual associations are primarily stored; they act as a "key-value memory" indexed by the attention output.



---

## 5. Concept Deep-Dive Q&A

*These questions test deeper, applied understanding of the day's concepts.*

---

**Q1: Can you walk me through how a transformer processes text from input to output?**


Show answer

Text is tokenised into integer IDs, which are looked up in an embedding table to get dense vectors. A positional encoding is added to preserve order. These vectors pass through N stacked transformer blocks, each containing multi-head self-attention followed by a feed-forward network — both wrapped in residual connections and layer norm. The attention sub-layer lets every token dynamically aggregate information from all other tokens. The FFN then applies a per-position non-linear transformation. The final block's output is projected to vocabulary size via a linear layer and normalised with softmax to give next-token probabilities.



---

**Q2: What is the difference between encoder-only models like BERT and decoder-only models like GPT? When would you pick each?**


Show answer

BERT-style encoders use bidirectional attention — each token can attend to all others, producing rich contextualised representations. They're ideal for classification, entity extraction, and generating sentence embeddings for semantic search. GPT-style decoders use causal (left-to-right) attention, enabling autoregressive text generation — one token at a time. For chat, code generation, or instruction-following you want decoder-only. For tasks where you need to understand and classify existing text, encoder-only models are usually faster and more parameter-efficient. Encoder-decoder (T5, BART) are a middle ground good for translation and summarisation where there's a distinct input and output.



---

**Q3: What is the attention mechanism, and intuitively why does it work?**


Show answer

Each token projects its embedding into three vectors — Q, K, V. 

Q represents what the token is looking for; 
K represents what it has to offer as context; 
V is the actual content it contributes. 

Relevance scores are computed as dot products between Q and all Ks, scaled by √d_k and softmaxed into weights. The token's new representation is then a weighted sum of all Vs. Intuitively: every word can 'ask a question' (Q) and 'scan the room' for relevant answers (K), then blend the relevant information (V). This lets the model resolve ambiguities like pronouns, long-range syntactic dependencies, and factual associations without fixed-size sliding windows.



---

**Q4: Why does attention have O(n²) complexity, and what are the implications for building systems?**


Show answer

Each token must compute a relevance score against every other token — n×n pairs — both in memory and compute. This means doubling context length quadruples attention cost. In practice this means: (1) very long documents must be chunked in naive RAG rather than fed whole; (2) long-context models (128K+) require techniques like FlashAttention or sparse attention; (3) inference latency and memory scale super-linearly with context. Architecturally I'd choose the smallest context window that meets requirements to control cost, and use retrieval to bring in only relevant chunks.


---

**Q7: Our production model sometimes loses track of information mentioned early in a very long conversation. Why, and how would you address it?**


Show answer

This is the 'lost in the middle' problem documented in research — LLMs tend to underweight information from the middle of long contexts, even when it nominally fits in the context window. This happens partly because positional encoding is learned on fixed-length sequences and partly because attention weights get very spread out over long sequences. Approaches: (1) RAG — retrieve only the relevant chunks at inference time, keeping effective context short; (2) summarise earlier turns and pass the summary forward; (3) use a model with better long-context training (e.g., Claude with 200K context uses techniques like extended position encoding and long-context fine-tuning); (4) hierarchical chunking with reranking to surface the most relevant content.



---

**Q8: How would you explain self-attention to a developer who has never seen it?**


Show answer

Imagine a database query. For every word in a sentence, you generate a query vector (what you need), and every word also generates a key (what it has). You run the query against all keys, get similarity scores, normalise them, and retrieve a weighted blend of the values. This is self-attention: the database and the query are the same sequence. The result is that every word's new representation is a contextualised blend of the whole sentence, with the model having learned which words matter for which. The key advantage over older RNNs: every token can directly access any other token in one step, so information doesn't need to be 'remembered' across many sequential steps.



---

**Q9: What's the role of the FFN (feed-forward network) layers inside a transformer block?**


Show answer

After attention allows tokens to exchange information across positions, the FFN refines each token's representation independently (same MLP applied to every position). Think of it as: attention gathers context, FFN processes it. Research (Geva et al., 2021) suggests the FFN weights act as a 'factual memory' — key-value stores where specific knowledge is retrieved when the attention layer activates the right pattern. They account for the majority of model parameters (the inner dimension is typically 4× d_model), which is why removing them dramatically degrades knowledge recall.



---

**Q10: Between GPT-4 and BERT-large for a customer support ticket classifier, which would you choose and why?**


Show answer

BERT-large (or a smaller distilled variant like DistilBERT). For classification tasks, encoder-only models produce better fixed representations because bidirectional attention captures full sentence context without the constraints of causal masking. They're also far cheaper to run — BERT-large is ~340M parameters vs GPT-4's estimated 1T+, making inference cost orders of magnitude lower. I'd fine-tune BERT-large on labelled tickets for a few epochs. GPT-4 would only make sense if the labels are very sparse (few-shot in-context), if the classes are extremely nuanced requiring complex reasoning, or if the same model is already being called for other pipeline steps and adding a separate BERT deployment isn't worth the ops complexity.



---

## 6. Further Reading

### Essential (read before Day 3)
- **The Illustrated Transformer** — Jay Alammar (2018). Best visual walkthrough of the architecture. https://jalammar.github.io/illustrated-transformer/
- **Attention Is All You Need** — Vaswani et al. (2017). Read §3 (Model Architecture) and §3.2 (Attention). https://arxiv.org/abs/1706.03762

### Strongly Recommended
- **Let's build GPT from scratch** — Andrej Karpathy (2023). 2-hour YouTube video building a miniature decoder-only GPT in ~200 lines of PyTorch. https://www.youtube.com/watch?v=kCc8FmEb1nY
- **The Annotated Transformer** — Harvard NLP. Line-by-line annotated PyTorch implementation of the original paper. https://nlp.seas.harvard.edu/2018/04/03/attention.html
- **Transformer Explainer** — Georgia Tech / Polo Club. Interactive visual demo in the browser. https://poloclub.github.io/transformer-explainer/

### Deep Dives
- **FlashAttention** (Dao et al., 2022) — IO-aware exact attention. https://arxiv.org/abs/2205.14135
- **RoFormer: Enhanced Transformer with Rotary Position Embedding** (Su et al., 2021). https://arxiv.org/abs/2104.09864
- **Transformer Feed-Forward Layers Are Key-Value Memories** (Geva et al., 2021). https://arxiv.org/abs/2012.14913
- **Lost in the Middle** (Liu et al., 2023) — How LLMs underweight middle-of-context information. https://arxiv.org/abs/2307.03172

---

## 7. Key Takeaways

1. **Transformers = stacked blocks of attention + FFN.** Each block refines token representations; stacking them builds progressively more abstract understanding.

2. **Self-attention lets every token directly query every other token.** The Q/K dot product is a learned relevance score; V delivers the actual content. This is what gives LLMs their ability to handle long-range dependencies.

3. **Scaling matters twice:** scale the dot products by √d_k (numerical stability), and scale the number of heads h (expressivity). Both are critical to making attention work in practice.

4. **Decoder-only for generation, encoder-only for classification/embeddings.** Causal masking is the key difference — it's what enables next-token prediction during both training and inference.

5. **Position must be injected explicitly.** Attention is permutation-invariant; without positional encoding (sinusoidal, learned, or RoPE), word order is invisible to the model.

6. **O(n²) is the fundamental constraint.** It is why context windows are bounded, why long documents must be chunked for RAG, and why FlashAttention and sparse attention techniques were invented.

7. **FFN layers are not filler.** They store factual associations and account for most model parameters — the attention layer gathers context; the FFN processes and applies knowledge.


| Concept              | Easy Meaning                                                                         |
| -------------------- | ------------------------------------------------------------------------------------ |
| Token                | A word or part of a word                                                             |
| Embedding            | Numeric representation of a token                                                    |
| Self-Attention       | Every token looks at other relevant tokens in the same sequence                      |
| Query (Q)            | What this token is looking for                                                       |
| Key (K)              | What this token offers to others                                                     |
| Value (V)            | The actual information contributed by the token                                      |
| Multi-Head Attention | Many attention mechanisms working in parallel, each learning different relationships |
| Positional Encoding  | Tells the model the order of tokens                                                  |
| FFN                  | Processes each token after attention has gathered context                            |
| Residual Connection  | Adds the original input back to help deep networks train                             |
| Layer Normalization  | Stabilizes training by normalizing activations                                       |
| Encoder              | Best for understanding text (classification, embeddings, search)                     |
| Decoder              | Best for generating text one token at a time                                         |
| Encoder-Decoder      | Best for tasks with separate input and output (translation, summarization)           |
| O(n²) Attention      | Every token compares with every other token, making long contexts expensive          |