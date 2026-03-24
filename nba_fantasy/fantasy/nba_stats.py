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
