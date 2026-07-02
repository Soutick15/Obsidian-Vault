# Day 11 Lab — LoRA Fine-Tuning Demo (CPU-Friendly)

**Track:** Developer | **Day:** 11 of 15

---

## What You Will Build

A minimal end-to-end LoRA fine-tune on a tiny model (`sshleifer/tiny-gpt2`) using a small HR Q&A instruction dataset derived from the shared Acme Corp corpus. You will:

1. Prepare a 12-example instruction dataset in the Alpaca format.
2. Apply a LoRA adapter (rank 4) using the `peft` library.
3. Train for a few steps on CPU.
4. Save the LoRA adapter to disk.
5. Load the adapter back and run before/after generation to see the difference.

**No API key required.** The model is downloaded from Hugging Face on first run (~10 MB for `sshleifer/tiny-gpt2`).

---

## Provider Flexibility Note

This lab is **entirely local** — it uses open-weight models via the `transformers` library. No external API (Anthropic, OpenAI, etc.) is called. The same PEFT techniques apply to any `transformers`-compatible model regardless of provider.

For a real fine-tune at scale, swap `sshleifer/tiny-gpt2` for a larger instruction-tuned model (e.g., `mistralai/Mistral-7B-Instruct-v0.2`, `meta-llama/Llama-3.1-8B-Instruct`) and run on a GPU — see the Colab section below.

---

## Setup

```bash
# From the repo root
cd /path/to/AI_Training

# Activate your environment (Python 3.11+)
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# Install day-11 dependencies
pip install -r labs/developer/day-11/requirements.txt

# Navigate to the lab
cd labs/developer/day-11
```

> **Note:** First run downloads `sshleifer/tiny-gpt2` (~10 MB). Subsequent runs use the local Hugging Face cache.

---

## Running the Lab

### Smoke test (< 30 seconds on CPU)

Runs 1 optimizer step, saves the adapter, loads it back, and prints before/after generation. Use this to verify your environment is set up correctly.

```bash
python solution.py --smoke
```

Expected output:

```
=== Day 11: LoRA Fine-Tuning Demo ===
Mode: SMOKE (1 step, tiny settings)

[1/5] Building HR instruction dataset (12 examples)...
      Loaded 12 examples.
[2/5] Loading base model: sshleifer/tiny-gpt2
      Parameters: 1,500,816
[3/5] Applying LoRA adapter (r=2, alpha=4)...
      Trainable params: 3,072  (0.2045% of total)
[4/5] Training...
      Step 1/1 | Loss: X.XXXX
      Training complete. Saving adapter to ./lora-adapter-smoke/
[5/5] Before/After Generation
  Prompt: "Q: How many PTO days do new employees get?"

  BEFORE (base model):
  Q: How many PTO days do new employees get? ...

  AFTER (LoRA adapter):
  Q: How many PTO days do new employees get? ...

Done. Adapter saved to: ./lora-adapter-smoke/
```

### Full demo (2–3 minutes on CPU)

Trains for 3 epochs over the full 12-example dataset.

```bash
python solution.py
```

### Starter skeleton (for learning)

Work through the TODOs in `starter.py`:

```bash
python starter.py --smoke
```

---

## Colab / GPU Run (Larger Models)

For a real fine-tune on a proper instruction-tuned model, use this Colab starter (GPU recommended):

```python
# In Colab: Runtime → Change runtime type → T4 GPU

!pip install transformers peft datasets torch accelerate bitsandbytes

from peft import LoraConfig, get_peft_model, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

model_id = "mistralai/Mistral-7B-Instruct-v0.2"  # swap to your preferred model

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,  # QLoRA double quantization
)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
)
tokenizer = AutoTokenizer.from_pretrained(model_id)

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# Continue with Trainer / SFTTrainer from TRL...
```

> **Memory guide:** `r=8`, Q+V only, NF4 4-bit → ~6 GB VRAM for a 7B model. Enough for a free Colab T4.

---

## File Descriptions

| File | Description |
|---|---|
| `README.md` | This file |
| `requirements.txt` | Python dependencies (no API key needed) |
| `starter.py` | Skeleton with TODOs — your starting point |
| `solution.py` | Complete implementation — reference / smoke test |

---

## Learning Checkpoints

After completing the lab, you should be able to answer:

- [ ] What percentage of parameters does LoRA train vs. the full model?
- [ ] Where is the adapter saved, and what files does it contain?
- [ ] How does the before/after generation differ? Why?
- [ ] What happens if you increase `r` from 2 to 16?
- [ ] What would change if you used `BitsAndBytesConfig` with `load_in_4bit=True`?
