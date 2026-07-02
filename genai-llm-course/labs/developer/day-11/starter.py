"""
Day 11 Starter — LoRA Fine-Tuning Demo
======================================
Work through each TODO in order. Run with:

    python starter.py --smoke     # 1 step, fast verification
    python starter.py             # full demo (a few minutes on CPU)

No API key required.
"""

import argparse
import os

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Day 11 LoRA Fine-Tuning Starter")
parser.add_argument(
    "--smoke",
    action="store_true",
    help="Smoke-test mode: 1 optimizer step, tiny settings, fast exit.",
)
args = parser.parse_args()

SMOKE = args.smoke
MODE_LABEL = "SMOKE (1 step, tiny settings)" if SMOKE else "FULL DEMO"

print("=== Day 11: LoRA Fine-Tuning Demo (Starter) ===")
print(f"Mode: {MODE_LABEL}\n")

# ---------------------------------------------------------------------------
# Hyperparameters — smoke mode overrides are already set for you
# ---------------------------------------------------------------------------
MODEL_ID = "sshleifer/tiny-gpt2"   # ~10 MB toy model; swap for a real model on GPU

LORA_R = 2 if SMOKE else 4
LORA_ALPHA = 4 if SMOKE else 8
LORA_DROPOUT = 0.0
TARGET_MODULES = ["c_attn"]        # GPT-2 uses combined QKV projection

MAX_LENGTH = 64 if SMOKE else 128
BATCH_SIZE = 2
NUM_EPOCHS = 1
NUM_STEPS = 1 if SMOKE else None   # None = run full epochs
LEARNING_RATE = 5e-4
ADAPTER_DIR = "./lora-adapter-smoke" if SMOKE else "./lora-adapter"

# ---------------------------------------------------------------------------
# Step 1 — Build the instruction dataset
# ---------------------------------------------------------------------------
print("[1/5] Building HR instruction dataset...")

# TODO: Define a list of 12 HR Q&A dictionaries.
# Each dict should have keys: "instruction" and "output".
# Use facts from the Acme Corp HR corpus (leave policy, benefits, etc.).
# Example:
#   {"instruction": "How many PTO days do new employees receive?",
#    "output": "New employees at Acme Corp accrue 15 days (120 hours) of PTO per year."}
#
# Tip: aim for diversity — cover at least 4 different HR topics.

raw_examples: list[dict] = []
# YOUR CODE HERE

print(f"      Loaded {len(raw_examples)} examples.")

# ---------------------------------------------------------------------------
# Step 2 — Load the base model and tokenizer
# ---------------------------------------------------------------------------
print(f"[2/5] Loading base model: {MODEL_ID}")

from transformers import AutoTokenizer, AutoModelForCausalLM  # noqa: E402

# TODO: Load the tokenizer from MODEL_ID.
# Set pad_token = eos_token (GPT-2 has no pad token by default).
tokenizer = None  # replace with AutoTokenizer.from_pretrained(...)

# TODO: Load the model from MODEL_ID.
# Hint: use AutoModelForCausalLM.from_pretrained(MODEL_ID)
model = None  # replace with AutoModelForCausalLM.from_pretrained(...)

# TODO: Print total parameter count.
# Hint: sum(p.numel() for p in model.parameters())
total_params = 0  # YOUR CODE HERE
print(f"      Parameters: {total_params:,}")

# ---------------------------------------------------------------------------
# Step 3 — Apply LoRA adapter
# ---------------------------------------------------------------------------
print("[3/5] Applying LoRA adapter...")

from peft import LoraConfig, get_peft_model, TaskType  # noqa: E402

# TODO: Create a LoraConfig with:
#   r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT,
#   target_modules=TARGET_MODULES, bias="none", task_type=TaskType.CAUSAL_LM
lora_config = None  # replace with LoraConfig(...)

# TODO: Wrap the model with get_peft_model(model, lora_config)
model = model  # replace with get_peft_model(model, lora_config)

# TODO: Print trainable parameter count and percentage.
# Hint: use model.print_trainable_parameters() — it prints directly.
# YOUR CODE HERE

# ---------------------------------------------------------------------------
# Step 4 — Tokenize the dataset and train
# ---------------------------------------------------------------------------
print("[4/5] Training...")

import torch  # noqa: E402
from torch.optim import AdamW  # noqa: E402
from torch.utils.data import Dataset, DataLoader  # noqa: E402

# TODO: Define a PROMPT_TEMPLATE string.
# It should combine instruction and output into a single string the model
# will be trained to generate. Example:
#   PROMPT_TEMPLATE = "Q: {instruction}\nA: {output}"
PROMPT_TEMPLATE = ""  # YOUR CODE HERE


class HRDataset(Dataset):
    """Tokenizes HR Q&A examples into (input_ids, labels) pairs."""

    def __init__(self, examples, tokenizer, max_length):
        self.items = []
        for ex in examples:
            # TODO: Format the example using PROMPT_TEMPLATE.
            text = ""  # YOUR CODE HERE

            # TODO: Tokenize `text` with:
            #   tokenizer(text, truncation=True, max_length=max_length,
            #             padding="max_length", return_tensors="pt")
            enc = None  # YOUR CODE HERE

            input_ids = enc["input_ids"].squeeze(0)
            attention_mask = enc["attention_mask"].squeeze(0)

            # For causal LM, labels = input_ids (loss on all tokens).
            # Padding positions should be -100 so they're ignored by CrossEntropy.
            labels = input_ids.clone()
            labels[attention_mask == 0] = -100

            self.items.append({"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels})

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx]


# TODO: Create an HRDataset from raw_examples, then wrap it in a DataLoader
#       with batch_size=BATCH_SIZE and shuffle=True.
dataset = None   # YOUR CODE HERE
loader = None    # YOUR CODE HERE

# TODO: Create an AdamW optimizer with lr=LEARNING_RATE over model.parameters().
optimizer = None  # YOUR CODE HERE

# Training loop
model.train()
step = 0
for epoch in range(NUM_EPOCHS):
    for batch in loader:
        optimizer.zero_grad()

        # TODO: Forward pass.
        #   Pass input_ids, attention_mask, labels from the batch to the model.
        #   Extract the loss from the outputs.
        loss = None  # YOUR CODE HERE

        # TODO: Backward pass and optimizer step.
        # YOUR CODE HERE

        step += 1
        print(f"      Step {step} | Loss: {loss.item():.4f}")

        if NUM_STEPS and step >= NUM_STEPS:
            break
    if NUM_STEPS and step >= NUM_STEPS:
        break

# TODO: Save the LoRA adapter to ADAPTER_DIR using model.save_pretrained(ADAPTER_DIR).
os.makedirs(ADAPTER_DIR, exist_ok=True)
# YOUR CODE HERE
print(f"      Training complete. Adapter saved to {ADAPTER_DIR}/")

# ---------------------------------------------------------------------------
# Step 5 — Before/After Generation
# ---------------------------------------------------------------------------
print("[5/5] Before/After Generation")

from peft import PeftModel  # noqa: E402

EVAL_PROMPT = "Q: How many PTO days do new employees get?\nA:"

# Load a fresh base model (no adapter) for the "BEFORE" generation.
# TODO: Load the base model again from MODEL_ID (same as Step 2).
base_model = None  # YOUR CODE HERE

def generate(m, prompt, max_new_tokens=40):
    """Generate text from model m given a prompt string."""
    # TODO: Tokenize the prompt, call m.generate(), decode and return the text.
    # Hint: use tokenizer(prompt, return_tensors="pt") and
    #       m.generate(input_ids, max_new_tokens=max_new_tokens,
    #                  pad_token_id=tokenizer.eos_token_id, do_sample=False)
    return ""  # YOUR CODE HERE


print(f"\n  Prompt: \"{EVAL_PROMPT}\"")

# TODO: Generate BEFORE text using base_model.
before = generate(base_model, EVAL_PROMPT)
print(f"\n  BEFORE (base model):\n  {before}")

# TODO: Load the saved adapter with PeftModel.from_pretrained(base_model, ADAPTER_DIR).
#       Set to eval mode and generate AFTER text.
adapted_model = None  # YOUR CODE HERE
after = generate(adapted_model, EVAL_PROMPT)
print(f"\n  AFTER (LoRA adapter):\n  {after}")

print(f"\nDone. Adapter saved to: {ADAPTER_DIR}/")
