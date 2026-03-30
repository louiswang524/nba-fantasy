# tests/test_screener.py
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock
from signals.base import BaseSignal, SignalResult
from signals.registry import _clear_registry, register_signal, get_signals
from screener import Screener


def make_mock_signal(result):
    """Register a mock signal that always returns `result`."""
    @register_signal
    class MockSignal(BaseSignal):
        time_horizon = "swing"
        asset_classes = ("stock",)
        def check(self, ticker, df):
            return result
    return get_signals()[-1]


def simple_df(n: int = 50) -> pd.DataFrame:
    close = np.linspace(100, 110, n)
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame({"close": close, "volume": np.full(n, 1e6)}, index=idx)


def test_screener_returns_signal_results():
    _clear_registry()
    expected = SignalResult("AAPL", "Test", "swing", "strong", "bullish", ["cond1"], 100.0)
    make_mock_signal(expected)

    screener = Screener()
    results = screener.run({"AAPL": simple_df()}, regime=None)
    assert len(results) == 1
    assert results[0].ticker == "AAPL"


def test_screener_suppresses_bullish_in_downtrend():
    _clear_registry()
    bullish = SignalResult("AAPL", "Bullish Test", "swing", "strong", "bullish", [], 100.0)
    make_mock_signal(bullish)

    from signals.technical.regime_gate import RegimeStatus
    screener = Screener()
    results = screener.run({"AAPL": simple_df()}, regime=RegimeStatus.DOWNTREND)
    assert len(results) == 0


def test_screener_allows_bearish_in_downtrend():
    _clear_registry()
    bearish = SignalResult("AAPL", "Bearish Test", "swing", "strong", "bearish", [], 100.0)
    make_mock_signal(bearish)

    from signals.technical.regime_gate import RegimeStatus
    screener = Screener()
    results = screener.run({"AAPL": simple_df()}, regime=RegimeStatus.DOWNTREND)
    assert len(results) == 1


def test_screener_skips_empty_dataframes():
    _clear_registry()
    expected = SignalResult("AAPL", "Test", "swing", "strong", "bullish", [], 100.0)
    make_mock_signal(expected)

    screener = Screener()
    results = screener.run({"AAPL": pd.DataFrame()}, regime=None)
    assert len(results) == 0


def test_screener_allows_intraday_bullish_in_downtrend():
    """Intraday signals are NOT suppressed by regime gate."""
    _clear_registry()

    @register_signal
    class IntraSignal(BaseSignal):
        time_horizon = "intraday"
        asset_classes = ("stock",)
        def check(self, ticker, df):
            return SignalResult(ticker, "Intraday Test", "intraday", "strong", "bullish", [], 100.0)

    from signals.technical.regime_gate import RegimeStatus
    screener = Screener()
    results = screener.run({"AAPL": simple_df()}, regime=RegimeStatus.DOWNTREND)
    assert len(results) == 1
