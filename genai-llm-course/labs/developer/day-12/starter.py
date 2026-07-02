"""
Day 12 Lab — Structured Extraction Service  (STARTER)
======================================================
Work through the TODO markers in order. Run solution.py if you get stuck.

Goal: extract {policy_name, entitlement, eligibility, source, confidence}
      from an HR query + context document, using a validation + repair loop.

Run with no API key (mock mode):
    python labs/developer/day-12/starter.py

Run with Anthropic key:
    export ANTHROPIC_API_KEY=sk-ant-...
    python labs/developer/day-12/starter.py
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    # python-dotenv is not installed; environment variables must be set manually.
    def load_dotenv(*args, **kwargs):  # type: ignore[misc]
        pass


# ---------------------------------------------------------------------------
# Logging setup
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
# TODO 1 — Define the Pydantic schema
# ---------------------------------------------------------------------------
# Import BaseModel and Field from pydantic.
# Define a class `PolicyExtraction(BaseModel)` with these fields:
#   policy_name : str  — canonical HR policy name
#   entitlement : str  — what the employee is entitled to
#   eligibility : str  — who qualifies for this policy
#   source      : str  — document or section cited
#   confidence  : Optional[float]  — model self-reported confidence 0.0–1.0
#                  use Field(default=None, ge=0.0, le=1.0)
#
# Hint: from pydantic import BaseModel, Field

# >>> your code here <<<


# ---------------------------------------------------------------------------
# Result container (provided — do not change)
# ---------------------------------------------------------------------------
@dataclass
class ExtractionResult:
    ok: bool
    data: Optional["PolicyExtraction"] = None  # type: ignore[name-defined]
    error: Optional[str] = None
    retries: int = 0


# ---------------------------------------------------------------------------
# TODO 2 — Provider detection
# ---------------------------------------------------------------------------
# Read ANTHROPIC_API_KEY and OPENAI_API_KEY from environment.
# Set PROVIDER to "anthropic", "openai", or "mock".
# Priority: anthropic > openai > mock
#
# >>> your code here <<<
PROVIDER = "mock"  # placeholder — replace with your detection logic


# ---------------------------------------------------------------------------
# TODO 3 — Mock LLM
# ---------------------------------------------------------------------------
# Implement `mock_llm(prompt: str, scenario: str) -> str`
#
# It should accept a `scenario` argument:
#   "valid"    → return a JSON string with all required fields populated
#   "malformed"→ return a JSON string that is MISSING the required "source" field
#                so Pydantic validation will fail on the first attempt
#
# The function must NOT call any external API.


def mock_llm(prompt: str, scenario: str = "valid") -> str:
    """Deterministic mock that simulates LLM responses."""
    # >>> your code here <<<
    raise NotImplementedError("TODO 3: implement mock_llm")


# ---------------------------------------------------------------------------
# TODO 4 — Extraction prompt template
# ---------------------------------------------------------------------------
# Implement `build_extraction_prompt(query, context, schema_json) -> str`
#
# The prompt should:
#   1. Give the model a brief system instruction (HR policy analyst role)
#   2. Include the user query and context clearly labelled
#   3. Include the JSON schema
#   4. Instruct the model to return ONLY a JSON object (no fences, no prose)


def build_extraction_prompt(query: str, context: str, schema_json: str) -> str:
    # >>> your code here <<<
    raise NotImplementedError("TODO 4: implement build_extraction_prompt")


# ---------------------------------------------------------------------------
# TODO 5 — Repair prompt template
# ---------------------------------------------------------------------------
# Implement `build_repair_prompt(raw_output, validation_error, schema_json) -> str`
#
# The prompt should:
#   1. Show the broken JSON output
#   2. Show the validation error message
#   3. Include the schema again
#   4. Ask for a corrected JSON object only


def build_repair_prompt(
    raw_output: str,
    validation_error: str,
    schema_json: str,
) -> str:
    # >>> your code here <<<
    raise NotImplementedError("TODO 5: implement build_repair_prompt")


# ---------------------------------------------------------------------------
# TODO 6 — Core extraction function with validation + repair loop
# ---------------------------------------------------------------------------
# Implement `extract(query, context, scenario) -> ExtractionResult`
#
# Steps:
#   a. Validate input (strip, check non-empty, check length <= MAX_INPUT_CHARS)
#   b. Get schema JSON from PolicyExtraction.model_json_schema()
#   c. Build extraction prompt
#   d. Loop up to MAX_RETRIES times:
#       - On attempt 1: call the LLM with the extraction prompt
#       - On attempts 2+: call the LLM with a repair prompt
#       - Parse the response as JSON (handle json.JSONDecodeError)
#       - Call PolicyExtraction.model_validate(parsed) (handle ValidationError)
#       - If OK: return ExtractionResult(ok=True, data=..., retries=attempt-1)
#   e. If all attempts fail: return ExtractionResult(ok=False, error=..., retries=MAX_RETRIES)
#
# For provider calls use call_provider(prompt, scenario) defined below.


def call_provider(prompt: str, scenario: str = "valid") -> str:
    """Route to real provider or mock based on PROVIDER."""
    if PROVIDER == "anthropic":
        import anthropic

        client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            timeout=30.0,
        )
        message = client.messages.create(
            model=MODEL_ANTHROPIC,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    elif PROVIDER == "openai":
        import openai

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
        return mock_llm(prompt, scenario=scenario)


def extract(query: str, context: str, scenario: str = "valid") -> ExtractionResult:
    """Extract HR policy fields from query + context with validation + repair."""
    # >>> your code here <<<
    raise NotImplementedError("TODO 6: implement extract()")


# ---------------------------------------------------------------------------
# TODO 7 — Structured logging
# ---------------------------------------------------------------------------
# In your extract() implementation, add log.info() calls for:
#   - Each attempt: "Attempt {n}/{MAX_RETRIES} — calling {PROVIDER} provider"
#   - Validation OK: "Validation OK on attempt {n}"
#   - Validation FAIL: "Validation FAILED on attempt {n}: {error}"
#   - Sending repair: "Sending repair prompt (attempt {n}/{MAX_RETRIES})"
#   - Total failure: "All {MAX_RETRIES} attempts failed"
#
# (Implement this as part of TODO 6 — listed separately so you don't forget.)


# ---------------------------------------------------------------------------
# TODO 8 — Demo in main()
# ---------------------------------------------------------------------------
# Run two cases:
#   Case 1 — success path   (scenario="valid")
#   Case 2 — malformed then repair (scenario="malformed")
#
# For each case:
#   - Print a header
#   - Call extract() with a realistic HR query and context
#   - Print the result (ok, fields if ok, error if not ok)

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


def main() -> None:
    print("=== Day 12 Lab: Structured Extraction Service ===")
    print(f"Provider: {PROVIDER}\n")

    # >>> TODO 8: implement the two demo cases <<<
    raise NotImplementedError("TODO 8: implement main()")


if __name__ == "__main__":
    main()
