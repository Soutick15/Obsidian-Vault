"""
Day 3 Lab — Generation, Decoding Parameters & Model Selection
=============================================================
starter.py — fill in the TODOs to complete the lab

Sections:
  1. Decoding visualiser  — pure numpy, no API
  2. Provider-flexible LLM call — mock by default, real API if env var set
  3. Model selection comparison table

Run when you think you're done:
    python starter.py

See solution.py for the working reference implementation.
"""

import os
import random

import numpy as np

# ---------------------------------------------------------------------------
# SECTION 1 — DECODING VISUALISER (pure numpy)
# ---------------------------------------------------------------------------

VOCAB = [
    "cat",
    "dog",
    "bird",
    "fish",
    "lion",
    "tree",
    "sky",
    "sun",
    "moon",
    "star",
]

# A raw logit vector (unnormalised scores the model might produce)
RAW_LOGITS = np.array([3.5, 2.8, 1.2, 0.9, 2.1, 0.3, 1.8, 2.5, 1.5, 0.6])


def softmax(logits: np.ndarray) -> np.ndarray:
    """
    TODO: Implement numerically stable softmax.
    Hint: subtract np.max(logits) before exponentiating to avoid overflow.
    Return a probability array that sums to 1.
    """
    raise NotImplementedError("Implement softmax")


def apply_temperature(logits: np.ndarray, temperature: float) -> np.ndarray:
    """
    TODO: Scale logits by temperature.
    Low temperature → sharper distribution.
    High temperature → flatter distribution.
    """
    raise NotImplementedError("Implement apply_temperature")


def top_k_filter(probs: np.ndarray, k: int) -> np.ndarray:
    """
    TODO: Zero out all probabilities except the top-k; re-normalise so they sum to 1.
    If k >= len(probs) or k <= 0, return probs unchanged.
    Hint: np.sort(probs)[-k] gives the k-th largest value.
    """
    raise NotImplementedError("Implement top_k_filter")


def top_p_filter(probs: np.ndarray, p: float) -> np.ndarray:
    """
    TODO: Keep the smallest set of tokens whose cumulative probability >= p; re-normalise.
    Steps:
      1. Sort tokens by probability descending.
      2. Compute cumulative sum.
      3. Include a token if its cumulative sum (before adding it) < p.
      4. Zero out excluded tokens; re-normalise.
    If p >= 1.0, return probs unchanged.
    Always include at least the top-1 token, even if it alone exceeds p.
    """
    raise NotImplementedError("Implement top_p_filter")


def print_distribution(label: str, probs: np.ndarray, vocab: list[str]) -> None:
    """Pretty-print a probability distribution as a bar chart."""
    print(f"\n  {label}")
    print("  " + "-" * 52)
    for token, prob in sorted(zip(vocab, probs), key=lambda x: -x[1]):
        bar = "█" * int(prob * 40)
        print(f"  {token:8s}  {prob:6.3f}  {bar}")


def run_decoding_visualiser() -> None:
    print("=" * 60)
    print("SECTION 1 — DECODING PARAMETER VISUALISER")
    print("=" * 60)
    print(f"\nVocabulary: {VOCAB}")
    print(f"Raw logits: {RAW_LOGITS}")

    # TODO: Compute baseline probabilities with softmax at T=1.0
    # base_probs = ...
    # print_distribution("Baseline (T=1.0)", base_probs, VOCAB)

    # TODO: Show temperature effect for T in [0.2, 0.5, 1.0, 1.5, 2.0]
    # for temp in [...]:
    #     ...

    # TODO: Show top-k effect (at T=1.0) for k in [1, 3, 5, 10]
    # for k in [...]:
    #     ...

    # TODO: Show top-p effect (at T=1.0) for p in [0.5, 0.8, 0.9, 0.95, 1.0]
    # for p in [...]:
    #     ...

    # TODO: Show combined T=0.8 + top-p=0.9
    # ...

    print("\n  INSIGHT: Low temperature concentrates probability on top tokens.")
    print(
        "  High temperature spreads it. Top-k/top-p clip low-probability tail tokens."
    )


# ---------------------------------------------------------------------------
# SECTION 2 — PROVIDER-FLEXIBLE LLM CALL
# ---------------------------------------------------------------------------

PROMPT = "Name one practical use case for a large language model in a software company. Be concise — one sentence only."
SYSTEM_PROMPT = "You are a helpful AI assistant. Always respond in one sentence."


class MockLLMClient:
    """
    Built-in mock — simulates LLM output variation with temperature.
    No API key needed.
    """

    LOW_TEMP_RESPONSES = [
        "A large language model can automate code review by detecting common bugs and style violations in pull requests.",
        "A large language model can power an internal documentation search assistant that answers developer questions in natural language.",
    ]

    HIGH_TEMP_RESPONSES = [
        "Imagine an LLM that writes your sprint retrospectives, turning raw bullet points into surprisingly insightful team narratives.",
        "An LLM could auto-generate test case descriptions from Jira tickets, saving the QA team hours of boilerplate writing each week.",
        "You could wire an LLM to your Slack incident channel to draft post-mortems in real time as the on-call engineer types updates.",
        "An LLM could act as a pair programmer that explains legacy COBOL code to developers who have never seen it before.",
    ]

    def complete(self, prompt: str, system: str, temperature: float) -> str:
        random.seed(int(temperature * 10))
        if temperature <= 0.3:
            return random.choice(self.LOW_TEMP_RESPONSES)
        elif temperature <= 0.8:
            pool = self.LOW_TEMP_RESPONSES + self.HIGH_TEMP_RESPONSES[:2]
            return random.choice(pool)
        else:
            return random.choice(self.HIGH_TEMP_RESPONSES)

    @property
    def provider_name(self) -> str:
        return "MOCK"


def get_client():
    """
    TODO: Implement provider detection.
    1. Check ANTHROPIC_API_KEY — if set, try to import anthropic and return a client.
    2. Else check OPENAI_API_KEY — if set, try to import openai and return a client.
    3. Else return MockLLMClient().
    Print a message saying which provider is being used.

    For the Anthropic client:
      - Use model "claude-haiku-4-5", max_tokens=128
    For the OpenAI client:
      - Use model "gpt-5-mini", max_tokens=128
    """
    print("  No API key detected — running with built-in mock client.")
    return MockLLMClient()


def run_temperature_comparison() -> None:
    print("\n" + "=" * 60)
    print("SECTION 2 — TEMPERATURE COMPARISON (LLM CALL)")
    print("=" * 60)
    print(f'\nPrompt: "{PROMPT}"\n')

    client = get_client()

    # TODO: Call client.complete() at temperature=0.0 and temperature=1.0
    # Run each 3 times and print the results side by side.
    # Print a brief insight comparing the two sets of outputs.
    print("  (TODO: implement temperature comparison)")


# ---------------------------------------------------------------------------
# SECTION 3 — MODEL SELECTION COMPARISON TABLE
# ---------------------------------------------------------------------------

MODEL_TABLE = [
    # TODO: Fill in at least 6 rows.
    # Format: (Family, Tier, Capability, Cost, Latency, Context, Hosting)
    # Example:
    # ("Claude (Anthropic)", "Small/Fast (Haiku class)", "Good", "$", "Low", "200K", "API only"),
]


def run_model_selection_table() -> None:
    print("\n" + "=" * 60)
    print("SECTION 3 — MODEL SELECTION COMPARISON TABLE")
    print("=" * 60)
    print("  * 'Free' = infrastructure cost only; no per-token fee\n")

    col_widths = [20, 22, 11, 6, 10, 10, 22]
    headers = ["Family", "Tier", "Capability", "Cost", "Latency", "Context", "Hosting"]

    def row_str(cells):
        return "  " + "  ".join(str(c).ljust(w) for c, w in zip(cells, col_widths))

    separator = "  " + "-" * (sum(col_widths) + 2 * len(col_widths))

    print(row_str(headers))
    print(separator)

    # TODO: Print MODEL_TABLE rows (or add your own rows above and print them here)
    if not MODEL_TABLE:
        print("  (TODO: populate MODEL_TABLE above)")
    else:
        for row in MODEL_TABLE:
            print(row_str(row))

    print(separator)
    print("\n  TODO: Add 3–5 decision heuristics (e.g. 'Data residency → self-hosted')")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------


def main() -> None:
    print("\n" + "#" * 60)
    print("#  DAY 3 LAB — GENERATION, DECODING & MODEL SELECTION  #")
    print("#" * 60)

    run_decoding_visualiser()
    run_temperature_comparison()
    run_model_selection_table()

    print("\n" + "=" * 60)
    print("LAB COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
