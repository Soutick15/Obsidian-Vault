"""
Day 5 Solution — APIs, Async & Testing
========================================
Reference implementation of normalize_text, word_frequencies, and the
argparse CLI with --selftest.

No network or API key required — all logic operates on plain strings.

Usage:
    python solution.py --selftest
    python solution.py "  Hello, World!  "
    python solution.py "the cat sat on the mat" --frequencies
"""

from __future__ import annotations

import re
import argparse
from collections import Counter


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Return a cleaned version of *text*.

    Rules applied in order:
    1. Strip leading and trailing whitespace.
    2. Collapse internal whitespace runs into a single space.
    3. Convert to lowercase.
    4. Remove characters that are NOT letters, digits, or spaces.

    Examples:
        normalize_text("  Hello, World!  ") -> "hello world"
        normalize_text("Python  3.11")      -> "python 311"
        normalize_text("  ")                -> ""

    Args:
        text: Raw input string.

    Returns:
        Cleaned string.
    """
    text = text.strip()
    text = re.sub(r"\s+", " ", text)   # collapse whitespace
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", "", text)  # keep letters, digits, spaces
    return text


def word_frequencies(text: str) -> dict[str, int]:
    """Return a dict mapping each word in *text* to its occurrence count.

    *text* is treated as already-normalized (lowercase, no punctuation).
    Words are separated by whitespace.  Empty input returns an empty dict.

    Examples:
        word_frequencies("the cat sat on the mat") ->
            {"the": 2, "cat": 1, "sat": 1, "on": 1, "mat": 1}
        word_frequencies("") -> {}
        word_frequencies("  ") -> {}

    Args:
        text: A normalized string.

    Returns:
        Dict of {word: count}.
    """
    words = text.split()        # str.split() with no arg handles extra spaces
    if not words:
        return {}
    return dict(Counter(words))


# ---------------------------------------------------------------------------
# HTTP reference — NOT required to run this exercise
# ---------------------------------------------------------------------------
# The snippet below shows how you would call a real REST API using httpx.
# It is commented out because it requires a network connection and an API key.
# Study the pattern, then note that the exercise functions above need neither.
#
# import httpx
#
# REFERENCE ONLY — do not uncomment to run the exercise
# def call_api_example(prompt: str, api_key: str) -> str:
#     """POST to a hypothetical completion API and return the response text."""
#     try:
#         with httpx.Client(timeout=15) as client:
#             r = client.post(
#                 "https://api.example.com/v1/complete",
#                 json={"prompt": prompt, "max_tokens": 50},
#                 headers={"Authorization": f"Bearer {api_key}"},
#             )
#             r.raise_for_status()            # raises HTTPStatusError on 4xx/5xx
#             return r.json()["text"]         # parse JSON body → dict
#     except httpx.TimeoutException:
#         raise RuntimeError("Request timed out")
#     except httpx.HTTPStatusError as e:
#         raise RuntimeError(f"API error {e.response.status_code}: {e.response.text}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    p = argparse.ArgumentParser(
        description="Normalize text and count word frequencies."
    )
    p.add_argument(
        "text",
        nargs="?",
        help="Text to normalize (optional when --selftest is used)",
    )
    p.add_argument(
        "--selftest",
        action="store_true",
        help="Run built-in smoke tests and exit (no network or API key needed)",
    )
    p.add_argument(
        "--frequencies",
        action="store_true",
        help="Also print word frequency counts",
    )
    return p


def _run_selftests() -> None:
    """Run smoke tests and print a summary.  Raises AssertionError on failure."""
    # normalize_text — basic cases
    assert normalize_text("  Hello, World!  ") == "hello world", \
        "normalize: strip + remove punctuation failed"
    assert normalize_text("Python  3.11") == "python 311", \
        "normalize: collapse whitespace + digits failed"
    assert normalize_text("  ") == "", \
        "normalize: all-whitespace should return empty string"
    assert normalize_text("UPPER") == "upper", \
        "normalize: lowercase failed"
    assert normalize_text("café") == "caf", \
        "normalize: non-ASCII letters removed (only a-z0-9 kept)"

    # word_frequencies — basic cases
    freqs = word_frequencies("the cat sat on the mat")
    assert freqs["the"] == 2, "word_frequencies: 'the' should appear twice"
    assert freqs["cat"] == 1, "word_frequencies: 'cat' should appear once"
    assert set(freqs.keys()) == {"the", "cat", "sat", "on", "mat"}, \
        "word_frequencies: unexpected keys"

    assert word_frequencies("") == {}, \
        "word_frequencies: empty string should return {}"
    assert word_frequencies("   ") == {}, \
        "word_frequencies: whitespace-only string should return {}"

    # Combined usage — normalize then count
    combined = word_frequencies(normalize_text("  The Cat, the Hat!  "))
    assert combined.get("the") == 2, "combined: 'the' should appear twice after normalize"
    assert combined.get("cat") == 1, "combined: 'cat' should appear once after normalize"
    assert combined.get("hat") == 1, "combined: 'hat' should appear once after normalize"

    print("All self-tests passed.")


def main() -> None:
    args = build_parser().parse_args()

    if args.selftest:
        _run_selftests()
        return

    if args.text:
        normalized = normalize_text(args.text)
        print(f"Normalized: {normalized!r}")
        if args.frequencies:
            freqs = word_frequencies(normalized)
            if freqs:
                print("Word frequencies:")
                for word, count in sorted(freqs.items(), key=lambda kv: -kv[1]):
                    print(f"  {word}: {count}")
            else:
                print("(no words found)")
    else:
        build_parser().print_help()


if __name__ == "__main__":
    main()
