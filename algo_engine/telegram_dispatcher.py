"""
algo_engine.telegram_dispatcher — Market-Wise Telegram Alert Dispatcher
=======================================================================

Dispatches live Telegram alerts formatted in HTML. Routes dynamically based
on symbol market category (NIFTY, MCX, NYMEX, CRYPTO, FOREX, WORLD).

CRITICAL USER MANDATE (from AGENTS.md):
    Telegram alerts must NEVER fire for unexecuted limit orders ('ACTIVE LIMIT' / 'OPEN').
    Telegram alerts fire ONLY when:
        1. A limit trade actually fills (⚡ TRADE ACTIVE)
        2. Trailing stop updates (🎯 TRAILING STOP UPDATE)
        3. Trade closes (🛑 TRADE CLOSED with exact_pct)
"""

from __future__ import annotations
import os
import json
import logging
from typing import Dict, Optional
import urllib.request
import urllib.error
from dotenv import load_dotenv

from .trade_manager import Trade, TradeStatus, TradeOutcome
from .feeds import normalize_symbol, get_market_category

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


class TelegramDispatcher:
    """
    Market-Wise Telegram Alert Dispatcher.
    
    Dynamically routes notifications to dedicated market channels.
    Strictly filters out unexecuted limit orders.
    """

    TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self,
                 bot_token: Optional[str] = None,
                 chat_id_map: Optional[Dict[str, str]] = None,
                 enabled: bool = True):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.enabled = enabled and bool(self.bot_token)

        # Dynamic channel routing per AGENTS.md
        self.chat_id_map = chat_id_map or {
            "NIFTY": os.getenv("TELEGRAM_CHAT_ID_NIFTY") or os.getenv("TELEGRAM_CHAT_ID_STOCKS", ""),
            "MCX": os.getenv("TELEGRAM_CHAT_ID_MCX", ""),
            "NYMEX": os.getenv("TELEGRAM_CHAT_ID_NYMEX") or os.getenv("TELEGRAM_CHAT_ID", ""),
            "CRYPTO": os.getenv("TELEGRAM_CHAT_ID_CRYPTO", ""),
            "FOREX": os.getenv("TELEGRAM_CHAT_ID_FOREX", ""),
            "WORLD": os.getenv("TELEGRAM_CHAT_ID_WORLD", ""),
        }
        self.fire_chat_id = os.getenv("TELEGRAM_CHAT_ID_FIRE") or os.getenv("TELEGRAM_CHAT_ID_FIRE_ALERT", "")

        if not self.bot_token:
            logger.info("[TelegramDispatcher] TELEGRAM_BOT_TOKEN not set. Telegram alerts disabled.")

    def get_chat_id(self, symbol: str) -> Optional[str]:
        """Resolve Telegram Chat ID based on canonical market category."""
        clean = normalize_symbol(symbol)
        mkt = get_market_category(clean)
        chat_id = self.chat_id_map.get(mkt)

        # Fallback for general channel if market-specific not configured
        if not chat_id:
            chat_id = os.getenv("TELEGRAM_CHAT_ID")

        return chat_id

    # ── High-Level Lifecycle Dispatchers ──────────────────────────

    def on_trade_fill(self, trade: Trade) -> bool:
        """
        Dispatches '⚡ TRADE ACTIVE' alert when a limit order fills.
        
        Mandate: Fires ONLY on fill, NEVER on limit placement.
        """
        if not self.enabled:
            return False

        direction_emoji = "🟢" if trade.is_long else "🔴"
        sym = trade.symbol
        mkt = get_market_category(sym)
        fire_badge = " | 🔥 <b>FIRE ALERT</b>" if getattr(trade, 'fire_alert', False) else ""

        msg = (
            f"<b>⚡ TRADE ACTIVE ({mkt})</b>{fire_badge}\n\n"
            f"<b>Symbol:</b> <code>{sym}</code>\n"
            f"<b>Setup:</b> {direction_emoji} <b>{trade.name}</b>\n"
            f"<b>Entry Price:</b> <code>{trade.entry_price}</code>\n"
            f"<b>Stop Loss:</b> <code>{trade.initial_sl}</code>\n"
            f"<b>Target 1:</b> <code>{trade.tp1}</code>\n"
            f"<b>Target 2:</b> <code>{trade.tp2}</code>\n"
            f"<b>Target 3:</b> <code>{trade.tp3}</code>\n"
            f"<b>Target 4:</b> <code>{trade.tp4}</code>\n\n"
            f"<i>Engine: TLCS Black Box v2.0 (Shadow Mode)</i>"
        )

        return self.send_message(sym, msg)

    def on_fire_alert(self, signal_or_trade, symbol: str = "") -> bool:
        """
        Dispatches dedicated '🔥 TLCS FIRE ALERT' alert.
        Routes to the market channel and dedicated fire channel if configured.
        """
        if not self.enabled:
            return False

        sym = symbol or getattr(signal_or_trade, 'symbol', '')
        clean = normalize_symbol(sym)
        mkt = get_market_category(clean)

        direction = getattr(signal_or_trade, 'direction', '')
        is_long = direction.upper() == "LONG" or getattr(signal_or_trade, 'is_long', False)
        direction_emoji = "🟢 ▲" if is_long else "🔴 ▼"
        name = getattr(signal_or_trade, 'name', 'SIGNAL')
        entry = getattr(signal_or_trade, 'entry_price', 0.0)
        sl = getattr(signal_or_trade, 'stop_loss', None) or getattr(signal_or_trade, 'initial_sl', 0.0)
        tp1 = getattr(signal_or_trade, 'tp1', 0.0)
        tp2 = getattr(signal_or_trade, 'tp2', 0.0)
        fire_zone = getattr(signal_or_trade, 'fire_zone', 'FIREZONE') or 'FIREZONE'
        opening_bias = getattr(signal_or_trade, 'opening_bias', '')
        day_type = getattr(signal_or_trade, 'day_type', '')

        bias_str = f"\n<b>Bias:</b> <code>{opening_bias}</code>" if opening_bias else ""
        day_str = f" | <b>Day:</b> <code>{day_type}</code>" if day_type else ""
        tp2_str = f"\n<b>Target 2:</b> <code>{tp2}</code>" if tp2 else ""

        msg = (
            f"<b>🔥 TLCS FIRE ALERT ({mkt})</b>\n\n"
            f"<b>Symbol:</b> <code>{sym}</code>\n"
            f"<b>Signal:</b> {direction_emoji} <b>{name}</b>\n"
            f"<b>Entry Price:</b> <code>{entry}</code>\n"
            f"<b>Stop Loss:</b> <code>{sl}</code>\n"
            f"<b>Target 1:</b> <code>{tp1}</code>"
            f"{tp2_str}"
            f"{bias_str}{day_str}\n"
            f"<b>Firezone:</b> <code>{fire_zone}</code>\n\n"
            f"<i>High-probability confluence alert generated inside Firezone.</i>"
        )

        sent = self.send_message(sym, msg)

        # Also dispatch to dedicated Fire Alert channel if configured and distinct
        if self.fire_chat_id:
            market_chat_id = self.get_chat_id(sym)
            if self.fire_chat_id != market_chat_id:
                self.send_raw_message(self.fire_chat_id, msg)

        return sent


    def on_trail_update(self, trade: Trade) -> bool:
        """Dispatches trailing stop adjustment notification."""
        if not self.enabled:
            return False

        sym = trade.symbol
        msg = (
            f"<b>🎯 TRAILING STOP UPDATE</b>\n\n"
            f"<b>Symbol:</b> <code>{sym}</code>\n"
            f"<b>Setup:</b> <b>{trade.name}</b>\n"
            f"<b>New Trailing Stop:</b> <code>{trade.current_sl}</code>\n"
            f"<b>Status:</b> <code>{trade.status.value}</code>\n"
            f"<b>Entry:</b> <code>{trade.entry_price}</code>\n\n"
            f"<i>Stop loss advanced to lock in profits.</i>"
        )
        return self.send_message(sym, msg)

    def on_trade_close(self, trade: Trade) -> bool:
        """
        Dispatches trade settlement alert with exact percentage return.
        """
        if not self.enabled:
            return False

        pct = trade.exact_pct or 0.0
        pct_str = f"{pct:+.2f}%"

        outcome = trade.outcome
        if outcome == TradeOutcome.WIN:
            emoji = "🏆 WIN"
        elif outcome == TradeOutcome.LOSS:
            emoji = "🛑 LOSS"
        elif outcome == TradeOutcome.BREAKEVEN:
            emoji = "⚖️ BREAKEVEN"
        else:
            emoji = "⚪ CANCELLED"

        sym = trade.symbol
        msg = (
            f"<b>{emoji} — TRADE CLOSED</b>\n\n"
            f"<b>Symbol:</b> <code>{sym}</code>\n"
            f"<b>Setup:</b> <b>{trade.name}</b>\n"
            f"<b>Exit Level:</b> <code>{trade.exit_level}</code>\n"
            f"<b>Exit Price:</b> <code>{trade.exit_price}</code>\n"
            f"<b>Entry Price:</b> <code>{trade.entry_price}</code>\n"
            f"<b>Realized Return:</b> <b>{pct_str}</b>\n\n"
            f"<i>Exact Return Formula: ((Exit - Entry) / Entry) * 100</i>"
        )
        return self.send_message(sym, msg)

    def send_raw_message(self, chat_id: str, html_text: str) -> bool:
        """
        Send formatted message directly to a specified Telegram chat ID.
        """
        if not self.enabled or not self.bot_token or not chat_id:
            return False

        url = self.TELEGRAM_API_URL.format(token=self.bot_token)
        payload = {
            "chat_id": chat_id,
            "text": html_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    logger.info(f"[TelegramDispatcher] Alert sent successfully to {chat_id}")
                    return True
                else:
                    logger.error(f"[TelegramDispatcher] Telegram API returned HTTP {response.status}")
                    return False
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            logger.error(f"[TelegramDispatcher] Telegram HTTP Error: {err_body}")
            return False
        except Exception as e:
            logger.error(f"[TelegramDispatcher] Error dispatching Telegram alert: {e}")
            return False

    def send_message(self, symbol: str, html_text: str) -> bool:
        """
        Send formatted message to the resolved Telegram channel for a symbol.
        """
        if not self.enabled or not self.bot_token:
            return False

        chat_id = self.get_chat_id(symbol)
        if not chat_id:
            logger.debug(f"[TelegramDispatcher] No chat ID configured for symbol: {symbol}")
            return False

        return self.send_raw_message(chat_id, html_text)

