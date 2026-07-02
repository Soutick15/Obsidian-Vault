# Day 11 — Fine-Tuning, LoRA & QLoRA

**Track:** Developer | **Week:** 2 | **Day:** 11 of 15

---

## 1. Objectives

By the end of Day 11 you will be able to:

1. Apply the **prompting → RAG → fine-tuning** decision framework and explain when each approach (or a combination) is appropriate.
2. Describe what supervised fine-tuning (SFT) and instruction tuning *actually* change in a model — and what they cannot change.
3. Explain the LoRA and QLoRA mechanics: low-rank adapters, the rank/alpha hyperparameters, and why they are memory-efficient.
4. Identify the main quantization schemes (4-bit bitsandbytes, GPTQ, AWQ, GGUF) and where each fits in a training or serving workflow.
5. Prepare a minimal instruction dataset, run a LoRA fine-tune on a tiny CPU-friendly model, save the adapter, and compare before/after outputs.

---

## 2. Concept Reading

### 2.1 The Decision Framework: Prompting → RAG → Fine-Tuning

Before writing a single line of training code, answer the following questions in order:

```
1. Can a well-crafted prompt (zero-shot or few-shot) solve this?
   YES → stop here. Iterate on the prompt.

2. Does the model lack specific *knowledge* it needs?
   YES → add RAG. Fine-tuning cannot reliably inject new factual knowledge.

3. Does the model's *behaviour, format, tone, or style* need to change
   in a way that prompt engineering cannot reliably deliver?
   YES → consider fine-tuning.

4. Do you have (a) quality labelled data, (b) GPU budget, and (c) time
   to iterate on training hyperparameters and evaluation?
   NO to any → fine-tuning will likely under-deliver. Revisit 1 or 2.
```

**Common mistake:** Teams reach for fine-tuning when the real gap is missing context (a RAG problem) or a poorly written system prompt.

**Combining approaches:** Fine-tuning and RAG are not mutually exclusive. A common production pattern:
- Fine-tune a model on company communication style / output format.
- Serve it with a RAG pipeline that supplies up-to-date factual context at inference time.

This gives you consistent *behaviour* from fine-tuning and current *knowledge* from RAG.

---

### 2.2 What Fine-Tuning Changes (and What It Cannot)

| What fine-tuning **can** change | What fine-tuning **cannot reliably** change |
|---|---|
| Output format / structure (JSON, Markdown, bullet lists) | Inject stable new factual knowledge beyond the training cutoff |
| Tone and writing style (formal, terse, domain-specific) | Make the model "forget" pre-training biases without catastrophic forgetting |
| Following a specific instruction schema consistently | Guarantee factual accuracy on unseen data |
| Domain jargon and terminology recognition | Replace retrieval for up-to-date or long-tail facts |
| Reducing verbosity or boilerplate | Exceed the capability ceiling of the base model |

**Key insight:** Fine-tuning adjusts *weights*; RAG adjusts *context*. Use each for what it does best.

---

### 2.3 Supervised Fine-Tuning (SFT) and Instruction Tuning

**Supervised fine-tuning** is the most straightforward adaptation: you continue training a pre-trained model on a dataset of `(input, output)` pairs using next-token prediction loss (same objective as pre-training, just on your data).

**Instruction tuning** is SFT where the inputs are natural-language instructions and the outputs are desired responses. The famous InstructGPT, Alpaca, and FLAN models were all instruction-tuned variants of base models.

Typical instruction dataset format (the "Alpaca" / ChatML style):

```json
{
  "instruction": "Summarise the parental leave policy in one sentence.",
  "input": "",
  "output": "Acme Corp provides 16 weeks of paid parental leave for primary caregivers and 6 weeks for secondary caregivers."
}
```

Or as a chat-style prompt:

```
### Instruction:
Summarise the parental leave policy in one sentence.

### Response:
Acme Corp provides 16 weeks of paid parental leave for primary caregivers...
```

**Quality > quantity.** 100 well-written, diverse, consistent examples often outperform 10 000 noisy ones. Common data quality issues:
- Inconsistent formatting (some examples capitalise keys, others don't)
- Wrong or hallucinated outputs in the training set
- Lack of diversity (all examples too similar → overfitting to surface patterns)
- Output length bias (model learns to always be short/long because your data was)

---

### 2.4 PEFT — Parameter-Efficient Fine-Tuning

Full fine-tuning updates *every* parameter. A 7B-parameter model in 16-bit precision needs ~14 GB just to store weights, plus optimizer states (Adam ≈ 3× model size) — easily 40–60 GB of GPU memory. That is impractical for most teams.

**PEFT** methods update only a small number of new parameters while keeping base model weights frozen.

#### LoRA — Low-Rank Adaptation

**Core idea:** Instead of updating weight matrix `W` (shape `d × k`), inject two small trainable matrices `A` (shape `d × r`) and `B` (shape `r × k`), where `r << min(d, k)`. The effective update is:

```
W_new = W + B × A        (the adapter delta)
```

Only `A` and `B` are trained. `W` is frozen. For a typical attention weight with `d=4096` and `r=8`, the adapter has `2 × 4096 × 8 = 65 536` parameters instead of `4096 × 4096 = 16 777 216` — a **256× reduction** in trainable parameters.

**Key hyperparameters:**

| Parameter | Typical range | Effect |
|---|---|---|
| `r` (rank) | 4–64 | Capacity of the adapter. Higher r = more expressive but more memory |
| `lora_alpha` | Equal to r, or 2×r | Scaling factor: `alpha/r` multiplies the adapter output. Higher = stronger update |
| `target_modules` | `q_proj`, `v_proj` (at minimum) | Which weight matrices to adapt. More modules = more capacity |
| `lora_dropout` | 0.05–0.1 | Regularisation on adapter activations |

**Serving:** The adapter weights are tiny (often < 100 MB). You can swap adapters at inference time to serve different fine-tuned "personalities" on the same frozen base.

#### QLoRA — Quantized LoRA

QLoRA (Dettmers et al., 2023) combines two ideas:

1. **4-bit quantization of the base model** using `bitsandbytes` NF4 (Normal Float 4) — this cuts base model GPU memory by ~4×.
2. **LoRA adapters trained in 16-bit** on top of the frozen 4-bit base.

The result: you can fine-tune a 7B model on a single 16 GB GPU (e.g., a consumer RTX 3090 or Colab A100). Without QLoRA this would require ~40 GB.

Additional QLoRA technique — **double quantization**: quantize the quantization constants themselves, saving a further ~0.35 bits/parameter.

---

### 2.5 Quantization for Training and Serving

Quantization reduces the bit-width of model weights (and sometimes activations), trading a small accuracy loss for large memory and speed gains.

| Format | Bits | Use case | Notes |
|---|---|---|---|
| FP16 / BF16 | 16 | Standard fine-tuning | Good accuracy; BF16 preferred on Ampere+ GPUs |
| INT8 | 8 | Serving; some training | `bitsandbytes` LLM.int8() |
| NF4 (bitsandbytes) | 4 | QLoRA training | Double-quantized; high quality 4-bit |
| GPTQ | 4 (post-training) | Fast GPU inference | Calibration dataset required; popular for serving |
| AWQ | 4 (post-training) | Fast GPU inference | Activation-aware; often better quality than GPTQ |
| GGUF | 2–8 (mixed) | CPU / edge inference | Used by llama.cpp; quantizes individual tensor groups |

**Practical rule of thumb:**
- Training: use BF16 (full) or NF4 + LoRA (QLoRA) depending on GPU budget.
- Serving: GGUF on CPU/edge, GPTQ or AWQ for GPU servers, INT8 for moderate compression.

---

### 2.6 Dataset Preparation

A minimal instruction dataset for our HR assistant context:

```python
examples = [
    {
        "instruction": "How many PTO days do new employees receive?",
        "output": "New employees at Acme Corp accrue 15 days (120 hours) of PTO per year."
    },
    {
        "instruction": "What is the 401(k) employer match?",
        "output": "Acme Corp matches 100% of employee contributions up to 4% of salary, with 3-year graded vesting."
    },
    # ... more examples
]
```

**Formatting pipeline:**

1. Convert to a consistent prompt template (same template at train and inference time — mismatch is a common bug).
2. Tokenize with `truncation=True` and a sensible `max_length` (128–512 for short Q&A).
3. Set `labels = input_ids` for causal LM training (loss computed on all tokens) OR mask the instruction tokens from loss (only train on the response).
4. Shuffle and split: 80/10/10 train/validation/test.

---

### 2.7 Evaluation and Overfitting

**Training metrics to watch:**
- `train_loss` should decrease steadily.
- `eval_loss` should track `train_loss` — if it rises while `train_loss` falls, you are overfitting.

**Signs of overfitting in LLM fine-tuning:**
- Model generates training examples verbatim.
- Eval loss diverges from train loss after just a few epochs.
- Outputs become repetitive or formulaic.

**Countermeasures:**
- Reduce epochs (1–3 is often enough for instruction tuning).
- Increase `lora_dropout`.
- Add more diverse training data.
- Use early stopping on `eval_loss`.

**Beyond loss:** Always do qualitative evaluation — run your real prompts and read the outputs. Automated metrics (ROUGE, BERTScore) are useful signals but not sufficient alone.

---

### 2.8 Cost, Effort, and When NOT to Fine-Tune

Fine-tuning carries real costs beyond GPU time:

| Cost dimension | Detail |
|---|---|
| Data collection | Curating 500–5 000 quality examples is weeks of work |
| Training infrastructure | GPU rental or on-premise; iteration cycles |
| Model hosting | Fine-tuned models must be served; can't use provider APIs that don't support custom weights |
| Maintenance | Base model updates require re-fine-tuning |
| Evaluation pipeline | You need automated + human eval to catch regressions |

**When NOT to fine-tune:**
- You haven't tried few-shot prompting seriously yet.
- You need to inject new factual knowledge (use RAG).
- Your dataset is small (< 50 examples) and not curated.
- You have no GPU budget and the model you need to tune is > 3B parameters.
- The task changes frequently (you'll be re-training constantly).

---

## 3. Hands-On Lab

**Lab directory:** `labs/developer/day-11/`

**What you will build:**
- A minimal LoRA fine-tune on `sshleifer/tiny-gpt2` (a 117-parameter toy GPT-2) using a small HR Q&A instruction dataset derived from the shared Acme Corp corpus.
- Train a few steps on CPU, save the LoRA adapter, load it back, and compare before/after generation.

**Files:**
| File | Purpose |
|---|---|
| `README.md` | Setup and run instructions |
| `requirements.txt` | Python dependencies |
| `starter.py` | Skeleton with `# TODO` markers |
| `solution.py` | Complete working implementation |

**Run (smoke test — completes in < 30 seconds on CPU):**

```bash
cd labs/developer/day-11
pip install -r requirements.txt
python solution.py --smoke
```

**Run (full demo — 2–3 minutes on CPU, seconds on GPU):**

```bash
python solution.py
```

See `labs/developer/day-11/README.md` for Colab/GPU instructions.

---

## 4. Self-Check Quiz

**Q1.** A developer wants the model to always return JSON with a specific schema. Should they use (a) prompt engineering, (b) RAG, or (c) fine-tuning?

<details>
<summary>Show answer</summary>

Start with (a) prompt engineering — structured output instructions plus few-shot examples in the system prompt often solve this reliably and at zero training cost. Fine-tuning is warranted only if the format still fails after serious prompt iteration.

</details>

---

**Q2.** True or False: Fine-tuning a model on your company's product documentation is an effective way to keep it up to date as documentation changes weekly.

<details>
<summary>Show answer</summary>

False. Updating a fine-tuned model weekly is expensive and slow. RAG (retrieval-augmented generation) is the correct tool for up-to-date factual knowledge.

</details>

---

**Q3.** In LoRA, what does the `rank` (r) parameter control?

<details>
<summary>Show answer</summary>

Rank controls the capacity (expressiveness) of the adapter. A lower rank (e.g., r=4) trains fewer parameters and is more regularised; a higher rank (e.g., r=64) can express more complex adaptations but uses more memory.

</details>

---

**Q4.** What is the key difference between LoRA and QLoRA?

<details>
<summary>Show answer</summary>

QLoRA additionally quantizes the frozen base model weights to 4-bit (NF4) using bitsandbytes, dramatically reducing GPU memory. LoRA adapters are still trained in 16-bit precision on top of the quantized base.

</details>

---

**Q5.** Name two signs that your LoRA fine-tune is overfitting.

<details>
<summary>Show answer</summary>

(1) Eval loss rises while train loss keeps falling. (2) The model reproduces training examples verbatim or produces formulaic / repetitive outputs on new prompts.

</details>

---

**Q6.** You have 30 HR Q&A examples and 1 week of engineering time. Should you fine-tune?

<details>
<summary>Show answer</summary>

Probably not. 30 examples is very likely insufficient for generalisation. Invest the time in prompt engineering and RAG first; collect more diverse, high-quality data before attempting fine-tuning.

</details>

---

**Q7.** Which quantization format is best suited for running a model on a laptop CPU with no GPU?

<details>
<summary>Show answer</summary>

GGUF (used by llama.cpp). It supports mixed-precision quantization (2–8 bit) and is optimised for CPU inference.

</details>

---

**Q8.** What does `lora_alpha` control and how does it relate to `r`?

<details>
<summary>Show answer</summary>

`lora_alpha` is a scaling factor applied to the adapter output: the effective scaling is `alpha / r`. A common default is `alpha = r` (scaling = 1). Setting `alpha = 2r` doubles the adapter's contribution. It lets you tune the adapter's influence without changing its parameter count.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1. Why can't fine-tuning reliably inject new factual knowledge?**

<details>
<summary>Show answer</summary>

Pre-training encodes knowledge into billions of weight interactions in a distributed, entangled way. Trying to update a subset of weights (or even all weights) on a small dataset to "add" a new fact tends to either (a) not stick — the model doesn't generalise the new fact robustly — or (b) cause catastrophic forgetting of related existing knowledge. The model doesn't store facts in addressable slots; it stores statistical patterns. Retrieval (RAG) is fundamentally better suited to injecting specific, verifiable facts because it supplies them explicitly at inference time.

</details>

---

**Q2. Can you combine fine-tuning and RAG in production, and if so, how?**

<details>
<summary>Show answer</summary>

Yes — this is a common and effective pattern. Fine-tune the model on your preferred output format, domain terminology, and interaction style. Then at inference time, use a RAG pipeline to inject current factual context into the prompt. The fine-tuned model "knows how to talk" and the retrieval system "knows what to say." The adapter stays frozen; only the retrieved context changes per query.

</details>

---

**Q3. Why does LoRA use two matrices (A and B) instead of just one low-rank update matrix?**

<details>
<summary>Show answer</summary>

A single matrix of rank r could be stored directly, but initializing it to zero while maintaining gradient flow requires the two-matrix decomposition. LoRA initializes A with random Gaussian values and B with **zeros**, so the **initial adapter contribution** (delta = B × A) is **zero** — the base model's output is completely **unchanged at step 0**. The adapter does not start as a copy of the base model; its initial contribution is simply absent. This stable initialization is critical; a single matrix initialized to zero gives zero gradients and no learning signal.

</details>

---

**Q4. What is "catastrophic forgetting" and how does LoRA help mitigate it?**

<details>
<summary>Show answer</summary>

Catastrophic forgetting occurs when updating model weights to learn new tasks causes the model to lose performance on tasks it previously handled well. LoRA mitigates this by keeping base model weights frozen — only the small adapter matrices are updated. Since the pre-trained knowledge is locked in the original weights, it cannot be overwritten by fine-tuning. This is a significant structural advantage over full fine-tuning, which modifies all weights and is prone to forgetting.

</details>

---

**Q5. What is the practical difference between GPTQ and AWQ for serving quantized models?**

<details>
<summary>Show answer</summary>

Both are 4-bit post-training quantization (PTQ) methods. GPTQ uses layer-wise quantization based on second-order information (Hessians) from a calibration dataset, and is well-supported by the AutoGPTQ library. AWQ (Activation-Aware Weight Quantization) identifies which weights are most important by analysing activation magnitudes, protecting those weights with higher precision — this often produces better quality at the same bit-width. In practice: AWQ tends to outperform GPTQ on quality benchmarks; GPTQ has broader tooling support. Both are suitable for GPU serving; neither is suited to CPU inference (use GGUF for that).

</details>

---

**Q6. How do you decide which layers/modules to target with LoRA adapters?**

<details>
<summary>Show answer</summary>

The standard starting point is the attention projection matrices: `q_proj` and `v_proj` (query and value). Research suggests value projections carry more task-specific information. Adding `k_proj`, `o_proj`, and feed-forward layers (`up_proj`, `down_proj`, `gate_proj`) generally improves performance but increases adapter size and training cost. A practical approach: start with `q_proj + v_proj`, establish a baseline, then expand to more modules if the baseline is insufficient.

</details>

---

**Q7. What is double quantization in QLoRA and why does it matter?**

<details>
<summary>Show answer</summary>

In 4-bit quantization, each block of weights has a quantization constant (scale factor) that is typically stored in FP32 — adding overhead. Double quantization quantizes these constants themselves (e.g., from FP32 to FP8), saving an additional ~0.35 bits per parameter. On a 7B model this saves roughly 3 GB of GPU memory, which can be the difference between fitting on a 16 GB card or not.

</details>

---

**Q8. How should you format the prompt template for fine-tuning, and why does template consistency matter?**

<details>
<summary>Show answer</summary>

You must use *exactly* the same prompt template during training and inference. If training data uses `### Instruction:\n{inst}\n\n### Response:\n` but inference uses `Instruction: {inst}\nAnswer:`, the model will not recognise the pattern it was trained on and outputs will degrade significantly. This is one of the most common fine-tuning bugs. Document your template as a constant in code and import it in both the training script and the inference wrapper.

</details>

---

**Q9. What is instruction tuning, and how does it differ from domain-specific fine-tuning?**

<details>
<summary>Show answer</summary>

Instruction tuning trains a model to follow natural-language instructions across a diverse range of tasks (summarisation, Q&A, translation, coding, etc.) — it is generalist fine-tuning for "helpfulness." Domain-specific fine-tuning trains on a narrower dataset for a specific task or domain (e.g., HR Q&A). The techniques are identical (SFT with cross-entropy loss); the difference is in dataset breadth. A common production pattern: start from an instruction-tuned base (e.g., a Llama-Instruct or Mistral-Instruct checkpoint) rather than a raw base model, then domain-fine-tune on top — you get instruction-following behaviour for free and only need to adapt style/domain.

</details>

---

**Q10. At what point does adding more fine-tuning data stop helping?**

<details>
<summary>Show answer</summary>

Returns are diminishing and highly task-dependent, but a rough rule: for instruction tuning on a narrow task, improvements plateau around 1 000–5 000 high-quality examples. Beyond that, data *diversity* matters more than raw count. If eval loss has converged and qualitative outputs look good, adding more data of the same type will not help — you need harder examples, edge cases, or adversarial inputs. Monitor eval loss vs. dataset size and stop collecting when the curve flattens.

</details>

---

## 6. Further Reading

| Resource | Why it's useful |
|---|---|
| Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models" (2021) — [arXiv:2106.09685](https://arxiv.org/abs/2106.09685) | The original LoRA paper; essential reading |
| Dettmers et al., "QLoRA: Efficient Finetuning of Quantized LLMs" (2023) — [arXiv:2305.14314](https://arxiv.org/abs/2305.14314) | QLoRA paper; introduces NF4 and double quantization |
| Hugging Face PEFT documentation — [huggingface.co/docs/peft](https://huggingface.co/docs/peft) | Library reference for LoRA, QLoRA, prefix tuning, and more |
| Hugging Face TRL (Transformer Reinforcement Learning) — [huggingface.co/docs/trl](https://huggingface.co/docs/trl) | `SFTTrainer` — the standard tool for instruction fine-tuning |
| "The Unreasonable Ineffectiveness of the Deeper Layers" (Gromov et al., 2024) — [arXiv:2403.17887](https://arxiv.org/abs/2403.17887) | On layer importance; informs which layers to target |
| bitsandbytes documentation — [github.com/bitsandbytes-foundation/bitsandbytes](https://github.com/bitsandbytes-foundation/bitsandbytes) | 4-bit/8-bit quantization library used in QLoRA |
| Tim Dettmers' blog: "Making LLMs Even More Accessible with bitsandbytes, 4-bit quantization and QLoRA" | Accessible walkthrough of QLoRA concepts |
| Axolotl framework — [github.com/OpenAccess-AI-Collective/axolotl](https://github.com/OpenAccess-AI-Collective/axolotl) | Production-grade fine-tuning framework with LoRA/QLoRA support |

---

## 7. Key Takeaways

1. **Use the decision framework:** prompting first, RAG for knowledge gaps, fine-tuning only for persistent behaviour/format/style changes that prompt engineering cannot solve.
2. **Fine-tuning changes behaviour, not knowledge** — it cannot reliably inject new facts; use RAG for that.
3. **LoRA is the default PEFT method:** two small matrices (rank r) injected into attention layers; only they are trained while the base is frozen. This prevents catastrophic forgetting and makes adapters tiny and swappable.
4. **QLoRA = LoRA + 4-bit base model quantization:** enables fine-tuning 7B+ models on consumer GPUs.
5. **Data quality beats data quantity:** 200 clean, diverse instruction examples outperform 2 000 noisy ones.
6. **Watch eval loss, not just train loss:** divergence between the two is the primary overfitting signal.
7. **Template consistency is non-negotiable:** the prompt format at training time must be identical at inference time.
8. **Quantization formats have distinct roles:** NF4 for training (QLoRA), GPTQ/AWQ for GPU serving, GGUF for CPU/edge inference.
