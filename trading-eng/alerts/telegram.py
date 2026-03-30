from __future__ import annotations
import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from telegram import Bot
from telegram.error import TelegramError

from signals.base import SignalResult
from signals.technical.regime_gate import RegimeStatus
from state.dedup import DedupStore

logger = logging.getLogger(__name__)

_STRENGTH_EMOJI = {"strong": "🚨", "moderate": "⚠️"}
_DIRECTION_EMOJI = {"bullish": "📈", "bearish": "📉", "neutral": "👀"}
_REGIME_LABELS = {
    RegimeStatus.UPTREND:   "SPY UPTREND ✅",
    RegimeStatus.DOWNTREND: "SPY DOWNTREND ⚠️",
    RegimeStatus.UNKNOWN:   "Regime UNKNOWN",
}


def format_alert_message(result: SignalResult, regime: Optional[RegimeStatus]) -> str:
    strength_emoji = _STRENGTH_EMOJI.get(result.strength, "⚡")
    direction_emoji = _DIRECTION_EMOJI.get(result.direction, "")
    horizon_label = result.time_horizon.capitalize()
    regime_label = _REGIME_LABELS.get(regime, "Regime N/A") if regime else "Regime N/A"
    conditions_text = "\n".join(f"  ✅ {c}" for c in result.conditions)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M ET")

    return (
        f"{strength_emoji} {result.strength.upper()} {result.direction.upper()} "
        f"| {result.ticker} | {horizon_label}\n\n"
        f"📊 Signal: {result.signal_name}\n"
        f"⏱ Horizon: {horizon_label}\n"
        f"💰 Price: ${result.price:.2f}\n"
        f"{direction_emoji} Conditions met:\n{conditions_text}\n\n"
        f"🌍 Market Regime: {regime_label}\n"
        f"🕐 Detected: {timestamp}"
    )


def format_summary_message(scanned: int, fired: int, timestamp: str) -> str:
    return f"📋 Scan complete: {scanned} tickers scanned | {fired} signals fired | {timestamp}"


class TelegramDispatcher:
    def __init__(self, token: str, chat_id: str, dedup: DedupStore) -> None:
        self._bot = Bot(token=token)
        self._chat_id = chat_id
        self._dedup = dedup

    async def _send(self, text: str) -> None:
        try:
            await self._bot.send_message(chat_id=self._chat_id, text=text)
        except TelegramError as e:
            logger.error(f"Telegram send failed: {e}")

    async def dispatch(
        self,
        results: list[SignalResult],
        regime: Optional[RegimeStatus],
        total_scanned: int,
    ) -> int:
        """Send alerts for non-deduplicated results. Returns count of alerts sent."""
        sent = 0
        for result in results:
            if self._dedup.already_fired(result):
                continue
            msg = format_alert_message(result, regime)
            await self._send(msg)
            self._dedup.mark_fired(result)
            sent += 1

        timestamp = datetime.now().strftime("%H:%M ET")
        summary = format_summary_message(total_scanned, sent, timestamp)
        await self._send(summary)
        return sent


def create_dispatcher() -> TelegramDispatcher:
    """Build dispatcher from environment variables."""
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    dedup = DedupStore()
    return TelegramDispatcher(token=token, chat_id=chat_id, dedup=dedup)
