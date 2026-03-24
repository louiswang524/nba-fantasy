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
    print(f"Warning: player not found in nba_api: {player_name}")
    return None

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

        time.sleep(1.5)
        season_dash = playerdashboardbygeneralsplits.PlayerDashboardByGeneralSplits(
            player_id=player_id,
            timeout=60,
        )
        season = extract_row(season_dash)

        time.sleep(1.5)
        last15_dash = playerdashboardbygeneralsplits.PlayerDashboardByGeneralSplits(
            player_id=player_id,
            last_n_games=15,
            timeout=60,
        )
        last_15 = extract_row(last15_dash)

        return {"season": season, "last_15": last_15}

    def fetch_with_retry():
        for attempt in range(3):
            try:
                return fetch()
            except Exception as e:
                if attempt == 2:
                    print(f"Warning: failed to fetch stats for {player_name} after 3 attempts: {e}")
                    return None
                time.sleep(3 * (attempt + 1))

    return cached_call(f"stats_{player_id}_{_current_season()}", NBA_TTL, fetch_with_retry)

def get_games_this_week(team_abbr: str, week_start: str, week_end: str) -> int:
    """
    Return number of NBA games team_abbr plays between week_start and week_end (inclusive).
    week_start/week_end: 'YYYY-MM-DD' strings from Yahoo matchup data.
    Season string is derived dynamically from the current date.
    """
    from nba_api.stats.endpoints import leaguegamelog

    season = _current_season()

    def fetch():
        time.sleep(1.5)
        log = leaguegamelog.LeagueGameLog(
            season=season,
            date_from_nullable=week_start,
            date_to_nullable=week_end,
            timeout=60,
        )
        df = log.get_data_frames()[0]
        team_games = df[df["TEAM_ABBREVIATION"] == team_abbr.upper()]
        return int(len(team_games))

    return cached_call(f"schedule_{season}_{team_abbr}_{week_start}_{week_end}", NBA_TTL, fetch)
