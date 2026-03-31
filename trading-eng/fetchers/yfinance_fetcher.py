from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# Max tickers per yfinance batch request (empirically safe limit)
_BATCH_SIZE = 100


class YFinanceFetcher:
    """Fetch OHLCV data from yfinance with parquet caching."""

    def __init__(self, cache_ttl_minutes: dict = None):
        self.cache_ttl_minutes = cache_ttl_minutes or {
            "15m": 15,
            "1h": 60,
            "1d": 1440,
            "1wk": 1440,
        }
        # Default lookback periods per interval.
        # 1d needs ≥200 bars for the 200-day MA regime gate (~10 months of trading days).
        # 1wk needs 2y for position signals. 15m capped at 60d by yfinance free tier.
        self.default_periods = {
            "15m": "60d",
            "1h": "60d",
            "1d": "1y",
            "1wk": "2y",
        }

    def _get_cache_path(self, ticker: str, interval: str) -> Path:
        safe_ticker = ticker.replace("-", "_").replace("/", "_")
        return CACHE_DIR / f"{safe_ticker}_{interval}.parquet"

    def _is_cache_valid(self, cache_path: Path, interval: str) -> bool:
        if not cache_path.exists():
            return False
        ttl_minutes = self.cache_ttl_minutes.get(interval, 1440)
        age_minutes = (datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)).total_seconds() / 60
        return age_minutes < ttl_minutes

    def _load_cache(self, cache_path: Path) -> pd.DataFrame | None:
        try:
            return pd.read_parquet(cache_path)
        except Exception as e:
            logger.warning(f"Failed to load cache {cache_path}: {e}")
            return None

    def _save_cache(self, cache_path: Path, df: pd.DataFrame) -> None:
        try:
            df.to_parquet(cache_path)
        except Exception as e:
            logger.warning(f"Failed to save cache {cache_path}: {e}")

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Flatten MultiIndex columns and lowercase."""
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        return df

    def fetch(self, ticker: str, interval: str = "1d", **kwargs) -> pd.DataFrame:
        """Fetch OHLCV for a single ticker with cache."""
        cache_path = self._get_cache_path(ticker, interval)
        if self._is_cache_valid(cache_path, interval):
            df = self._load_cache(cache_path)
            if df is not None and not df.empty:
                logger.debug(f"Cache hit: {ticker}/{interval}")
                return df

        kwargs.setdefault("period", self.default_periods.get(interval, "1y"))
        logger.debug(f"Fetching {ticker}/{interval} from yfinance")
        try:
            df = yf.download(ticker, interval=interval, progress=False, **kwargs)
            if df.empty:
                logger.warning(f"No data for {ticker}/{interval}")
                return pd.DataFrame()
            df = self._normalize_columns(df)
            self._save_cache(cache_path, df)
            return df
        except Exception as e:
            logger.error(f"Failed to fetch {ticker}/{interval}: {e}")
            return pd.DataFrame()

    def fetch_batch(
        self, tickers: list[str], interval: str = "1d", **kwargs
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch OHLCV for multiple tickers efficiently.

        Strategy:
        1. Return cached data immediately for tickers with valid cache.
        2. Batch-download stale tickers via yfinance (one request per 100 tickers).
        3. Each batch download runs in a thread to overlap I/O.
        """
        result: dict[str, pd.DataFrame] = {}
        stale: list[str] = []

        # Step 1: cache-first pass
        for ticker in tickers:
            cache_path = self._get_cache_path(ticker, interval)
            if self._is_cache_valid(cache_path, interval):
                df = self._load_cache(cache_path)
                if df is not None and not df.empty:
                    result[ticker] = df
                    continue
            stale.append(ticker)

        if not stale:
            logger.info(f"All {len(tickers)} tickers served from cache")
            return result

        logger.info(f"Cache hit: {len(result)}, fetching {len(stale)} stale tickers in batches of {_BATCH_SIZE}")

        # Step 2: split stale tickers into chunks
        chunks = [stale[i : i + _BATCH_SIZE] for i in range(0, len(stale), _BATCH_SIZE)]

        # Step 3: fetch chunks in parallel threads
        with ThreadPoolExecutor(max_workers=min(len(chunks), 8)) as pool:
            futures = {pool.submit(self._fetch_chunk, chunk, interval, kwargs): chunk for chunk in chunks}
            for future in as_completed(futures):
                chunk_result = future.result()
                result.update(chunk_result)

        return result

    def _fetch_chunk(self, tickers: list[str], interval: str, kwargs: dict) -> dict[str, pd.DataFrame]:
        """Download a batch of tickers in one yfinance call and split by ticker."""
        kwargs = {**kwargs}
        kwargs.setdefault("period", self.default_periods.get(interval, "1y"))
        chunk_result: dict[str, pd.DataFrame] = {}
        try:
            raw = yf.download(
                tickers,
                interval=interval,
                progress=False,
                group_by="ticker",
                auto_adjust=True,
                **kwargs,
            )
            if raw.empty:
                return chunk_result

            if len(tickers) == 1:
                # yfinance returns a flat DataFrame for a single ticker
                df = self._normalize_columns(raw.copy())
                df = df.dropna(how="all")
                if not df.empty:
                    ticker = tickers[0]
                    self._save_cache(self._get_cache_path(ticker, interval), df)
                    chunk_result[ticker] = df
            else:
                # MultiIndex: (ticker, price_field) — top level is ticker
                for ticker in tickers:
                    try:
                        if ticker not in raw.columns.get_level_values(0):
                            continue
                        df = raw.xs(ticker, axis=1, level=0).copy()
                        df = self._normalize_columns(df)
                        df = df.dropna(how="all")
                        if not df.empty:
                            self._save_cache(self._get_cache_path(ticker, interval), df)
                            chunk_result[ticker] = df
                    except Exception as e:
                        logger.warning(f"Failed to extract {ticker} from batch: {e}")
        except Exception as e:
            logger.error(f"Batch fetch failed for chunk of {len(tickers)}: {e}")
            # Fall back to individual fetches for this chunk
            for ticker in tickers:
                df = self.fetch(ticker, interval=interval, **kwargs)
                if not df.empty:
                    chunk_result[ticker] = df

        return chunk_result
