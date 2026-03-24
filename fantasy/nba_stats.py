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
    normalized = _normalize(player_name)
    for p in players.get_players():
        if _normalize(p["full_name"]) == normalized:
            return p["id"]
    # Not in static list — rookies/two-way players may still be found via bulk stats
    return None


def _fetch_all_stats(last_n_games: int = 0, measure_type: str = "Base") -> tuple[dict, dict]:
    """
    Download all players' per-game stats in one API call.
    measure_type: "Base" for counting stats, "Advanced" for USG_PCT, PACE, PIE.
    Returns (stats_by_id, name_to_id). name_to_id is only populated for Base.
    """
    from nba_api.stats.endpoints import leaguedashplayerstats
    time.sleep(1.5)
    df = leaguedashplayerstats.LeagueDashPlayerStats(
        season=_current_season(),
        per_mode_detailed="PerGame",
        last_n_games=last_n_games,
        measure_type_detailed_defense=measure_type,
        timeout=60,
    ).get_data_frames()[0]

    if measure_type == "Advanced":
        col_map = {"USG_PCT": "USG_PCT", "PACE": "PACE", "PIE": "PIE"}
    else:
        col_map = {
            "PTS": "PTS", "REB": "REB", "AST": "AST", "STL": "STL",
            "BLK": "BLK", "TOV": "TOV", "FGM": "FGM", "FGA": "FGA",
            "FG3M": "FG3M", "FTM": "FTM", "FTA": "FTA",
        }

    stats_by_id = {}
    name_to_id = {}
    for _, row in df.iterrows():
        pid = str(int(row["PLAYER_ID"]))
        stats_by_id[pid] = {col: float(row[nba_col]) if nba_col in df.columns else 0.0
                            for col, nba_col in col_map.items()}
        if measure_type == "Base":
            name_to_id[_normalize(str(row["PLAYER_NAME"]))] = pid
    return stats_by_id, name_to_id


def _get_all_stats_cached() -> tuple[dict, dict, dict]:
    """Return (season_stats, last15_stats, name_to_id) all keyed by str player_id.
    season_stats includes advanced metrics (USG_PCT, PACE, PIE) merged in."""
    season = _current_season()

    def fetch_season():
        stats, name_map = _fetch_all_stats(last_n_games=0, measure_type="Base")
        return {"stats": stats, "name_to_id": name_map}

    def fetch_last15():
        stats, _ = _fetch_all_stats(last_n_games=15, measure_type="Base")
        return stats

    def fetch_advanced():
        stats, _ = _fetch_all_stats(last_n_games=0, measure_type="Advanced")
        return stats

    season_data = cached_call(f"all_stats_season_{season}", NBA_TTL, fetch_season)
    last15_stats = cached_call(f"all_stats_last15_{season}", NBA_TTL, fetch_last15)
    adv_stats = cached_call(f"all_stats_advanced_{season}", NBA_TTL, fetch_advanced)

    # Merge advanced stats (USG_PCT, PACE, PIE) into season stats
    season_stats = season_data["stats"]
    for pid, adv in adv_stats.items():
        if pid in season_stats:
            season_stats[pid].update(adv)

    return season_stats, last15_stats, season_data["name_to_id"]


def get_player_stats(player_name: str) -> dict | None:
    """
    Return per-game stat averages for a player.
    season dict includes USG_PCT, PACE, PIE from advanced stats.
    Returns {"season": {...}, "last_15": {...}} or None if not found.
    """
    season_all, last15_all, name_to_id = _get_all_stats_cached()

    key = None
    player_id = get_player_id(player_name)
    if player_id is not None:
        key = str(player_id)

    if key is None or key not in season_all:
        key = name_to_id.get(_normalize(player_name))

    if key is None or key not in season_all:
        print(f"Warning: no stats found for {player_name}")
        return None

    return {"season": season_all[key], "last_15": last15_all.get(key, season_all[key])}


def batch_get_player_stats(players: list[dict]) -> list[dict]:
    """Fetch stats for a list of player dicts. Each dict must have 'name'."""
    return [{**p, "stats": get_player_stats(p["name"])} for p in players]


def get_week_games_detail(team_abbr: str, week_start: str, week_end: str) -> dict:
    """
    Return detailed game info for a team this week.
    Returns {"total": int, "b2b_count": int, "dates": [...], "opponents": [...]}.
    b2b_count = number of games that are the 2nd game of a back-to-back.
    """
    import requests
    from datetime import datetime

    season = _current_season()

    def fetch():
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
            games = []
            for gd in data["leagueSchedule"]["gameDates"]:
                gdate = datetime.strptime(gd["gameDate"], "%m/%d/%Y %H:%M:%S")
                if start <= gdate <= end:
                    for game in gd["games"]:
                        home = game["homeTeam"]["teamTricode"]
                        away = game["awayTeam"]["teamTricode"]
                        if home == abbr:
                            games.append((gdate.date(), away))
                        elif away == abbr:
                            games.append((gdate.date(), home))
            games.sort()
            game_dates = [str(g[0]) for g in games]
            opponents = [g[1] for g in games]
            b2b = sum(
                1 for i in range(1, len(games))
                if (games[i][0] - games[i - 1][0]).days == 1
            )
            return {"total": len(games), "b2b_count": b2b, "dates": game_dates, "opponents": opponents}
        except Exception as e:
            print(f"Warning: schedule fetch failed for {team_abbr}: {e}")
            return {"total": 0, "b2b_count": 0, "dates": [], "opponents": []}

    return cached_call(f"games_detail_{season}_{team_abbr}_{week_start}_{week_end}", NBA_TTL, fetch)


def get_games_this_week(team_abbr: str, week_start: str, week_end: str) -> int:
    """Return number of games this week. Wraps get_week_games_detail."""
    return get_week_games_detail(team_abbr, week_start, week_end)["total"]


def get_team_def_factors() -> dict:
    """
    Return {team_abbr: factor} where factor > 1.0 = weak defense (good for offensive players).
    Computed as league_avg_drtg / team_drtg, so poor defenses score above 1.0.
    """
    season = _current_season()

    def fetch():
        from nba_api.stats.endpoints import leaguedashteamstats
        time.sleep(1.0)
        df = leaguedashteamstats.LeagueDashTeamStats(
            season=season,
            per_mode_simple="PerGame",
            measure_type_detailed_defense="Advanced",
            timeout=60,
        ).get_data_frames()[0]
        avg = float(df["DEF_RATING"].mean())
        return {
            str(row["TEAM_ABBREVIATION"]): round(avg / float(row["DEF_RATING"]), 4)
            for _, row in df.iterrows()
            if float(row["DEF_RATING"]) > 0
        }

    return cached_call(f"team_def_factors_{season}", NBA_TTL, fetch)


def get_matchup_factor(team_abbr: str, week_start: str, week_end: str) -> float:
    """
    Return average defensive factor of opponents this week.
    >1.0 = favorable schedule (weak defenses), <1.0 = tough defensive schedule.
    """
    def_factors = get_team_def_factors()
    detail = get_week_games_detail(team_abbr, week_start, week_end)
    opponents = detail.get("opponents", [])
    if not opponents:
        return 1.0
    factors = [def_factors.get(opp, 1.0) for opp in opponents]
    return round(sum(factors) / len(factors), 4)


def get_player_game_log(player_name: str, last_n: int = 15) -> list[dict]:
    """Return per-game stat dicts for a player's last N games (used for consistency scoring)."""
    season = _current_season()
    player_id = get_player_id(player_name)

    if player_id is None:
        _, _, name_to_id = _get_all_stats_cached()
        pid_str = name_to_id.get(_normalize(player_name))
        player_id = int(pid_str) if pid_str else None

    if player_id is None:
        return []

    def fetch():
        from nba_api.stats.endpoints import playergamelog
        time.sleep(1.0)
        try:
            df = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season,
                timeout=60,
            ).get_data_frames()[0].head(last_n)
            col_map = {
                "PTS": "PTS", "REB": "REB", "AST": "AST", "STL": "STL",
                "BLK": "BLK", "TOV": "TOV", "FGM": "FGM", "FGA": "FGA",
                "FG3M": "FG3M", "FTM": "FTM", "FTA": "FTA",
            }
            return [
                {col: float(row[nba_col]) if nba_col in df.columns else 0.0
                 for col, nba_col in col_map.items()}
                for _, row in df.iterrows()
            ]
        except Exception as e:
            print(f"Warning: game log fetch failed for {player_name}: {e}")
            return []

    return cached_call(f"gamelog_{season}_{player_id}_{last_n}", NBA_TTL, fetch)
