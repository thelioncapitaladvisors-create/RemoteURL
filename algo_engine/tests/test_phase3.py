"""
Unit Tests for Phase 3: Headless Daemon & Shadow Database Pipeline
==================================================================

Tests:
    1. ShadowPipeline record lifecycle (signal -> fill -> trail -> close)
    2. Exact percentage injection in metadata
    3. ShadowPipeline local storage fallback
    4. TelegramDispatcher HTML message formatting & market channel routing
    5. Strict Telegram rule: No alerts for unexecuted limits (active trades only)
    6. EngineDaemon end-to-end event coordination
"""

import sys
import os
import json
import time
import unittest
from typing import List, Dict, Any

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from algo_engine.pivots import OHLC
from algo_engine.strategies import StrategySignal
from algo_engine.trade_manager import Trade, TradeStatus, TradeOutcome
from algo_engine.feeds import Tick
from algo_engine.shadow_pipeline import ShadowPipeline
from algo_engine.telegram_dispatcher import TelegramDispatcher
from algo_engine.engine_daemon import EngineDaemon


class TestShadowPipeline(unittest.TestCase):

    def setUp(self):
        self.fallback_file = "algo_engine/data/test_shadow_signals.json"
        if os.path.exists(self.fallback_file):
            os.remove(self.fallback_file)
        # Initialize in pure local mode by pointing to invalid Supabase or empty table
        self.pipeline = ShadowPipeline(
            supabase_url=None,
            supabase_key=None,
            disable_supabase=True,
            local_fallback_path=self.fallback_file,
        )

    def tearDown(self):
        if os.path.exists(self.fallback_file):
            os.remove(self.fallback_file)

    def test_record_signal(self):
        """Signal creation stores proper shadow schema."""
        sig = StrategySignal(
            name="LONG LIGHTNING",
            direction="LONG",
            entry_price=2850.0,
            stop_loss=2835.0,
            tp1=2880.0,
            tp2=2900.0,
            tp3=2925.0,
            tp4=2950.0,
            bar_index=1,
            zone="LONG ZONE",
            opening_bias="IN RANGE IN VALUE",
            day_type="TREND DAY",
        )

        trade_id = self.pipeline.record_signal(sig, "NSE:RELIANCE")
        self.assertIsNotNone(trade_id)

        records = self.pipeline.get_recent_signals(limit=10)
        self.assertEqual(len(records), 1)
        row = records[0]

        self.assertEqual(row["symbol"], "RELIANCE")
        self.assertEqual(row["type"], "LONG LIGHTNING")
        self.assertEqual(row["entry"], 2850.0)
        self.assertEqual(row["stop"], 2835.0)
        self.assertEqual(row["target"], 2880.0)
        self.assertEqual(row["status"], "OPEN")
        self.assertEqual(row["outcome"], "OPEN")
        self.assertEqual(row["pricing_type"], "SHADOW")
        self.assertEqual(row["source"], "BLACKBOX")
        self.assertEqual(row["exchange"], "NIFTY")

    def test_record_fill(self):
        """Fill event updates status to '⚡ TRADE ACTIVE'."""
        sig = StrategySignal("LONG SCALP", "LONG", 100.0, 95.0, 110.0, 120.0, 130.0, 140.0, 0)
        trade_id = self.pipeline.record_signal(sig, "BTCUSDT")

        trade = Trade(
            trade_id=trade_id,
            name="LONG SCALP",
            direction="LONG",
            symbol="BTCUSDT",
            entry_price=100.0,
            has_hit_entry=True,
            status=TradeStatus.ACTIVE,
        )

        self.pipeline.record_fill(trade)
        records = self.pipeline.get_recent_signals(limit=1)
        self.assertEqual(records[0]["status"], "⚡ TRADE ACTIVE")
        self.assertEqual(records[0]["trigger"], "TradeFill")
        self.assertIn("real_entry_time", records[0]["metadata"])

    def test_record_trade_close_with_exact_pct(self):
        """Settlement injects exact_pct into metadata."""
        sig = StrategySignal("SHORT MISSILE", "SHORT", 100.0, 105.0, 90.0, 80.0, 70.0, 60.0, 0)
        trade_id = self.pipeline.record_signal(sig, "CL")

        trade = Trade(
            trade_id=trade_id,
            name="SHORT MISSILE",
            direction="SHORT",
            symbol="CL",
            entry_price=100.0,
            exit_price=90.0,
            has_hit_entry=True,
            is_closed=True,
            exit_level="TP1",
            exact_pct=10.0,  # +10% gain on short
        )

        self.pipeline.record_trade_close(trade)
        records = self.pipeline.get_recent_signals(limit=1)
        row = records[0]

        self.assertEqual(row["outcome"], "WIN")
        self.assertEqual(row["exit_price"], 90.0)
        self.assertEqual(row["metadata"]["exact_pct"], 10.0)
        self.assertEqual(row["metadata"]["exit_level"], "TP1")


class TestTelegramDispatcher(unittest.TestCase):

    def setUp(self):
        self.chat_map = {
            "NIFTY": "-100111111",
            "MCX": "-100222222",
            "NYMEX": "-100333333",
            "CRYPTO": "-100444444",
            "FOREX": "-100555555",
            "WORLD": "-100666666",
        }
        self.dispatcher = TelegramDispatcher(
            bot_token="test_mock_token_123456",
            chat_id_map=self.chat_map,
            enabled=True,
        )

    def test_market_channel_routing(self):
        """Verify dynamic chat ID resolution per canonical market."""
        self.assertEqual(self.dispatcher.get_chat_id("RELIANCE"), "-100111111")
        self.assertEqual(self.dispatcher.get_chat_id("CRUDEOIL"), "-100222222")
        self.assertEqual(self.dispatcher.get_chat_id("CL"), "-100333333")
        self.assertEqual(self.dispatcher.get_chat_id("BTCUSDT"), "-100444444")
        self.assertEqual(self.dispatcher.get_chat_id("EURUSD"), "-100555555")
        self.assertEqual(self.dispatcher.get_chat_id("NAS100"), "-100666666")

    def test_strict_active_trades_only_mandate(self):
        """TelegramDispatcher does NOT provide an 'on_limit_create' method, preventing unexecuted limit spam."""
        # Method must not exist to uphold zero unexecuted limit spam rule
        self.assertFalse(hasattr(self.dispatcher, "on_limit_created"))
        self.assertFalse(hasattr(self.dispatcher, "on_signal_open"))

    def test_message_formatting(self):
        """Verify HTML formatting contains required badges and formulas."""
        trade = Trade(
            trade_id="t1",
            name="LONG LIGHTNING",
            direction="LONG",
            symbol="BTCUSDT",
            entry_price=65000.0,
            initial_sl=64000.0,
            current_sl=65000.0,
            tp1=67000.0,
            tp2=68500.0,
            tp3=70000.0,
            tp4=72000.0,
            exit_price=67000.0,
            exact_pct=3.08,
            exit_level="TP1",
            is_closed=True,
        )

        # Mock send_message to inspect text payload
        sent_messages = []
        self.dispatcher.send_message = lambda sym, text: sent_messages.append((sym, text)) or True

        # Test Fill
        self.dispatcher.on_trade_fill(trade)
        self.assertEqual(len(sent_messages), 1)
        sym, text = sent_messages[0]
        self.assertEqual(sym, "BTCUSDT")
        self.assertIn("⚡ TRADE ACTIVE", text)
        self.assertIn("65000.0", text)

        # Test Close
        self.dispatcher.on_trade_close(trade)
        self.assertEqual(len(sent_messages), 2)
        _, text_close = sent_messages[1]
        self.assertIn("🏆 WIN — TRADE CLOSED", text_close)
        self.assertIn("+3.08%", text_close)
        self.assertIn("((Exit - Entry) / Entry) * 100", text_close)


class TestEngineDaemon(unittest.TestCase):

    def test_daemon_lifecycle(self):
        """EngineDaemon starts, subscribes, and stops cleanly."""
        daemon = EngineDaemon(
            mock_mode=True,
            active_markets=["NIFTY", "CRYPTO"],
            enable_telegram=False,
            enable_supabase=False,
        )

        daemon.start()
        self.assertTrue(daemon._running)
        time.sleep(0.2)
        daemon.stop()
        self.assertFalse(daemon._running)

    def test_daemon_tick_handling(self):
        """Live ticks are evaluated by daemon trade manager."""
        daemon = EngineDaemon(
            mock_mode=True,
            active_markets=["NIFTY"],
            enable_telegram=False,
            enable_supabase=False,
        )

        sig = StrategySignal(
            name="LONG SCALP",
            direction="LONG",
            entry_price=100.0,
            stop_loss=95.0,
            tp1=110.0, tp2=120.0, tp3=130.0, tp4=140.0,
            bar_index=0
        )
        trade = daemon.trade_manager.create_trade(sig, symbol="RELIANCE")

        # Simulate tick reaching entry (100.0) on bar_index 1
        tick = Tick(symbol="RELIANCE", price=99.5, volume=10.0, market="NIFTY")
        daemon._on_live_tick(tick)

        self.assertTrue(trade.has_hit_entry, "Trade must fill on tick matching entry level")


if __name__ == '__main__':
    unittest.main(verbosity=2)
