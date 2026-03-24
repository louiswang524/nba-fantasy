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
    give_stats = [{"season": {"PTS": 20.0, "REB": 5.0, "GP": 50}, "last_15": {"PTS": 30.0, "REB": 3.0, "GP": 15}}]
    receive_stats = [{"season": {"PTS": 5.0, "REB": 10.0, "GP": 50}, "last_15": {"PTS": 6.0, "REB": 12.0, "GP": 15}}]
    delta = trade_category_delta(give_stats, receive_stats, games_remaining=3)
    assert delta["PTS"] < 0   # losing points
    assert delta["REB"] > 0   # gaining rebounds
