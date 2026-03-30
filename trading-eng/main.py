#!/usr/bin/env python3
"""
Trading Signal Alert Engine — Entry Point

Usage:
    python main.py --mode intraday    # 15-min scan, market hours
    python main.py --mode daily       # daily swing/position scan
    python main.py --mode premarket   # 8am earnings/event scan
"""
from __future__ import annotations
import argparse
import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("trading_engine.log"),
    ],
)
logger = logging.getLogger("main")

# Import signals package to trigger all @register_signal decorators
import signals  # noqa: F401, E402

from universe import load_config, load_universe, get_tickers_for_mode
from fetchers.yfinance_fetcher import YFinanceFetcher
from signals.technical.regime_gate import MarketRegimeGate, RegimeStatus
from screener import Screener
from alerts.telegram import create_dispatcher


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trading Signal Alert Engine")
    parser.add_argument(
        "--mode",
        choices=["intraday", "daily", "premarket"],
        required=True,
        help="Scan mode",
    )
    return parser.parse_args()


def get_interval_for_mode(mode: str) -> str:
    return {"intraday": "15m", "daily": "1d", "premarket": "1d"}[mode]


async def run(mode: str) -> None:
    logger.info(f"Starting scan: mode={mode}")

    config = load_config()
    universe = load_universe(config)
    tickers = get_tickers_for_mode(universe, mode)
    logger.info(f"Universe: {len(tickers)} tickers")

    interval = get_interval_for_mode(mode)
    fetcher = YFinanceFetcher()

    # Fetch market data
    logger.info(f"Fetching OHLCV data (interval={interval})")
    data = fetcher.fetch_batch(tickers, interval=interval)
    logger.info(f"Fetched data for {len(data)} tickers")

    # Detect market regime using SPY daily data
    spy_df = fetcher.fetch("SPY", interval="1d")
    gate = MarketRegimeGate()
    regime = gate.detect(spy_df)
    logger.info(f"Market regime: {regime.value}")

    # Run screener
    screener = Screener()
    results = screener.run(data, regime=regime)
    logger.info(f"Signals fired: {len(results)}")

    # Dispatch alerts
    dispatcher = create_dispatcher()
    sent = await dispatcher.dispatch(results, regime=regime, total_scanned=len(data))
    logger.info(f"Alerts sent: {sent}")


def main() -> None:
    args = parse_args()
    asyncio.run(run(args.mode))


if __name__ == "__main__":
    main()
