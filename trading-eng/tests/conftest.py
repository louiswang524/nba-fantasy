import numpy as np
import pandas as pd
import pytest


def _make_df(n: int, close_values: list[float] | None = None, volume_multiplier: float = 1.0) -> pd.DataFrame:
    if close_values is not None:
        close = np.array(close_values, dtype=float)
        n = len(close)
    else:
        close = np.linspace(100, 110, n)

    base_vol = 1_000_000
    volume = np.full(n, base_vol * volume_multiplier)
    # Make last bar volume a spike if multiplier > 1
    volume[-1] = base_vol * volume_multiplier

    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "open":   close * 0.99,
        "high":   close * 1.02,
        "low":    close * 0.97,
        "close":  close,
        "volume": volume,
    }, index=idx)


@pytest.fixture
def uptrend_df():
    """200 bars of steady uptrend; price well above 200 MA."""
    close = np.linspace(80, 120, 200)
    return _make_df(200, close_values=close.tolist())


@pytest.fixture
def downtrend_df():
    """200 bars of steady downtrend; price well below 200 MA."""
    close = np.linspace(120, 80, 200)
    return _make_df(200, close_values=close.tolist())


@pytest.fixture
def oversold_df():
    """90 bars: steady decline forcing RSI < 32, volume spike on last bar, price near BB lower."""
    # Drop sharply over last 20 bars to depress RSI
    first = np.linspace(100, 90, 70)
    last = np.linspace(90, 65, 20)
    close = np.concatenate([first, last])
    base_vol = 1_000_000
    volume = np.full(len(close), base_vol)
    volume[-1] = base_vol * 3.0  # volume spike
    idx = pd.date_range("2024-01-01", periods=len(close), freq="D")
    return pd.DataFrame({"open": close * 0.99, "high": close * 1.01,
                          "low": close * 0.97, "close": close, "volume": volume}, index=idx)


@pytest.fixture
def overbought_df():
    """90 bars: steady rise forcing RSI > 68, volume spike on last bar, price near BB upper."""
    first = np.linspace(100, 110, 70)
    last = np.linspace(110, 135, 20)
    close = np.concatenate([first, last])
    base_vol = 1_000_000
    volume = np.full(len(close), base_vol)
    volume[-1] = base_vol * 3.0
    idx = pd.date_range("2024-01-01", periods=len(close), freq="D")
    return pd.DataFrame({"open": close * 0.99, "high": close * 1.02,
                          "low": close * 0.97, "close": close, "volume": volume}, index=idx)


@pytest.fixture
def flat_df():
    """90 bars of flat price — no signals should fire."""
    close = np.full(90, 100.0)
    return _make_df(90, close_values=close.tolist())
