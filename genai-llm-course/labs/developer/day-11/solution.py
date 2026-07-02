"""
Day 11 Solution — LoRA Fine-Tuning Demo
========================================
Complete working implementation. Run with:

    python solution.py --smoke     # 1 step, fast verification (< 30 s on CPU)
    python solution.py             # full demo

No API key required. Downloads sshleifer/tiny-gpt2 (~10 MB) on first run.
"""

import argparse
import os

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Day 11 LoRA Fine-Tuning Solution")
parser.add_argument(
    "--smoke",
    action="store_true",
    help="Smoke-test mode: 1 optimizer step, tiny settings, fast exit.",
)
args = parser.parse_args()

SMOKE = args.smoke
MODE_LABEL = "SMOKE (1 step, tiny settings)" if SMOKE else "FULL DEMO"

print("=== Day 11: LoRA Fine-Tuning Demo ===")
print(f"Mode: {MODE_LABEL}\n")

# ---------------------------------------------------------------------------
# Hyperparameters
# ---------------------------------------------------------------------------
MODEL_ID = "sshleifer/tiny-gpt2"   # Tiny model (~10 MB); CPU-friendly toy

LORA_R = 2 if SMOKE else 4
LORA_ALPHA = 4 if SMOKE else 8
LORA_DROPOUT = 0.0
TARGET_MODULES = ["c_attn"]        # GPT-2 uses a single combined QKV projection

MAX_LENGTH = 64 if SMOKE else 128
BATCH_SIZE = 2
NUM_EPOCHS = 1
NUM_STEPS = 1 if SMOKE else None   # None = run all steps in NUM_EPOCHS
LEARNING_RATE = 5e-4
ADAPTER_DIR = "./lora-adapter-smoke" if SMOKE else "./lora-adapter"

# Prompt template — MUST be identical at train and inference time.
PROMPT_TEMPLATE = "Q: {instruction}\nA: {output}"
PROMPT_TEMPLATE_INFERENCE = "Q: {instruction}\nA:"

# ---------------------------------------------------------------------------
# Step 1 — Build the HR instruction dataset
# ---------------------------------------------------------------------------
print("[1/5] Building HR instruction dataset (12 examples)...")

# Derived from the Acme Corp HR corpus (data/hr-corpus/).
# Key facts kept consistent with the corpus (see hr-corpus/README.md).
RAW_EXAMPLES = [
    {
        "instruction": "How many PTO days do new employees receive?",
        "output": "New employees at Acme Corp accrue 15 days (120 hours) of PTO per year during their first two years of service.",
    },
    {
        "instruction": "What is the 401(k) employer match at Acme Corp?",
        "output": "Acme Corp matches 100% of employee contributions up to 4% of salary, with a 3-year graded vesting schedule.",
    },
    {
        "instruction": "How long is paid parental leave for primary caregivers?",
        "output": "Primary caregivers receive 16 weeks of fully paid parental leave. Secondary caregivers receive 6 weeks.",
    },
    {
        "instruction": "What is the home office stipend for remote employees?",
        "output": "Remote employees receive a one-time home office stipend of $750 to set up their workspace.",
    },
    {
        "instruction": "How often are performance reviews conducted?",
        "output": "Acme Corp conducts performance reviews twice per year: a mid-year review in July and an annual review in January.",
    },
    {
        "instruction": "What is the employee referral bonus?",
        "output": "Employees who refer a successful candidate receive a $2,000 referral bonus after the new hire completes 90 days.",
    },
    {
        "instruction": "When do annual merit increases take effect?",
        "output": "Annual merit increases are effective March 1 each year.",
    },
    {
        "instruction": "How many days of unused PTO can roll over to the next year?",
        "output": "Up to 5 unused PTO days may carry over into the next calendar year. Any balance above 5 days is forfeited on January 1.",
    },
    {
        "instruction": "What health insurance options does Acme Corp provide?",
        "output": "Acme Corp offers medical, dental, and vision insurance. The company covers a significant portion of the premium for employees and eligible dependents.",
    },
    {
        "instruction": "Is there a waiting period before new employees can use PTO?",
        "output": "No. PTO begins accruing from day one and may be used immediately — there is no waiting period.",
    },
    {
        "instruction": "What are the core hours for remote employees?",
        "output": "Remote employees are expected to be available during core hours of 10 AM to 3 PM in their local time zone.",
    },
    {
        "instruction": "What merit increase range corresponds to a 'Meets Expectations' rating?",
        "output": "A 'Meets Expectations' performance rating corresponds to a merit increase in the range of 3–5%.",
    },
]

print(f"      Loaded {len(RAW_EXAMPLES)} examples.")

# ---------------------------------------------------------------------------
# Step 2 — Load the base model and tokenizer
# ---------------------------------------------------------------------------
print(f"[2/5] Loading base model: {MODEL_ID}")

from transformers import AutoTokenizer, AutoModelForCausalLM  # noqa: E402

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
# GPT-2 has no pad token; use eos_token as pad.
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
total_params = sum(p.numel() for p in model.parameters())
print(f"      Parameters: {total_params:,}")

# ---------------------------------------------------------------------------
# Step 3 — Apply LoRA adapter
# ---------------------------------------------------------------------------
print(f"[3/5] Applying LoRA adapter (r={LORA_R}, alpha={LORA_ALPHA})...")

from peft import LoraConfig, get_peft_model, TaskType  # noqa: E402

lora_config = LoraConfig(
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    lora_dropout=LORA_DROPOUT,
    target_modules=TARGET_MODULES,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

model = get_peft_model(model, lora_config)

# Print trainable parameter summary
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
pct = 100 * trainable / total_params
print(f"      Trainable params: {trainable:,}  ({pct:.4f}% of total)")

# ---------------------------------------------------------------------------
# Step 4 — Tokenize the dataset and train
# ---------------------------------------------------------------------------
print("[4/5] Training...")

import torch  # noqa: E402
from torch.optim import AdamW  # noqa: E402
from torch.utils.data import Dataset, DataLoader  # noqa: E402


class HRDataset(Dataset):
    """Tokenizes HR Q&A examples into (input_ids, labels) pairs for causal LM."""

    def __init__(self, examples, tokenizer, max_length):
        self.items = []
        for ex in examples:
            text = PROMPT_TEMPLATE.format(
                instruction=ex["instruction"],
                output=ex["output"],
            )
            enc = tokenizer(
                text,
                truncation=True,
                max_length=max_length,
                padding="max_length",
                return_tensors="pt",
            )
            input_ids = enc["input_ids"].squeeze(0)
            attention_mask = enc["attention_mask"].squeeze(0)

            # Labels: same as input_ids for causal LM.
            # Padding positions masked with -100 (ignored by CrossEntropyLoss).
            labels = input_ids.clone()
            labels[attention_mask == 0] = -100

            self.items.append(
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "labels": labels,
                }
            )

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx]


dataset = HRDataset(RAW_EXAMPLES, tokenizer, MAX_LENGTH)
loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)

model.train()
step = 0
for epoch in range(NUM_EPOCHS):
    for batch in loader:
        optimizer.zero_grad()

        outputs = model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            labels=batch["labels"],
        )
        loss = outputs.loss
        loss.backward()
        optimizer.step()

        step += 1
        print(f"      Step {step}/{NUM_STEPS if NUM_STEPS else '?'} | Loss: {loss.item():.4f}")

        if NUM_STEPS is not None and step >= NUM_STEPS:
            break
    if NUM_STEPS is not None and step >= NUM_STEPS:
        break

# Save the LoRA adapter (only adapter weights, not the full model).
os.makedirs(ADAPTER_DIR, exist_ok=True)
model.save_pretrained(ADAPTER_DIR)
print(f"      Training complete. Saving adapter to ./{ADAPTER_DIR}/")

# ---------------------------------------------------------------------------
# Step 5 — Before/After Generation
# ---------------------------------------------------------------------------
print("[5/5] Before/After Generation")

from peft import PeftModel  # noqa: E402

EVAL_PROMPT = PROMPT_TEMPLATE_INFERENCE.format(
    instruction="How many PTO days do new employees get?"
)


def generate(m, prompt: str, max_new_tokens: int = 40) -> str:
    """Greedy decode from model m given prompt string."""
    m.eval()
    with torch.no_grad():
        enc = tokenizer(prompt, return_tensors="pt")
        output_ids = m.generate(
            enc["input_ids"],
            max_new_tokens=max_new_tokens,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=False,
        )
    # Decode only the newly generated tokens (exclude the prompt).
    new_ids = output_ids[0][enc["input_ids"].shape[1]:]
    return tokenizer.decode(new_ids, skip_special_tokens=True).strip()


print(f'\n  Prompt: "{EVAL_PROMPT}"')

# BEFORE: fresh base model with no adapter.
print("\n  Loading base model for BEFORE generation...")
base_model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
before = generate(base_model, EVAL_PROMPT)
print(f"\n  BEFORE (base model):\n  {before!r}")

# AFTER: load the saved LoRA adapter on top of the same base model.
print("\n  Loading adapter for AFTER generation...")
adapted_model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
after = generate(adapted_model, EVAL_PROMPT)
print(f"\n  AFTER (LoRA adapter):\n  {after!r}")

print(f"\nDone. Adapter saved to: {ADAPTER_DIR}/")
print("\nNote: With sshleifer/tiny-gpt2 (a random-weight toy model), outputs are")
print("mostly noise — that is expected. The demo validates the training loop,")
print("adapter save/load, and before/after generation pipeline. Run on a real")
print("instruction-tuned model (e.g., Mistral-7B-Instruct) on GPU for")
print("meaningful output differences.")
