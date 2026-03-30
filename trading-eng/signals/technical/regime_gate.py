from __future__ import annotations
from enum import Enum
import pandas as pd


class RegimeStatus(Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    UNKNOWN = "unknown"


class MarketRegimeGate:
    """
    Detects market regime using SPY price vs 200-day MA.
    If price > 200 MA → UPTREND (bullish signals allowed).
    If price < 200 MA → DOWNTREND (bullish swing/position signals suppressed).
    """

    def detect(self, df: pd.DataFrame) -> RegimeStatus:
        if "close" not in df.columns or len(df) < 200:
            return RegimeStatus.UNKNOWN
        ma200 = df["close"].rolling(200).mean().iloc[-1]
        price = df["close"].iloc[-1]
        if price > ma200:
            return RegimeStatus.UPTREND
        return RegimeStatus.DOWNTREND
