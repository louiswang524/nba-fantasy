# Fantasy Match Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modular Jupyter notebook suite backed by a Python library that helps a Yahoo H2H categories fantasy basketball player win weekly matchups.

**Architecture:** A `fantasy/` Python package handles all data fetching and computation; four thin notebooks import from it. External API calls (Yahoo, nba_api, Gemini) are all cached to disk with per-source TTLs. Analysis is pure Python/pandas; AI recommendations come from a single Gemini call per notebook run.

**Tech Stack:** Python 3.11+, yahoo_oauth, requests, nba_api, google-genai, pandas, pytest, jupyter

---

## File Map

| File | Responsibility |
|------|---------------|
| `requirements.txt` | Pinned dependencies |
| `.gitignore` | Exclude credentials, cache, .env |
| `fantasy/__init__.py` | Package marker |
| `fantasy/cache.py` | Disk cache: atomic read/write with TTL |
| `fantasy/auth.py` | Yahoo OAuth2 flow + token refresh + league discovery |
| `fantasy/yahoo_client.py` | Direct requests to Yahoo Fantasy API v2 (JSON) |
| `fantasy/nba_stats.py` | nba_api wrappers: player stats + schedule |
| `fantasy/analysis.py` | Projection model, category scoring, trade delta |
| `fantasy/llm.py` | Gemini API: send structured context, return text |
| `tests/test_cache.py` | Cache TTL, atomic write, key hashing |
| `tests/test_analysis.py` | Projection model math, category classification |
| `tests/test_llm.py` | Gemini prompt assembly, response parsing |
| `notebooks/01_matchup_planner.ipynb` | Weekly strategy notebook |
| `notebooks/02_start_sit.ipynb` | Daily lineup notebook |
| `notebooks/03_waiver_wire.ipynb` | Waiver wire notebook |
| `notebooks/04_trade_analyzer.ipynb` | Trade analysis notebook |

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `fantasy/__init__.py`
- Create: `tests/__init__.py`
- Create: `cache/.gitkeep`
- Create: `notebooks/` (directory)

- [ ] **Step 1: Create requirements.txt**

```
yahoo_oauth==1.3.1
nba_api==1.4.1
google-genai>=1.0.0
requests==2.31.0
pandas==2.1.4
matplotlib==3.8.2
python-dotenv==1.0.0
jupyter==1.0.0
pytest==7.4.3
pytest-mock==3.12.0
```

- [ ] **Step 2: Create .gitignore**

```
credentials.json
.env
cache/
__pycache__/
*.pyc
.ipynb_checkpoints/
```

- [ ] **Step 3: Create .env.example**

```
YAHOO_CLIENT_ID=your_client_id_here
YAHOO_CLIENT_SECRET=your_client_secret_here
YAHOO_LEAGUE_KEY=nba.l.XXXXX
YAHOO_TEAM_KEY=nba.l.XXXXX.t.X
GEMINI_API_KEY=your_gemini_api_key_here
```

- [ ] **Step 4: Create empty package markers**

```bash
mkdir -p fantasy tests notebooks cache
touch fantasy/__init__.py tests/__init__.py cache/.gitkeep
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without errors.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .gitignore .env.example fantasy/__init__.py tests/__init__.py cache/.gitkeep
git commit -m "feat: scaffold project structure"
```

---

## Task 2: Cache Module

**Files:**
- Create: `fantasy/cache.py`
- Create: `tests/test_cache.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_cache.py
import json
import time
import pytest
from pathlib import Path
from fantasy.cache import cached_call

def test_cache_stores_and_retrieves(tmp_path, monkeypatch):
    monkeypatch.setenv("CACHE_DIR", str(tmp_path))
    call_count = 0
    def fetch():
        nonlocal call_count
        call_count += 1
        return {"value": 42}
    result1 = cached_call("test_key", ttl=60, fetch_fn=fetch)
    result2 = cached_call("test_key", ttl=60, fetch_fn=fetch)
    assert result1 == {"value": 42}
    assert result2 == {"value": 42}
    assert call_count == 1  # fetch called only once

def test_cache_expires(tmp_path, monkeypatch):
    monkeypatch.setenv("CACHE_DIR", str(tmp_path))
    call_count = 0
    def fetch():
        nonlocal call_count
        call_count += 1
        return {"tick": call_count}
    cached_call("expiry_key", ttl=1, fetch_fn=fetch)
    time.sleep(1.1)
    cached_call("expiry_key", ttl=1, fetch_fn=fetch)
    assert call_count == 2

def test_cache_different_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("CACHE_DIR", str(tmp_path))
    cached_call("key_a", ttl=60, fetch_fn=lambda: "a")
    cached_call("key_b", ttl=60, fetch_fn=lambda: "b")
    assert cached_call("key_a", ttl=60, fetch_fn=lambda: "x") == "a"
    assert cached_call("key_b", ttl=60, fetch_fn=lambda: "x") == "b"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_cache.py -v
```

Expected: `ModuleNotFoundError: No module named 'fantasy.cache'`

- [ ] **Step 3: Implement fantasy/cache.py**

```python
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Callable

# Default to project root cache/ regardless of notebook working directory.
# Override with CACHE_DIR env var if needed.
_DEFAULT_CACHE_DIR = Path(__file__).parent.parent / "cache"

def _cache_dir() -> Path:
    d = Path(os.environ.get("CACHE_DIR", str(_DEFAULT_CACHE_DIR)))
    d.mkdir(exist_ok=True)
    return d

def _cache_path(key: str) -> Path:
    hashed = hashlib.md5(key.encode()).hexdigest()
    return _cache_dir() / f"{hashed}.json"

def cached_call(key: str, ttl: int, fetch_fn: Callable[[], Any]) -> Any:
    """Return cached result if fresh, otherwise call fetch_fn and cache result."""
    path = _cache_path(key)
    if path.exists():
        entry = json.loads(path.read_text())
        if time.time() - entry["cached_at"] < ttl:
            return entry["data"]
    data = fetch_fn()
    entry = {"data": data, "cached_at": time.time()}
    # Atomic write: write to temp file then rename
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(entry))
    tmp.rename(path)
    return data
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_cache.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add fantasy/cache.py tests/test_cache.py
git commit -m "feat: add disk cache with TTL and atomic writes"
```

---

## Task 3: Yahoo Auth Module

**Files:**
- Create: `fantasy/auth.py`

Note: This module cannot be unit-tested without real Yahoo credentials. Manual testing only.

- [ ] **Step 1: Register a Yahoo Developer App**

1. Go to https://developer.yahoo.com/apps/
2. Create a new app → select "Fantasy Sports" API
3. Set redirect URI to `oob` (out-of-band / installed app)
4. Copy `client_id` and `client_secret` into `.env`

- [ ] **Step 2: Create fantasy/auth.py**

```python
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from yahoo_oauth import OAuth2

load_dotenv()

CREDENTIALS_FILE = "credentials.json"

def get_oauth() -> OAuth2:
    """Return an authenticated Yahoo OAuth2 session, refreshing token if needed."""
    if not Path(CREDENTIALS_FILE).exists():
        # First-time setup: write a minimal credentials file for yahoo_oauth
        creds = {
            "consumer_key": os.environ["YAHOO_CLIENT_ID"],
            "consumer_secret": os.environ["YAHOO_CLIENT_SECRET"],
        }
        Path(CREDENTIALS_FILE).write_text(json.dumps(creds))
    oauth = OAuth2(None, None, from_file=CREDENTIALS_FILE)
    if not oauth.token_is_valid():
        oauth.refresh_access_token()
    return oauth

def discover_leagues() -> None:
    """Print all leagues and teams for the authenticated user."""
    import requests
    oauth = get_oauth()
    url = "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_keys=nba/leagues?format=json"
    resp = requests.get(url, headers={"Authorization": f"Bearer {oauth.access_token}"})
    resp.raise_for_status()
    data = resp.json()
    leagues = (data["fantasy_content"]["users"]["0"]["user"][1]["games"]
               ["0"]["game"][1]["leagues"])
    for i in range(leagues["count"]):
        league = leagues[str(i)]["league"][0]
        print(f"League: {league['name']}  key={league['league_key']}")
        teams_url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league['league_key']}/teams?format=json"
        tr = requests.get(teams_url, headers={"Authorization": f"Bearer {oauth.access_token}"})
        teams = tr.json()["fantasy_content"]["league"][1]["teams"]
        for j in range(teams["count"]):
            team = teams[str(j)]["team"][0]
            print(f"  Team: {team[2]['name']}  key={team[0][0]['team_key']}")

if __name__ == "__main__":
    print("Authenticating with Yahoo...")
    get_oauth()
    print("Auth successful. Discovering leagues...")
    discover_leagues()
    print("\nCopy YAHOO_LEAGUE_KEY and YAHOO_TEAM_KEY into your .env file.")
```

- [ ] **Step 3: Run auth discovery**

```bash
python -m fantasy.auth
```

Expected: browser opens for OAuth consent → tokens saved to `credentials.json` → leagues and team keys printed.

- [ ] **Step 4: Fill in .env with league/team keys from output**

- [ ] **Step 5: Commit**

```bash
git add fantasy/auth.py
git commit -m "feat: add Yahoo OAuth auth and league discovery"
```

---

## Task 4: Yahoo Client Module

**Files:**
- Create: `fantasy/yahoo_client.py`

Note: Integration-only; mock in other tests.

- [ ] **Step 1: Create fantasy/yahoo_client.py**

```python
import os
import time
import requests
from dotenv import load_dotenv
from fantasy.auth import get_oauth
from fantasy.cache import cached_call

load_dotenv()

LEAGUE_KEY = os.environ.get("YAHOO_LEAGUE_KEY", "")
TEAM_KEY = os.environ.get("YAHOO_TEAM_KEY", "")
BASE = "https://fantasysports.yahooapis.com/fantasy/v2"
YAHOO_TTL = 15 * 60  # 15 minutes

def _get(path: str) -> dict:
    """Make an authenticated GET request to Yahoo Fantasy API."""
    oauth = get_oauth()
    url = f"{BASE}{path}?format=json"
    resp = requests.get(url, headers={"Authorization": f"Bearer {oauth.access_token}"})
    resp.raise_for_status()
    return resp.json()["fantasy_content"]

def get_my_roster() -> list[dict]:
    """Return list of player dicts on my roster with stats and injury status."""
    def fetch():
        data = _get(f"/team/{TEAM_KEY}/roster;out=stats,percent_owned")
        players = data["team"][1]["roster"]["0"]["players"]
        result = []
        for i in range(players["count"]):
            p = players[str(i)]["player"]
            info = {item: val for d in p[0] for item, val in (d.items() if isinstance(d, dict) else {}.items())}
            result.append({
                "name": info.get("full_name", ""),
                "player_key": info.get("player_key", ""),
                "team_abbr": info.get("editorial_team_abbr", ""),
                "status": info.get("status", ""),  # INJ/GTD/OUT/Q/D or ""
                "position": info.get("display_position", ""),
            })
        return result
    return cached_call(f"roster_{TEAM_KEY}", YAHOO_TTL, fetch)

def get_current_matchup() -> dict:
    """Return current week matchup: my team + opponent team key, week start/end dates."""
    def fetch():
        data = _get(f"/team/{TEAM_KEY}/matchups")
        matchups = data["team"][1]["matchups"]
        # Find the current week matchup (is_current == 1)
        for i in range(matchups["count"]):
            m = matchups[str(i)]["matchup"]
            if m.get("is_current") == "1" or m.get("is_current") == 1:
                teams = m["0"]["teams"]
                team_keys = [teams[str(j)]["team"][0][0]["team_key"] for j in range(2)]
                opp_key = [k for k in team_keys if k != TEAM_KEY][0]
                return {
                    "week": m.get("week"),
                    "week_start": m.get("week_start"),
                    "week_end": m.get("week_end"),
                    "opponent_team_key": opp_key,
                }
        raise RuntimeError("No current matchup found")
    return cached_call(f"matchup_{TEAM_KEY}", YAHOO_TTL, fetch)

def get_roster_by_team(team_key: str) -> list[dict]:
    """Return roster for any team (used to fetch opponent's roster)."""
    def fetch():
        data = _get(f"/team/{team_key}/roster;out=stats")
        players = data["team"][1]["roster"]["0"]["players"]
        result = []
        for i in range(players["count"]):
            p = players[str(i)]["player"]
            info = {item: val for d in p[0] for item, val in (d.items() if isinstance(d, dict) else {}.items())}
            result.append({
                "name": info.get("full_name", ""),
                "team_abbr": info.get("editorial_team_abbr", ""),
                "status": info.get("status", ""),
                "position": info.get("display_position", ""),
            })
        return result
    return cached_call(f"roster_{team_key}", YAHOO_TTL, fetch)

def get_free_agents(count: int = 50) -> list[dict]:
    """Return top available free agents sorted by percent ownership."""
    def fetch():
        data = _get(f"/league/{LEAGUE_KEY}/players;status=FA;sort=PO;count={count};out=stats,percent_owned")
        players = data["league"][1]["players"]
        result = []
        for i in range(players["count"]):
            p = players[str(i)]["player"]
            info = {item: val for d in p[0] for item, val in (d.items() if isinstance(d, dict) else {}.items())}
            result.append({
                "name": info.get("full_name", ""),
                "team_abbr": info.get("editorial_team_abbr", ""),
                "status": info.get("status", ""),
                "position": info.get("display_position", ""),
            })
        return result
    return cached_call(f"free_agents_{LEAGUE_KEY}", YAHOO_TTL, fetch)

DEFAULT_CATEGORIES = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FG%", "FT%", "3PTM"]

def get_league_categories() -> list[str]:
    """
    Return list of scoring category stat names for this league.
    Falls back to DEFAULT_CATEGORIES if Yahoo settings parsing fails
    (Yahoo's settings JSON structure varies by league type).
    """
    def fetch():
        try:
            data = _get(f"/league/{LEAGUE_KEY}/settings")
            settings = data["league"][1]["settings"][0]
            stat_cats = settings["stat_categories"]["stats"]
            return [s["stat"]["display_name"] for s in stat_cats if s["stat"].get("enabled") == "1"]
        except (KeyError, IndexError, TypeError) as e:
            print(f"Warning: could not parse league categories ({e}). Using defaults: {DEFAULT_CATEGORIES}")
            return DEFAULT_CATEGORIES
    return cached_call(f"categories_{LEAGUE_KEY}", YAHOO_TTL * 24, fetch)
```

- [ ] **Step 2: Smoke test (requires valid .env + credentials.json)**

```bash
python -c "from fantasy.yahoo_client import get_my_roster; print(get_my_roster()[:2])"
```

Expected: list of player dicts printed.

- [ ] **Step 3: Commit**

```bash
git add fantasy/yahoo_client.py
git commit -m "feat: add Yahoo Fantasy API client"
```

---

## Task 5: NBA Stats Module

**Files:**
- Create: `fantasy/nba_stats.py`

- [ ] **Step 1: Create fantasy/nba_stats.py**

```python
import time
from datetime import date
from fantasy.cache import cached_call

NBA_TTL = 60 * 60  # 1 hour

STAT_COLS = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FGM", "FGA", "FG3M", "FTM", "FTA"]

def _current_season() -> str:
    """Return NBA season string like '2025-26' based on today's date."""
    today = date.today()
    year = today.year
    if today.month >= 10:
        return f"{year}-{str(year + 1)[-2:]}"
    return f"{year - 1}-{str(year)[-2:]}"

def get_player_id(player_name: str) -> int | None:
    """Look up NBA player ID by full name."""
    from nba_api.stats.static import players
    matches = players.find_players_by_full_name(player_name)
    if not matches:
        print(f"Warning: player not found in nba_api: {player_name}")
        return None
    return matches[0]["id"]

def get_player_stats(player_name: str) -> dict | None:
    """
    Return per-game stat averages for a player:
    - season: per-game averages for the full season
    - last_15: per-game averages over last 15 games
    Returns None if player not found.

    Uses PlayerDashboardByGeneralSplits which returns per-game averages directly
    (NOT cumulative totals — do NOT divide by GP).
    Two separate calls are made: one without last_n_games filter (season) and
    one with last_n_games=15 (recent form). dfs[0] is the overall row in both cases.
    """
    from nba_api.stats.endpoints import playerdashboardbygeneralsplits
    player_id = get_player_id(player_name)
    if player_id is None:
        return None

    def fetch():
        def extract_row(dash) -> dict:
            df = dash.get_data_frames()[0]  # index 0 = overall/summary row
            if df.empty:
                return {col: 0.0 for col in STAT_COLS}
            row = df.iloc[0]
            return {col: float(row[col]) if col in df.columns else 0.0 for col in STAT_COLS}

        time.sleep(0.6)
        season_dash = playerdashboardbygeneralsplits.PlayerDashboardByGeneralSplits(
            player_id=player_id,
            timeout=30,
        )
        season = extract_row(season_dash)

        time.sleep(0.6)
        last15_dash = playerdashboardbygeneralsplits.PlayerDashboardByGeneralSplits(
            player_id=player_id,
            last_n_games=15,
            timeout=30,
        )
        last_15 = extract_row(last15_dash)

        return {"season": season, "last_15": last_15}

    return cached_call(f"stats_{player_id}", NBA_TTL, fetch)

def get_games_this_week(team_abbr: str, week_start: str, week_end: str) -> int:
    """
    Return number of NBA games team_abbr plays between week_start and week_end (inclusive).
    week_start/week_end: 'YYYY-MM-DD' strings from Yahoo matchup data.
    Season string is derived dynamically from the current date.
    """
    from nba_api.stats.endpoints import leaguegamelog

    season = _current_season()

    def fetch():
        time.sleep(0.6)
        log = leaguegamelog.LeagueGameLog(
            season=season,
            date_from_nullable=week_start,
            date_to_nullable=week_end,
            timeout=30,
        )
        df = log.get_data_frames()[0]
        team_games = df[df["TEAM_ABBREVIATION"] == team_abbr.upper()]
        return int(len(team_games))

    return cached_call(f"schedule_{team_abbr}_{week_start}_{week_end}", NBA_TTL, fetch)
```

- [ ] **Step 2: Smoke test**

```bash
python -c "from fantasy.nba_stats import get_player_stats; print(get_player_stats('LeBron James'))"
```

Expected: dict with 'season' and 'last_15' stat averages.

- [ ] **Step 3: Commit**

```bash
git add fantasy/nba_stats.py
git commit -m "feat: add nba_api stats and schedule module"
```

---

## Task 6: Analysis Module

**Files:**
- Create: `fantasy/analysis.py`
- Create: `tests/test_analysis.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_analysis.py
import pytest
from fantasy.analysis import (
    blend_stats,
    injury_multiplier,
    project_player,
    project_team_categories,
    classify_categories,
    trade_category_delta,
)

def test_blend_stats():
    season = {"PTS": 20.0, "REB": 5.0}
    last15 = {"PTS": 30.0, "REB": 3.0}
    blended = blend_stats(season, last15)
    assert abs(blended["PTS"] - (20.0 * 0.3 + 30.0 * 0.7)) < 0.01
    assert abs(blended["REB"] - (5.0 * 0.3 + 3.0 * 0.7)) < 0.01

def test_injury_multiplier():
    assert injury_multiplier("") == 1.0
    assert injury_multiplier("GTD") == 0.5
    assert injury_multiplier("Q") == 0.5
    assert injury_multiplier("OUT") == 0.0
    assert injury_multiplier("INJ") == 0.0

def test_project_player():
    stats = {"season": {"PTS": 20.0, "REB": 5.0, "GP": 50}, "last_15": {"PTS": 30.0, "REB": 3.0, "GP": 15}}
    result = project_player(stats, games_remaining=3, injury_status="")
    assert abs(result["PTS"] - (20.0 * 0.3 + 30.0 * 0.7) * 3) < 0.1

def test_project_player_injured():
    stats = {"season": {"PTS": 20.0, "REB": 5.0, "GP": 50}, "last_15": {"PTS": 30.0, "REB": 3.0, "GP": 15}}
    result = project_player(stats, games_remaining=3, injury_status="OUT")
    assert result["PTS"] == 0.0

def test_project_player_gtd():
    stats = {"season": {"PTS": 20.0, "REB": 5.0, "GP": 50}, "last_15": {"PTS": 30.0, "REB": 3.0, "GP": 15}}
    result = project_player(stats, games_remaining=3, injury_status="GTD")
    assert abs(result["PTS"] - (20.0 * 0.3 + 30.0 * 0.7) * 3 * 0.5) < 0.1

def test_project_team_categories():
    players = [
        {"name": "A", "injury_status": "", "games_remaining": 3,
         "stats": {"season": {"PTS": 20.0, "REB": 5.0, "GP": 50}, "last_15": {"PTS": 30.0, "REB": 3.0, "GP": 15}}},
        {"name": "B", "injury_status": "OUT", "games_remaining": 2,
         "stats": {"season": {"PTS": 10.0, "REB": 8.0, "GP": 40}, "last_15": {"PTS": 12.0, "REB": 7.0, "GP": 10}}},
    ]
    totals = project_team_categories(players)
    assert totals["PTS"] > 0
    # B is OUT, so only A contributes to PTS
    expected_pts = (20.0 * 0.3 + 30.0 * 0.7) * 3
    assert abs(totals["PTS"] - expected_pts) < 0.1

def test_classify_categories():
    my = {"PTS": 100, "REB": 50, "AST": 30}
    opp = {"PTS": 80, "REB": 55, "AST": 30}
    result = classify_categories(my, opp, margin=0.05)
    assert result["PTS"] == "win"
    assert result["REB"] == "loss"
    assert result["AST"] == "tossup"

def test_trade_category_delta():
    roster = [
        {"name": "A", "injury_status": "", "games_remaining": 3,
         "stats": {"season": {"PTS": 20.0, "REB": 5.0, "GP": 50}, "last_15": {"PTS": 30.0, "REB": 3.0, "GP": 15}}},
    ]
    give_stats = [{"season": {"PTS": 20.0, "REB": 5.0, "GP": 50}, "last_15": {"PTS": 30.0, "REB": 3.0, "GP": 15}}]
    receive_stats = [{"season": {"PTS": 5.0, "REB": 10.0, "GP": 50}, "last_15": {"PTS": 6.0, "REB": 12.0, "GP": 15}}]
    delta = trade_category_delta(roster, give_stats, receive_stats, games_remaining=3)
    assert delta["PTS"] < 0   # losing points
    assert delta["REB"] > 0   # gaining rebounds
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_analysis.py -v
```

Expected: `ModuleNotFoundError: No module named 'fantasy.analysis'`

- [ ] **Step 3: Implement fantasy/analysis.py**

```python
import pandas as pd
from typing import Any

STAT_COLS = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FGM", "FGA", "FG3M", "FTM", "FTA"]

def blend_stats(season: dict, last_15: dict) -> dict:
    """Blend season (30%) and last-15-game (70%) per-game averages."""
    result = {}
    for col in STAT_COLS:
        s = season.get(col, 0.0)
        l = last_15.get(col, 0.0)
        result[col] = s * 0.3 + l * 0.7
    return result

def injury_multiplier(status: str) -> float:
    """Return projection multiplier based on Yahoo injury status."""
    if status in ("OUT", "INJ"):
        return 0.0
    if status in ("GTD", "Q"):
        return 0.5
    return 1.0

def project_player(stats: dict, games_remaining: int, injury_status: str) -> dict:
    """Return projected category totals for a player over games_remaining games."""
    mult = injury_multiplier(injury_status)
    blended = blend_stats(stats["season"], stats["last_15"])
    return {col: blended[col] * games_remaining * mult for col in STAT_COLS}

def project_team_categories(players: list[dict]) -> dict:
    """
    Sum projected category totals across all players.
    Each player dict: {name, injury_status, games_remaining, stats}
    """
    totals = {col: 0.0 for col in STAT_COLS}
    for p in players:
        if p.get("stats") is None:
            continue
        proj = project_player(p["stats"], p["games_remaining"], p.get("injury_status", ""))
        for col in STAT_COLS:
            totals[col] += proj[col]
    return totals

def classify_categories(my: dict, opp: dict, margin: float = 0.05) -> dict:
    """
    Classify each category as 'win', 'loss', or 'tossup'.
    margin: fractional difference threshold for tossup (default 5%).
    For TOV, lower is better (inverted).
    """
    result = {}
    for col in my:
        m, o = my[col], opp[col]
        total = (m + o) / 2 if (m + o) > 0 else 1
        diff = (m - o) / total
        if col == "TOV":
            diff = -diff  # lower TOV is better
        if diff > margin:
            result[col] = "win"
        elif diff < -margin:
            result[col] = "loss"
        else:
            result[col] = "tossup"
    return result

def trade_category_delta(
    roster: list[dict],
    give_stats: list[dict],
    receive_stats: list[dict],
    games_remaining: int,
) -> dict:
    """
    Compute per-category change if you give away give_stats players and receive receive_stats players.
    Returns delta dict: positive = gain, negative = loss.
    All players use games_remaining for projection.
    """
    def sum_projections(stats_list: list[dict]) -> dict:
        totals = {col: 0.0 for col in STAT_COLS}
        for s in stats_list:
            proj = project_player(s, games_remaining, "")
            for col in STAT_COLS:
                totals[col] += proj[col]
        return totals

    give_totals = sum_projections(give_stats)
    receive_totals = sum_projections(receive_stats)
    return {col: receive_totals[col] - give_totals[col] for col in STAT_COLS}
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_analysis.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add fantasy/analysis.py tests/test_analysis.py
git commit -m "feat: add projection model and category analysis"
```

---

## Task 7: LLM Module

**Files:**
- Create: `fantasy/llm.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_llm.py
import pytest
from unittest.mock import MagicMock, patch
from fantasy.llm import build_matchup_prompt, build_start_sit_prompt, ask_gemini

def test_build_matchup_prompt_contains_categories():
    my_proj = {"PTS": 200, "REB": 80, "AST": 50}
    opp_proj = {"PTS": 180, "REB": 90, "AST": 45}
    classification = {"PTS": "win", "REB": "loss", "AST": "tossup"}
    prompt = build_matchup_prompt(my_proj, opp_proj, classification)
    assert "PTS" in prompt
    assert "win" in prompt
    assert "tossup" in prompt

def test_build_start_sit_prompt_contains_players():
    players = [
        {"name": "LeBron James", "status": "", "games_remaining": 3, "projected": {"PTS": 75}},
        {"name": "Joel Embiid", "status": "GTD", "games_remaining": 2, "projected": {"PTS": 30}},
    ]
    prompt = build_start_sit_prompt(players)
    assert "LeBron James" in prompt
    assert "Joel Embiid" in prompt
    assert "GTD" in prompt

def test_ask_gemini_returns_text(monkeypatch):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Start LeBron, sit Embiid."
    mock_client.models.generate_content.return_value = mock_response
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
    with patch("fantasy.llm.genai.Client", return_value=mock_client):
        result = ask_gemini("Test prompt")
    assert result == "Start LeBron, sit Embiid."
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_llm.py -v
```

Expected: `ModuleNotFoundError: No module named 'fantasy.llm'`

- [ ] **Step 3: Implement fantasy/llm.py**

```python
import json
import os
from dotenv import load_dotenv
import google.genai as genai

load_dotenv()

MODEL = "gemini-2.0-flash"

def ask_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the response text."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in .env")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=MODEL, contents=prompt)
    if not response.text:
        print(f"Raw Gemini response: {response}")
        raise ValueError("Gemini returned empty or malformed response")
    return response.text

def build_matchup_prompt(
    my_proj: dict,
    opp_proj: dict,
    classification: dict,
) -> str:
    lines = ["You are an expert fantasy basketball analyst. Here is this week's H2H category matchup projection:\n"]
    lines.append(f"{'Category':<8} {'My Team':>10} {'Opponent':>10} {'Status':>10}")
    lines.append("-" * 42)
    for cat in my_proj:
        lines.append(f"{cat:<8} {my_proj[cat]:>10.1f} {opp_proj[cat]:>10.1f} {classification.get(cat, '?'):>10}")
    lines.append("\nProvide a concise weekly strategy: which categories to focus on winning, which to punt, and 2-3 specific streaming/lineup actions to swing toss-up categories.")
    return "\n".join(lines)

def build_start_sit_prompt(players: list[dict]) -> str:
    lines = ["You are an expert fantasy basketball analyst. Here is today's roster ranked by projected contribution:\n"]
    lines.append(f"{'Rank':<5} {'Player':<22} {'Status':<6} {'Games Left':<12} {'Proj PTS':<10}")
    lines.append("-" * 58)
    for i, p in enumerate(players, 1):
        pts = p.get("projected", {}).get("PTS", 0)
        lines.append(f"{i:<5} {p['name']:<22} {p.get('status',''):<6} {p.get('games_remaining', 0):<12} {pts:<10.1f}")
    lines.append("\nGive a clear start/sit recommendation for each player with one sentence of reasoning. Be direct.")
    return "\n".join(lines)

def build_waiver_prompt(free_agents: list[dict], my_weaknesses: list[str]) -> str:
    lines = [f"You are a fantasy basketball analyst. My team is weak in: {', '.join(my_weaknesses)}.\n"]
    lines.append("Top available free agents scored against my needs:\n")
    lines.append(f"{'Rank':<5} {'Player':<22} {'Pos':<6} {'Games Left':<12} {'Fit Score':<10}")
    lines.append("-" * 58)
    for i, p in enumerate(free_agents[:20], 1):
        lines.append(f"{i:<5} {p['name']:<22} {p.get('position',''):<6} {p.get('games_remaining',0):<12} {p.get('fit_score',0):<10.2f}")
    lines.append("\nRecommend the top 5 pickups with one sentence of reasoning each.")
    return "\n".join(lines)

def build_trade_prompt(delta: dict, matchup_context: dict) -> str:
    lines = ["You are a fantasy basketball analyst evaluating a trade. Per-category impact (+ = gain):\n"]
    lines.append(f"{'Category':<8} {'Delta':>10} {'Matchup Status':>15}")
    lines.append("-" * 36)
    for cat in delta:
        status = matchup_context.get(cat, "?")
        lines.append(f"{cat:<8} {delta[cat]:>+10.1f} {status:>15}")
    lines.append("\nGive a verdict: ACCEPT, DECLINE, or COUNTER with brief reasoning (3-5 sentences).")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_llm.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add fantasy/llm.py tests/test_llm.py
git commit -m "feat: add Gemini LLM module with prompt builders"
```

---

## Task 8: Notebook 01 — Matchup Planner

**Files:**
- Create: `notebooks/01_matchup_planner.ipynb`

- [ ] **Step 1: Create the notebook**

Cell 1 — Imports:
```python
import sys; sys.path.insert(0, "..")
from fantasy.yahoo_client import get_my_roster, get_current_matchup, get_roster_by_team, get_league_categories
from fantasy.nba_stats import get_player_stats, get_games_this_week
from fantasy.analysis import project_team_categories, classify_categories
from fantasy.llm import build_matchup_prompt, ask_gemini
import pandas as pd
```

Cell 2 — Fetch data:
```python
matchup = get_current_matchup()
my_roster = get_my_roster()
opp_roster = get_roster_by_team(matchup["opponent_team_key"])
categories = get_league_categories()
week_start, week_end = matchup["week_start"], matchup["week_end"]
print(f"Week {matchup['week']}: {week_start} → {week_end}")
print(f"Opponent team: {matchup['opponent_team_key']}")
```

Cell 3 — Build player dicts with stats + games:
```python
def enrich_players(roster):
    enriched = []
    for p in roster:
        stats = get_player_stats(p["name"])
        games = get_games_this_week(p["team_abbr"], week_start, week_end)
        enriched.append({**p, "stats": stats, "games_remaining": games})
    return enriched

my_players = enrich_players(my_roster)
opp_players = enrich_players(opp_roster)
```

Cell 4 — Project and classify:
```python
my_proj = project_team_categories(my_players)
opp_proj = project_team_categories(opp_players)
classification = classify_categories(my_proj, opp_proj)

df = pd.DataFrame({
    "My Team": my_proj,
    "Opponent": opp_proj,
    "Status": classification,
}).round(1)
print(df.to_string())
```

Cell 5 — AI recommendation:
```python
prompt = build_matchup_prompt(my_proj, opp_proj, classification)
advice = ask_gemini(prompt)
print("\n=== WEEKLY GAME PLAN ===\n")
print(advice)
```

- [ ] **Step 2: Launch and run all cells**

```bash
jupyter notebook notebooks/01_matchup_planner.ipynb
```

Expected: category projection table printed, followed by Gemini weekly strategy.

- [ ] **Step 3: Commit**

```bash
git add notebooks/01_matchup_planner.ipynb
git commit -m "feat: add matchup planner notebook"
```

---

## Task 9: Notebook 02 — Start/Sit

**Files:**
- Create: `notebooks/02_start_sit.ipynb`

- [ ] **Step 1: Create the notebook**

Cell 1 — Imports:
```python
import sys; sys.path.insert(0, "..")
from fantasy.yahoo_client import get_my_roster, get_current_matchup
from fantasy.nba_stats import get_player_stats, get_games_this_week
from fantasy.analysis import project_player
from fantasy.llm import build_start_sit_prompt, ask_gemini
import pandas as pd
```

Cell 2 — Fetch and enrich:
```python
matchup = get_current_matchup()
roster = get_my_roster()
week_start, week_end = matchup["week_start"], matchup["week_end"]

players = []
for p in roster:
    stats = get_player_stats(p["name"])
    games = get_games_this_week(p["team_abbr"], week_start, week_end)
    projected = project_player(stats, games, p["status"]) if stats else {}
    players.append({**p, "stats": stats, "games_remaining": games, "projected": projected})

# Sort by projected PTS descending
players.sort(key=lambda x: x["projected"].get("PTS", 0), reverse=True)
```

Cell 3 — Display roster table:
```python
rows = []
for p in players:
    rows.append({
        "Player": p["name"],
        "Pos": p["position"],
        "Status": p["status"] or "Active",
        "Games Left": p["games_remaining"],
        "Proj PTS": round(p["projected"].get("PTS", 0), 1),
        "Proj REB": round(p["projected"].get("REB", 0), 1),
        "Proj AST": round(p["projected"].get("AST", 0), 1),
    })
print(pd.DataFrame(rows).to_string(index=False))
```

Cell 4 — AI start/sit card:
```python
prompt = build_start_sit_prompt(players)
advice = ask_gemini(prompt)
print("\n=== TODAY'S LINEUP CARD ===\n")
print(advice)
```

- [ ] **Step 2: Launch and run all cells**

```bash
jupyter notebook notebooks/02_start_sit.ipynb
```

Expected: ranked roster table + Gemini lineup card.

- [ ] **Step 3: Commit**

```bash
git add notebooks/02_start_sit.ipynb
git commit -m "feat: add start/sit lineup notebook"
```

---

## Task 10: Notebook 03 — Waiver Wire

**Files:**
- Create: `notebooks/03_waiver_wire.ipynb`

- [ ] **Step 1: Create the notebook**

Cell 1 — Imports:
```python
import sys; sys.path.insert(0, "..")
from fantasy.yahoo_client import get_my_roster, get_free_agents, get_current_matchup
from fantasy.nba_stats import get_player_stats, get_games_this_week
from fantasy.analysis import project_team_categories, project_player, STAT_COLS
from fantasy.llm import build_waiver_prompt, ask_gemini
import pandas as pd
```

Cell 2 — Identify my weakest categories:
```python
matchup = get_current_matchup()
week_start, week_end = matchup["week_start"], matchup["week_end"]
my_roster = get_my_roster()

my_players = []
for p in my_roster:
    stats = get_player_stats(p["name"])
    games = get_games_this_week(p["team_abbr"], week_start, week_end)
    my_players.append({**p, "stats": stats, "games_remaining": games})

my_totals = project_team_categories(my_players)
# Identify bottom 3 categories by absolute projected value (normalized)
sorted_cats = sorted(my_totals, key=lambda c: my_totals[c])
weak_cats = sorted_cats[:3]
print(f"Weakest categories: {weak_cats}")
```

Cell 3 — Score free agents:
```python
fas = get_free_agents(count=50)

scored = []
for fa in fas:
    stats = get_player_stats(fa["name"])
    games = get_games_this_week(fa["team_abbr"], week_start, week_end)
    if stats is None:
        continue
    proj = project_player(stats, games, fa.get("status", ""))
    # Fit score: sum of projected values in my weak categories, boosted by games
    fit = sum(proj.get(c, 0) for c in weak_cats)
    scored.append({**fa, "games_remaining": games, "projected": proj, "fit_score": fit})

scored.sort(key=lambda x: x["fit_score"], reverse=True)
print(pd.DataFrame([{
    "Player": p["name"], "Pos": p["position"], "Status": p["status"] or "Active",
    "Games": p["games_remaining"], "Fit Score": round(p["fit_score"], 2)
} for p in scored[:20]]).to_string(index=False))
```

Cell 4 — AI recommendations:
```python
prompt = build_waiver_prompt(scored, weak_cats)
advice = ask_gemini(prompt)
print("\n=== WAIVER WIRE PICKUPS ===\n")
print(advice)
```

- [ ] **Step 2: Launch and run all cells**

```bash
jupyter notebook notebooks/03_waiver_wire.ipynb
```

Expected: scored free agent table + top 5 pickup recommendations.

- [ ] **Step 3: Commit**

```bash
git add notebooks/03_waiver_wire.ipynb
git commit -m "feat: add waiver wire analysis notebook"
```

---

## Task 11: Notebook 04 — Trade Analyzer

**Files:**
- Create: `notebooks/04_trade_analyzer.ipynb`

- [ ] **Step 1: Create the notebook**

Cell 1 — **EDIT THIS CELL** with your trade:
```python
# === CONFIGURE YOUR TRADE HERE ===
GIVE = ["Player Name A", "Player Name B"]  # players you are giving away
RECEIVE = ["Player Name C"]               # players you are receiving
GAMES_REMAINING = 4                        # games left in current week
```

Cell 2 — Imports:
```python
import sys; sys.path.insert(0, "..")
from fantasy.yahoo_client import get_my_roster, get_current_matchup, get_roster_by_team
from fantasy.nba_stats import get_player_stats, get_games_this_week
from fantasy.analysis import project_team_categories, classify_categories, trade_category_delta
from fantasy.llm import build_trade_prompt, ask_gemini
import pandas as pd
```

Cell 3 — Fetch stats for trade players:
```python
give_stats = []
for name in GIVE:
    stats = get_player_stats(name)
    if stats is None:
        print(f"Warning: no stats found for {name}")
    else:
        give_stats.append(stats)

receive_stats = []
for name in RECEIVE:
    stats = get_player_stats(name)
    if stats is None:
        print(f"Warning: no stats found for {name}")
    else:
        receive_stats.append(stats)
```

Cell 4 — Current matchup context:
```python
matchup = get_current_matchup()
week_start, week_end = matchup["week_start"], matchup["week_end"]
my_roster = get_my_roster()
opp_roster = get_roster_by_team(matchup["opponent_team_key"])

def enrich(roster):
    return [{**p, "stats": get_player_stats(p["name"]),
             "games_remaining": get_games_this_week(p["team_abbr"], week_start, week_end)}
            for p in roster]

my_players = enrich(my_roster)
opp_players = enrich(opp_roster)
my_proj = project_team_categories(my_players)
opp_proj = project_team_categories(opp_players)
matchup_context = classify_categories(my_proj, opp_proj)
```

Cell 5 — Compute and display trade delta:
```python
delta = trade_category_delta(my_players, give_stats, receive_stats, GAMES_REMAINING)

df = pd.DataFrame({
    "Delta": delta,
    "Matchup Status": matchup_context,
}).round(2)
df["Delta"] = df["Delta"].apply(lambda x: f"{x:+.1f}")
print(f"Trade: Give {GIVE} → Receive {RECEIVE}\n")
print(df.to_string())
```

Cell 6 — AI verdict:
```python
prompt = build_trade_prompt(delta, matchup_context)
advice = ask_gemini(prompt)
print("\n=== TRADE VERDICT ===\n")
print(advice)
```

- [ ] **Step 2: Launch and run all cells (with real player names filled in)**

```bash
jupyter notebook notebooks/04_trade_analyzer.ipynb
```

Expected: per-category delta table + ACCEPT/DECLINE/COUNTER verdict.

- [ ] **Step 3: Commit**

```bash
git add notebooks/04_trade_analyzer.ipynb
git commit -m "feat: add trade analyzer notebook"
```

---

## Task 12: Run Full Test Suite

- [ ] **Step 1: Run all tests**

```bash
pytest tests/ -v
```

Expected: all tests PASS. No failures.

- [ ] **Step 2: Run notebooks end-to-end (smoke test)**

Open each notebook in Jupyter and run all cells. Verify:
- No import errors
- API calls return data (or load from cache on second run)
- Gemini returns a recommendation

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "feat: complete fantasy match tool - all notebooks and library"
```

---

## Quick Reference

```bash
# Install
pip install -r requirements.txt

# First-time Yahoo auth + league discovery
python -m fantasy.auth

# Run tests
pytest tests/ -v

# Launch a notebook
jupyter notebook notebooks/01_matchup_planner.ipynb

# Clear cache
rm -rf cache/
```
