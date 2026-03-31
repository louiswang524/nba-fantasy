from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
import logging
import pandas as pd

from signals.base import SignalResult
from signals.registry import get_signals
from signals.technical.regime_gate import RegimeStatus

logger = logging.getLogger(__name__)

# Evaluate this many tickers in parallel
_SCREENER_WORKERS = 16


class Screener:
    def run(
        self,
        data: dict[str, pd.DataFrame],
        regime: Optional[RegimeStatus],
    ) -> list[SignalResult]:
        """
        Evaluate all registered signals across all tickers in parallel.

        Args:
            data: {ticker → OHLCV DataFrame}
            regime: detected market regime

        Returns:
            list of SignalResult for all triggered (non-suppressed) signals
        """
        signals = get_signals()
        eligible = {t: df for t, df in data.items() if not df.empty and len(df) >= 5}

        results: list[SignalResult] = []
        with ThreadPoolExecutor(max_workers=_SCREENER_WORKERS) as pool:
            futures = {
                pool.submit(_evaluate_ticker, ticker, df, signals, regime): ticker
                for ticker, df in eligible.items()
            }
            for future in as_completed(futures):
                ticker_results = future.result()
                results.extend(ticker_results)

        return results


def _evaluate_ticker(
    ticker: str,
    df: pd.DataFrame,
    signals: list,
    regime: Optional[RegimeStatus],
) -> list[SignalResult]:
    """Evaluate all signals for a single ticker. Designed to run in a thread."""
    results = []
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
