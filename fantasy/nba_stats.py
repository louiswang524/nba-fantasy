import time
import unicodedata
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

def _normalize(name: str) -> str:
    """Strip accents and lowercase for fuzzy name matching."""
    return unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode().lower()

def get_player_id(player_name: str) -> int | None:
    """Look up NBA player ID by full name, with accent-insensitive fallback."""
    from nba_api.stats.static import players
    matches = players.find_players_by_full_name(player_name)
    if matches:
        return matches[0]["id"]
    # Fallback: strip accents and search all players
    normalized = _normalize(player_name)
    for p in players.get_players():
        if _normalize(p["full_name"]) == normalized:
            return p["id"]
    # Not in static list — rookies/two-way players may still be found via bulk stats lookup
    return None

def _fetch_all_stats(last_n_games: int = 0) -> tuple[dict, dict]:
    """
    Download all players' per-game stats in one API call.
    Returns (stats_by_id, name_to_id) where stats_by_id is keyed by str(player_id).
    last_n_games=0 means full season.
    """
    from nba_api.stats.endpoints import leaguedashplayerstats
    time.sleep(1.5)
    df = leaguedashplayerstats.LeagueDashPlayerStats(
        season=_current_season(),
        per_mode_detailed="PerGame",
        last_n_games=last_n_games,
        timeout=60,
    ).get_data_frames()[0]

    stats_by_id = {}
    name_to_id = {}
    col_map = {"PTS": "PTS", "REB": "REB", "AST": "AST", "STL": "STL",
               "BLK": "BLK", "TOV": "TOV", "FGM": "FGM", "FGA": "FGA",
               "FG3M": "FG3M", "FTM": "FTM", "FTA": "FTA"}
    for _, row in df.iterrows():
        pid = str(int(row["PLAYER_ID"]))
        stats_by_id[pid] = {col: float(row[nba_col]) if nba_col in df.columns else 0.0
                            for col, nba_col in col_map.items()}
        name_to_id[_normalize(str(row["PLAYER_NAME"]))] = pid
    return stats_by_id, name_to_id


def _get_all_stats_cached() -> tuple[dict, dict, dict]:
    """Return (season_stats, last15_stats, name_to_id) all keyed/mapped by str player_id."""
    season = _current_season()

    def fetch_season():
        stats, name_map = _fetch_all_stats(last_n_games=0)
        return {"stats": stats, "name_to_id": name_map}

    def fetch_last15():
        stats, _ = _fetch_all_stats(last_n_games=15)
        return stats

    season_data = cached_call(f"all_stats_season_{season}", NBA_TTL, fetch_season)
    last15_stats = cached_call(f"all_stats_last15_{season}", NBA_TTL, fetch_last15)
    return season_data["stats"], last15_stats, season_data["name_to_id"]


def get_player_stats(player_name: str) -> dict | None:
    """
    Return per-game stat averages for a player by looking up from bulk download.
    Falls back to name-based lookup from the bulk stats dataframe (handles rookies
    not in nba_api's static player list).
    Returns dict with 'season' and 'last_15' keys, or None if not found.
    """
    season_all, last15_all, name_to_id = _get_all_stats_cached()

    # Try nba_api static lookup first
    key = None
    player_id = get_player_id(player_name)
    if player_id is not None:
        key = str(player_id)

    # Fallback: match by normalized name directly from bulk stats
    if key is None or key not in season_all:
        key = name_to_id.get(_normalize(player_name))

    if key is None or key not in season_all:
        print(f"Warning: no stats found for {player_name}")
        return None

    return {"season": season_all[key], "last_15": last15_all.get(key, season_all[key])}

def batch_get_player_stats(players: list[dict]) -> list[dict]:
    """
    Fetch stats for a list of player dicts sequentially.
    Each dict must have 'name'. Returns the same list with 'stats' added.
    Sequential to respect NBA API rate limits.
    """
    return [{**p, "stats": get_player_stats(p["name"])} for p in players]

def _get_team_id(team_abbr: str) -> int:
    """Look up NBA team ID by abbreviation."""
    from nba_api.stats.static import teams
    matches = [t for t in teams.get_teams() if t["abbreviation"] == team_abbr.upper()]
    if not matches:
        raise ValueError(f"Team not found: {team_abbr}")
    return matches[0]["id"]

def get_games_this_week(team_abbr: str, week_start: str, week_end: str) -> int:
    """
    Return number of NBA games team_abbr plays between week_start and week_end (inclusive).
    Uses the full season schedule (includes future games, unlike game log).
    """
    import requests
    from datetime import datetime, timedelta

    season = _current_season()

    def fetch():
        start = datetime.strptime(week_start, "%Y-%m-%d")
        end = datetime.strptime(week_end, "%Y-%m-%d")
        abbr = team_abbr.upper()
        count = 0

        # Walk each day in the week and check the scoreboard
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            url = f"https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json"
            try:
                time.sleep(0.3)
                resp = requests.get(url, timeout=30)
                data = resp.json()
                for gd in data["leagueSchedule"]["gameDates"]:
                    if gd["gameDate"].startswith(date_str):
                        for game in gd["games"]:
                            if (game["homeTeam"]["teamTricode"] == abbr or
                                    game["awayTeam"]["teamTricode"] == abbr):
                                count += 1
                break  # full schedule fetched at once
            except Exception:
                pass
            current += timedelta(days=1)

        # Fallback: count from full schedule json
        return count

    def fetch_from_schedule():
        abbr = team_abbr.upper()
        start = datetime.strptime(week_start, "%Y-%m-%d")
        end = datetime.strptime(week_end, "%Y-%m-%d")
        try:
            time.sleep(0.5)
            resp = requests.get(
                "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json",
                timeout=30,
            )
            data = resp.json()
            count = 0
            for gd in data["leagueSchedule"]["gameDates"]:
                gdate = datetime.strptime(gd["gameDate"], "%m/%d/%Y %H:%M:%S")
                if start <= gdate <= end:
                    for game in gd["games"]:
                        if (game["homeTeam"]["teamTricode"] == abbr or
                                game["awayTeam"]["teamTricode"] == abbr):
                            count += 1
            return count
        except Exception as e:
            print(f"Warning: schedule fetch failed for {team_abbr}: {e}")
            return 0

    return cached_call(f"schedule_{season}_{team_abbr}_{week_start}_{week_end}", NBA_TTL, fetch_from_schedule)
