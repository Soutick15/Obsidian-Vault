"""
Day 12 Lab — Structured Extraction Service  (SOLUTION)
=======================================================
Demonstrates:
  • Schema-first design with Pydantic
  • Validation + repair loop
  • Provider-flexible LLM calls (anthropic / openai / mock)
  • Input validation, structured logging, graceful degradation

Run with no API key (mock mode — default):
    python labs/developer/day-12/solution.py

Run with Anthropic key:
    export ANTHROPIC_API_KEY=sk-ant-...
    python labs/developer/day-12/solution.py

Run with OpenAI key:
    export OPENAI_API_KEY=sk-...
    python labs/developer/day-12/solution.py

Priority: anthropic > openai > mock
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_RETRIES = 3  # initial attempt + up to 2 repairs
MAX_INPUT_CHARS = 6_000  # guard against runaway inputs
MODEL_ANTHROPIC = "claude-haiku-4-5"
MODEL_OPENAI = "gpt-5-mini"

# ---------------------------------------------------------------------------
# 1. Schema — single source of truth
# ---------------------------------------------------------------------------


class PolicyExtraction(BaseModel):
    """Structured representation of an HR policy extracted from context."""

    policy_name: str = Field(description="Canonical HR policy name")
    entitlement: str = Field(description="What the employee is entitled to")
    eligibility: str = Field(description="Who qualifies for this policy")
    source: str = Field(description="Document or section cited")
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Model self-reported confidence 0.0–1.0",
    )


# ---------------------------------------------------------------------------
# 2. Result container
# ---------------------------------------------------------------------------


@dataclass
class ExtractionResult:
    ok: bool
    data: Optional[PolicyExtraction] = None
    error: Optional[str] = None
    retries: int = 0


# ---------------------------------------------------------------------------
# 3. Provider detection
# ---------------------------------------------------------------------------


def _detect_provider() -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return "mock"


PROVIDER = _detect_provider()


# ---------------------------------------------------------------------------
# 4. Mock LLM  (deterministic, no network)
# ---------------------------------------------------------------------------

# Track call count per scenario so we can return malformed on first call
# and valid on the repair call.
_mock_call_counts: dict[str, int] = {}


def mock_llm(prompt: str, scenario: str = "valid") -> str:
    """
    Deterministic mock LLM.

    scenario="valid"    → always returns valid JSON.
    scenario="malformed"→ returns BROKEN JSON on call #1, valid JSON on call #2+.
    """
    _mock_call_counts[scenario] = _mock_call_counts.get(scenario, 0) + 1
    call_n = _mock_call_counts[scenario]

    if scenario == "valid":
        return json.dumps(
            {
                "policy_name": "Annual Leave Policy",
                "entitlement": "20 days per calendar year, increasing to 25 days after 5 years",
                "eligibility": "All permanent employees who have completed 3 months of service",
                "source": "Employee Handbook v3.2, Section 4.2",
                "confidence": 0.95,
            }
        )

    elif scenario == "malformed":
        if call_n == 1:
            # Missing required "source" field — Pydantic will reject this
            return json.dumps(
                {
                    "policy_name": "Remote Work Policy",
                    "entitlement": "Up to 3 days per week working from home",
                    "eligibility": "Employees with at least 6 months tenure and manager approval",
                    # "source" deliberately omitted to trigger validation failure
                    "confidence": "high",  # wrong type too — should be float
                }
            )
        else:
            # Repair call — return valid JSON
            return json.dumps(
                {
                    "policy_name": "Remote Work Policy",
                    "entitlement": "Up to 3 days per week working from home",
                    "eligibility": "Employees with at least 6 months tenure and manager approval",
                    "source": "Remote Work Guidelines 2024, Clause 2.1",
                    "confidence": 0.88,
                }
            )

    else:
        raise ValueError(f"Unknown mock scenario: {scenario!r}")


# ---------------------------------------------------------------------------
# 5. Prompt templates  (separated from business logic)
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT_TEMPLATE = """\
You are an HR policy analyst. Given a user query and a context document, \
extract the structured fields listed in the schema below.

<query>
{query}
</query>

<context>
{context}
</context>

Return ONLY a JSON object matching this schema. No markdown fences. No explanation.

Schema:
{schema}
"""

REPAIR_PROMPT_TEMPLATE = """\
The following JSON failed schema validation.

<broken_json>
{raw_output}
</broken_json>

Validation error:
{validation_error}

Return ONLY a corrected JSON object matching this schema. No fences. No explanation.

Schema:
{schema}
"""


def build_extraction_prompt(query: str, context: str, schema_json: str) -> str:
    return EXTRACTION_PROMPT_TEMPLATE.format(
        query=query,
        context=context,
        schema=schema_json,
    )


def build_repair_prompt(
    raw_output: str,
    validation_error: str,
    schema_json: str,
) -> str:
    return REPAIR_PROMPT_TEMPLATE.format(
        raw_output=raw_output,
        validation_error=validation_error,
        schema=schema_json,
    )


# ---------------------------------------------------------------------------
# 6. Provider call  (routes to real API or mock)
# ---------------------------------------------------------------------------


def call_provider(prompt: str, scenario: str = "valid") -> str:
    """Call the configured provider and return raw text response."""
    if PROVIDER == "anthropic":
        import anthropic  # type: ignore[import]

        client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            timeout=30.0,
        )
        message = client.messages.create(
            model=MODEL_ANTHROPIC,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        # Filter for text block; ignore tool_use blocks if any
        for block in message.content:
            if block.type == "text":
                return block.text
        raise ValueError("No text block in Anthropic response")

    elif PROVIDER == "openai":
        import openai  # type: ignore[import]

        client = openai.OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            timeout=30.0,
        )
        response = client.chat.completions.create(
            model=MODEL_OPENAI,
            max_tokens=512,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    else:  # mock
        # Small simulated delay so timing logs look realistic
        time.sleep(0.05)
        return mock_llm(prompt, scenario=scenario)


# ---------------------------------------------------------------------------
# 7. Input validation
# ---------------------------------------------------------------------------


def validate_input(text: str, label: str) -> str:
    text = text.strip()
    if not text:
        raise ValueError(f"{label} must not be empty")
    if len(text) > MAX_INPUT_CHARS:
        raise ValueError(
            f"{label} is too long: {len(text)} chars (max {MAX_INPUT_CHARS})"
        )
    return text


# ---------------------------------------------------------------------------
# 8. Core extraction function  (validation + repair loop)
# ---------------------------------------------------------------------------


def extract(
    query: str,
    context: str,
    scenario: str = "valid",
) -> ExtractionResult:
    """
    Extract HR policy fields from query + context.

    Returns ExtractionResult(ok=True, data=PolicyExtraction(...)) on success,
    or ExtractionResult(ok=False, error="...") after all retries are exhausted.
    """
    # --- Input validation ---
    try:
        query = validate_input(query, "query")
        context = validate_input(context, "context")
    except ValueError as exc:
        return ExtractionResult(ok=False, error=str(exc))

    schema_json = json.dumps(PolicyExtraction.model_json_schema(), indent=2)
    prompt = build_extraction_prompt(query, context, schema_json)
    raw_output = ""
    last_error = ""

    for attempt in range(1, MAX_RETRIES + 1):
        if attempt == 1:
            log.info(
                "Attempt %d/%d — calling %s provider", attempt, MAX_RETRIES, PROVIDER
            )
        else:
            log.info("Sending repair prompt (attempt %d/%d)", attempt, MAX_RETRIES)
            prompt = build_repair_prompt(raw_output, last_error, schema_json)

        # --- LLM call with simple backoff on transient errors ---
        try:
            raw_output = call_provider(prompt, scenario=scenario)
        except Exception as exc:
            last_error = f"Provider call failed: {exc}"
            log.warning("Provider error on attempt %d: %s", attempt, exc)
            if attempt < MAX_RETRIES:
                delay = (2 ** (attempt - 1)) + random.uniform(0, 0.3)
                time.sleep(delay)
            continue

        # --- JSON parse ---
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            last_error = f"JSON parse error: {exc}"
            log.info("JSON parse FAILED on attempt %d: %s", attempt, exc)
            continue

        # --- Pydantic validation ---
        try:
            extraction = PolicyExtraction.model_validate(parsed)
            log.info("Validation OK on attempt %d", attempt)
            return ExtractionResult(
                ok=True,
                data=extraction,
                retries=attempt - 1,
            )
        except ValidationError as exc:
            last_error = str(exc)
            log.info(
                "Validation FAILED on attempt %d: %s",
                attempt,
                exc.errors()[0]["msg"] if exc.errors() else str(exc),
            )

    log.warning("All %d attempts failed. Last error: %s", MAX_RETRIES, last_error)
    return ExtractionResult(
        ok=False,
        error=f"Extraction failed after {MAX_RETRIES} attempts. Last error: {last_error}",
        retries=MAX_RETRIES,
    )


# ---------------------------------------------------------------------------
# 9. Demo
# ---------------------------------------------------------------------------

HR_QUERY = "What is the annual leave entitlement for full-time employees?"

HR_CONTEXT = """
Employee Handbook v3.2 — Section 4.2: Annual Leave Policy

All permanent employees who have completed three (3) months of continuous
service are entitled to annual leave. Full-time employees accrue 20 days
of paid annual leave per calendar year. After five years of service,
the entitlement increases to 25 days per year. Leave must be approved
by the employee's line manager with a minimum of two weeks' notice.
Unused leave may be carried over to the next year up to a maximum of
10 days; any excess is forfeited.
"""

REMOTE_QUERY = "Can I work from home and how many days per week is allowed?"

REMOTE_CONTEXT = """
Remote Work Guidelines 2024 — Clause 2.1: Eligibility and Entitlement

Employees who have been with the company for at least six (6) months and
have obtained written approval from their line manager are eligible for
the hybrid remote-work arrangement. Eligible employees may work remotely
for up to three (3) days per calendar week. Remote work days must be
agreed in advance and documented in the HR portal. Employees in their
first six months of service are required to work on-site full-time.
"""


def _print_result(result: ExtractionResult) -> None:
    if result.ok and result.data:
        status = (
            "OK" if result.retries == 0 else f"OK (after {result.retries} repair(s))"
        )
        print(f"Result: {status}")
        d = result.data
        print(f"  policy_name : {d.policy_name}")
        print(f"  entitlement : {d.entitlement}")
        print(f"  eligibility : {d.eligibility}")
        print(f"  source      : {d.source}")
        print(f"  confidence  : {d.confidence}")
    else:
        print(f"Result: FAILED — {result.error}")


def main() -> None:
    print("=== Day 12 Lab: Structured Extraction Service ===")
    print(f"Provider: {PROVIDER}\n")

    # --- Case 1: Success path ---
    print("--- Case 1: Success path ---")
    result1 = extract(HR_QUERY, HR_CONTEXT, scenario="valid")
    _print_result(result1)

    print()

    # --- Case 2: Malformed output → repair ---
    print("--- Case 2: Malformed-output → repair path ---")
    result2 = extract(REMOTE_QUERY, REMOTE_CONTEXT, scenario="malformed")
    _print_result(result2)

    print()

    # --- Verify both results are typed ---
    assert result1.ok, "Case 1 should succeed"
    assert isinstance(result1.data, PolicyExtraction), (
        "Case 1 data should be PolicyExtraction"
    )

    assert result2.ok, "Case 2 should succeed after repair"
    assert isinstance(result2.data, PolicyExtraction), (
        "Case 2 data should be PolicyExtraction"
    )
    assert result2.retries >= 1, "Case 2 should have required at least one repair"

    print("=== All assertions passed. Typed objects returned correctly. ===")


if __name__ == "__main__":
    main()
