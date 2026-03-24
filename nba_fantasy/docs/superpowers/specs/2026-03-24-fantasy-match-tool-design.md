# Fantasy Match Tool — Design Spec

**Date:** 2026-03-24
**Platform:** Yahoo Fantasy Basketball (Head-to-Head Categories)
**Interface:** Jupyter Notebooks + shared Python library

---

## Overview

A modular Python toolkit to help a Yahoo H2H categories fantasy basketball player win their weekly matchup. Covers four core use cases: weekly matchup strategy, daily start/sit decisions, waiver wire pickups, and trade analysis. Powered by Yahoo Fantasy API (roster/matchup/player status), NBA stats via `nba_api`, and Gemini AI recommendations.

---

## Architecture

```
nba_fantasy/
├── fantasy/                  # Python package (core logic)
│   ├── __init__.py
│   ├── auth.py               # Yahoo OAuth2 flow + token refresh
│   ├── yahoo_client.py       # Direct Yahoo Fantasy API wrapper (requests + yahoo_oauth)
│   ├── nba_stats.py          # NBA stats fetcher (nba_api)
│   ├── analysis.py           # Category projection, schedule scoring, trade value
│   └── llm.py                # Gemini API calls for AI recommendations
├── notebooks/
│   ├── 01_matchup_planner.ipynb
│   ├── 02_start_sit.ipynb
│   ├── 03_waiver_wire.ipynb
│   └── 04_trade_analyzer.ipynb
├── cache/                    # One JSON file per cache key (URL/query hash)
├── credentials.json          # Yahoo OAuth tokens (gitignored)
├── .env                      # API keys and league config (gitignored)
└── requirements.txt
```

**Data flow:**
1. `auth.py` handles Yahoo OAuth once, caches tokens in `credentials.json`; all subsequent runs auto-refresh
2. Each notebook imports `fantasy.*` — no re-auth, no repeated API calls (TTL cache)
3. Stats cache TTL: 1 hour. Yahoo roster/player cache TTL: 15 minutes
4. `llm.py` sends structured context to Gemini and returns plain-language recommendations

---

## Configuration

**Required `.env` variables:**
```
YAHOO_CLIENT_ID=...
YAHOO_CLIENT_SECRET=...
YAHOO_LEAGUE_KEY=...        # e.g. nba.l.12345 (found via auth discovery step)
YAHOO_TEAM_KEY=...          # e.g. nba.l.12345.t.3 (your team within the league)
GEMINI_API_KEY=...
```

Both `credentials.json` and `.env` are gitignored.

**League/team discovery:** On first run, `auth.py` prints all leagues and teams for the authenticated user so you can copy the correct keys into `.env`.

---

## Yahoo API Approach

`yahoo_fantasy_api` (community library) is **not used** due to known reliability issues (broken auth, slow free-agent queries, lagging Yahoo API compatibility). Instead:

- `yahoo_oauth` handles OAuth token management only
- `yahoo_client.py` makes direct `requests` calls to `https://fantasysports.yahooapis.com/fantasy/v2/`
- All responses parsed from Yahoo's XML/JSON format manually
- Player injury status (INJ/GTD/OUT/Q/D flags) is read directly from Yahoo's player objects — no external news feed needed

---

## Features

### `01_matchup_planner.ipynb` — Weekly Strategy
- Pulls your roster + current opponent's roster from Yahoo API
- Projects per-category totals for both teams over remaining matchup days
- Classifies each category: likely win / toss-up / likely loss
- Recommends categories to target, categories to punt, and streaming pickups for toss-up categories
- Gemini prompt input: structured dict of your category projections vs. opponent's, categories by status
- Gemini output: weekly game plan narrative with specific actions

### `02_start_sit.ipynb` — Daily Lineup
- Fetches your active roster with Yahoo injury flags (INJ/GTD/OUT/Q/D)
- Shows games remaining this week per player
- Ranks by projected category contribution (see Projection Model)
- Gemini prompt input: ranked player list with projected stats and injury flags
- Gemini output: daily lineup card with start/sit decisions and brief reasoning

### `03_waiver_wire.ipynb` — Pickup Recommendations
- Fetches top available free agents from Yahoo (direct API, paginated)
- Scores each against your team's weakest categories
- Boosts players with more games remaining this week
- Gemini prompt input: top 20 scored free agents with category fit analysis
- Gemini output: top 5 pickup recommendations with reasoning

### `04_trade_analyzer.ipynb` — Trade Evaluation
- Input: hardcoded cell at top of notebook — `GIVE = ["Player A", "Player B"]`, `RECEIVE = ["Player C"]`
- Computes per-category delta for your team (projected totals before vs. after trade)
- Considers your current weekly matchup context (categories you need)
- Gemini prompt input: before/after category comparison table + matchup context
- Gemini output: accept / decline / counter-propose verdict with reasoning

---

## Projection Model

All projections use a **per-game rate × games remaining** model:

1. **Stat window:** Blend of last-15-day per-game averages (70% weight) and season per-game averages (30% weight). Captures recent form while dampening small-sample noise.
2. **Games remaining:** Derived from `nba_api` schedule data (filtered to dates within the Yahoo scoring week). The Yahoo scoring week start/end dates are fetched from `yahoo_client.py`. `nba_stats.py` owns the schedule lookup; `yahoo_client.py` owns the week boundaries.
3. **Injury adjustment:** Players with Yahoo status `OUT` or `INJ` are projected at 0. Players with `GTD` or `Q` are projected at 50% of their rate. Active players are projected at 100%.
4. **Category totals:** Per-game rate × adjusted games remaining, summed across all rostered starters.

---

## Caching Strategy

- **Format:** One JSON file per cache key in `cache/`, named by MD5 hash of the request parameters
- **Structure per file:** `{"data": <response>, "cached_at": <unix timestamp>}`
- **TTL check:** On read, compare `cached_at` to current time; re-fetch if expired
- **TTLs:** Yahoo API calls: 15 minutes. `nba_api` calls: 1 hour
- **Multi-kernel safety:** Cache files are read/written atomically (write to temp file, rename). Simultaneous notebook runs are safe.
- **Reset:** Delete `cache/` directory to force full re-fetch

---

## Rate Limiting

- **Yahoo API:** Rate limit mitigated by the cache. Notebooks make at most a handful of uncached calls per session.
- **`nba_api`:** Use `timeout=30` on all calls. Add `time.sleep(0.6)` between sequential player stat calls to avoid HTTP 429s.
- **Gemini API:** Each notebook makes exactly one Gemini call per run; no rate concerns.

---

## Error Handling

Notebooks use `raise` with descriptive messages on failure:
- Yahoo token refresh failure → `RuntimeError("Yahoo token refresh failed — re-run auth.py")`
- Missing player stats → skip player, log warning via `print()`
- Gemini malformed response → print raw response and `raise ValueError`

No silent failures. Errors surface immediately in the notebook cell output.

---

## Dependencies (pinned versions)

```
yahoo_oauth==1.3.1
nba_api==1.4.1
google-genai>=1.0.0          # Gemini 2.x SDK; use model="gemini-2.0-flash"
requests==2.31.0
pandas==2.1.4
matplotlib==3.8.2
python-dotenv==1.0.0
jupyter==1.0.0
```

---

## Out of Scope

- No web UI or deployment
- No multi-user support
- No automated lineup submission to Yahoo (read-only recommendations)
- No external injury news feeds (Yahoo player status flags are sufficient)
