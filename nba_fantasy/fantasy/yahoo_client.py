import os
import requests
from dotenv import load_dotenv
from fantasy.auth import get_oauth
from fantasy.cache import cached_call

load_dotenv()

LEAGUE_KEY = os.environ.get("YAHOO_LEAGUE_KEY", "")
BASE = "https://fantasysports.yahooapis.com/fantasy/v2"
YAHOO_TTL = 15 * 60  # 15 minutes
DEFAULT_CATEGORIES = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FG%", "FT%", "3PTM"]

def _get(path: str) -> dict:
    """Make an authenticated GET request to Yahoo Fantasy API."""
    oauth = get_oauth()
    url = f"{BASE}{path}?format=json"
    resp = requests.get(url, headers={"Authorization": f"Bearer {oauth.access_token}"})
    resp.raise_for_status()
    return resp.json()["fantasy_content"]

def _get_my_team_key() -> str:
    """Auto-discover the current user's team key in the league via Yahoo login."""
    explicit = os.environ.get("YAHOO_TEAM_KEY", "")
    if explicit:
        return explicit
    data = _get(f"/league/{LEAGUE_KEY}/teams")
    teams = data["league"][1]["teams"]
    for i in range(teams["count"]):
        team = teams[str(i)]["team"]
        info = {k: v for d in team[0] for k, v in (d.items() if isinstance(d, dict) else {}.items())}
        managers = info.get("managers", [])
        for m in managers:
            if m.get("manager", {}).get("is_current_login") == "1":
                return info["team_key"]
    raise RuntimeError("Could not find your team in the league. Set YAHOO_TEAM_KEY in .env manually.")

_MY_TEAM_KEY: str | None = None

def _team_key() -> str:
    global _MY_TEAM_KEY
    if _MY_TEAM_KEY is None:
        _MY_TEAM_KEY = _get_my_team_key()
    return _MY_TEAM_KEY

def _parse_player(p: list) -> dict:
    """Parse a Yahoo player list into a flat dict."""
    info = {item: val for d in p[0] for item, val in (d.items() if isinstance(d, dict) else {}.items())}
    name_field = info.get("name", "")
    name = name_field.get("full", "") if isinstance(name_field, dict) else name_field
    return {
        "name": name,
        "player_key": info.get("player_key", ""),
        "team_abbr": info.get("editorial_team_abbr", ""),
        "status": info.get("status", ""),  # INJ/GTD/OUT/Q/D or ""
        "position": info.get("display_position", ""),
    }

def get_my_roster() -> list[dict]:
    """Return list of player dicts on my roster with stats and injury status."""
    def fetch():
        data = _get(f"/team/{_team_key()}/roster")
        players = data["team"][1]["roster"]["0"]["players"]
        return [_parse_player(players[str(i)]["player"]) for i in range(players["count"])]
    return cached_call(f"roster_{_team_key()}", YAHOO_TTL, fetch)

def get_current_matchup() -> dict:
    """Return current week matchup: my team + opponent team key, week start/end dates."""
    def fetch():
        data = _get(f"/team/{_team_key()}/matchups")
        matchups = data["team"][1]["matchups"]
        # Find the current week matchup (midevent = in progress, preevent = upcoming)
        for i in range(matchups["count"]):
            m = matchups[str(i)]["matchup"]
            if m.get("status") in ("midevent", "preevent"):
                teams = m["0"]["teams"]
                team_keys = [teams[str(j)]["team"][0][0]["team_key"] for j in range(2)]
                opp_key = [k for k in team_keys if k != _team_key()][0]
                return {
                    "week": m.get("week"),
                    "week_start": m.get("week_start"),
                    "week_end": m.get("week_end"),
                    "opponent_team_key": opp_key,
                }
        raise RuntimeError("No current matchup found")
    return cached_call(f"matchup_{_team_key()}", YAHOO_TTL, fetch)

def get_roster_by_team(team_key: str) -> list[dict]:
    """Return roster for any team (used to fetch opponent's roster)."""
    def fetch():
        data = _get(f"/team/{team_key}/roster")
        players = data["team"][1]["roster"]["0"]["players"]
        return [_parse_player(players[str(i)]["player"]) for i in range(players["count"])]
    return cached_call(f"roster_{team_key}", YAHOO_TTL, fetch)

def get_free_agents(count: int = 50) -> list[dict]:
    """Return top available free agents sorted by percent ownership."""
    def fetch():
        data = _get(f"/league/{LEAGUE_KEY}/players;status=FA;sort=PO;count={count};out=stats,percent_owned")
        players = data["league"][1]["players"]
        result = []
        for i in range(players["count"]):
            result.append(_parse_player(players[str(i)]["player"]))
        return result
    return cached_call(f"free_agents_{LEAGUE_KEY}", YAHOO_TTL, fetch)

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
