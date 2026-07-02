"""
Day 5 Tests — normalize_text and word_frequencies
==================================================
Run with:
    pytest curriculum/python-foundation/exercises/day-05/ -v

No network or API key required.  All tests operate on plain strings.
"""

import pytest
from solution import normalize_text, word_frequencies


# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------

class TestNormalizeText:
    """Tests for normalize_text."""

    def test_strips_leading_trailing_whitespace(self):
        assert normalize_text("  hello  ") == "hello"

    def test_collapses_internal_whitespace(self):
        assert normalize_text("hello   world") == "hello world"

    def test_lowercases(self):
        assert normalize_text("HELLO") == "hello"

    def test_removes_punctuation(self):
        assert normalize_text("Hello, World!") == "hello world"

    def test_keeps_digits(self):
        # digits should survive normalization
        result = normalize_text("Python 3")
        assert "3" in result
        assert "python" in result

    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_whitespace_only(self):
        assert normalize_text("   \t\n  ") == ""

    def test_already_normalized(self):
        assert normalize_text("hello world") == "hello world"

    def test_mixed_case_with_punctuation(self):
        assert normalize_text("  Hello, World!  ") == "hello world"


# ---------------------------------------------------------------------------
# word_frequencies
# ---------------------------------------------------------------------------

class TestWordFrequencies:
    """Tests for word_frequencies."""

    def test_basic_sentence(self):
        freqs = word_frequencies("the cat sat on the mat")
        assert freqs["the"] == 2
        assert freqs["cat"] == 1
        assert freqs["sat"] == 1
        assert freqs["on"] == 1
        assert freqs["mat"] == 1

    def test_empty_string(self):
        assert word_frequencies("") == {}

    def test_whitespace_only(self):
        assert word_frequencies("   ") == {}

    def test_single_word(self):
        assert word_frequencies("hello") == {"hello": 1}

    def test_repeated_word(self):
        assert word_frequencies("go go go") == {"go": 3}

    def test_no_extra_keys(self):
        freqs = word_frequencies("a b c")
        assert set(freqs.keys()) == {"a", "b", "c"}


# ---------------------------------------------------------------------------
# Parametrize — normalize_text edge cases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("Hello, World!", "hello world"),
    ("  SPACES  ",   "spaces"),
    ("MiXeD CaSe",  "mixed case"),
    ("tab\there",    "tab here"),
    ("num123ber",    "num123ber"),
    ("!!!",          ""),
])
def test_normalize_parametrized(raw: str, expected: str):
    """normalize_text handles a variety of inputs correctly."""
    assert normalize_text(raw) == expected


# ---------------------------------------------------------------------------
# Parametrize — word_frequencies counts
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,word,expected_count", [
    ("apple apple apple", "apple", 3),
    ("one two three",     "two",   1),
    ("",                  "any",   0),
])
def test_word_count_parametrized(text: str, word: str, expected_count: int):
    """word_frequencies returns the correct count for specific words."""
    freqs = word_frequencies(text)
    assert freqs.get(word, 0) == expected_count


# ---------------------------------------------------------------------------
# Fixture — shared normalized sentence
# ---------------------------------------------------------------------------

@pytest.fixture
def normalized_sentence() -> str:
    """A pre-normalized sentence for tests that need shared input."""
    return "the quick brown fox jumps over the lazy dog"


def test_fixture_word_count(normalized_sentence: str):
    freqs = word_frequencies(normalized_sentence)
    assert freqs["the"] == 2
    assert freqs["fox"] == 1
    assert freqs["dog"] == 1


def test_fixture_unique_words(normalized_sentence: str):
    freqs = word_frequencies(normalized_sentence)
    # "the" appears twice; all others should appear once
    single_occurrence = [w for w, c in freqs.items() if c == 1]
    assert len(single_occurrence) == len(freqs) - 1


# ---------------------------------------------------------------------------
# Combined usage
# ---------------------------------------------------------------------------

def test_normalize_then_count():
    """Typical pipeline: normalize raw text, then count words."""
    raw = "  The Cat, the Hat!  "
    freqs = word_frequencies(normalize_text(raw))
    assert freqs.get("the") == 2
    assert freqs.get("cat") == 1
    assert freqs.get("hat") == 1
    # Comma and exclamation should not appear as words
    assert "cat," not in freqs
    assert "hat!" not in freqs
