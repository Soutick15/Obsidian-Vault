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
- Tokenize a short phrase and compute a cosine similarity by hand, then reproduce both with code.

---

## 2. Concept Reading

### 2.1 The Nesting Hierarchy from broadest to narrowest: 

AI → ML → DL → GenAI → LLM

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
│  │  │  │  DL models that *generate* new content │  │  │  │
│  │  │  │  (text, images, audio, code, video)    │  │  │  │
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

Recap: AI is the broadest umbrella; every LLM is a GenAI model, every GenAI model here is a Deep Learning model, every Deep Learning model is a Machine Learning model, and Machine Learning is one way (not the only way) to build AI.

---

### 2.2 What an LLM Actually is

An LLM is a probability distribution over the next token given all previous sequence of tokens so far. It predicts the most likely next token based on the input and the knowledge it learned during training.

This process is repeated token-by-token until a stop condition.

An LLM is an AI model trained on massive amounts of text data. It learns patterns in language and can understand and generate human-like text. 

Instead of looking up answers in a database,  LLMs are used for tasks like question answering, code generation, summarization, translation, and conversational AI.

That sounds abstract, so here is the everyday version: it works like the autocomplete on your phone keyboard, which looks at the last few words you typed and suggests the most likely next word — except an LLM does this with a vastly larger vocabulary, a vastly longer memory of what came before, and a model trained on a huge slice of the internet instead of just your own texting history.
At every step the model does:

```
P(next_token | token_1, token_2, ..., token_n)  →  sample one token  →  append  →  repeat
```

("Sample" means the model picks one token, weighted by how likely it thinks each option is — not necessarily always the single most-likely one.)

That's it. Everything else — answering questions, writing code, following instructions — is an emergent behaviour of training that distribution on enormous, diverse text.

Recap: an LLM repeatedly predicts one next token at a time from everything typed so far, and that simple loop — run billions of times during training — is what produces language ability, reasoning-like behaviour, and also its failure modes (hallucination, non-determinism).

#### What this implies for developers

| Implication               | Why it matters                                                                                                                                                                                                                                     |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Non-determinism**       | Sampling means the same prompt can return different outputs. Use `temperature=0` for near-deterministic output. Use `temperature=3` (or higher) for more creative answer<br><br>Exact reproducibility is NOT guaranteed across providers/hardware. |
| **No persistent memory**  | The model has no state between API calls. Everything it "knows" about your session must be in the current prompt.                                                                                                                                  |
| **Can hallucinate**       | If the most probable next token continues a plausible but wrong sentence, the model does it. It has no external fact-checker.                                                                                                                      |
| **Patterns, not logic**   | LLMs are very good at mimicking the *form* of reasoning they saw in training data. They are not running a symbolic solver.                                                                                                                         |
| **Context is everything** | The model only sees what you put in the prompt. Richer context = better output.                                                                                                                                                                    |

---
#### What LLMs can and cannot do

| CAN DO well                       | CANNOT DO reliably                          |
| --------------------------------- | ------------------------------------------- |
| Summarisation & extraction        | Precise arithmetic (unless tool-use)        |
| Paraphrasing & rewriting          | Real-time / up-to-date information          |
| Code generation & explanation     | Deterministic exact-match logic             |
| Instruction following (with care) | Count characters/tokens in own output       |
| Language translation              | Access external URLs / APIs (without tools) |
| Chain-of-thought reasoning        | Guarantee factual correctness               |
| Classification & sentiment        | Recall every training fact accurately<br>   |

**"What are LLM hallucinations and how do you mitigate them?"**

Hallucinations are when an LLM outputs fluent, confident-sounding content that is factually incorrect or entirely fabricated. They arise because the model is optimising for probable next tokens, not for factual accuracy. 

Common mitigations: 
(1) RAG — ground the model's answer in retrieved, verified documents; 
(2) tool use — let the model call APIs or databases for facts rather than recalling from parameters; 
(3) output validation — use structured output schemas and post-process/verify critical fields; 
(4) chain-of-thought prompting — asking the model to reason step-by-step reduces but does not eliminate hallucinations; 
(5) human-in-the-loop review for high-stakes outputs.


---
### 2.3 Tokens & Tokenisation. Why Token matters for cost estimation?

When we type any prompt in human readable language like English, LLM doesn't understand this language. It first breaks the sentence into smaller units called Token (tokens) that models can process.

Recap: a token is a sub-word puzzle piece, not a word or a character; BPE builds its set of pieces from what appeared most often in training text, so common English words are cheap (one piece) and rare words, code, and non-English text are expensive (several pieces).


#### 2.3.0 What is a token?

>A `token` is the smallest unit of text that an LLM model processes — not a character, not a word. Modern LLMs use sub-word tokenisers.
>
>A token can be : A whole word, Part of a word, A punctuation mark, A number, A symbol.

A **token** is the basic unit a model reads and writes — not a character, not a word. Modern LLMs use sub-word tokenisers, meaning a token is often a chunk smaller than a whole word: think of tokens as puzzle pieces that get glued together to spell out words and sentences. Common words are usually a single piece; longer or rarer words get broken into two or more pieces.

```
Text → Tokenizer → Tokens  
```
#### 2.3.1 Tokenisation  

>Tokenisation is simply the process of breaking text into token that models can process. 
>
>Tokenisation is handled by an algorithm like BPE (Byte-Pair Encoding) that merges common byte sequences into single tokens. 
>
>As a rule of thumb, one token ≈ 4 English characters or 0.75 words. 
>
>Cost and context limits are both measured in tokens, so understanding tokenisation lets you estimate API cost, check whether a document fits in the context window, and optimise prompts for efficiency.
>
> Non-English text, code, or rare words cost more tokens per character, because those puzzle pieces were formed from whatever text the tokeniser was built from — mostly English web text.


Rule of thumb (English text): 

```

(character / 4) ≈ token

1 token ≈ 4 characters  ≈  0.75 words

80 tokens ≈ 320 characters 

```

Concrete example — the phrase `"unbelievable"` is not common enough to be its own puzzle piece, so a BPE tokeniser splits it into smaller pieces it does recognise. Or internally it may even assign token IDs:


```
"Hello"          → ["Hello"]                          1 token
"Hello, world!"  → ["Hello", ",", " world", "!"]      4 tokens
"unbelievable"   → ["un", "believ", "able"]           3 tokens
"2024-06-17"     → ["2024", "-", "06", "-", "17"]     5 tokens
```

Or internally it may even assign token IDs:

```
"Hello"  → 512
"world"  → 981
```


Different LLM models have different tokenisers.  They do not Tokenise the Same Way. For example, lets take the word : "unbelievable"
- One model may split it into : `["un", "believable"]`
- Another model may split it into : `["un", "believ", "able"]` both are correct.

Tokenisation is Useful, Suppose the model has never seen as particular word before, so it can split it into smaller chunks which it already knows those smaller pieces. So it can understand the new word.

---
#### 2.3.2 Byte-Pair Encoding (BPE) — how the puzzle pieces are chosen

Byte-Pair Encoding (BPE) is a subword tokenization algorithm used by many Large Language Models. Instead of splitting text into whole words or individual characters, BPE breaks text into frequently occurring subwords. This helps the model handle unknown words, reduce vocabulary size, and efficiently tokenize rare or complex words.

```
unhappiness
↓
["un", "happi", "ness"] 
```

Instead of treating `"unhappiness"` as one unknown word, BPE splits it into meaningful subword tokens that the model already understands.

BPE builds its set of puzzle pieces (the *vocabulary*) by scanning huge amounts of text and repeatedly merging whichever pair of adjacent pieces appears most often, starting from individual characters:

```
Step (characters):         h e l l o   w o r l d
merge most frequent pair : h e ll o   w o r l d  ("l"+"l" -> "ll")
Merge again :              he ll o  w o r ld.    ("h"+"e" -> "he")
...
After many merges: common words end up as one piece;
               rare words stay split into several pieces.
```

**Why does this matter to you as a developer?**

- **API cost** scales with tokens, not characters. 1 million tokens ≠ 1 million words.
- **Context limits** are measured in tokens. Knowing `~4 chars/token` lets you estimate fit.
- **Prompt design** — avoid excessive punctuation, whitespace, or non-standard characters; they inflate token counts.


**Q8. "How does BPE tokenisation handle a word it has never seen before?"**

BPE cannot produce a single token for an unseen word because that word was never frequent enough in training to get its own merged entry in the vocabulary. Instead, BPE falls back to smaller sub-word pieces — potentially down to individual bytes or characters — that are always in the vocabulary. So an invented word like "grokkinomics" might be tokenised as `["gr", "ok", "kin", "om", "ics"]`, costing five tokens instead of one. This graceful degradation means BPE never produces an unknown-token error, but rare words and non-English text cost more tokens per unit of meaning.

---
#### 2.3.3 Context Window

The **context window** is the maximum number of tokens a model can process in a single forward pass. It includes both 
- **input** tokens (your prompt + conversation history) and 
- **output** tokens (the model's response).

LLMs can only "remember" a limited amount of information **during one conversation/request**. That memory is called the **Context Window**.

Exceeding it causes an API error; common mitigations include chunking, summarisation, or retrieval-augmented generation.


```
┌───────────────────────────────────────────────────────┐
│                    Context Window (e.g. 128 k tokens) │
│  ┌──────────────────────────┐  ┌─────────────────────┐│
│  │     INPUT tokens         │  │  OUTPUT tokens      ││
│  │  system prompt +         │  │  model completion   ││
│  │  conversation history +  │  │  (max_tokens)       ││
│  │  user message +          │  │                     ││
│  │  retrieved docs (RAG)    │  │                     ││
│  └──────────────────────────┘  └─────────────────────┘│
└───────────────────────────────────────────────────────┘
         input_tokens + output_tokens ≤ context_limit
```


**Common context limits (approximate, check current docs):**

| Model           | Context Window |
| --------------- | -------------- |
| GPT-5.5         | 1M tokens      |
| Claude Opus 4.8 | 1M tokens      |
| Gemini 3.1 Pro  | 1M tokens      |
| Llama 4 Scout   | 10M tokens     |
| DeepSeek V4 Pro | 1M tokens      |
| Grok 4          | 2M tokens      |

Exceeding the context window raises an error. Strategies to handle large inputs: chunking, summarisation, RAG (covered in later days).


This drives several architectural decisions: 
- for long documents you chunk them and retrieve only the relevant chunks (RAG);
- for long conversations you summarise or trim history; 
- for very large code bases you index the codebase and surface only relevant files. Choosing a model with a larger context window can simplify design but increases cost per call.

---
### 2.4 Embeddings

```
Text → Tokenizer → Tokens → 
Embeddings → Vectors → Cosine Similarity → How similar are these vectors? → Best Matching Documents → LLM
```

- An **embedding** is a fixed-length numerical vector produced by a model that represents the semantic content of a piece of text. 
- Embeddings convert words, sentences, or documents into numerical vectors. Text with similar meanings tends to produce vectors that are close together in vector space. Similarity metrics (such as cosine similarity) measure how close those vectors are.
- Semantically similar text produces vectors that are close in the vector space, measured by cosine similarity. 
- Embeddings are widely used in 
	- semantic search : search by meaning instead of keyword.
	- recommendation systems, 
	- vector databases, and 
	- Retrieval-Augmented Generation (RAG).


LLM-derived embeddings place semantically similar text close together in vector space.

Let's simplify that. Imagine we have the below sentences, and the converted to numbers, because computers compare numbers much more easily than sentences. 

```
"The cat sat on the mat"   →  [0.12, -0.34, 0.88, ..., 0.05]   (384 floats)


"A kitten rested on a rug" →  [0.11, -0.31, 0.85, ..., 0.07]   (384 floats, similar!)


"The stock market crashed"  →  [-0.55, 0.72, -0.12, ..., 0.91]  (384 floats, different)
```

This long list of numbers is called a **vector**. The vector is typically hundreds to thousands of floats.

Notice in the above example "The cat sat on the mat" and "A kitten rested on a rug" They produces vectors that are close to each other in vector space.
Means the meaning is similar even though the words are different. 

But the "The stock market crashed" generated vector is totally different.


```
					"The cat sat on the mat."
								↓
							Tokenizer
								↓
			["The", "cat", "sat", "on", "the", "mat"]
								↓		
						Embedding Layer
								↓
					[
					  [0.25, -0.81, ...],   ← "The"
					  [-0.13, 0.72, ...],   ← "cat"
					  [0.88, -0.20, ...],   ← "sat"
					  ...
					]	
								↓
							   LLM
```

---
#### 2.4.1 Cosine similarity ( cos(θ) )


> **Cosine Similarity** is the standard technique used to measure how similar two embedding vectors are. Instead of comparing exact words, it compares the **direction** of the vectors, which represents their semantic meaning. The result ranges from **-1 to +1**, where **+1 means the vectors are almost identical**, values around **0.85 or higher indicate very similar meaning**, and values near **0 indicate unrelated content**. It is widely used in semantic search, vector databases, and RAG systems to retrieve the most relevant documents.


We have converted the sentences into vectors. Now how do we compare them?

Cosine similarity is the standard metric for comparing embeddings. It measures the *angle* between two vectors, independent of their magnitude:

Suppose we have two sentences.

```
Sentence A: "The cat sat on the mat."
Sentence B: "A kitten rested on a rug."
```

Embedding Model converts them into vectors.

```
Sentence A ↓ [0.12, -0.34, 0.88, ..., 0.05]
Sentence B ↓ [0.11, -0.31, 0.85, ..., 0.07]
```

How do we know whether they're similar? 
We can comparing every number, it works but thats is impossible for large texts as it produces large vectors.

We need one number that says "These two vectors are 92% similar." That's exactly what Cosine Similarity gives us. 

The below formula calculates Angle between two vectors. The result is always in Range of : -1.0 (opposite) to +1.0 (identical)


```
           A · B
cos(θ) = ─────────      
          |A| × |B|

```

- **cos(θ) = 0.85 - 1** (Small angel ==  high cosine similarity. The sentences are semantically very similar. 
- **cos(θ) = 0.5 – 0.85** ( Large Angle == low cosine similarity)
- **cos(θ) = -1 < 0.5** ( Opposite direction : Completely different)


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

Cosine Similarity doesn't care much about **how long** the vectors are. It only cares about Direction.


#### 2.4.2 Why embeddings matter for AI projects

- **Semantic search** — find documents by meaning, not keywords. Instead of searching "Spring Boot" exactly, we search by meaning. Spring Boot ≈ Java Backend ≈ REST API
- **RAG (Retrieval-Augmented Generation) chunk retrieval** — retrieve relevant chunks and send only those to the LLM context. This saves context window.
- **Document Clustering & classification** — group similar documents without labels.
- **Duplicate detection** — high cosine similarity flags near-duplicates.
- **recommendation systems**


**How Embedding is used in a RAG pipeline?** 
- In a RAG pipeline, you pre-embed your knowledge-base documents and store them in a vector database. At query time, you embed the user's question and retrieve the top-K most similar document chunks. Those chunks are inserted into the LLM's context window, giving it grounded, relevant information to answer from.

---
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
**Q4. Why does a rare or non-English word tend to cost more tokens than a common English word?**

BPE builds its vocabulary from the most frequent merges in the training corpus (mostly English web text). Rare or non-English words did not appear frequently enough to earn a single merged token, so they are split into many sub-word or even character-level tokens.

**Q7. Give two concrete reasons why an LLM might produce a factually wrong answer.**

(1) the most-probable next token continues a plausible-sounding but incorrect sentence; 
(2) the model's training data contained incorrect or outdated information; 
(3) the model has no external fact-checking mechanism; 
(4) stochastic sampling introduces variation.

---

**Q1. "Can you explain what a large language model is to a non-technical stakeholder?"**


An LLM is a software system trained on enormous amounts of text — think most of the internet — to predict what word (more precisely, what token) comes next in a sequence. Through that training it learns grammar, facts, reasoning patterns, and writing styles. When you send it a prompt, it generates a continuation token by token. Despite this simple mechanism, well-trained models exhibit surprisingly powerful language abilities, which is why they can be used for tasks like summarisation, question answering, code generation, and support automation.

---

**Q4. "Why are LLMs non-deterministic, and when would you want deterministic output?"**


LLMs sample from a probability distribution over the vocabulary at each token step. Even with the same prompt, different samples produce different completions. You control this with the `temperature` parameter: `temperature=0` makes the model always pick the highest-probability token, producing near-deterministic output — but exact reproducibility is NOT guaranteed across providers or hardware due to floating-point and batching differences. You want near-deterministic output for testing, compliance outputs, or structured data extraction where repeatability matters. For creative tasks you want higher temperature to get diverse outputs.

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
