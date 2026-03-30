from signals.base import SignalResult
from alerts.telegram import format_alert_message, format_summary_message
from signals.technical.regime_gate import RegimeStatus


def make_result(**kwargs) -> SignalResult:
    defaults = dict(
        ticker="AAPL",
        signal_name="Oversold Confluence",
        time_horizon="swing",
        strength="strong",
        direction="bullish",
        conditions=["RSI(14) = 28.4 (oversold)", "Volume 3.2× avg", "Price at BB lower"],
        price=187.42,
    )
    defaults.update(kwargs)
    return SignalResult(**defaults)


def test_format_alert_contains_ticker():
    msg = format_alert_message(make_result(), regime=RegimeStatus.UPTREND)
    assert "AAPL" in msg


def test_format_alert_contains_signal_name():
    msg = format_alert_message(make_result(), regime=RegimeStatus.UPTREND)
    assert "Oversold Confluence" in msg


def test_format_alert_contains_conditions():
    msg = format_alert_message(make_result(), regime=RegimeStatus.UPTREND)
    assert "RSI(14)" in msg
    assert "Volume" in msg


def test_format_alert_shows_regime():
    msg = format_alert_message(make_result(), regime=RegimeStatus.UPTREND)
    assert "UPTREND" in msg

    msg_down = format_alert_message(make_result(), regime=RegimeStatus.DOWNTREND)
    assert "DOWNTREND" in msg_down


def test_format_summary():
    msg = format_summary_message(scanned=503, fired=7, timestamp="10:15 ET")
    assert "503" in msg
    assert "7" in msg
    assert "10:15 ET" in msg
