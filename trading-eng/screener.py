from __future__ import annotations
from typing import Optional
import logging
import pandas as pd

from signals.base import SignalResult
from signals.registry import get_signals
from signals.technical.regime_gate import RegimeStatus

logger = logging.getLogger(__name__)


class Screener:
    def run(
        self,
        data: dict[str, pd.DataFrame],
        regime: Optional[RegimeStatus],
    ) -> list[SignalResult]:
        """
        Iterate all (ticker, signal) pairs.
        Suppresses bullish swing/position signals during DOWNTREND regime.
        Suppresses bearish swing/position signals during UPTREND regime.

        Args:
            data: {ticker → OHLCV DataFrame}
            regime: detected market regime (RegimeStatus or None)

        Returns:
            list of SignalResult for all triggered signals
        """
        results: list[SignalResult] = []
        signals = get_signals()

        for ticker, df in data.items():
            if df.empty or len(df) < 5:
                continue
            for signal in signals:
                try:
                    result = signal.check(ticker, df)
                except Exception as e:
                    logger.warning(f"Signal {signal.__class__.__name__} failed on {ticker}: {e}")
                    continue

                if result is None:
                    continue

                if _is_suppressed(result, regime):
                    logger.debug(f"Suppressed {result.signal_name} for {ticker} (regime={regime})")
                    continue

                results.append(result)

        return results


def _is_suppressed(result: SignalResult, regime: Optional[RegimeStatus]) -> bool:
    """Suppress swing/position signals that conflict with market regime."""
    if regime is None or result.time_horizon == "intraday":
        return False
    if regime == RegimeStatus.DOWNTREND and result.direction == "bullish":
        return True
    if regime == RegimeStatus.UPTREND and result.direction == "bearish":
        return True
    return False
