"""
Day 4 Lab — Prompt Library (STARTER)

The mock LLM client, the run() helper, and the safe JSON parser are already
written below — you don't need to touch them. Your job is the three TODOs:
(1) write a few-shot classification prompt, (2) write a JSON-extraction
prompt, and (3) call the safe JSON parser in the demo (TODO 3, near the
bottom of this file). See Day 4, Section 3 (Worked Example) in the
curriculum for the pattern to follow.

Run with:
    python starter.py                          # mock (no key needed)
    ANTHROPIC_API_KEY=sk-ant-... python starter.py
    OPENAI_API_KEY=sk-...        python starter.py
    USE_MOCK=true                python starter.py  # force mock even with key
"""

import json
import os
import re

# ---------------------------------------------------------------------------
# Attempt to load .env (optional — works if python-dotenv is installed)
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on shell environment


# ===========================================================================
# SECTION 1 — Prompt builders
# Each returns a list of message dicts: [{"role": ..., "content": ...}]
# ===========================================================================


def few_shot_classify(text: str, examples: list[dict], labels: list[str]) -> list[dict]:
    """
    Build a messages list for few-shot classification.

    Args:
        text:     The input to classify.
        examples: List of {"input": ..., "label": ...} dicts.
        labels:   Allowed label strings.

    Returns:
        messages list for run().
    """
    # TODO 1 — build and return the messages list. Follow Day 4, Section 3:
    #   - Join `labels` with commas; instruct: "Classify ... as exactly one
    #     of: <labels>." and "Return ONLY the label — no explanation."
    #   - One line per example:  'Review: "<input>" -> <label>'
    #   - End with the target line (no label after the arrow): 'Review: "<text>" ->'
    #   - Return  [{"role": "user", "content": <the text you built>}]
    raise NotImplementedError("TODO 1: implement few_shot_classify")


def extract_json(text: str, fields: list[str]) -> list[dict]:
    """
    Build a messages list for structured JSON extraction.

    Args:
        text:   Source text.
        fields: Field names to extract; use null if not found.

    Returns:
        messages list for run().
    """
    # TODO 2 — build and return the messages list. Follow Day 4, Section 2.6:
    #   - List the field names in the instruction.
    #   - Instruct: "Return ONLY a valid JSON object — no markdown fences,
    #     no explanation." and "If a field is not present, use null."
    #   - Show a one-line example shape: {"<field>": null, ...}
    #   - Wrap the source text in <document>...</document> delimiters.
    #   - Return  [{"role": "user", "content": <the text you built>}]
    raise NotImplementedError("TODO 2: implement extract_json")


# ===========================================================================
# SECTION 2 — Safe JSON parser
# ===========================================================================


def parse_json_safe(text: str, fallback: dict | None = None) -> dict:
    """
    Parse LLM output as JSON, stripping markdown fences if present.
    Returns fallback dict on parse failure — never raises.
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
# SECTION 3 — Deterministic mock
# ===========================================================================


def _mock_response(messages: list[dict], system: str) -> str:
    """
    Return a plausible response without any API call.
    Inspects the last user message to decide what to produce.
    """
    last_content = messages[-1]["content"] if messages else ""

    # --- Classification: prompt ends with '->' (no label yet) ---
    if "->" in last_content:
        lines = [ln.strip() for ln in last_content.splitlines() if "->" in ln]
        last_line = lines[-1] if lines else ""
        if last_line.endswith("->"):
            target = last_line.lower()
            if any(
                w in target
                for w in [
                    "late",
                    "damag",
                    "broken",
                    "disappoint",
                    "bad",
                    "poor",
                    "terrible",
                    "worst",
                ]
            ):
                return "NEGATIVE"
            if any(
                w in target
                for w in [
                    "great",
                    "love",
                    "excellent",
                    "amazing",
                    "perfect",
                    "fantastic",
                ]
            ):
                return "POSITIVE"
            return "NEUTRAL"

    # --- JSON extraction: prompt mentions JSON object + fields ---
    if "JSON object" in last_content or "json" in system.lower():
        email_match = re.search(r"[\w.+-]+@[\w-]+\.\w+", last_content)
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", last_content)
        name_match = re.search(r"Dr\.?\s+\w+|Mr\.?\s+\w+|Ms\.?\s+\w+", last_content)
        topic_match = re.search(r"discuss\s+(.+?)(?:\.|$)", last_content, re.IGNORECASE)
        return json.dumps(
            {
                "sender_name": name_match.group(0).strip() if name_match else None,
                "sender_email": email_match.group(0) if email_match else None,
                "meeting_date": date_match.group(0) if date_match else None,
                "meeting_topic": topic_match.group(1).strip() if topic_match else None,
            }
        )

    return "[MOCK] No specific handler matched."


# ===========================================================================
# SECTION 4 — Provider-flexible runner
# ===========================================================================


def run(messages: list[dict], system: str = "You are a helpful assistant.") -> str:
    """
    Send messages to the best available provider.

    Detection order:
      1. USE_MOCK=true  -> deterministic mock (no API call)
      2. ANTHROPIC_API_KEY present -> Claude (claude-haiku-4-5)
      3. OPENAI_API_KEY present    -> OpenAI (gpt-5.4-mini)
      4. Fallback                  -> deterministic mock

    Args:
        messages: List of {"role": ..., "content": ...} dicts.
        system:   System prompt string.

    Returns:
        Model reply as a plain string.
    """
    if os.getenv("USE_MOCK", "").lower() == "true":
        return _mock_response(messages, system)

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=512,
                system=system,
                messages=messages,
            )
            return response.content[0].text
        except Exception as exc:
            print(f"[WARN] Anthropic API call failed: {exc}. Falling back to mock.")
            return _mock_response(messages, system)

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=openai_key)
            full_msgs = [{"role": "system", "content": system}] + messages
            response = client.chat.completions.create(
                model="gpt-5.4-mini",
                max_tokens=512,
                messages=full_msgs,
            )
            return response.choices[0].message.content
        except Exception as exc:
            print(f"[WARN] OpenAI API call failed: {exc}. Falling back to mock.")
            return _mock_response(messages, system)

    # No key detected — use mock
    return _mock_response(messages, system)


# ===========================================================================
# Demo
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
    # TODO 3 — call the safe parser on `raw`, with a fallback mapping every
    # field in `fields` to None (so downstream code always gets the keys).
    parsed = None  # replace with: parse_json_safe(raw, fallback={f: None for f in fields})
    print("--- extract_json ---")
    print(f'Input   : "{email_text}"')
    print(f"Parsed  : {parsed}\n")

    print("All demos complete.")


if __name__ == "__main__":
    demo()
