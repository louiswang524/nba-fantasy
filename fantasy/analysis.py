import statistics

STAT_COLS = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FGM", "FGA", "FG3M", "FTM", "FTA"]


def blend_stats(season: dict, last_15: dict) -> dict:
    """Blend season (30%) and last-15-game (70%) per-game averages."""
    result = {}
    for col in STAT_COLS:
        s = season.get(col, 0.0)
        recent = last_15.get(col, 0.0)
        result[col] = s * 0.3 + recent * 0.7
    return result


def injury_multiplier(status: str) -> float:
    """Return projection multiplier based on Yahoo injury status."""
    if status in ("OUT", "INJ"):
        return 0.0
    if status in ("GTD", "Q"):
        return 0.75
    return 1.0


def project_player(
    stats: dict,
    games_info,           # int or dict from get_week_games_detail
    injury_status: str,
    matchup_factor: float = 1.0,
) -> dict:
    """
    Return projected category totals for a player.
    - games_info: int (simple count) or dict with {total, b2b_count, ...}
    - matchup_factor: >1.0 = weak opponent defense, <1.0 = tough defense
    - Applies B2B penalty (85% effectiveness for back-to-back games)
    - Applies team pace adjustment relative to league average (~100)
    """
    mult = injury_multiplier(injury_status)
    blended = blend_stats(stats["season"], stats["last_15"])

    # Game count with B2B penalty
    if isinstance(games_info, dict):
        total = games_info.get("total", 0)
        b2b = games_info.get("b2b_count", 0)
        effective_games = (total - b2b) + b2b * 0.85
    else:
        effective_games = float(games_info)

    # Pace adjustment: team pace relative to league average (~100 possessions/48min)
    player_pace = stats["season"].get("PACE", 100.0) or 100.0
    pace_factor = player_pace / 100.0

    scale = effective_games * mult * pace_factor * matchup_factor
    return {col: blended[col] * scale for col in STAT_COLS}


def project_team_categories(players: list[dict]) -> dict:
    """
    Sum projected category totals across all players.
    Player dicts support: games_detail (dict) or games_remaining (int), matchup_factor.
    """
    totals = {col: 0.0 for col in STAT_COLS}
    for p in players:
        if p.get("stats") is None:
            continue
        games_info = p.get("games_detail", p.get("games_remaining", 0))
        proj = project_player(
            p["stats"],
            games_info,
            p.get("status", ""),
            matchup_factor=p.get("matchup_factor", 1.0),
        )
        for col in STAT_COLS:
            totals[col] += proj[col]
    return totals


def classify_categories(my: dict, opp: dict, margin: float = 0.05) -> dict:
    """
    Classify each category as 'win', 'loss', or 'tossup'.
    Handles both raw (TOV) and Yahoo (TO) turnover category names.
    """
    result = {}
    for col in my:
        m, o = my.get(col, 0.0), opp.get(col, 0.0)
        total = (m + o) / 2 if (m + o) > 0 else 1
        diff = (m - o) / total
        if col in ("TOV", "TO"):
            diff = -diff  # lower turnovers is better
        if diff > margin:
            result[col] = "win"
        elif diff < -margin:
            result[col] = "loss"
        else:
            result[col] = "tossup"
    return result


def consistency_score(game_logs: list[dict]) -> dict:
    """Return per-stat std deviation across game logs. Higher = more volatile player."""
    if len(game_logs) < 2:
        return {col: 0.0 for col in STAT_COLS}
    return {
        col: statistics.stdev(g.get(col, 0.0) for g in game_logs)
        for col in STAT_COLS
    }


def usage_spike(stats: dict) -> float:
    """Return USG% change from season avg to last-15 games. Positive = expanding role."""
    season_usg = stats["season"].get("USG_PCT", 0.0) or 0.0
    last15_usg = stats["last_15"].get("USG_PCT", 0.0) or 0.0
    return round(last15_usg - season_usg, 1)


def trade_category_delta(
    give_stats: list[dict],
    receive_stats: list[dict],
    games_remaining: int,
) -> dict:
    """
    Compute per-category change if you give away give_stats and receive receive_stats.
    Returns delta dict: positive = gain, negative = loss.
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
