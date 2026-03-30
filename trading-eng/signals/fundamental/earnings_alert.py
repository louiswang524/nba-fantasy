from __future__ import annotations
from typing import Optional
import os
import pandas as pd

from signals.base import BaseSignal, SignalResult
from signals.registry import register_signal
from fetchers.alphavantage_fetcher import get_upcoming_earnings


@register_signal
class EarningsAlertSignal(BaseSignal):
    """
    Fires a WATCH alert when a ticker has earnings within 3 calendar days.
    Requires ALPHA_VANTAGE_KEY in environment.
    Silently skips if API key is absent (don't block other signals).
    """
    time_horizon = "position"
    asset_classes = ("stock",)

    def __init__(self) -> None:
        self._upcoming: dict[str, str] | None = None

    def _load_upcoming(self) -> dict[str, str]:
        if self._upcoming is None:
            api_key = os.getenv("ALPHA_VANTAGE_KEY", "")
            if not api_key:
                self._upcoming = {}
            else:
                try:
                    self._upcoming = get_upcoming_earnings(api_key, days_ahead=3)
                except Exception:
                    self._upcoming = {}
        return self._upcoming

    def check(self, ticker: str, df: pd.DataFrame) -> Optional[SignalResult]:
        if "close" not in df.columns or df.empty:
            return None

        upcoming = self._load_upcoming()
        if ticker not in upcoming:
            return None

        price = float(df["close"].iloc[-1])
        report_date = upcoming[ticker]

        return SignalResult(
            ticker=ticker,
            signal_name="Pre-Earnings Alert",
            time_horizon=self.time_horizon,
            strength="moderate",
            direction="neutral",
            conditions=[
                f"Earnings report on {report_date}",
                f"Within 3 calendar days",
            ],
            price=round(price, 2),
        )
