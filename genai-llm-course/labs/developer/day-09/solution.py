"""
Day 9 Lab — Tool-Using Agent (solution.py)
==========================================
Complete working implementation.
Run from the repo root:  python labs/developer/day-09/solution.py

Runs in mock mode (no API key) OR real-LLM mode if ANTHROPIC_API_KEY or
OPENAI_API_KEY is set in the environment / .env file.

Tools implemented:
  - search_hr_docs  : RAG over the shared HR corpus via ChromaDB
  - calculator      : safe arithmetic evaluation
  - get_today       : returns today's ISO date
"""

import datetime
import json
import math
import os
from pathlib import Path

# Load .env if present (keys optional — lab runs without them)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]
HR_CORPUS_DIR = REPO_ROOT / "data" / "hr-corpus"

# ---------------------------------------------------------------------------
# Tool schemas (Anthropic-style; converted for OpenAI as needed)
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "search_hr_docs",
        "description": (
            "Searches the Acme HR policy corpus and returns the top-3 most "
            "relevant passages. Use this for questions about PTO, leave, "
            "benefits, compensation, remote work, or any company policy."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language search query.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "calculator",
        "description": (
            "Evaluates a simple arithmetic expression and returns the numeric "
            "result as a string. Supports +, -, *, /, **, parentheses, and "
            "the math module. Do NOT use for anything other than arithmetic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A valid Python arithmetic expression.",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "get_today",
        "description": "Returns today's date in ISO 8601 format (YYYY-MM-DD).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ---------------------------------------------------------------------------
# Chunking helper
# ---------------------------------------------------------------------------
def _chunk_text(text: str, max_chars: int = 400) -> list:
    """Split text into chunks of ~max_chars by paragraph boundaries."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if current and len(current) + len(para) + 2 > max_chars:
            chunks.append(current.strip())
            current = para
        else:
            current = (current + "\n\n" + para).strip() if current else para
    if current:
        chunks.append(current.strip())
    return chunks


# ---------------------------------------------------------------------------
# Build HR ChromaDB index
# ---------------------------------------------------------------------------
def build_hr_index():
    """
    Load HR corpus, chunk, embed with sentence-transformers, store in
    an in-memory ChromaDB collection. Returns (collection, embed_model).
    """
    import chromadb
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.Client()  # in-memory

    # Delete existing collection if rebuilding
    try:
        client.delete_collection("hr_docs")
    except Exception:
        pass
    collection = client.create_collection("hr_docs")

    docs, ids, embeddings = [], [], []
    for md_file in sorted(HR_CORPUS_DIR.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        chunks = _chunk_text(text, max_chars=400)
        for idx, chunk in enumerate(chunks):
            doc_id = f"{md_file.stem}_chunk_{idx}"
            emb = model.encode(chunk).tolist()
            docs.append(chunk)
            ids.append(doc_id)
            embeddings.append(emb)

    # Add in batches to avoid ChromaDB limits
    batch_size = 50
    for i in range(0, len(docs), batch_size):
        collection.add(
            documents=docs[i : i + batch_size],
            ids=ids[i : i + batch_size],
            embeddings=embeddings[i : i + batch_size],
        )

    return collection, model


# ---------------------------------------------------------------------------
# Tool: search_hr_docs
# ---------------------------------------------------------------------------
def search_hr_docs(query: str, collection, model) -> str:
    """Embed query, retrieve top-3 chunks from HR corpus, return formatted text."""
    query_emb = model.encode(query).tolist()
    results = collection.query(query_embeddings=[query_emb], n_results=3)
    passages = results["documents"][0]
    ids = results["ids"][0]

    lines = []
    for rank, (passage, doc_id) in enumerate(zip(passages, ids), start=1):
        source = doc_id.split("_chunk_")[0]
        lines.append(f"[{rank}] {passage}\n    [Source: {source}]")
    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Tool: calculator
# ---------------------------------------------------------------------------
def calculator(expression: str) -> str:
    """Safely evaluate a numeric expression and return result as string."""
    try:
        safe_globals = {"__builtins__": {}, "math": math}
        result = eval(expression, safe_globals)  # noqa: S307
        return str(result)
    except Exception as exc:
        return f"Error: {exc}"


# ---------------------------------------------------------------------------
# Tool: get_today
# ---------------------------------------------------------------------------
def get_today() -> str:
    return datetime.date.today().isoformat()


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------
def execute_tool(tool_name: str, tool_input: dict, collection, model) -> str:
    """Dispatch a tool call and return the result as a string."""
    try:
        if tool_name == "search_hr_docs":
            return search_hr_docs(tool_input["query"], collection, model)
        elif tool_name == "calculator":
            return calculator(tool_input["expression"])
        elif tool_name == "get_today":
            return get_today()
        else:
            return f"Error: unknown tool '{tool_name}'"
    except Exception as exc:
        return f"Error executing {tool_name}: {exc}"


# ---------------------------------------------------------------------------
# Mock agent (no API key required)
# ---------------------------------------------------------------------------
def _extract_tool_results(messages: list) -> list:
    """Return list of (tool_name, result) from tool_result messages."""
    results = []
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "tool":
            results.append((msg.get("name", "unknown"), msg.get("content", "")))
    return results


def mock_agent_step(messages: list, iteration: int) -> dict:
    """
    Deterministic mock agent. Returns tool calls for iterations 0 and 1,
    then synthesises a final answer on iteration 2+.
    """
    if iteration == 0:
        return {
            "type": "tool_use",
            "tool_name": "search_hr_docs",
            "tool_input": {"query": "annual PTO days accrual years of service"},
        }
    elif iteration == 1:
        return {
            "type": "tool_use",
            "tool_name": "calculator",
            "tool_input": {"expression": "15 * 8"},
        }
    else:
        # Collect tool results from conversation history
        tool_results = _extract_tool_results(messages)
        hr_snippet = ""
        calc_result = ""
        for name, content in tool_results:
            if name == "search_hr_docs":
                hr_snippet = content[:300]
            elif name == "calculator":
                calc_result = content.strip()

        answer = (
            "Based on the HR policy, employees with 0–2 years of service receive "
            "15 PTO days per year (120 hours). "
            f"At 8 hours per day, that equals {calc_result or '120'} work-hours of paid time off."
        )
        return {"type": "final_answer", "content": answer}


# ---------------------------------------------------------------------------
# Agent loop — Anthropic real-LLM path
# ---------------------------------------------------------------------------
def _run_anthropic(question: str, collection, model, max_iterations: int):
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = [{"role": "user", "content": question}]

    for iteration in range(max_iterations):
        print(f"\n[Turn {iteration + 1}] Agent reasoning...")
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nFinal Answer: {block.text}")
            return

        # Process tool calls
        tool_calls_made = False
        assistant_content = []
        for block in response.content:
            assistant_content.append(block)
            if block.type == "tool_use":
                tool_calls_made = True
                print(f"  -> Tool call: {block.name}({json.dumps(block.input)})")
                result = execute_tool(block.name, block.input, collection, model)
                print(f"  <- Result: {result[:200]}")

                # Append assistant turn (with tool_use block)
                messages.append({"role": "assistant", "content": assistant_content})
                # Append tool result
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
                assistant_content = []  # reset for next potential block
                break  # one tool at a time for clarity

        if not tool_calls_made:
            # No tool call and not end_turn — extract text
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nFinal Answer: {block.text}")
            return

    print("\n[WARNING] Max iterations reached without final answer.")


# ---------------------------------------------------------------------------
# Agent loop — OpenAI real-LLM path
# ---------------------------------------------------------------------------
def _tools_to_openai_format(tools: list) -> list:
    """Convert Anthropic-style tool schemas to OpenAI format."""
    openai_tools = []
    for t in tools:
        openai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
        )
    return openai_tools


def _run_openai(question: str, collection, model, max_iterations: int):
    import openai as oai

    client = oai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    oai_tools = _tools_to_openai_format(TOOLS)
    messages = [{"role": "user", "content": question}]

    for iteration in range(max_iterations):
        print(f"\n[Turn {iteration + 1}] Agent reasoning...")
        response = client.chat.completions.create(
            model="gpt-5-mini",
            tools=oai_tools,
            messages=messages,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            print(f"\nFinal Answer: {msg.content}")
            return

        messages.append(msg)
        for tc in msg.tool_calls:
            tool_name = tc.function.name
            tool_input = json.loads(tc.function.arguments)
            print(f"  -> Tool call: {tool_name}({json.dumps(tool_input)})")
            result = execute_tool(tool_name, tool_input, collection, model)
            print(f"  <- Result: {result[:200]}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

    print("\n[WARNING] Max iterations reached without final answer.")


# ---------------------------------------------------------------------------
# Agent loop — mock path
# ---------------------------------------------------------------------------
def _run_mock(question: str, collection, model, max_iterations: int):
    messages: list = [{"role": "user", "content": question}]

    for iteration in range(max_iterations):
        print(f"\n[Turn {iteration + 1}] Agent reasoning...")
        step = mock_agent_step(messages, iteration)

        if step["type"] == "final_answer":
            print(f"\nFinal Answer: {step['content']}")
            return

        tool_name = step["tool_name"]
        tool_input = step["tool_input"]
        print(f"  -> Tool call: {tool_name}({json.dumps(tool_input)})")
        result = execute_tool(tool_name, tool_input, collection, model)
        print(f"  <- Result: {result[:300]}")

        # Append to message history (simplified format for mock)
        messages.append({"role": "assistant", "content": f"[tool_use: {tool_name}]"})
        messages.append({"role": "tool", "name": tool_name, "content": result})

    print("\n[WARNING] Max iterations reached without final answer.")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def run_agent(question: str, collection, model, max_iterations: int = 10):
    """Run the agent in the appropriate mode and print results."""
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    if anthropic_key and anthropic_key.startswith("sk-"):
        print("Mode: ANTHROPIC (claude-haiku-4-5)\n")
        _run_anthropic(question, collection, model, max_iterations)
    elif openai_key and openai_key.startswith("sk-"):
        print("Mode: OPENAI (gpt-5-mini)\n")
        _run_openai(question, collection, model, max_iterations)
    else:
        print("Mode: MOCK (no API key detected)\n")
        _run_mock(question, collection, model, max_iterations)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Day 9 Agent — HR Policy Q&A ===\n")
    print("Building HR index (this may take ~20s on first run)...")
    collection, embed_model = build_hr_index()
    print("Index ready.\n")

    question = (
        "How many PTO days do I get after 2 years of service, "
        "and how many work-hours is that at 8 hours per day?"
    )
    print(f"Question: {question}\n")
    run_agent(question, collection, embed_model)
