"""
Day 5 Starter — APIs, Async & Testing
======================================
Implement the two functions below, then wire up the argparse CLI.
No network or API key required — everything works on plain strings.

Run your tests with:
    pytest curriculum/python-foundation/exercises/day-05/ -v

Run the built-in smoke test with:
    python curriculum/python-foundation/exercises/day-05/starter.py --selftest
"""

from __future__ import annotations

import re
import argparse
from collections import Counter


# ---------------------------------------------------------------------------
# Core functions — implement these
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Return a cleaned version of *text*.

    Rules (apply in order):
    1. Strip leading and trailing whitespace.
    2. Collapse any internal run of whitespace (spaces, tabs, newlines) into a
       single space.
    3. Convert to lowercase.
    4. Remove all characters that are NOT letters, digits, or spaces.

    Examples:
        normalize_text("  Hello, World!  ") -> "hello world"
        normalize_text("Python  3.11")      -> "python 311"
        normalize_text("  ")                -> ""

    Args:
        text: Raw input string.

    Returns:
        Cleaned string.
    """
    # TODO: implement the four rules above using str methods and/or re module
    raise NotImplementedError("implement normalize_text")


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
        text: A normalized string (as returned by normalize_text).

    Returns:
        Dict of {word: count}, ordered by insertion (Python 3.7+).
    """
    # TODO: split text into words and count them.
    # Hint: str.split() with no arguments handles multiple spaces correctly.
    # Hint: collections.Counter is your friend, but a plain loop also works.
    raise NotImplementedError("implement word_frequencies")


# ---------------------------------------------------------------------------
# HTTP reference — NOT required to run the exercise
# ---------------------------------------------------------------------------
# The block below shows how you would call a real API using httpx.
# It is commented out because it requires a network connection and an API key.
# Study it, then run the exercise functions above (no network needed).
#
# import httpx
#
# REFERENCE ONLY — do not uncomment to run the exercise
# def call_api_example(prompt: str, api_key: str) -> str:
#     """POST to a hypothetical completion API and return the response text."""
#     with httpx.Client(timeout=15) as client:
#         r = client.post(
#             "https://api.example.com/v1/complete",
#             json={"prompt": prompt, "max_tokens": 50},
#             headers={"Authorization": f"Bearer {api_key}"},
#         )
#         r.raise_for_status()            # raises HTTPStatusError on 4xx/5xx
#         return r.json()["text"]         # parse JSON body → dict


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    p = argparse.ArgumentParser(
        description="Normalize text and count word frequencies."
    )
    # TODO: add a positional argument "text" that accepts zero or one value
    #       (hint: nargs="?") so that --selftest works without providing text.
    # TODO: add a --selftest flag (action="store_true") that runs smoke tests.
    # TODO: add a --frequencies flag (action="store_true") that also prints
    #       word frequencies when processing normal text.
    raise NotImplementedError("implement build_parser — remove this line and add arguments")
    return p


def main() -> None:
    args = build_parser().parse_args()

    if args.selftest:
        # TODO: call normalize_text and word_frequencies on sample inputs,
        #       assert the expected results, and print "All self-tests passed."
        raise NotImplementedError("implement selftest block")

    if args.text:
        normalized = normalize_text(args.text)
        print(f"Normalized: {normalized!r}")
        # TODO: if args.frequencies is True, also print word_frequencies result
    else:
        build_parser().print_help()


if __name__ == "__main__":
    main()
