"""
Day 9 Lab — Tool-Using Agent (starter.py)
==========================================
Complete the six TODO sections below.
Run from the repo root:  python labs/developer/day-09/starter.py

The agent answers:
  "How many PTO days do I get after 2 years of service,
   and how many work-hours is that at 8 hours per day?"

It has three tools:
  - search_hr_docs  : RAG over the HR corpus
  - calculator      : safe arithmetic evaluation
  - get_today       : returns today's ISO date

Runs in mock mode (no API key) or real-LLM mode (Anthropic / OpenAI).
"""

import os
import json
import math
import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]
HR_CORPUS_DIR = REPO_ROOT / "data" / "hr-corpus"

# ---------------------------------------------------------------------------
# Tool schemas (JSON Schema format understood by Claude and OpenAI)
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
            "the math module (e.g. 'math.sqrt(144)'). Do NOT use for anything "
            "other than arithmetic."
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
# TODO 1 — Build the HR ChromaDB index
# ---------------------------------------------------------------------------
def build_hr_index():
    """
    Load every .md file from HR_CORPUS_DIR, split into ~400-char chunks,
    embed with sentence-transformers ('all-MiniLM-L6-v2'), and store in an
    in-memory ChromaDB collection called 'hr_docs'.

    Return the (collection, embedding_model) tuple.

    Steps:
      1. Import chromadb and SentenceTransformer.
      2. Create an in-memory ChromaDB client and get-or-create collection 'hr_docs'.
      3. For each .md file in HR_CORPUS_DIR:
         a. Read the text.
         b. Split into chunks of ~400 characters (simple split on double newlines
            then merge until chunk length > 400).
         c. Embed the chunks with the SentenceTransformer model.
         d. Add to the collection with unique ids like "filename_chunk_0".
      4. Return (collection, model).
    """
    # TODO: implement this function
    raise NotImplementedError("TODO 1: implement build_hr_index()")


# ---------------------------------------------------------------------------
# TODO 2 — Retrieval tool
# ---------------------------------------------------------------------------
def search_hr_docs(query: str, collection, model) -> str:
    """
    Embed `query` with `model`, query `collection` for top-3 results,
    and return a formatted string of the matching passages.

    Return format (plain text, not JSON):
      [1] <passage text>
      [Source: filename]

      [2] ...
    """
    # TODO: implement this function
    raise NotImplementedError("TODO 2: implement search_hr_docs()")


# ---------------------------------------------------------------------------
# TODO 3 — Calculator tool
# ---------------------------------------------------------------------------
def calculator(expression: str) -> str:
    """
    Safely evaluate `expression` using eval() with a restricted namespace
    that only exposes math builtins.

    Return the result as a string, e.g. "120" or "3.14159".
    On error, return a descriptive error string starting with "Error: ".

    Hint: use eval(expression, {"__builtins__": {}, "math": math})
    """
    # TODO: implement this function
    raise NotImplementedError("TODO 3: implement calculator()")


# ---------------------------------------------------------------------------
# get_today — already implemented (zero-argument tool example)
# ---------------------------------------------------------------------------
def get_today() -> str:
    return datetime.date.today().isoformat()


# ---------------------------------------------------------------------------
# TODO 4 — Tool dispatcher
# ---------------------------------------------------------------------------
def execute_tool(tool_name: str, tool_input: dict, collection, model) -> str:
    """
    Dispatch a tool call to the correct Python function.
    Return the result as a string.

    On unknown tool name, return "Error: unknown tool '<tool_name>'".
    """
    # TODO: implement this function
    raise NotImplementedError("TODO 4: implement execute_tool()")


# ---------------------------------------------------------------------------
# TODO 5 — Mock agent step
# ---------------------------------------------------------------------------
def mock_agent_step(messages: list, iteration: int) -> dict:
    """
    A deterministic mock that mimics an LLM selecting tools based on keyword
    rules. Returns a dict with keys:
      - "type": "tool_use" | "final_answer"
      - "tool_name": str (if type == "tool_use")
      - "tool_input": dict (if type == "tool_use")
      - "content": str (if type == "final_answer")

    Implement the following rule sequence:
      iteration 0  -> search_hr_docs with query "annual PTO days accrual years of service"
      iteration 1  -> calculator with expression "15 * 8"
      iteration 2+ -> final_answer synthesising what was found

    The final_answer content should incorporate the actual tool results stored
    in the messages list (look for role=="tool" messages).
    """
    # TODO: implement this function
    raise NotImplementedError("TODO 5: implement mock_agent_step()")


# ---------------------------------------------------------------------------
# TODO 6 — Agent loop
# ---------------------------------------------------------------------------
def run_agent(question: str, collection, model, max_iterations: int = 10):
    """
    Run the agent loop until the LLM (or mock) produces a final answer or
    max_iterations is reached.

    Algorithm:
      1. Build the initial messages list: [{"role": "user", "content": question}]
      2. Detect provider: if ANTHROPIC_API_KEY -> use Anthropic; elif
         OPENAI_API_KEY -> use OpenAI; else -> mock.
      3. Loop up to max_iterations:
         a. Call the LLM (or mock_agent_step).
         b. If the response is a tool call:
            i.  Print the tool call.
            ii. Execute via execute_tool().
            iii.Print the result.
            iv. Append assistant message (tool call) and tool result to messages.
         c. If the response is a final answer: print and return.
      4. If max_iterations reached, print a warning and return.

    For Anthropic real-LLM mode, pass tools in Anthropic format.
    For OpenAI real-LLM mode, convert TOOLS to OpenAI format (wrap in
    {"type": "function", "function": {...}}).

    Print a header showing the mode (MOCK / ANTHROPIC / OPENAI).
    """
    # TODO: implement this function
    raise NotImplementedError("TODO 6: implement run_agent()")


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
