"""
Day 5 Mini-Project -- Streaming CLI Assistant with Tool Calling (STARTER)
=========================================================================
Work through the TODO markers below. Run solution.py if you get stuck.

Concepts you will implement:
  1. Provider detection (Anthropic / OpenAI / Mock)
  2. Multi-turn conversation history
  3. Streaming responses token-by-token
  4. Tool-calling round-trip (define -> detect -> execute -> return)
"""

import ast
import operator
import os
import time

# ---------------------------------------------------------------------------
# Load .env if present (optional)
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# TODO 1: Detect which provider to use.
#
# Read ANTHROPIC_API_KEY and OPENAI_API_KEY from environment variables.
# Set PROVIDER to "anthropic", "openai", or "mock" based on which key is present.
# Priority: anthropic > openai > mock
# ---------------------------------------------------------------------------
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_KEY    = os.getenv("OPENAI_API_KEY", "")

PROVIDER = "mock"  # TODO: replace with detection logic


# ---------------------------------------------------------------------------
# TODO 2: Define the calculator tool schema.
#
# For Anthropic: a list with one dict containing "name", "description",
# and "input_schema" (JSON Schema object with "expression" property).
#
# For OpenAI: a list with one dict: {"type": "function", "function": {...}}
# ---------------------------------------------------------------------------
TOOL_NAME = "calculate"

ANTHROPIC_TOOLS = []  # TODO: fill in the Anthropic tool schema

OPENAI_TOOLS = []     # TODO: fill in the OpenAI tool schema


# ---------------------------------------------------------------------------
# Safe calculator (provided -- no changes needed)
# ---------------------------------------------------------------------------
_ALLOWED_OPS = {
    ast.Add:  operator.add,
    ast.Sub:  operator.sub,
    ast.Mult: operator.mul,
    ast.Div:  operator.truediv,
    ast.Pow:  operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_calculate(expression: str) -> str:
    """Safely evaluate a simple arithmetic expression."""
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as e:
        return f"Error: {e}"

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported: {ast.dump(node)}")

    try:
        result = _eval(tree)
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(result)
    except (ValueError, ZeroDivisionError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# TODO 3: Implement the Anthropic chat function.
#
# Steps:
#   a) Call client.messages.create() with the tool schema. (no streaming yet)
#   b) If stop_reason == "tool_use", extract the tool block, run safe_calculate,
#      append the tool_result message to history, then call again.
#   c) For the final answer, use client.messages.stream() and print each chunk.
#   d) Return the full assistant text string.
# ---------------------------------------------------------------------------
def anthropic_chat(client, history: list, system: str) -> str:
    """Call Claude, handle tool use, stream the final answer."""
    # TODO: implement
    raise NotImplementedError("Implement anthropic_chat")


# ---------------------------------------------------------------------------
# TODO 4: Implement the OpenAI chat function.
#
# Steps:
#   a) Build messages list: [{"role":"system","content":system}] + history
#   b) Call client.chat.completions.create() with tools. (non-streaming first)
#   c) If finish_reason == "tool_calls", extract tool call, run safe_calculate,
#      append tool result, then stream the final answer.
#   d) Return the full assistant text string.
# ---------------------------------------------------------------------------
def openai_chat(client, history: list, system: str) -> str:
    """Call OpenAI, handle tool use, stream the final answer."""
    # TODO: implement
    raise NotImplementedError("Implement openai_chat")


# ---------------------------------------------------------------------------
# Mock helpers (provided -- study these to understand the patterns)
# ---------------------------------------------------------------------------
import re


def _extract_math_expression(text: str):
    cleaned = re.sub(r'(?i)(what\s+is|calculate|compute|evaluate|find|solve|result\s+of)\s*', '', text)
    cleaned = re.sub(r'[?!.]', '', cleaned).strip()
    if re.search(r'[\d\+\-\*\/\(\)\s\.]+', cleaned):
        candidate = re.sub(r'[^\d\+\-\*\/\(\)\.\s]', '', cleaned).strip()
        if candidate and re.search(r'\d', candidate):
            return candidate
    return None


# ---------------------------------------------------------------------------
# TODO 5: Implement mock_chat.
#
# The mock should:
#   a) Check if the last user message looks like a maths question (use _extract_math_expression).
#   b) If yes: print a tool call annotation, run safe_calculate, print tool result,
#      then "stream" the answer word-by-word with time.sleep(0.04) between words.
#   c) If no: "stream" a generic helpful reply word-by-word.
#   d) Return the full assistant text.
# ---------------------------------------------------------------------------
def mock_chat(history: list, system: str) -> str:
    """Deterministic mock -- no API key needed."""
    # TODO: implement
    last_user = next(
        (m["content"] for m in reversed(history) if m["role"] == "user"), ""
    )
    print("\nAssistant: ", end="", flush=True)

    # Hint: use _extract_math_expression(last_user) to detect maths questions
    # Hint: simulate streaming with:  for word in text.split(): print(word+" ", end="", flush=True); time.sleep(0.04)

    placeholder = "Mock response -- implement mock_chat to see streaming."
    print(placeholder)
    return placeholder


# ---------------------------------------------------------------------------
# Main conversation loop
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a helpful AI assistant. You have access to a calculator tool. "
    "Use it when the user asks you to perform arithmetic. "
    "Be concise and friendly."
)


def build_client():
    if PROVIDER == "anthropic":
        try:
            import anthropic
            return anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        except ImportError:
            print("Warning: 'anthropic' package not installed. Falling back to mock.")
            return None
    elif PROVIDER == "openai":
        try:
            import openai
            return openai.OpenAI(api_key=OPENAI_KEY)
        except ImportError:
            print("Warning: 'openai' package not installed. Falling back to mock.")
            return None
    return None


def main():
    client = build_client()
    effective_provider = PROVIDER if client else "mock"

    print("=" * 60)
    print("  Day 5 Mini-Project -- Streaming CLI Assistant (STARTER)")
    print(f"  Provider: {effective_provider.upper()}")
    print(f"  Tool available: {TOOL_NAME}")
    print("  Type 'quit' or 'exit' to end the session.")
    print("=" * 60)
    print()

    history = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        history.append({"role": "user", "content": user_input})

        # TODO 6: Call the right backend based on effective_provider
        if effective_provider == "anthropic":
            reply = anthropic_chat(client, history, SYSTEM_PROMPT)
        elif effective_provider == "openai":
            reply = openai_chat(client, history, SYSTEM_PROMPT)
        else:
            reply = mock_chat(history, SYSTEM_PROMPT)

        history.append({"role": "assistant", "content": reply})
        print()


if __name__ == "__main__":
    main()
