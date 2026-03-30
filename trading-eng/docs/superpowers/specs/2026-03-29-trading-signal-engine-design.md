# Trading Signal Alert Engine — Design Spec
**Date:** 2026-03-29
**Status:** Approved

---

## Overview

A locally-scheduled Python engine that scans the US market (S&P 500 stocks, ETFs, crypto) for high-conviction trading signals across multiple time horizons and delivers real-time alerts via Telegram. The differentiating design principle is **confluence-first signals**: alerts only fire when multiple independent conditions align simultaneously, dramatically reducing noise versus single-indicator screeners.

---

## Architecture

```
cron (every 15 min during market hours)
        │
        ▼
┌─────────────────────────────────────────────┐
│                  main.py                    │
│  orchestrates the pipeline each run         │
└────────────┬────────────────────────────────┘
             │
     ┌───────▼────────┐
     │  Data Layer    │  fetchers/
     │  yfinance      │  ├── yfinance_fetcher.py
     │  + crypto      │  └── crypto_fetcher.py
     └───────┬────────┘
             │  OHLCV + price DataFrames (cached to parquet)
     ┌───────▼────────┐
     │  Screener      │  screener.py
     │  runs all      │  iterates universe × registered signals
     │  registered    │
     │  signals       │
     └───────┬────────┘
             │  List[SignalResult]
     ┌───────▼────────┐
     │  Signal        │  signals/
     │  Registry      │  ├── technical/
     │                │  ├── fundamental/
     │                │  └── quant/
     └───────┬────────┘
             │  triggered signals (deduplicated)
     ┌───────▼────────┐
     │  Alert         │  alerts/
     │  Dispatcher    │  └── telegram.py
     └────────────────┘
```

---

## Data Layer

### Sources
- **Stocks + ETFs:** `yfinance` — OHLCV across multiple timeframes (15m, 1d, 1wk). No API key required.
- **Crypto:** `yfinance` crypto pairs (BTC-USD, ETH-USD, SOL-USD, etc.) — same fetcher, different ticker format.
- **Fundamental / events:** Alpha Vantage free tier — earnings calendar, economic indicators (50 req/day limit).

### Universe Configuration (`config.yaml`)
```yaml
universe:
  sp500: true          # auto-loads S&P 500 tickers from Wikipedia via pandas
  etfs: ["SPY", "QQQ", "IWM", "GLD", "TLT"]
  crypto: ["BTC-USD", "ETH-USD", "SOL-USD"]
  watchlist: []        # optional extra tickers

timeframes:
  intraday: "15m"      # last 5 days of 15-min bars
  swing: "1d"          # last 90 days of daily bars
  position: "1wk"      # last 2 years of weekly bars
```

### Caching
Each run caches fetched DataFrames to `cache/` as parquet files with a TTL. Signals reuse cached data within a run to avoid redundant API calls and reduce rate-limit exposure.

---

## Signal Interface

Every signal implements `BaseSignal` and self-registers via `@register_signal`:

```python
@register_signal
class RSIConfluenceSignal(BaseSignal):
    time_horizon = "swing"           # "intraday" | "swing" | "position"
    asset_classes = ["stock", "etf"] # ["stock", "etf", "crypto"]

    def check(self, ticker: str, df: pd.DataFrame) -> SignalResult | None:
        ...  # return SignalResult if triggered, None otherwise
```

`SignalResult` fields:
- `ticker` — ticker symbol
- `signal_name` — human-readable name
- `time_horizon` — intraday / swing / position
- `strength` — `"strong"` | `"moderate"`
- `direction` — `"bullish"` | `"bearish"` | `"neutral"`
- `conditions` — list of condition strings that were met (for Telegram formatting)
- `price` — current price at detection time

Adding a new signal requires only: create a file in `signals/<category>/`, implement `check()`, decorate with `@register_signal`. No changes to core pipeline.

---

## Built-in Signals (Phase 1)

All signals are confluence-based — multiple independent conditions must align.

| Signal | Conditions Required | Horizon | Direction |
|---|---|---|---|
| Oversold Confluence | RSI < 32 + volume spike (>2×) + BB lower band touch | swing | bullish |
| Overbought Confluence | RSI > 68 + volume spike (>2×) + BB upper band touch | swing | bearish |
| Bullish Breakout | MA golden cross + volume > 2× avg + price > 52w high | position | bullish |
| Bearish Breakdown | MA death cross + volume spike + price < 52w low | position | bearish |
| Intraday Momentum | MACD cross + volume spike + price > VWAP | intraday | bullish/bearish |
| Mean Reversion Setup | Z-score > 2σ + RSI extreme + low volatility regime | swing | contrarian |
| Pre-Earnings Alert | Earnings in ≤3 days + IV rank elevated | position | watch |
| Market Regime Gate | SPY trend filter — gates all swing/position signals | meta | meta |

### Market Regime Gate
The regime gate runs before all swing and position signals. If SPY is in a downtrend (price < 200-day MA), bullish swing/position signals are suppressed. This context-awareness is the primary differentiator from standard retail screeners.

---

## Alert Dispatcher

### Telegram Message Format
```
🚨 STRONG BULLISH | AAPL | Swing

📊 Signal: Oversold Confluence
⏱ Horizon: Swing (1–5 days)
💰 Price: $187.42
📈 Conditions met:
  ✅ RSI(14) = 28.4 (oversold)
  ✅ Volume 3.2× 20-day avg
  ✅ Price at BB lower band

🌍 Market Regime: SPY UPTREND ✅
🕐 Detected: 2026-03-29 10:15 ET
```

### Deduplication
`state/fired_signals.json` tracks `(ticker, signal_name, date)` tuples. The same signal will not re-fire for the same ticker on the same calendar day. Prevents spam during choppy markets.

### Alert Grouping
Signals from the same run are batched per ticker. A summary message is sent at the end of each run:
```
📋 Scan complete: 503 tickers scanned | 7 signals fired | 10:15 ET
```

### Configuration
Telegram bot token and chat ID stored in `.env` — never hardcoded. Uses `python-telegram-bot` async library.

---

## Scheduling (cron)

```cron
# Intraday scan — every 15 min, 9:30am–4:00pm ET, Mon–Fri
*/15 9-15 * * 1-5 cd /path/to/trading-eng && python main.py --mode intraday

# Swing/Position scan — once daily at market open, Mon–Fri
30 9 * * 1-5 cd /path/to/trading-eng && python main.py --mode daily

# Pre-market scan — 8:00am ET for earnings/events
0 8 * * 1-5 cd /path/to/trading-eng && python main.py --mode premarket
```

---

## Project Structure

```
trading-eng/
├── main.py                  # entry point, orchestrates pipeline
├── config.yaml              # universe, timeframes, signal params
├── .env                     # TELEGRAM_TOKEN, CHAT_ID, ALPHA_VANTAGE_KEY
├── screener.py              # iterates universe × registered signals
├── fetchers/
│   ├── base.py
│   ├── yfinance_fetcher.py
│   └── crypto_fetcher.py
├── signals/
│   ├── base.py              # BaseSignal, SignalResult, @register_signal
│   ├── registry.py
│   ├── technical/
│   │   ├── rsi_confluence.py
│   │   ├── breakout_confluence.py
│   │   └── intraday_momentum.py
│   ├── quant/
│   │   └── mean_reversion.py
│   └── fundamental/
│       └── earnings_alert.py
├── alerts/
│   └── telegram.py
├── state/
│   └── fired_signals.json   # deduplication state
├── cache/                   # parquet cache, auto-managed TTL
└── tests/
    ├── test_signals.py
    └── test_fetchers.py
```

---

## Key Dependencies

```
yfinance
pandas
numpy
ta                   # technical analysis indicators
python-telegram-bot
python-dotenv
requests             # Alpha Vantage API
pyarrow              # parquet cache
pytest
```

---

## What Could Break / Test Coverage

| Risk | Mitigation |
|---|---|
| yfinance rate limits on 500+ tickers | Batched fetches + parquet cache with TTL |
| Stale cache serving wrong signals | TTL enforced per timeframe (15m cache for intraday, 1d for daily) |
| Telegram bot silent failures | Log all dispatch attempts; alert on repeated failure |
| Signal fires on bad/missing data | Each signal validates df length and required columns before computing |
| Dedup state file corruption | Write atomically; fall back to empty state on parse error |
| Alpha Vantage 50 req/day limit | Earnings calls cached for 24h; premarket scan only |
