# tests/test_cache.py
import json
import time
import pytest
from pathlib import Path
from fantasy.cache import cached_call

def test_cache_stores_and_retrieves(tmp_path, monkeypatch):
    monkeypatch.setenv("CACHE_DIR", str(tmp_path))
    call_count = 0
    def fetch():
        nonlocal call_count
        call_count += 1
        return {"value": 42}
    result1 = cached_call("test_key", ttl=60, fetch_fn=fetch)
    result2 = cached_call("test_key", ttl=60, fetch_fn=fetch)
    assert result1 == {"value": 42}
    assert result2 == {"value": 42}
    assert call_count == 1  # fetch called only once

def test_cache_expires(tmp_path, monkeypatch):
    monkeypatch.setenv("CACHE_DIR", str(tmp_path))
    call_count = 0
    def fetch():
        nonlocal call_count
        call_count += 1
        return {"tick": call_count}
    cached_call("expiry_key", ttl=1, fetch_fn=fetch)
    time.sleep(1.1)
    cached_call("expiry_key", ttl=1, fetch_fn=fetch)
    assert call_count == 2

def test_cache_different_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("CACHE_DIR", str(tmp_path))
    cached_call("key_a", ttl=60, fetch_fn=lambda: "a")
    cached_call("key_b", ttl=60, fetch_fn=lambda: "b")
    assert cached_call("key_a", ttl=60, fetch_fn=lambda: "x") == "a"
    assert cached_call("key_b", ttl=60, fetch_fn=lambda: "x") == "b"
