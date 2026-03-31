from __future__ import annotations
from io import StringIO
from pathlib import Path
import yaml
import pandas as pd
import requests


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_sp500_tickers() -> list[str]:
    """Fetch S&P 500 tickers from Wikipedia. Returns empty list on failure."""
    try:
        # Wikipedia blocks requests without a User-Agent header
        html = requests.get(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            headers={"User-Agent": "Mozilla/5.0 (trading-signal-engine)"},
            timeout=10,
        ).text
        tables = pd.read_html(StringIO(html), attrs={"id": "constituents"})
        tickers = tables[0]["Symbol"].tolist()
        # yfinance uses '-' not '.' for tickers like BRK.B → BRK-B
        return [t.replace(".", "-") for t in tickers]
    except Exception:
        return []


def load_universe(config: dict) -> dict[str, list[str]]:
    """
    Returns:
        {
            "stocks": [...],   # S&P 500 if config.universe.sp500 is true
            "etfs": [...],
            "crypto": [...],
            "watchlist": [...],
        }
    """
    u = config.get("universe", {})
    stocks = load_sp500_tickers() if u.get("sp500", False) else []
    etfs = u.get("etfs", [])
    crypto = u.get("crypto", [])
    watchlist = u.get("watchlist", [])
    return {"stocks": stocks, "etfs": etfs, "crypto": crypto, "watchlist": watchlist}


def get_tickers_for_mode(universe: dict[str, list[str]], mode: str) -> list[str]:
    """
    mode "intraday"  → stocks + etfs (crypto skipped: 15m data unreliable on yfinance free)
    mode "daily"     → stocks + etfs + crypto + watchlist
    mode "premarket" → watchlist + etfs + stocks (earnings check — smaller universe)
    """
    if mode == "intraday":
        return universe["stocks"] + universe["etfs"]
    elif mode == "daily":
        return universe["stocks"] + universe["etfs"] + universe["crypto"] + universe["watchlist"]
    elif mode == "premarket":
        return universe["watchlist"] + universe["etfs"] + universe["stocks"]
    return []
