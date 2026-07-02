"""
Day 4 Lab — Reusable Prompt Library (STARTER)

Complete all five TODO blocks. Run with:
    python starter.py              # mock (no key needed)
    ANTHROPIC_API_KEY=... python starter.py
    OPENAI_API_KEY=...   python starter.py
"""

import json
import os

# ---------------------------------------------------------------------------
# Attempt to load .env (optional — works if python-dotenv is installed)
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on shell environment


# ===========================================================================
# SECTION 1 — Prompt builder functions
# Each function returns a list of message dicts: [{"role": ..., "content": ...}]
# The caller passes this list to run() together with a system string.
# ===========================================================================


def few_shot_classify(text: str, examples: list[dict], labels: list[str]) -> list[dict]:
    """
    Build a messages list for few-shot sentiment/topic classification.

    Args:
        text:     The input text to classify.
        examples: List of dicts with keys "input" and "label".
                  E.g. [{"input": "Great product!", "label": "POSITIVE"}, ...]
        labels:   Allowed label strings. E.g. ["POSITIVE", "NEGATIVE", "NEUTRAL"]

    Returns:
        A messages list ready to pass to run().

    TODO 1:
        - Format the examples as lines: 'Review: "<input>" → <label>'
        - Append the target text as: 'Review: "<text>" →'
        - Wrap everything in a single user message.
        - Include the allowed labels in the instruction.
    """
    # TODO 1 — replace the line below with your implementation
    raise NotImplementedError("TODO 1: implement few_shot_classify")


def extract_json(text: str, fields: list[str]) -> list[dict]:
    """
    Build a messages list that instructs the model to extract named fields
    from text and return them as a JSON object.

    Args:
        text:   The source text (e.g. an email body).
        fields: Field names to extract. E.g. ["sender_name", "sender_email", "date"]
                If a field is not found, the model should use null.

    Returns:
        A messages list ready to pass to run().

    TODO 2:
        - List the fields in the prompt.
        - Wrap text in <document>...</document> delimiters.
        - Instruct: return ONLY a JSON object, no markdown, no explanation.
        - Add a one-line example of the expected JSON shape.
    """
    # TODO 2 — replace the line below with your implementation
    raise NotImplementedError("TODO 2: implement extract_json")


def summarize(text: str, bullets: int = 3) -> list[dict]:
    """
    Build a messages list for bullet-point summarisation.

    Args:
        text:    The text to summarise.
        bullets: Number of bullet points to produce.

    Returns:
        A messages list ready to pass to run().

    TODO 3:
        - Instruct the model to produce exactly <bullets> bullet points.
        - Each bullet ≤ 20 words.
        - Wrap text in <document>...</document> delimiters.
    """
    # TODO 3 — replace the line below with your implementation
    raise NotImplementedError("TODO 3: implement summarize")


def rewrite(
    text: str, style: str = "concise and formal", max_pct: int = 80
) -> list[dict]:
    """
    Build a messages list for text rewriting.

    Args:
        text:    The text to rewrite.
        style:   Target style description.
        max_pct: Maximum output length as % of input word count.

    Returns:
        A messages list ready to pass to run().

    TODO 4:
        - Instruct the model to rewrite to the given style.
        - Cap at max_pct% of original word count.
        - Keep all factual content; only change style/length.
        - Wrap original text in <original>...</original> delimiters.
    """
    # TODO 4 — replace the line below with your implementation
    raise NotImplementedError("TODO 4: implement rewrite")


# ===========================================================================
# SECTION 2 — Safe JSON parser
# ===========================================================================


def parse_json_safe(text: str, fallback: dict | None = None) -> dict:
    """
    Parse LLM output as JSON, stripping markdown fences if present.
    Returns fallback dict on parse failure (never raises).
    """
    try:
        t = text.strip()
        # Strip ```json ... ``` or ``` ... ``` fences the model sometimes adds.
        # NOTE: str.strip(chars) removes individual characters, not substrings —
        # use split/rsplit to correctly remove the opening and closing fence lines.
        if t.startswith("```"):
            t = t.split("\n", 1)[1] if "\n" in t else t
            t = t.rsplit("```", 1)[0]
        t = t.strip()
        return json.loads(t)
    except json.JSONDecodeError as exc:
        print(f"[WARN] JSON parse failed: {exc}")
        return fallback if fallback is not None else {}


# ===========================================================================
# SECTION 3 — Provider-flexible runner
# ===========================================================================


def _mock_response(messages: list[dict], system: str) -> str:
    """
    Deterministic mock that returns plausible output based on the last
    user message content — no API call needed.
    """
    last_content = messages[-1]["content"] if messages else ""

    # Classification: look for the "→" pattern at the end
    if "→" in last_content and "POSITIVE" in last_content:
        # Count examples to detect the target (last "→" with no label)
        lines = [ln for ln in last_content.splitlines() if "→" in ln]
        last_line = lines[-1] if lines else ""
        if last_line.strip().endswith("→"):
            # Heuristic: pick label based on keywords
            target = last_line.lower()
            if any(
                w in target
                for w in ["late", "damage", "broken", "disappoint", "bad", "poor"]
            ):
                return "NEGATIVE"
            if any(
                w in target
                for w in ["great", "love", "excellent", "amazing", "perfect"]
            ):
                return "POSITIVE"
            return "NEUTRAL"

    # JSON extraction: return a plausible JSON object
    if "JSON object" in last_content or "json" in system.lower():
        import re

        # Try to extract an email address from the text
        email_match = re.search(r"[\w.+-]+@[\w-]+\.\w+", last_content)
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", last_content)
        name_match = re.search(
            r"Dr\.?\s+\w+|Mr\.?\s+\w+|Ms\.?\s+\w+|\b([A-Z][a-z]+\s[A-Z][a-z]+)\b",
            last_content,
        )
        return json.dumps(
            {
                "sender_name": name_match.group(0).strip() if name_match else None,
                "sender_email": email_match.group(0) if email_match else None,
                "meeting_date": date_match.group(0) if date_match else None,
                "meeting_topic": "Q3 budget"
                if "budget" in last_content.lower()
                else None,
            }
        )

    # Summarise
    if (
        "bullet" in last_content.lower()
        or "summarise" in last_content.lower()
        or "summarize" in last_content.lower()
    ):
        first_80 = last_content[:80].replace("\n", " ").strip()
        return f"[MOCK SUMMARY] {first_80}..."

    # Rewrite
    if "rewrite" in last_content.lower() or "<original>" in last_content:
        first_80 = last_content[:80].replace("\n", " ").strip()
        return f"[MOCK REWRITE] {first_80}..."

    return "[MOCK] No specific handler matched."


def run(messages: list[dict], system: str = "You are a helpful assistant.") -> str:
    """
    Send messages to the best available provider.

    Detection order:
      1. ANTHROPIC_API_KEY in env  → use Claude (claude-haiku-4-5)
      2. OPENAI_API_KEY in env     → use OpenAI (gpt-5-mini)
      3. Neither (or USE_MOCK=true) → return deterministic mock response

    Args:
        messages: List of {"role": ..., "content": ...} dicts (user/assistant only).
        system:   System prompt string.

    Returns:
        The model's reply as a plain string.

    TODO 5:
        - If USE_MOCK env var == "true", call _mock_response() and return.
        - Check ANTHROPIC_API_KEY; if present, import anthropic and call
          client.messages.create() with model="claude-haiku-4-5", max_tokens=512.
          Return response.content[0].text.
        - Check OPENAI_API_KEY; if present, import openai and call
          client.chat.completions.create() with model="gpt-5-mini", max_tokens=512.
          Prepend {"role":"system","content": system} to the messages list.
          Return response.choices[0].message.content.
        - Fallback: call _mock_response() and return the result.
    """
    # TODO 5 — replace the line below with your implementation
    raise NotImplementedError("TODO 5: implement run()")


# ===========================================================================
# Demo — runs all four prompt builders and prints results
# ===========================================================================


def demo():
    provider = "MOCK"
    if os.getenv("USE_MOCK", "").lower() != "true":
        if os.getenv("ANTHROPIC_API_KEY"):
            provider = "Anthropic (Claude)"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "OpenAI"

    print(f"\n=== Provider: {provider} ===\n")

    # --- few_shot_classify ---
    examples = [
        {"input": "Loved the product, arrived super quickly!", "label": "POSITIVE"},
        {"input": "Broke after two days. Very disappointed.", "label": "NEGATIVE"},
        {"input": "It arrived on time.", "label": "NEUTRAL"},
        {
            "input": "Absolutely terrible customer service experience.",
            "label": "NEGATIVE",
        },
        {"input": "Works as described.", "label": "NEUTRAL"},
    ]
    target = "The shipment arrived three days late and was damaged."
    msgs = few_shot_classify(target, examples, ["POSITIVE", "NEGATIVE", "NEUTRAL"])
    result = run(
        msgs, system="You are a precise text classifier. Return only the label."
    )
    print("--- few_shot_classify ---")
    print(f'Input   : "{target}"')
    print(f"Result  : {result.strip()}\n")

    # --- extract_json ---
    email_text = (
        "Please reschedule our meeting with Dr. Patel (d.patel@clinic.org) "
        "to 2026-07-15 to discuss Q3 budget."
    )
    fields = ["sender_name", "sender_email", "meeting_date", "meeting_topic"]
    msgs = extract_json(email_text, fields)
    raw = run(msgs, system="You extract structured data. Return only JSON.")
    parsed = parse_json_safe(raw, fallback={f: None for f in fields})
    print("--- extract_json ---")
    print(f'Input   : "{email_text}"')
    print(f"Parsed  : {parsed}\n")

    # --- summarize ---
    article = (
        "Artificial intelligence is transforming industries from healthcare to finance. "
        "Recent advances in large language models have enabled applications that were "
        "impossible five years ago, including automated document analysis, code generation, "
        "and real-time translation. However, concerns around data privacy, bias, and "
        "energy consumption remain active areas of research and regulation."
    )
    msgs = summarize(article, bullets=3)
    result = run(msgs, system="You are a concise summariser.")
    print("--- summarize ---")
    print(f"Input   : {len(article)} chars")
    print(f"Result  : {result.strip()}\n")

    # --- rewrite ---
    verbose = (
        "I am writing to you in order to let you know that it would be greatly "
        "appreciated if you could provide us with your feedback at your earliest "
        "possible convenience."
    )
    msgs = rewrite(verbose, style="concise and formal", max_pct=60)
    result = run(msgs, system="You are a professional editor.")
    print("--- rewrite ---")
    print(f"Input   : {len(verbose)} chars")
    print(f"Result  : {result.strip()}\n")

    print("All demos complete.")


if __name__ == "__main__":
    demo()
