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
