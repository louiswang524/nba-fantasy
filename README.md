# NBA Fantasy Basketball Tool

A Python/Jupyter notebook toolkit for winning Yahoo Fantasy Basketball H2H categories leagues. Uses Yahoo Fantasy API for live roster/matchup data, NBA stats API for player statistics, and Gemini AI for strategic recommendations.

## Features

| Notebook | What it does |
|---|---|
| `01_matchup_planner` | Analyzes your current weekly matchup and generates a game plan |
| `02_start_sit` | Ranks your roster and gives start/sit decisions for today |
| `03_waiver_wire` | Scores free agents against your weakest categories |
| `04_trade_analyzer` | Evaluates trade impact by category with an accept/decline verdict |

## Setup

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get API credentials

**Yahoo Fantasy API**
1. Go to [developer.yahoo.com/apps](https://developer.yahoo.com/apps/) and create an app
2. Select **Installed Application**, enable **Fantasy Sports → Read**
3. Copy your Client ID and Client Secret

**Gemini API**
1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Create an API key

### 3. Find your league and team keys

Run this after setting up OAuth:
```python
from fantasy.auth import get_oauth
import requests, json

oauth = get_oauth()
url = "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_keys=nba/leagues?format=json"
resp = requests.get(url, headers={"Authorization": f"Bearer {oauth.access_token}"})
print(json.dumps(resp.json(), indent=2))
```

Look for your `league_key` (e.g. `nba.l.123456`) and `team_key` (e.g. `nba.l.123456.t.4`).

### 4. Create `.env`

```
YAHOO_CLIENT_ID=your_client_id
YAHOO_CLIENT_SECRET=your_client_secret
YAHOO_LEAGUE_KEY=nba.l.XXXXXX
YAHOO_TEAM_KEY=nba.l.XXXXXX.t.X
GEMINI_API_KEY=your_gemini_key
```

### 5. Run

```bash
jupyter notebook
```

Open any notebook in the `notebooks/` folder and run all cells. The first run fetches live data (takes ~1-2 min due to NBA API rate limits); subsequent runs use the cache.

## Architecture

```
fantasy/
  auth.py          # Yahoo OAuth2 via yahoo_oauth
  yahoo_client.py  # Yahoo Fantasy API calls (roster, matchup, free agents)
  nba_stats.py     # NBA player stats via nba_api (season + last 15 games)
  analysis.py      # Projection model: 70% last-15 + 30% season × games × injury
  llm.py           # Gemini API prompt builders and response handler
  cache.py         # Disk cache with TTL (MD5-keyed JSON files)
notebooks/
  01_matchup_planner.ipynb
  02_start_sit.ipynb
  03_waiver_wire.ipynb
  04_trade_analyzer.ipynb
```

## Notes

- 2025 rookies (Cooper Flagg, Donovan Clingan, etc.) are not in nba_api's player database and will be skipped
- Stats are cached for 1 hour, schedules for 1 hour, rosters for 15 minutes
- The projection model uses a 70/30 blend of last-15-game and full-season averages, adjusted for games remaining and injury status
