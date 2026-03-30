from __future__ import annotations
from typing import Optional
import pandas as pd

from signals.base import BaseSignal, SignalResult
from signals.registry import register_signal


def _ma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()


def _vol_ratio(df: pd.DataFrame) -> float:
    avg = df["volume"].rolling(20).mean().iloc[-1]
    return float(df["volume"].iloc[-1] / avg) if avg > 0 else 0.0


@register_signal
class BullishBreakoutSignal(BaseSignal):
    time_horizon = "position"
    asset_classes = ("stock", "etf")

    def check(self, ticker: str, df: pd.DataFrame) -> Optional[SignalResult]:
        if len(df) < 210 or not {"close", "volume"}.issubset(df.columns):
            return None

        close = df["close"]
        ma50 = _ma(close, 50)
        ma200 = _ma(close, 200)

        golden_cross = ma50.iloc[-1] > ma200.iloc[-1] and ma50.iloc[-2] <= ma200.iloc[-2]
        vol_ok = _vol_ratio(df) >= 2.0
        high_52w = close.rolling(252).max().iloc[-1]
        price = float(close.iloc[-1])
        price_ok = price >= high_52w * 0.99

        if not (golden_cross and vol_ok and price_ok):
            return None

        vol_r = _vol_ratio(df)
        return SignalResult(
            ticker=ticker,
            signal_name="Bullish Breakout",
            time_horizon=self.time_horizon,
            strength="strong",
            direction="bullish",
            conditions=[
                f"Golden cross: MA50 ({ma50.iloc[-1]:.2f}) > MA200 ({ma200.iloc[-1]:.2f})",
                f"Volume {vol_r:.1f}× 20-day avg",
                f"Price at/near 52-week high (${price:.2f})",
            ],
            price=round(price, 2),
        )


@register_signal
class BearishBreakdownSignal(BaseSignal):
    time_horizon = "position"
    asset_classes = ("stock", "etf")

    def check(self, ticker: str, df: pd.DataFrame) -> Optional[SignalResult]:
        if len(df) < 210 or not {"close", "volume"}.issubset(df.columns):
            return None

        close = df["close"]
        ma50 = _ma(close, 50)
        ma200 = _ma(close, 200)

        death_cross = ma50.iloc[-1] < ma200.iloc[-1] and ma50.iloc[-2] >= ma200.iloc[-2]
        vol_ok = _vol_ratio(df) >= 2.0
        low_52w = close.rolling(252).min().iloc[-1]
        price = float(close.iloc[-1])
        price_ok = price <= low_52w * 1.01

        if not (death_cross and vol_ok and price_ok):
            return None

        vol_r = _vol_ratio(df)
        return SignalResult(
            ticker=ticker,
            signal_name="Bearish Breakdown",
            time_horizon=self.time_horizon,
            strength="strong",
            direction="bearish",
            conditions=[
                f"Death cross: MA50 ({ma50.iloc[-1]:.2f}) < MA200 ({ma200.iloc[-1]:.2f})",
                f"Volume {vol_r:.1f}× 20-day avg",
                f"Price at/near 52-week low (${price:.2f})",
            ],
            price=round(price, 2),
        )
