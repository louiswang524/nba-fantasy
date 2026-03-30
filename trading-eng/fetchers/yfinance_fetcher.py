from __future__ import annotations
from datetime import datetime, timedelta
from pathlib import Path
import logging

import pandas as pd
import yfinance as yf
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


class YFinanceFetcher:
    """Fetch OHLCV data from yfinance with parquet caching."""

    def __init__(self, cache_ttl_minutes: dict = None):
        """
        Args:
            cache_ttl_minutes: {interval: ttl_minutes}
                e.g. {"15m": 15, "1d": 1440}
        """
        self.cache_ttl_minutes = cache_ttl_minutes or {
            "15m": 15,
            "1h": 60,
            "1d": 1440,
            "1wk": 1440,
        }

    def _get_cache_path(self, ticker: str, interval: str) -> Path:
        """Get cache file path for ticker/interval."""
        # Replace special characters in ticker for filename
        safe_ticker = ticker.replace("-", "_").replace("/", "_")
        filename = f"{safe_ticker}_{interval}.parquet"
        return CACHE_DIR / filename

    def _is_cache_valid(self, cache_path: Path, interval: str) -> bool:
        """Check if cache file exists and is fresh."""
        if not cache_path.exists():
            return False

        ttl_minutes = self.cache_ttl_minutes.get(interval, 1440)
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age_minutes = (datetime.now() - mtime).total_seconds() / 60
        return age_minutes < ttl_minutes

    def _load_cache(self, cache_path: Path) -> pd.DataFrame:
        """Load DataFrame from parquet cache."""
        try:
            return pd.read_parquet(cache_path)
        except Exception as e:
            logger.warning(f"Failed to load cache {cache_path}: {e}")
            return None

    def _save_cache(self, cache_path: Path, df: pd.DataFrame) -> None:
        """Save DataFrame to parquet cache."""
        try:
            df.to_parquet(cache_path)
        except Exception as e:
            logger.warning(f"Failed to save cache {cache_path}: {e}")

    def fetch(self, ticker: str, interval: str = "1d", **kwargs) -> pd.DataFrame:
        """
        Fetch OHLCV data for a single ticker.
        Uses parquet cache if available and fresh.

        Args:
            ticker: e.g. "AAPL", "BTC-USD"
            interval: e.g. "15m", "1h", "1d", "1wk"
            **kwargs: additional yfinance.download kwargs

        Returns:
            DataFrame with OHLCV data
        """
        cache_path = self._get_cache_path(ticker, interval)

        # Try cache
        if self._is_cache_valid(cache_path, interval):
            df = self._load_cache(cache_path)
            if df is not None and not df.empty:
                logger.debug(f"Loaded {ticker}/{interval} from cache")
                return df

        # Fetch from yfinance
        logger.debug(f"Fetching {ticker}/{interval} from yfinance")
        try:
            df = yf.download(ticker, interval=interval, progress=False, **kwargs)
            if df.empty:
                logger.warning(f"No data for {ticker}/{interval}")
                return pd.DataFrame()

            # Ensure consistent column names
            df.columns = [c.lower() for c in df.columns]
            self._save_cache(cache_path, df)
            return df
        except Exception as e:
            logger.error(f"Failed to fetch {ticker}/{interval}: {e}")
            return pd.DataFrame()

    def fetch_batch(
        self, tickers: list[str], interval: str = "1d", **kwargs
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch OHLCV data for multiple tickers.

        Args:
            tickers: list of ticker symbols
            interval: e.g. "15m", "1h", "1d", "1wk"
            **kwargs: additional yfinance.download kwargs

        Returns:
            {ticker: DataFrame} for successful fetches
        """
        data = {}
        for ticker in tickers:
            df = self.fetch(ticker, interval=interval, **kwargs)
            if not df.empty:
                data[ticker] = df
        return data
