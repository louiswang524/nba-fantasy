from __future__ import annotations
from typing import Optional
import pandas as pd
from ta.trend import MACD

from signals.base import BaseSignal, SignalResult
from signals.registry import register_signal


def _vwap(df: pd.DataFrame) -> float:
    """Session VWAP: cumulative (close × volume) / cumulative volume."""
    cum_vol = df["volume"].cumsum()
    cum_tp_vol = (df["close"] * df["volume"]).cumsum()
    return float(cum_tp_vol.iloc[-1] / cum_vol.iloc[-1]) if cum_vol.iloc[-1] > 0 else 0.0


def _vol_ratio(df: pd.DataFrame) -> float:
    avg = df["volume"].rolling(20).mean().iloc[-1]
    return float(df["volume"].iloc[-1] / avg) if avg > 0 else 0.0


@register_signal
class IntradayMomentumSignal(BaseSignal):
    time_horizon = "intraday"
    asset_classes = ("stock", "etf")

    def check(self, ticker: str, df: pd.DataFrame) -> Optional[SignalResult]:
        if len(df) < 35 or not {"close", "volume"}.issubset(df.columns):
            return None

        macd_ind = MACD(close=df["close"])
        macd_line = macd_ind.macd()
        signal_line = macd_ind.macd_signal()

        macd_cross_bullish = (
            macd_line.iloc[-1] > signal_line.iloc[-1]
            and macd_line.iloc[-2] <= signal_line.iloc[-2]
        )
        macd_cross_bearish = (
            macd_line.iloc[-1] < signal_line.iloc[-1]
            and macd_line.iloc[-2] >= signal_line.iloc[-2]
        )

        if not (macd_cross_bullish or macd_cross_bearish):
            return None

        vol_ratio = _vol_ratio(df)
        if vol_ratio < 2.0:
            return None

        price = float(df["close"].iloc[-1])
        vwap = _vwap(df)

        if macd_cross_bullish and price <= vwap:
            return None
        if macd_cross_bearish and price >= vwap:
            return None

        direction = "bullish" if macd_cross_bullish else "bearish"
        vwap_label = "above" if macd_cross_bullish else "below"

        return SignalResult(
            ticker=ticker,
            signal_name="Intraday Momentum",
            time_horizon=self.time_horizon,
            strength="strong",
            direction=direction,
            conditions=[
                f"MACD {direction} crossover",
                f"Volume {vol_ratio:.1f}× 20-bar avg",
                f"Price ${price:.2f} {vwap_label} VWAP ${vwap:.2f}",
            ],
            price=round(price, 2),
        )
