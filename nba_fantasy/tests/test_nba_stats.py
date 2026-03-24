# tests/test_nba_stats.py
from unittest.mock import patch
import datetime
from fantasy.nba_stats import _current_season


def test_current_season_during_regular_season():
    """Jan-Sep: season started previous October."""
    with patch("fantasy.nba_stats.date") as mock_date:
        mock_date.today.return_value = datetime.date(2026, 3, 15)
        assert _current_season() == "2025-26"


def test_current_season_after_october():
    """Oct+: new season has started."""
    with patch("fantasy.nba_stats.date") as mock_date:
        mock_date.today.return_value = datetime.date(2025, 11, 1)
        assert _current_season() == "2025-26"


def test_current_season_september_edge():
    """Sep is still the previous season."""
    with patch("fantasy.nba_stats.date") as mock_date:
        mock_date.today.return_value = datetime.date(2025, 9, 30)
        assert _current_season() == "2024-25"


def test_current_season_october_edge():
    """Oct 1 starts the new season."""
    with patch("fantasy.nba_stats.date") as mock_date:
        mock_date.today.return_value = datetime.date(2025, 10, 1)
        assert _current_season() == "2025-26"
