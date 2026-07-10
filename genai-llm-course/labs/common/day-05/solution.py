"""
Day 5 Mini-Project -- Streaming CLI Assistant with Tool Calling
===============================================================
A provider-flexible CLI assistant that demonstrates:
  1. Multi-turn conversation (stateful message history)
  2. Streaming responses (token-by-token output)
  3. Tool calling (calculator round-trip)

See curriculum/common/Day-05-apis-streaming-tools.md, Section 3 (Worked
Example), for a step-by-step walkthrough of the exact request/reply and
tool-call round trip this file wires into a chat loop.

Provider detection (in priority order):
  ANTHROPIC_API_KEY set -> use real Claude API
  OPENAI_API_KEY set    -> use real OpenAI API
  Neither set           -> MOCK mode (deterministic, no key needed)

Usage:
  python solution.py                          # mock mode
  ANTHROPIC_API_KEY=sk-ant-... python solution.py
  OPENAI_API_KEY=sk-...        python solution.py
"""

import ast
import operator
import os
import re
import sys
import time

# ---------------------------------------------------------------------------
# Load .env if present (optional helper; falls back gracefully if not installed)
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; env vars loaded from shell

# ---------------------------------------------------------------------------
# Detect provider
# ---------------------------------------------------------------------------
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

if ANTHROPIC_KEY:
    PROVIDER = "anthropic"
elif OPENAI_KEY:
    PROVIDER = "openai"
else:
    PROVIDER = "mock"

# ---------------------------------------------------------------------------
# Tool definition -- shared schema concept
# ---------------------------------------------------------------------------
TOOL_NAME = "calculate"
TOOL_DESCRIPTION = (
    "Evaluate a simple arithmetic expression (addition, subtraction, "
    "multiplication, division, parentheses) and return the numeric result."
)

# Anthropic tool schema
ANTHROPIC_TOOLS = [
    {
        "name": TOOL_NAME,
        "description": TOOL_DESCRIPTION,
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A Python-evaluable arithmetic expression, e.g. '3 * (7 + 2)'",
                }
            },
            "required": ["expression"],
        },
    }
]

# OpenAI tool schema
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": TOOL_NAME,
            "description": TOOL_DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A Python-evaluable arithmetic expression, e.g. '3 * (7 + 2)'",
                    }
                },
                "required": ["expression"],
            },
        },
    }
]

# ---------------------------------------------------------------------------
# Safe calculator -- only allows arithmetic, no exec/eval of arbitrary code
# ---------------------------------------------------------------------------
_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_calculate(expression: str) -> str:
    """Evaluate a simple arithmetic expression safely. Returns result as string."""
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as e:
        return f"Error: invalid expression -- {e}"

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported operation: {ast.dump(node)}")

    try:
        result = _eval(tree)
        # Return integer string when result is whole number
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(result)
    except (ValueError, ZeroDivisionError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# MOCK client -- no API key needed
#
# Mirrors the two-step shape of a real API call (Section 2.3 / Section 3):
#   1. mock_check_for_tool_call(...)  -- stands in for checking
#      response.stop_reason == "tool_use" on the first (non-streaming) call.
#   2. mock_stream_answer(...)        -- stands in for client.messages.stream(...)
#      on the second call, once the tool result is known.
# ---------------------------------------------------------------------------


def _extract_math_expression(text: str):
    """
    Heuristic: if the user message looks like a maths question, extract the
    expression. Returns (expression_str) or None.
    """
    # Remove question words and punctuation
    cleaned = re.sub(
        r"(?i)(what\s+is|calculate|compute|evaluate|find|solve|result\s+of)\s*",
        "",
        text,
    )
    cleaned = re.sub(r"[?!.]", "", cleaned).strip()
    # If it looks like an arithmetic expression, return it
    if re.search(r"[\d\+\-\*\/\(\)\s\.]+", cleaned):
        candidate = re.sub(r"[^\d\+\-\*\/\(\)\.\s]", "", cleaned).strip()
        if candidate and re.search(r"\d", candidate):
            return candidate
    return None


def mock_check_for_tool_call(history: list):
    """
    Looks at the most recent user message and returns an arithmetic
    expression string if it looks like a maths question (e.g. "45 * 3 + 17"),
    or None otherwise.
    """
    last_user = next(
        (m["content"] for m in reversed(history) if m["role"] == "user"), ""
    )
    return _extract_math_expression(last_user)


def mock_stream_answer(history: list, system: str, tool_expr=None, tool_result=None):
    """
    Returns a generator of text chunks ("words") that make up the final
    answer. If tool_expr/tool_result are given, the answer reports the
    calculation; otherwise it's a generic greeting.
    """
    if tool_expr is not None and tool_result is not None:
        answer = f"The result of {tool_expr} is {tool_result}."
    else:
        answer = (
            "I am your AI assistant. I can hold a multi-turn conversation, "
            "stream responses token by token, and call a calculator tool "
            "when you ask a maths question. Try asking something like: "
            "'What is 45 * 3 + 17?'"
        )
    for word in answer.split():
        yield word + " "
        time.sleep(0.04)


def stream_print(chunks) -> str:
    """
    The streaming print helper. Prints each chunk immediately (flush=True,
    Section 2.2) so text appears word-by-word, and returns the full
    concatenated text once the stream ends.
    """
    full_text = ""
    for chunk in chunks:
        print(chunk, end="", flush=True)
        full_text += chunk
    print()
    return full_text.strip()


def mock_chat(history: list, system: str) -> str:
    """
    Deterministic mock -- no API key needed. Implements the same three
    moves as a real tool-calling round trip:
      1. Check whether a tool call is needed.
      2. If so, run the tool and print the call + result.
      3. Stream the final answer.
    Returns the full assistant text so it can be appended to history.
    """
    tool_expr = mock_check_for_tool_call(history)
    tool_result = None

    if tool_expr:
        print(f"\n[Tool call: {TOOL_NAME}({tool_expr!r})]", flush=True)
        tool_result = safe_calculate(tool_expr)
        print(f"[Tool result: {tool_result}]", flush=True)

    print("\nAssistant: ", end="", flush=True)
    full_text = stream_print(
        mock_stream_answer(history, system, tool_expr=tool_expr, tool_result=tool_result)
    )
    return full_text


# ---------------------------------------------------------------------------
# Anthropic implementation (given -- run this with a real ANTHROPIC_API_KEY)
# ---------------------------------------------------------------------------


def anthropic_chat(client, history: list, system: str):
    """
    Send history to Claude. If the model requests a tool call, execute it and
    send the result back. Streams the final answer to stdout.
    Returns the final assistant text so it can be appended to history.
    """
    # First request
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=system,
        tools=ANTHROPIC_TOOLS,
        messages=history,
    )

    if response.stop_reason == "tool_use":
        # Find the tool_use block
        tool_block = next(b for b in response.content if b.type == "tool_use")
        expr = tool_block.input.get("expression", "")
        print(f"\n[Tool call: {TOOL_NAME}({expr!r})]", flush=True)
        result = safe_calculate(expr)
        print(f"[Tool result: {result}]", flush=True)

        # Build updated history with tool result
        extended_history = history + [
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": result,
                    }
                ],
            },
        ]

        # Second request -- stream the final answer
        print("\nAssistant: ", end="", flush=True)
        full_text = ""
        with client.messages.stream(
            model="claude-haiku-4-5",
            max_tokens=512,
            system=system,
            tools=ANTHROPIC_TOOLS,
            messages=extended_history,
        ) as stream:
            for chunk in stream.text_stream:
                print(chunk, end="", flush=True)
                full_text += chunk
        print()  # newline after stream
        return full_text

    else:
        # No tool call -- stream directly (or return text if already complete)
        # Re-request with streaming for consistent UX
        print("\nAssistant: ", end="", flush=True)
        full_text = ""
        with client.messages.stream(
            model="claude-haiku-4-5",
            max_tokens=1024,
            system=system,
            messages=history,
        ) as stream:
            for chunk in stream.text_stream:
                print(chunk, end="", flush=True)
                full_text += chunk
        print()
        return full_text


# ---------------------------------------------------------------------------
# OpenAI implementation (given -- run this with a real OPENAI_API_KEY)
# ---------------------------------------------------------------------------


def openai_chat(client, history: list, system: str):
    """
    Send history to OpenAI. Handles tool calls and streams the final answer.
    Returns the final assistant text.
    """
    import json

    messages = [{"role": "system", "content": system}] + history

    # Two-phase approach: non-streaming first pass to detect tool calls cleanly,
    # then a second streaming request for the final answer once the tool result is known.
    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        max_tokens=1024,
        tools=OPENAI_TOOLS,
        messages=messages,
    )

    choice = response.choices[0]

    if choice.finish_reason == "tool_calls":
        tool_call = choice.message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        expr = args.get("expression", "")
        print(f"\n[Tool call: {TOOL_NAME}({expr!r})]", flush=True)
        result = safe_calculate(expr)
        print(f"[Tool result: {result}]", flush=True)

        # Append assistant message with tool_calls + tool result
        messages.append(choice.message)  # assistant message with tool_calls
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
        )

        # Stream the final answer
        print("\nAssistant: ", end="", flush=True)
        full_text = ""
        stream = client.chat.completions.create(
            model="gpt-5.4-mini",
            max_tokens=512,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                print(delta, end="", flush=True)
                full_text += delta
        print()
        return full_text

    else:
        text = choice.message.content or ""
        # Re-request with streaming for UX consistency
        print("\nAssistant: ", end="", flush=True)
        full_text = ""
        stream = client.chat.completions.create(
            model="gpt-5.4-mini",
            max_tokens=1024,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                print(delta, end="", flush=True)
                full_text += delta
        print()
        return full_text


# ---------------------------------------------------------------------------
# Main conversation loop
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a helpful AI assistant. You have access to a calculator tool. "
    "Use it when the user asks you to perform arithmetic. "
    "Be concise and friendly."
)


def build_client():
    """Build and return the real API client, or None for mock mode."""
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

    # Banner
    print("=" * 60)
    print("  Day 5 Mini-Project -- Streaming CLI Assistant")
    print(f"  Provider: {effective_provider.upper()}")
    if effective_provider == "anthropic":
        print("  Model: claude-haiku-4-5")
    elif effective_provider == "openai":
        print("  Model: gpt-5.4-mini")
    print(f"  Tool available: {TOOL_NAME}")
    print("  Type 'quit' or 'exit' to end the session.")
    print("=" * 60)
    print()

    history = []  # list of {"role": "user"|"assistant", "content": str}

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

        # Dispatch to the right backend
        if effective_provider == "anthropic":
            reply = anthropic_chat(client, history, SYSTEM_PROMPT)
        elif effective_provider == "openai":
            reply = openai_chat(client, history, SYSTEM_PROMPT)
        else:
            reply = mock_chat(history, SYSTEM_PROMPT)

        history.append({"role": "assistant", "content": reply})
        print()  # blank line between turns


if __name__ == "__main__":
    main()
