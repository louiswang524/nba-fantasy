from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd


@dataclass
class SignalResult:
    """Represents a triggered signal with all metadata for alert dispatch."""
    ticker: str
    signal_name: str
    time_horizon: str  # "intraday" | "swing" | "position"
    strength: str  # "strong" | "moderate"
    direction: str  # "bullish" | "bearish" | "neutral"
    conditions: list[str]  # list of condition strings that were met
    price: float  # current price at detection time
    confidence_score: float = 0.0  # 0–100, higher = more conviction
    # ATR-based trade levels (None for neutral/watch signals)
    entry_low: Optional[float] = None
    entry_high: Optional[float] = None
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    stop_pct: Optional[float] = None   # stop distance as % of price
    target_pct: Optional[float] = None  # target distance as % of price


class BaseSignal:
    """Base class for all signals. Subclasses must implement check()."""
    time_horizon: str  # override in subclass
    asset_classes: tuple[str, ...] = ()  # override in subclass
    required_interval: str = "1d"  # data interval this signal expects — screener filters by this

    def check(self, ticker: str, df: pd.DataFrame) -> Optional[SignalResult]:
        """
        Check if the signal fires for the given ticker and OHLCV data.

        Args:
            ticker: ticker symbol
            df: OHLCV DataFrame with columns [open, high, low, close, volume]

        Returns:
            SignalResult if signal fires, None otherwise
        """
        raise NotImplementedError(f"{self.__class__.__name__}.check() must be implemented")
