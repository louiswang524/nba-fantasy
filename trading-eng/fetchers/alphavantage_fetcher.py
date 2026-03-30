from __future__ import annotations
from datetime import datetime, timedelta
from pathlib import Path
import json
import requests


CACHE_PATH = Path("cache/earnings_calendar.json")
CACHE_TTL = timedelta(hours=24)


def fetch_earnings_calendar(api_key: str) -> list[dict]:
    """
    Fetch 3-month earnings calendar from Alpha Vantage.
    Returns list of dicts: {symbol, reportDate, fiscalDateEnding, estimate, currency}.
    Cached for 24 hours to stay within 50 req/day free tier limit.
    """
    if CACHE_PATH.exists():
        mtime = datetime.fromtimestamp(CACHE_PATH.stat().st_mtime)
        if datetime.now() - mtime < CACHE_TTL:
            with open(CACHE_PATH) as f:
                return json.load(f)

    url = (
        f"https://www.alphavantage.co/query"
        f"?function=EARNINGS_CALENDAR&horizon=3month&apikey={api_key}"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    # Response is CSV
    lines = response.text.strip().split("\n")
    if len(lines) < 2:
        return []

    headers = [h.strip() for h in lines[0].split(",")]
    rows = []
    for line in lines[1:]:
        values = [v.strip() for v in line.split(",")]
        if len(values) == len(headers):
            rows.append(dict(zip(headers, values)))

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(rows, f)

    return rows


def get_upcoming_earnings(api_key: str, days_ahead: int = 3) -> dict[str, str]:
    """
    Returns {ticker: reportDate} for companies reporting within `days_ahead` days.
    """
    rows = fetch_earnings_calendar(api_key)
    today = datetime.now().date()
    cutoff = today + timedelta(days=days_ahead)

    upcoming: dict[str, str] = {}
    for row in rows:
        try:
            report_date = datetime.strptime(row["reportDate"], "%Y-%m-%d").date()
            if today <= report_date <= cutoff:
                upcoming[row["symbol"]] = row["reportDate"]
        except (KeyError, ValueError):
            continue
    return upcoming
