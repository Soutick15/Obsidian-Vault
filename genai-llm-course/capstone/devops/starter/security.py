"""
Security module — audit logging, input guardrails, secrets validation.

TODOs:
  1. Implement audit_log() — structured log with user, action, query, timestamp
  2. Implement check_input_guardrail() — block off-topic/harmful queries
  3. Implement validate_secrets() — check required env vars are set (not hardcoded)

Run in mock mode: python -c "from capstone.devops.starter.security import audit_log; print('OK')"
"""
import json
import logging
import os
import re
import time
import uuid
from typing import Optional

logger = logging.getLogger("acme_hr.security")

# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

def audit_log(
    action: str,
    query: Optional[str] = None,
    user_id: Optional[str] = "anonymous",
    result: str = "allowed",
    extra: Optional[dict] = None,
) -> dict:
    """
    Write a structured audit log entry.

    TODO:
      - Build an audit record with: timestamp, event_id (uuid), action, user_id, query, result, extra
      - Print as JSON to stdout (or write to audit log file)
      - Return the audit record dict
    """
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event_id": str(uuid.uuid4()),
        "action": action,
        "user_id": user_id,
        "query": query,
        "result": result,
        **(extra or {}),
    }
    print(json.dumps({"audit": record}))
    return record


# ---------------------------------------------------------------------------
# Input guardrails
# ---------------------------------------------------------------------------

# Patterns that indicate off-topic or potentially harmful queries
_BLOCK_PATTERNS = [
    r"\b(hack|exploit|bypass|inject|jailbreak)\b",
    r"\b(credit.?card|ssn|social.security)\b",
    r"\b(password|passwd|secret.?key)\b",
    r"ignore.{0,20}(previous|above|prior).{0,20}instruction",
    r"you are now",
    r"act as",
]

_HR_TOPIC_HINTS = [
    "pto", "leave", "vacation", "benefit", "salary", "pay", "onboard",
    "remote", "policy", "hr", "holiday", "insurance", "401k", "performance",
    "review", "hire", "employee", "manager", "team", "office", "work",
]

def check_input_guardrail(query: str) -> dict:
    """
    Check if a query should be blocked.

    Returns: {"allowed": bool, "reason": str}

    TODO:
      - Check against _BLOCK_PATTERNS (re.search, case-insensitive) → block if match
      - Check if query contains any HR topic hint → allow
      - If very short (< 5 chars) → block as invalid
      - If none of the above → allow with "no_topic_restriction" reason
      (Be permissive — this is a demo guardrail, not production)
    """
    query_lower = query.lower().strip()

    if len(query_lower) < 5:
        return {"allowed": False, "reason": "query_too_short"}

    for pattern in _BLOCK_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return {"allowed": False, "reason": f"blocked_pattern: {pattern}"}

    # TODO: add HR topic check and permissive default
    return {"allowed": True, "reason": "default_allow"}


# ---------------------------------------------------------------------------
# Secrets validation
# ---------------------------------------------------------------------------

REQUIRED_ENV_VARS = [
    # Add your required env vars here — none required for mock mode
]

OPTIONAL_ENV_VARS = {
    "LLM_PROVIDER": "mock",
    "ANTHROPIC_API_KEY": None,
    "OPENAI_API_KEY": None,
    "APP_VERSION": "0.1.0",
    "LOG_LEVEL": "INFO",
}

def validate_secrets(strict: bool = False) -> dict:
    """
    Validate that required environment variables are set.

    TODO:
      - Check each var in REQUIRED_ENV_VARS is set (non-empty)
      - Check no secrets appear to be hardcoded (this is a doc/convention check)
      - Return {"valid": bool, "missing": [...], "warnings": [...]}
    """
    missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
    warnings = []
    for var, default in OPTIONAL_ENV_VARS.items():
        val = os.getenv(var, default)
        if val and len(str(val)) > 10 and var.endswith("_KEY"):
            warnings.append(f"{var} is set (ensure it comes from env, not hardcode)")

    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "warnings": warnings,
        "mock_mode": os.getenv("LLM_PROVIDER", "mock") == "mock",
    }


if __name__ == "__main__":
    audit_log("test_action", query="What is the PTO policy?", user_id="dev")
    result = check_input_guardrail("What is the PTO policy?")
    print(f"Guardrail check: {result}")
    secrets = validate_secrets()
    print(f"Secrets validation: {secrets}")
    print("security OK")
