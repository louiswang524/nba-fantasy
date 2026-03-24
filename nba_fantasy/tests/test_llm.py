# tests/test_llm.py
from unittest.mock import MagicMock, patch
import pytest
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

def test_ask_gemini_raises_on_missing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        ask_gemini("test")

def test_ask_gemini_raises_on_empty_response(monkeypatch):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = ""
    mock_client.models.generate_content.return_value = mock_response
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
    with patch("fantasy.llm.genai.Client", return_value=mock_client):
        with pytest.raises(ValueError, match="empty or malformed"):
            ask_gemini("test")
