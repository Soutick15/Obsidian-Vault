"""
Capstone Starter — agent.py
============================
Tool-using agent for HR queries.
Runs in mock mode (no API key) or with Anthropic/OpenAI when keys are set.

Provider selection via LLM_PROVIDER env var:
    mock        — deterministic mock, no key needed (default)
    anthropic   — claude-haiku-4-5, needs ANTHROPIC_API_KEY
    openai      — gpt-5-mini, needs OPENAI_API_KEY
"""

import datetime
import json
import os

from dotenv import load_dotenv
from pydantic import BaseModel
from retrieve import format_context, retrieve  # type: ignore

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
MAX_TURNS = 6


# ---------------------------------------------------------------------------
# Structured output
# ---------------------------------------------------------------------------
class AgentResponse(BaseModel):
    answer: str
    sources: list[str] = []
    tool_calls_made: list[str] = []
    model_used: str = "mock"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
def tool_search_hr_docs(query: str, collection=None, embed_model=None) -> str:
    """RAG retrieval from the HR corpus."""
    # TODO: call retrieve(query, collection, embed_model) and return format_context(chunks)
    chunks = retrieve(query, collection, embed_model)
    return format_context(chunks)


def tool_calculator(expression: str) -> str:
    """Evaluate a safe arithmetic expression."""
    # TODO: safely evaluate expression using only math operations
    # Hint: only allow digits, operators, spaces, and parentheses
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Error: invalid characters in expression"
    try:
        result = eval(expression, {"__builtins__": {}})  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def tool_get_today(_: str = "") -> str:
    """Return today's date as ISO string."""
    return datetime.date.today().isoformat()


TOOL_REGISTRY = {
    "search_hr_docs": tool_search_hr_docs,
    "calculator": tool_calculator,
    "get_today": tool_get_today,
}

TOOLS_SCHEMA = [
    {
        "name": "search_hr_docs",
        "description": "Search the HR policy corpus for relevant information.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    },
    {
        "name": "calculator",
        "description": "Evaluate a simple arithmetic expression.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "e.g. '15 * 8'"}
            },
            "required": ["expression"],
        },
    },
    {
        "name": "get_today",
        "description": "Return today's date in ISO format.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


# ---------------------------------------------------------------------------
# Mock agent (no API key)
# ---------------------------------------------------------------------------
def _mock_run(question: str, collection=None, embed_model=None) -> AgentResponse:
    """Deterministic mock agent: search then optionally calculate."""
    tool_calls = []

    context = tool_search_hr_docs(question, collection, embed_model)
    tool_calls.append("search_hr_docs")

    # If question has numeric calculation keywords, simulate a calculator call
    calc_result = ""
    if any(
        k in question.lower()
        for k in ["hours", "days", "calculate", "how many", "total"]
    ):
        calc_result = tool_calculator("15 * 8")
        tool_calls.append("calculator")

    answer_parts = [f"Based on HR policy:\n{context}"]
    if calc_result:
        answer_parts.append(f"\nCalculation result: {calc_result}")

    sources = list({c["source"] for c in retrieve(question, collection, embed_model)})

    return AgentResponse(
        answer="\n".join(answer_parts),
        sources=sources,
        tool_calls_made=tool_calls,
        model_used="mock",
    )


# ---------------------------------------------------------------------------
# Anthropic agent
# ---------------------------------------------------------------------------
def _anthropic_run(question: str, collection=None, embed_model=None) -> AgentResponse:
    """Agent using Anthropic claude-haiku-4-5 with tool use."""
    # TODO: implement using anthropic SDK tool-calling loop
    # Hint: follow the pattern from labs/developer/day-09/solution.py _run_anthropic()
    import anthropic  # type: ignore

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = [{"role": "user", "content": question}]
    tool_calls_made: list[str] = []
    sources: list[str] = []

    for _ in range(MAX_TURNS):
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            tools=TOOLS_SCHEMA,
            messages=messages,
        )
        if response.stop_reason == "end_turn":
            answer = next((b.text for b in response.content if hasattr(b, "text")), "")
            return AgentResponse(
                answer=answer,
                sources=sources,
                tool_calls_made=tool_calls_made,
                model_used="claude-haiku-4-5",
            )
        assistant_content = list(response.content)
        for block in response.content:
            if block.type == "tool_use":
                tool_calls_made.append(block.name)
                if block.name == "search_hr_docs":
                    result = tool_search_hr_docs(
                        block.input.get("query", ""), collection, embed_model
                    )
                    sources.extend(
                        [
                            c["source"]
                            for c in retrieve(
                                block.input.get("query", ""), collection, embed_model
                            )
                        ]
                    )
                elif block.name == "calculator":
                    result = tool_calculator(block.input.get("expression", ""))
                elif block.name == "get_today":
                    result = tool_get_today()
                else:
                    result = "Unknown tool"
                messages.append({"role": "assistant", "content": assistant_content})
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result,
                            }
                        ],
                    }
                )
                break
    return AgentResponse(
        answer="Max turns reached.",
        sources=sources,
        tool_calls_made=tool_calls_made,
        model_used="claude-haiku-4-5",
    )


# ---------------------------------------------------------------------------
# OpenAI agent
# ---------------------------------------------------------------------------
def _openai_run(question: str, collection=None, embed_model=None) -> AgentResponse:
    """Agent using OpenAI gpt-5-mini with function calling."""
    # TODO: implement using OpenAI SDK function-calling loop
    from openai import OpenAI  # type: ignore

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    oai_tools = [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in TOOLS_SCHEMA
    ]
    messages = [
        {
            "role": "system",
            "content": "You are an HR assistant. Use tools to answer HR questions.",
        },
        {"role": "user", "content": question},
    ]
    tool_calls_made: list[str] = []
    sources: list[str] = []

    for _ in range(MAX_TURNS):
        response = client.chat.completions.create(
            model="gpt-5-mini", messages=messages, tools=oai_tools, max_tokens=1024
        )
        choice = response.choices[0]
        if choice.finish_reason == "stop":
            return AgentResponse(
                answer=choice.message.content or "",
                sources=sources,
                tool_calls_made=tool_calls_made,
                model_used="gpt-5-mini",
            )
        if choice.finish_reason == "tool_calls":
            messages.append(choice.message)
            for tc in choice.message.tool_calls:
                tool_calls_made.append(tc.function.name)
                args = json.loads(tc.function.arguments)
                if tc.function.name == "search_hr_docs":
                    result = tool_search_hr_docs(
                        args.get("query", ""), collection, embed_model
                    )
                elif tc.function.name == "calculator":
                    result = tool_calculator(args.get("expression", ""))
                elif tc.function.name == "get_today":
                    result = tool_get_today()
                else:
                    result = "Unknown tool"
                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": result}
                )
    return AgentResponse(
        answer="Max turns reached.",
        sources=sources,
        tool_calls_made=tool_calls_made,
        model_used="gpt-5-mini",
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def run_agent(question: str, collection=None, embed_model=None) -> AgentResponse:
    """Route to the correct backend based on LLM_PROVIDER."""
    if LLM_PROVIDER == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
        return _anthropic_run(question, collection, embed_model)
    if LLM_PROVIDER == "openai" and os.getenv("OPENAI_API_KEY"):
        return _openai_run(question, collection, embed_model)
    return _mock_run(question, collection, embed_model)


if __name__ == "__main__":
    import sys

    q = (
        " ".join(sys.argv[1:])
        or "How many PTO days after 2 years, and how many hours at 8h/day?"
    )
    print(f"Question: {q}\n")
    resp = run_agent(q)
    print(f"Answer: {resp.answer}")
    print(f"Sources: {resp.sources}")
    print(f"Tools: {resp.tool_calls_made}")
    print(f"Model: {resp.model_used}")
