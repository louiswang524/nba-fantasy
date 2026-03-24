from typing import Any

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
    for col in my:  # iterate caller-supplied keys (supports full STAT_COLS or subset)
        m, o = my.get(col, 0.0), opp.get(col, 0.0)
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
