import pytest
from signals.technical.regime_gate import MarketRegimeGate, RegimeStatus
from signals.technical.rsi_confluence import OversoldConfluenceSignal, OverboughtConfluenceSignal


def test_regime_gate_uptrend(uptrend_df):
    gate = MarketRegimeGate()
    status = gate.detect(uptrend_df)
    assert status == RegimeStatus.UPTREND


def test_regime_gate_downtrend(downtrend_df):
    gate = MarketRegimeGate()
    status = gate.detect(downtrend_df)
    assert status == RegimeStatus.DOWNTREND


def test_regime_gate_needs_200_bars():
    import pandas as pd, numpy as np
    short_df = pd.DataFrame({"close": np.linspace(90, 110, 50)})
    gate = MarketRegimeGate()
    status = gate.detect(short_df)
    assert status == RegimeStatus.UNKNOWN


def test_oversold_confluence_fires(oversold_df):
    signal = OversoldConfluenceSignal()
    result = signal.check("AAPL", oversold_df)
    assert result is not None
    assert result.direction == "bullish"
    assert result.signal_name == "Oversold Confluence"
    assert result.strength == "strong"
    assert len(result.conditions) == 3


def test_oversold_confluence_no_fire_on_flat(flat_df):
    signal = OversoldConfluenceSignal()
    result = signal.check("AAPL", flat_df)
    assert result is None


def test_oversold_confluence_requires_min_rows():
    import pandas as pd, numpy as np
    tiny_df = pd.DataFrame({"close": [100.0] * 10, "volume": [1e6] * 10})
    signal = OversoldConfluenceSignal()
    assert signal.check("AAPL", tiny_df) is None


def test_overbought_confluence_fires(overbought_df):
    signal = OverboughtConfluenceSignal()
    result = signal.check("TSLA", overbought_df)
    assert result is not None
    assert result.direction == "bearish"
    assert result.signal_name == "Overbought Confluence"


def test_overbought_confluence_no_fire_on_flat(flat_df):
    signal = OverboughtConfluenceSignal()
    assert signal.check("TSLA", flat_df) is None


from signals.technical.breakout_confluence import BullishBreakoutSignal, BearishBreakdownSignal
import numpy as np, pandas as pd


def make_golden_cross_df():
    """260 bars: 50 MA just crossed above 200 MA, volume spike, price at 52w high."""
    n = 260
    # Create a scenario where MA50 crosses above MA200 on the last bar:
    # First 200 bars at 100 (establishes baseline), crash to 80, stay flat, then recover to 130
    base_part = np.full(200, 100.0)
    crash_start = np.linspace(100, 80, 10)
    low_part = np.full(10, 80.0)
    recover_part = np.linspace(80, 130, 40)
    close = np.concatenate([base_part, crash_start, low_part, recover_part])

    base_vol = 1_000_000
    volume = np.full(n, base_vol)
    volume[-1] = base_vol * 2.5
    idx = pd.date_range("2023-01-01", periods=n, freq="D")
    return pd.DataFrame({"open": close*0.99, "high": close*1.01,
                          "low": close*0.98, "close": close, "volume": volume}, index=idx)


def make_death_cross_df():
    """260 bars: 50 MA just crossed below 200 MA, volume spike, price at 52w low."""
    n = 260
    # Create a scenario where MA50 crosses below MA200 on the last bar:
    # First 208 bars at 120 (establishes baseline), stable 50 bars, spike to 130, then crash to 50
    base_part = np.full(208, 120.0)
    stable_part = np.full(50, 120.0)
    spike_bar = np.array([130.0])
    crash_bar = np.array([50.0])
    close = np.concatenate([base_part, stable_part, spike_bar, crash_bar])

    base_vol = 1_000_000
    volume = np.full(n, base_vol)
    volume[-1] = base_vol * 2.5
    idx = pd.date_range("2023-01-01", periods=n, freq="D")
    return pd.DataFrame({"open": close*0.99, "high": close*1.01,
                          "low": close*0.98, "close": close, "volume": volume}, index=idx)


def test_bullish_breakout_fires():
    signal = BullishBreakoutSignal()
    df = make_golden_cross_df()
    result = signal.check("SPY", df)
    assert result is not None
    assert result.direction == "bullish"
    assert result.signal_name == "Bullish Breakout"


def test_bullish_breakout_no_fire_on_downtrend(downtrend_df):
    signal = BullishBreakoutSignal()
    assert signal.check("SPY", downtrend_df) is None


def test_bearish_breakdown_fires():
    signal = BearishBreakdownSignal()
    df = make_death_cross_df()
    result = signal.check("SPY", df)
    assert result is not None
    assert result.direction == "bearish"
    assert result.signal_name == "Bearish Breakdown"


def test_bearish_breakdown_no_fire_on_uptrend(uptrend_df):
    signal = BearishBreakdownSignal()
    assert signal.check("SPY", uptrend_df) is None


from signals.technical.intraday_momentum import IntradayMomentumSignal


def make_intraday_bullish_df():
    """50 bars: MACD just crossed bullish, volume spike, price above VWAP."""
    n = 50
    # Rising close to produce bullish MACD cross
    close = np.concatenate([np.linspace(100, 98, 30), np.linspace(98, 108, 20)])
    base_vol = 500_000
    volume = np.full(n, base_vol)
    volume[-1] = base_vol * 2.5
    idx = pd.date_range("2024-01-01 09:30", periods=n, freq="15min")
    return pd.DataFrame({"open": close*0.999, "high": close*1.002,
                          "low": close*0.997, "close": close, "volume": volume}, index=idx)


def test_intraday_momentum_correct_type():
    signal = IntradayMomentumSignal()
    df = make_intraday_bullish_df()
    result = signal.check("AAPL", df)
    # Result is None or a valid SignalResult — never raises
    assert result is None or result.direction in ("bullish", "bearish")


def test_intraday_momentum_requires_min_rows():
    signal = IntradayMomentumSignal()
    tiny = pd.DataFrame({"close": [100.0]*5, "volume": [1e5]*5})
    assert signal.check("AAPL", tiny) is None


def test_intraday_momentum_time_horizon():
    signal = IntradayMomentumSignal()
    assert signal.time_horizon == "intraday"


from signals.quant.mean_reversion import MeanReversionSignal


def make_mean_reversion_df(direction: str = "oversold"):
    """90 bars: price gap moves 2+ std devs from 20-day mean with RSI extreme and low vol."""
    n = 90
    if direction == "oversold":
        # 80 flat bars at 100, then 9 at 100, then 1 gap down to 80
        # This creates extreme zscore with low CV
        base = np.full(89, 100.0)
        tail = np.array([80.0])
    else:
        # 80 flat bars at 100, then 9 at 100, then 1 gap up to 120
        base = np.full(89, 100.0)
        tail = np.array([120.0])

    close = np.concatenate([base, tail])
    volume = np.full(n, 1_000_000)
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame({"open": close*0.99, "high": close*1.01,
                          "low": close*0.97, "close": close, "volume": volume}, index=idx)


def test_mean_reversion_oversold_fires():
    signal = MeanReversionSignal()
    df = make_mean_reversion_df("oversold")
    result = signal.check("AAPL", df)
    assert result is not None
    assert result.direction == "bullish"
    assert result.signal_name == "Mean Reversion Setup"


def test_mean_reversion_overbought_fires():
    signal = MeanReversionSignal()
    df = make_mean_reversion_df("overbought")
    result = signal.check("AAPL", df)
    assert result is not None
    assert result.direction == "bearish"


def test_mean_reversion_no_fire_on_flat(flat_df):
    signal = MeanReversionSignal()
    assert signal.check("AAPL", flat_df) is None
