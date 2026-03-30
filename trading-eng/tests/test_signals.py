import pytest
from signals.technical.regime_gate import MarketRegimeGate, RegimeStatus


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
