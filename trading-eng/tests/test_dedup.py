import json, pytest
from pathlib import Path
from state.dedup import DedupStore
from signals.base import SignalResult


def make_result(ticker="AAPL", name="Test Signal") -> SignalResult:
    return SignalResult(ticker, name, "swing", "strong", "bullish", ["cond"], 150.0)


def test_dedup_new_signal_not_seen(tmp_path):
    store = DedupStore(state_path=tmp_path / "state.json")
    result = make_result()
    assert not store.already_fired(result)


def test_dedup_marks_as_fired(tmp_path):
    store = DedupStore(state_path=tmp_path / "state.json")
    result = make_result()
    store.mark_fired(result)
    assert store.already_fired(result)


def test_dedup_persists_to_disk(tmp_path):
    path = tmp_path / "state.json"
    store = DedupStore(state_path=path)
    store.mark_fired(make_result())

    # New instance reads same file
    store2 = DedupStore(state_path=path)
    assert store2.already_fired(make_result())


def test_dedup_different_signal_not_seen(tmp_path):
    store = DedupStore(state_path=tmp_path / "state.json")
    store.mark_fired(make_result("AAPL", "Signal A"))
    assert not store.already_fired(make_result("AAPL", "Signal B"))


def test_dedup_handles_corrupt_file(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("not valid json{{")
    store = DedupStore(state_path=path)  # should not raise
    assert not store.already_fired(make_result())
