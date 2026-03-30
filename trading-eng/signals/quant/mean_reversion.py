from __future__ import annotations
from typing import Optional
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator

from signals.base import BaseSignal, SignalResult
from signals.registry import register_signal


@register_signal
class MeanReversionSignal(BaseSignal):
    """
    Fires when:
      - |z-score| > 2.0 (price > 2 std devs from 20-day mean)
      - RSI extreme (< 35 for oversold, > 65 for overbought)
      - Low volatility regime (20-day rolling std / mean < 0.03)
    """
    time_horizon = "swing"
    asset_classes = ("stock", "etf", "crypto")

    ZSCORE_THRESHOLD = 2.0
    LOW_VOL_THRESHOLD = 0.03

    def check(self, ticker: str, df: pd.DataFrame) -> Optional[SignalResult]:
        if len(df) < 50 or "close" not in df.columns:
            return None

        close = df["close"]
        rolling_mean = close.rolling(20).mean()
        rolling_std = close.rolling(20).std()
        long_std = close.rolling(50).std()
        long_mean = close.rolling(50).mean()

        price = float(close.iloc[-1])
        mean = float(rolling_mean.iloc[-1])
        std = float(rolling_std.iloc[-1])
        long_vol = float(long_std.iloc[-1])
        long_price_mean = float(long_mean.iloc[-1])

        if std == 0 or mean == 0 or long_vol == 0 or long_price_mean == 0:
            return None

        zscore = (price - mean) / std
        # Low volatility regime: check if overall market volatility is low (50-day CV)
        vol_regime = long_vol / long_price_mean

        rsi_val = float(RSIIndicator(close=close, window=14).rsi().iloc[-1])

        oversold = zscore < -self.ZSCORE_THRESHOLD and rsi_val < 35
        overbought = zscore > self.ZSCORE_THRESHOLD and rsi_val > 65
        low_vol = vol_regime < self.LOW_VOL_THRESHOLD

        if not ((oversold or overbought) and low_vol):
            return None

        direction = "bullish" if oversold else "bearish"
        return SignalResult(
            ticker=ticker,
            signal_name="Mean Reversion Setup",
            time_horizon=self.time_horizon,
            strength="moderate",
            direction=direction,
            conditions=[
                f"Z-score = {zscore:.2f} ({'oversold' if oversold else 'overbought'})",
                f"RSI(14) = {rsi_val:.1f}",
                f"Low vol regime: CV(50) = {vol_regime:.3f} < 0.03",
            ],
            price=round(price, 2),
        )
