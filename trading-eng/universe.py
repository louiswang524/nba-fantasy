from __future__ import annotations
from pathlib import Path
from typing import Optional
import yaml


def load_config() -> dict:
    """Load configuration from config.yaml."""
    config_path = Path("config.yaml")
    if not config_path.exists():
        raise FileNotFoundError("config.yaml not found")

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def load_universe(config: dict) -> dict[str, list[str]]:
    """
    Load ticker universe from config.
    Returns: {mode: [tickers]} where mode in [intraday, daily, premarket]
    """
    universe_config = config.get("universe", {})

    # Gather all tickers
    tickers = set()

    # S&P 500 index
    if universe_config.get("sp500"):
        # In production, you'd load the S&P 500 list from a file or API
        # For now, we'll use a placeholder that can be extended
        tickers.update(["SPY"])

    # ETFs
    etfs = universe_config.get("etfs", [])
    tickers.update(etfs)

    # Crypto
    crypto = universe_config.get("crypto", [])
    tickers.update(crypto)

    # Watchlist
    watchlist = universe_config.get("watchlist", [])
    tickers.update(watchlist)

    # Map modes to the same universe for now
    # In production, you might have mode-specific universes
    return {
        "intraday": sorted(list(tickers)),
        "daily": sorted(list(tickers)),
        "premarket": sorted(list(tickers)),
    }


def get_tickers_for_mode(universe: dict[str, list[str]], mode: str) -> list[str]:
    """Get tickers for a specific scan mode."""
    if mode not in universe:
        raise ValueError(f"Unknown mode: {mode}")
    return universe[mode]
