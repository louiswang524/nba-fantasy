from __future__ import annotations
from typing import Optional
import pandas as pd
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

from signals.base import BaseSignal, SignalResult
from signals.registry import register_signal


def _rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    return RSIIndicator(close=df["close"], window=period).rsi()


def _bb_lower(df: pd.DataFrame) -> pd.Series:
    return BollingerBands(close=df["close"]).bollinger_lband()


def _bb_upper(df: pd.DataFrame) -> pd.Series:
    return BollingerBands(close=df["close"]).bollinger_hband()


def _vol_ratio(df: pd.DataFrame) -> float:
    avg = df["volume"].rolling(20).mean().iloc[-1]
    return float(df["volume"].iloc[-1] / avg) if avg > 0 else 0.0


@register_signal
class OversoldConfluenceSignal(BaseSignal):
    time_horizon = "swing"
    asset_classes = ("stock", "etf", "crypto")

    def check(self, ticker: str, df: pd.DataFrame) -> Optional[SignalResult]:
        if len(df) < 30 or not {"close", "volume"}.issubset(df.columns):
            return None

        rsi_val = float(_rsi(df).iloc[-1])
        price = float(df["close"].iloc[-1])
        vol_ratio = _vol_ratio(df)
        bb_low = float(_bb_lower(df).iloc[-1])

        rsi_ok = rsi_val < 32
        vol_ok = vol_ratio >= 2.0
        bb_ok = price <= bb_low * 1.05

        if not (rsi_ok and vol_ok and bb_ok):
            return None

        return SignalResult(
            ticker=ticker,
            signal_name="Oversold Confluence",
            time_horizon=self.time_horizon,
            strength="strong",
            direction="bullish",
            conditions=[
                f"RSI(14) = {rsi_val:.1f} (oversold < 32)",
                f"Volume {vol_ratio:.1f}× 20-day avg",
                f"Price at BB lower band (${price:.2f})",
            ],
            price=round(price, 2),
        )


@register_signal
class OverboughtConfluenceSignal(BaseSignal):
    time_horizon = "swing"
    asset_classes = ("stock", "etf", "crypto")

    def check(self, ticker: str, df: pd.DataFrame) -> Optional[SignalResult]:
        if len(df) < 30 or not {"close", "volume"}.issubset(df.columns):
            return None

        rsi_val = float(_rsi(df).iloc[-1])
        price = float(df["close"].iloc[-1])
        vol_ratio = _vol_ratio(df)
        bb_high = float(_bb_upper(df).iloc[-1])

        rsi_ok = rsi_val > 68
        vol_ok = vol_ratio >= 2.0
        bb_ok = price >= bb_high * 0.98

        if not (rsi_ok and vol_ok and bb_ok):
            return None

        return SignalResult(
            ticker=ticker,
            signal_name="Overbought Confluence",
            time_horizon=self.time_horizon,
            strength="strong",
            direction="bearish",
            conditions=[
                f"RSI(14) = {rsi_val:.1f} (overbought > 68)",
                f"Volume {vol_ratio:.1f}× 20-day avg",
                f"Price at BB upper band (${price:.2f})",
            ],
            price=round(price, 2),
        )
