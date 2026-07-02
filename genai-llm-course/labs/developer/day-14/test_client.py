"""
Day 14 Lab — Standalone test suite using FastAPI TestClient.
============================================================
Runs without a live server. No API key required (mock mode).

Usage:
    pytest labs/developer/day-14/test_client.py -v
    # or:
    python labs/developer/day-14/test_client.py
"""

import json
import os
import sys

# Make sure solution is importable from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import pytest
from fastapi.testclient import TestClient

# Import the app from solution
from labs.developer.day_14.solution import app, APP_API_KEY

client = TestClient(app)
AUTH = {"Authorization": f"Bearer {APP_API_KEY}"}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
def test_health_returns_200():
    r = client.get("/health")
    assert r.status_code == 200


def test_health_body():
    r = client.get("/health")
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "provider" in data


def test_health_no_auth_required():
    """Health endpoint must be public."""
    r = client.get("/health")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def test_chat_requires_auth():
    r = client.post("/chat", json={"question": "What is PTO?"})
    assert r.status_code in (401, 403)


def test_chat_rejects_bad_key():
    r = client.post(
        "/chat",
        headers={"Authorization": "Bearer wrong-key"},
        json={"question": "What is PTO?"},
    )
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def test_chat_rejects_empty_question():
    r = client.post("/chat", headers=AUTH, json={"question": ""})
    assert r.status_code == 422


def test_chat_rejects_missing_question():
    r = client.post("/chat", headers=AUTH, json={})
    assert r.status_code == 422


def test_chat_rejects_question_too_long():
    r = client.post("/chat", headers=AUTH, json={"question": "x" * 2001})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Streaming chat
# ---------------------------------------------------------------------------
def test_chat_streams_sse():
    with client.stream("POST", "/chat", headers=AUTH,
                       json={"question": "What is the PTO policy?"}) as r:
        assert r.status_code == 200
        lines = list(r.iter_lines())

    data_lines = [l for l in lines if l.startswith("data: ")]
    assert len(data_lines) >= 2, f"Expected SSE lines, got: {lines}"


def test_chat_sse_chunks_are_valid_json():
    with client.stream("POST", "/chat", headers=AUTH,
                       json={"question": "Tell me about benefits"}) as r:
        for line in r.iter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                payload = json.loads(line[6:])
                assert "chunk" in payload, f"Missing 'chunk' key in {payload}"


def test_chat_sse_ends_with_done():
    lines = []
    with client.stream("POST", "/chat", headers=AUTH,
                       json={"question": "remote work policy"}) as r:
        lines = list(r.iter_lines())
    assert "data: [DONE]" in lines, f"Missing [DONE] sentinel. Lines: {lines[-3:]}"


def test_chat_accepts_session_id():
    with client.stream("POST", "/chat", headers=AUTH,
                       json={"question": "What is PTO?", "session_id": "abc123"}) as r:
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        test_health_returns_200,
        test_health_body,
        test_health_no_auth_required,
        test_chat_requires_auth,
        test_chat_rejects_bad_key,
        test_chat_rejects_empty_question,
        test_chat_rejects_missing_question,
        test_chat_rejects_question_too_long,
        test_chat_streams_sse,
        test_chat_sse_chunks_are_valid_json,
        test_chat_sse_ends_with_done,
        test_chat_accepts_session_id,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
