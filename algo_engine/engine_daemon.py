"""
algo_engine.engine_daemon — Black Box Signal Engine Background Service Daemon
=============================================================================

Master background service coordinating:
    1. Real-time market feed ingestion (DhanHQ, Binance, Global)
    2. Multi-timeframe candle building (1m, 5m, 15m, Daily)
    3. Mathematical indicators & Day Type classification (Camarilla, CPR, EMAs, ATR)
    4. 12 Canonical Strategy triggers with H4/L4 gating
    5. Stateful trade lifecycle management (limits, fills, trailing stops, settlements)
    6. Supabase shadow pipeline syncing (`shadow_signals`)
    7. Market-wise Telegram alerting for active executions
"""

from __future__ import annotations
import os
import sys
import time
import signal
import logging
import argparse
from typing import Dict, List, Optional

from .pivots import (
    OHLC, compute_daily_levels, compute_emas_from_bars,
    compute_atr, compute_pivot_trend_emas
)
from .day_types import DayTypeClassifier, DayTypeResult
from .strategies import StrategyEngine, StrategySignal, MarketContext
from .trade_manager import TradeManager, Trade, TradeStatus
from .feeds import FeedManager, CandleAggregator, Tick, normalize_symbol, get_market_category
from .shadow_pipeline import ShadowPipeline
from .telegram_dispatcher import TelegramDispatcher

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("EngineDaemon")


class EngineDaemon:
    """
    Standalone Black Box Signal Engine Daemon.
    
    Coordinates the full event-driven quantitative trading pipeline.
    """

    def __init__(self,
                 mock_mode: bool = False,
                 active_markets: Optional[List[str]] = None,
                 enable_telegram: bool = True,
                 enable_supabase: bool = True):
        self.mock_mode = mock_mode
        self.active_markets = active_markets or ["NIFTY", "MCX", "CRYPTO", "NYMEX", "FOREX", "WORLD"]
        self.enable_telegram = enable_telegram
        self.enable_supabase = enable_supabase

        # Core Engines
        self.aggregator = CandleAggregator(timeframes=["1m", "5m", "15m", "1d"])
        self.feed_manager = FeedManager(aggregator=self.aggregator, mock_mode=mock_mode)
        self.strategy_engine = StrategyEngine()
        self.trade_manager = TradeManager()
        self.day_type_classifiers: Dict[str, DayTypeClassifier] = {}

        # Sinks
        self.shadow_pipeline = ShadowPipeline() if enable_supabase else None
        self.telegram = TelegramDispatcher(enabled=enable_telegram)

        # State tracking
        self._running = False
        self._start_time = time.time()
        self._active_trade_count = 0
        self._signals_generated = 0

        # Wire up event callbacks
        self.feed_manager.on_tick(self._on_live_tick)
        self.aggregator.on_bar_close(self._on_bar_close)

    # ── Pipeline Event Handlers ──────────────────────────────────

    def _on_live_tick(self, tick: Tick) -> None:
        """
        Handle incoming sub-second tick.
        Evaluates active trades in TradeManager for limit fills and stops.
        """
        sym = tick.symbol
        active_trades = [t for t in self.trade_manager.active_trades if t.symbol == sym]

        if not active_trades:
            return

        # Create lightweight synthetic bar from current tick for evaluation
        tick_bar = OHLC(
            open=tick.price,
            high=tick.price,
            low=tick.price,
            close=tick.price,
            volume=tick.volume,
        )

        for trade in active_trades:
            was_open_limit = not trade.has_hit_entry
            old_sl = trade.current_sl

            # Update trade state
            self.trade_manager.update(
                trade=trade,
                bar=tick_bar,
                bar_index=trade.signal_bar_index + 1,  # Safe subsequent bar indicator
            )

            # Check for limit fill transition
            if was_open_limit and trade.has_hit_entry:
                logger.info(f"[EngineDaemon] ⚡ TRADE ACTIVE: {trade.name} for {trade.symbol} filled at {trade.entry_price}")
                if self.shadow_pipeline:
                    self.shadow_pipeline.record_fill(trade)
                if self.telegram:
                    self.telegram.on_trade_fill(trade)

            # Check for trailing stop movement
            elif trade.has_hit_entry and trade.current_sl != old_sl and not trade.is_closed:
                logger.info(f"[EngineDaemon] 🎯 Trailing stop moved: {trade.symbol} to {trade.current_sl}")
                if self.shadow_pipeline:
                    self.shadow_pipeline.record_trail_update(trade)
                if self.telegram:
                    self.telegram.on_trail_update(trade)

            # Check for trade exit / closure
            elif trade.is_closed:
                logger.info(f"[EngineDaemon] 🛑 Trade closed: {trade.symbol} {trade.name} | Outcome: {trade.outcome.value} | Return: {trade.exact_pct}%")
                if self.shadow_pipeline:
                    self.shadow_pipeline.record_trade_close(trade)
                if self.telegram:
                    self.telegram.on_trade_close(trade)

    def _on_bar_close(self, symbol: str, timeframe: str, bar: OHLC) -> None:
        """
        Handle finalized candle event.
        Executes indicators, Day Types, and 12 Strategy Triggers.
        """
        if timeframe == "1d":
            self._handle_daily_bar_close(symbol, bar)
        elif timeframe == "15m":
            self._handle_15m_bar_close(symbol, bar)

    def _handle_daily_bar_close(self, symbol: str, bar: OHLC) -> None:
        """Execute Daily Day Type Blueprint & Sequence classifiers."""
        if symbol not in self.day_type_classifiers:
            self.day_type_classifiers[symbol] = DayTypeClassifier()

        classifier = self.day_type_classifiers[symbol]
        result: DayTypeResult = classifier.evaluate(bar)

        if result.has_any_signal():
            blueprints = result.get_active_blueprints()
            sequences = result.get_active_sequences()
            logger.info(f"[EngineDaemon] Day Type Update for {symbol}: Blueprints={blueprints}, Sequences={sequences}")

    def _handle_15m_bar_close(self, symbol: str, bar: OHLC) -> None:
        """Execute 15-minute Strategy Triggers."""
        bars_15m = self.aggregator.get_bars(symbol, "15m")
        bars_daily = self.aggregator.get_bars(symbol, "1d")

        # Need prior daily bar for Camarilla & CPR levels
        if not bars_daily:
            # Bootstrap with current 15m bar if daily history is not yet populated
            prev_high, prev_low, prev_close = bar.high, bar.low, bar.close
        else:
            prev_day = bars_daily[-1]
            prev_high, prev_low, prev_close = prev_day.high, prev_day.low, prev_day.close

        # 1. Compute Daily Camarilla & CPR Levels
        daily_levels = compute_daily_levels(prev_high, prev_low, prev_close)

        # 2. Compute Intraday Indicators (EMAs on Typical Price, ATR)
        if len(bars_15m) >= 14:
            short_emas, med_emas, _ = compute_emas_from_bars(bars_15m)
            p_fast, p_slow = compute_pivot_trend_emas(bars_15m)
            atrs = compute_atr(bars_15m, period=14)

            short_ema = short_emas[-1]
            med_ema = med_emas[-1]
            pivot_trend_fast = p_fast[-1]
            pivot_trend_slow = p_slow[-1]
            atr_val = atrs[-1]
        else:
            short_ema = bar.typical_price
            med_ema = bar.typical_price
            pivot_trend_fast = bar.typical_price
            pivot_trend_slow = bar.typical_price
            atr_val = max(bar.range, 1.0)

        # 3. Assemble MarketContext
        ctx = MarketContext(
            bar=bar,
            bar_index=len(bars_15m),
            H4=daily_levels.camarilla.H4,
            L4=daily_levels.camarilla.L4,
            H3=daily_levels.camarilla.H3,
            L3=daily_levels.camarilla.L3,
            cpr_pivot=daily_levels.cpr.pivot,
            cpr_tc=daily_levels.cpr.tc,
            cpr_bc=daily_levels.cpr.bc,
            is_ncpr=daily_levels.cpr.is_narrow,
            short_ema=short_ema,
            med_ema=med_ema,
            pivot_trend_fast=pivot_trend_fast,
            pivot_trend_slow=pivot_trend_slow,
            atr=atr_val,
            session_highest=max((b.high for b in bars_15m[-10:]), default=bar.high),
            session_lowest=min((b.low for b in bars_15m[-10:]), default=bar.low),
        )

        # 4. Evaluate Strategy Triggers (with H4/L4 Touch-Point Gating)
        new_signals = self.strategy_engine.evaluate(ctx)

        for sig in new_signals:
            self._signals_generated += 1
            logger.info(
                f"[EngineDaemon] 🚀 SIGNAL TRIGGERED: {sig.name} for {symbol} | "
                f"Entry={sig.entry_price}, SL={sig.stop_loss}, TP1={sig.tp1}"
            )

            # Create stateful trade in TradeManager
            trade = self.trade_manager.create_trade(sig, symbol=symbol)

            # Sync limit placement to Supabase shadow table
            if self.shadow_pipeline:
                self.shadow_pipeline.record_signal(sig, symbol=symbol)

    # ── Daemon Lifecycle Controls ────────────────────────────────

    def start(self) -> None:
        """Start daemon and data feeds."""
        logger.info(f"=== TLCS Black Box Signal Engine Daemon v2.0 ===")
        logger.info(f"Mode: {'MOCK SIMULATION' if self.mock_mode else 'LIVE PRODUCTION'}")
        logger.info(f"Subscribed Markets: {self.active_markets}")

        self._running = True
        self._start_time = time.time()

        # Subscribe markets
        for mkt in self.active_markets:
            self.feed_manager.subscribe_market(mkt)

        # Start ingestion feeds
        self.feed_manager.start()
        logger.info("Engine daemon started successfully.")

    def stop(self) -> None:
        """Gracefully stop daemon and clean up connections."""
        logger.info("Stopping Engine daemon...")
        self._running = False
        self.feed_manager.stop()
        logger.info("Engine daemon stopped.")

    def run_forever(self, heartbeat_interval: float = 30.0) -> None:
        """Blocking run loop with periodic heartbeat log."""
        self.start()

        def _signal_handler(sig, frame):
            logger.info(f"Received shutdown signal ({sig}). Exiting cleanly...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        try:
            while self._running:
                time.sleep(heartbeat_interval)
                uptime = int(time.time() - self._start_time)
                active_trades = len(self.trade_manager.active_trades)
                closed_trades = len(self.trade_manager.closed_trades)
                logger.info(
                    f"[Heartbeat] Uptime: {uptime}s | "
                    f"Signals: {self._signals_generated} | "
                    f"Active Trades: {active_trades} | "
                    f"Closed: {closed_trades}"
                )
        except (KeyboardInterrupt, SystemExit):
            self.stop()


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="TLCS Black Box Signal Engine Daemon")
    parser.add_argument("--mock", action="store_true", help="Run in mock simulation mode")
    parser.add_argument("--markets", type=str, default="ALL", help="Comma-separated markets (e.g. NIFTY,CRYPTO)")
    parser.add_argument("--no-telegram", action="store_true", help="Disable Telegram alerting")
    parser.add_argument("--no-supabase", action="store_true", help="Disable Supabase syncing")

    args = parser.parse_args()

    markets = None
    if args.markets != "ALL":
        markets = [m.strip().upper() for m in args.markets.split(",")]

    daemon = EngineDaemon(
        mock_mode=args.mock,
        active_markets=markets,
        enable_telegram=not args.no_telegram,
        enable_supabase=not args.no_supabase,
    )
    daemon.run_forever()


if __name__ == "__main__":
    main()
