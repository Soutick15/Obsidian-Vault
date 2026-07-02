"""
Day 3 Lab — Generation, Decoding Parameters & Model Selection
=============================================================
solution.py — fully working solution (no API key required)

Sections:
  1. Decoding visualiser  — pure numpy, no API
  2. Provider-flexible LLM call — mock by default, real API if env var set
  3. Model selection comparison table

Run:
    python solution.py

Optional real API call:
    ANTHROPIC_API_KEY=sk-ant-... python solution.py
    OPENAI_API_KEY=sk-...        python solution.py
"""

import math
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
    """Numerically stable softmax."""
    shifted = logits - np.max(logits)
    exp_l = np.exp(shifted)
    return exp_l / exp_l.sum()


def apply_temperature(logits: np.ndarray, temperature: float) -> np.ndarray:
    """Divide logits by temperature before softmax."""
    if temperature <= 0:
        raise ValueError("Temperature must be > 0")
    return logits / temperature


def top_k_filter(probs: np.ndarray, k: int) -> np.ndarray:
    """Zero out all probabilities except the top-k; re-normalise."""
    if k <= 0 or k >= len(probs):
        return probs
    # Find the k-th largest value
    threshold = np.sort(probs)[-k]
    filtered = np.where(
        probs >= threshold, probs, 0.0
    )  # >= can include >k tokens on ties; acceptable tie-breaking behaviour
    total = filtered.sum()
    if total == 0:
        return probs  # fallback: nothing to filter
    return filtered / total


def top_p_filter(probs: np.ndarray, p: float) -> np.ndarray:
    """Keep the smallest set of tokens whose cumulative prob >= p; re-normalise."""
    if p >= 1.0:
        return probs
    sorted_indices = np.argsort(probs)[::-1]  # descending
    sorted_probs = probs[sorted_indices]
    cumulative = np.cumsum(sorted_probs)
    # Include tokens until cumulative probability exceeds p
    cutoff_mask = (
        cumulative - sorted_probs < p
    )  # include if adding this token keeps us under threshold
    cutoff_mask[0] = True  # always keep at least top-1, even if it alone exceeds p
    filtered_sorted = np.where(cutoff_mask, sorted_probs, 0.0)
    # Map back to original order
    filtered = np.zeros_like(probs)
    filtered[sorted_indices] = filtered_sorted
    total = filtered.sum()
    if total == 0:
        return probs
    return filtered / total


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

    # --- Baseline ---
    base_probs = softmax(RAW_LOGITS)
    print_distribution("Baseline (T=1.0)", base_probs, VOCAB)

    # --- Temperature effect ---
    for temp in [0.2, 0.5, 1.0, 1.5, 2.0]:
        scaled_logits = apply_temperature(RAW_LOGITS, temp)
        probs = softmax(scaled_logits)
        print_distribution(f"Temperature = {temp}", probs, VOCAB)

    # --- Top-k effect (at T=1.0) ---
    for k in [1, 3, 5, 10]:
        probs = top_k_filter(base_probs.copy(), k)
        print_distribution(f"Top-k (k={k}, T=1.0)", probs, VOCAB)

    # --- Top-p effect (at T=1.0) ---
    for p in [0.5, 0.8, 0.9, 0.95, 1.0]:
        probs = top_p_filter(base_probs.copy(), p)
        print_distribution(f"Top-p (p={p}, T=1.0)", probs, VOCAB)

    # --- Combined: T=0.8, top-p=0.9 (typical production setting) ---
    combined_logits = apply_temperature(RAW_LOGITS, 0.8)
    combined_probs = top_p_filter(softmax(combined_logits), 0.9)
    print_distribution(
        "Combined: T=0.8 + top-p=0.9 (typical chat setting)", combined_probs, VOCAB
    )

    print("\n  INSIGHT: Low temperature concentrates probability on top tokens.")
    print(
        "  High temperature spreads it. Top-k/top-p clip low-probability tail tokens."
    )


# ---------------------------------------------------------------------------
# SECTION 2 — PROVIDER-FLEXIBLE LLM CALL
# ---------------------------------------------------------------------------

PROMPT = "Name one practical use case for a large language model in a software company. Be concise — one sentence only."

SYSTEM_PROMPT = "You are a helpful AI assistant. Always respond in one sentence."


# -- Mock client (no API key needed) ----------------------------------------


class MockLLMClient:
    """
    Simulates LLM behaviour with a small deterministic vocabulary to
    demonstrate how temperature affects output variation.
    """

    # Pre-written responses at different temperature bands
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
        """Return a mock completion that varies with temperature."""
        random.seed(int(temperature * 10))  # seed gives reproducibility in demo
        if temperature <= 0.3:
            return random.choice(self.LOW_TEMP_RESPONSES)
        elif temperature <= 0.8:
            # Mix — pick from combined pool
            pool = self.LOW_TEMP_RESPONSES + self.HIGH_TEMP_RESPONSES[:2]
            return random.choice(pool)
        else:
            return random.choice(self.HIGH_TEMP_RESPONSES)

    @property
    def provider_name(self) -> str:
        return "MOCK"


# -- Anthropic client (optional) --------------------------------------------


def try_anthropic_client():
    """Return an Anthropic-backed client if the key is present, else None."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        import anthropic  # noqa: PLC0415
    except ImportError:
        print(
            "  [NOTE] ANTHROPIC_API_KEY is set but 'anthropic' package not installed."
        )
        print("         Run: pip install anthropic")
        return None

    class AnthropicClient:
        def __init__(self, key: str) -> None:
            self._client = anthropic.Anthropic(api_key=key)

        def complete(self, prompt: str, system: str, temperature: float) -> str:
            response = self._client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=128,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()

        @property
        def provider_name(self) -> str:
            return "Anthropic (claude-haiku-4-5)"

    return AnthropicClient(api_key)


# -- OpenAI client (optional) -----------------------------------------------


def try_openai_client():
    """Return an OpenAI-backed client if the key is present, else None."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        import openai  # noqa: PLC0415
    except ImportError:
        print("  [NOTE] OPENAI_API_KEY is set but 'openai' package not installed.")
        print("         Run: pip install openai")
        return None

    class OpenAIClient:
        def __init__(self, key: str) -> None:
            self._client = openai.OpenAI(api_key=key)

        def complete(self, prompt: str, system: str, temperature: float) -> str:
            response = self._client.chat.completions.create(
                model="gpt-5-mini",
                max_tokens=128,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content.strip()

        @property
        def provider_name(self) -> str:
            return "OpenAI (gpt-5-mini)"

    return OpenAIClient(api_key)


def get_client():
    """Return the best available client: Anthropic > OpenAI > Mock."""
    client = try_anthropic_client() or try_openai_client()
    if client is None:
        print("  No API key detected — running with built-in mock client.")
        print("  (Set ANTHROPIC_API_KEY or OPENAI_API_KEY to use a real model.)\n")
        client = MockLLMClient()
    else:
        print(f"  Using provider: {client.provider_name}\n")
    return client


def run_temperature_comparison() -> None:
    print("\n" + "=" * 60)
    print("SECTION 2 — TEMPERATURE COMPARISON (LLM CALL)")
    print("=" * 60)
    print(f'\nPrompt: "{PROMPT}"\n')

    client = get_client()

    temperatures = [0.0, 1.0]
    results: dict[float, list[str]] = {}

    for temp in temperatures:
        responses = []
        n_samples = 3  # run 3 times to show variation
        for i in range(n_samples):
            # For mock, use slight temperature variation per sample to show spread
            effective_temp = temp if temp > 0 else 0.1 * (i + 1) * 0.01 + temp
            response = client.complete(
                PROMPT, SYSTEM_PROMPT, temperature=effective_temp if temp > 0 else temp
            )
            responses.append(response)
        results[temp] = responses

    for temp, responses in results.items():
        label = (
            "LOW (T=0.0) — deterministic / focused"
            if temp == 0.0
            else "HIGH (T=1.0) — varied / creative"
        )
        print(f"\n  Temperature = {temp}  [{label}]")
        print("  " + "-" * 56)
        for i, r in enumerate(responses, 1):
            print(f"  Sample {i}: {r}")

    print("\n  INSIGHT: At T=0, outputs are identical (or very similar).")
    print("  At T=1.0, each sample varies. Match temperature to your task.")


# ---------------------------------------------------------------------------
# SECTION 3 — MODEL SELECTION COMPARISON TABLE
# ---------------------------------------------------------------------------

MODEL_TABLE = [
    # (Family, Model tier, Capability, Cost tier, Latency, Context, Hosting)
    (
        "Claude (Anthropic)",
        "Small/Fast (Haiku class)",
        "Good",
        "$",
        "Low",
        "200K",
        "API only",
    ),
    (
        "Claude (Anthropic)",
        "Mid (Sonnet class)",
        "Very Good",
        "$$",
        "Medium",
        "200K",
        "API only",
    ),
    (
        "Claude (Anthropic)",
        "Large (Opus class)",
        "Excellent",
        "$$$",
        "High",
        "200K",
        "API only",
    ),
    ("GPT (OpenAI)", "Small (5-mini)", "Good", "$", "Low", "128K", "API / Azure"),
    ("GPT (OpenAI)", "Large (4o)", "Excellent", "$$$", "Medium", "128K", "API / Azure"),
    (
        "GPT o-series",
        "Reasoning (o3)",
        "Top",
        "$$$$",
        "Very High",
        "200K",
        "API / Azure",
    ),
    ("Llama (Meta)", "3B–8B", "Fair", "Free*", "Very Low", "8K-128K", "Self-hosted"),
    ("Llama (Meta)", "70B+", "Very Good", "Free*", "Medium", "128K", "Self-hosted"),
    (
        "Mistral",
        "7B / Mixtral 8x7B",
        "Good",
        "Free*",
        "Low",
        "32K",
        "Self-hosted / API",
    ),
    (
        "Qwen (Alibaba)",
        "7B–72B",
        "Good (CJK)",
        "Free*",
        "Medium",
        "32K-128K",
        "Self-hosted / API",
    ),
    (
        "Gemma (Google)",
        "2B–9B",
        "Fair",
        "Free*",
        "Very Low",
        "8K",
        "Self-hosted / Edge",
    ),
]


def run_model_selection_table() -> None:
    print("\n" + "=" * 60)
    print("SECTION 3 — MODEL SELECTION COMPARISON TABLE")
    print("=" * 60)
    print("  * 'Free' = infrastructure cost only (GPU/CPU); no per-token fee\n")

    col_widths = [20, 22, 11, 6, 10, 10, 22]
    headers = ["Family", "Tier", "Capability", "Cost", "Latency", "Context", "Hosting"]

    def row_str(cells):
        return "  " + "  ".join(str(c).ljust(w) for c, w in zip(cells, col_widths))

    separator = "  " + "-" * (sum(col_widths) + 2 * len(col_widths))

    print(row_str(headers))
    print(separator)
    for row in MODEL_TABLE:
        print(row_str(row))

    print(separator)
    print("\n  DECISION HEURISTICS:")
    print("  • Prototype / iterate fast  →  Small/Fast hosted (Haiku / 4o-mini)")
    print("  • Hard reasoning / code     →  Sonnet / Opus / GPT-4o / o3")
    print("  • Data residency required   →  Self-hosted Llama 70B or Mistral")
    print("  • Multilingual (CJK)        →  Benchmark Qwen alongside Claude/GPT")
    print("  • Edge / mobile             →  Llama 3.2 1B-3B or Gemma 2B")
    print(
        "  • Always benchmark on YOUR task — leaderboard ranks don't always generalise."
    )


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
    print("Next steps:")
    print("  • Try starter.py and fill in the TODOs yourself")
    print("  • Set ANTHROPIC_API_KEY or OPENAI_API_KEY to run with a real model")
    print("  • Experiment with different temperature + top-p combos in the visualiser")
    print()


if __name__ == "__main__":
    main()
