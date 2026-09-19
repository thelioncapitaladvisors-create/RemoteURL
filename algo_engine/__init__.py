"""
TLCS Black Box Signal Engine — Phase 1
=======================================
Standalone Python replication of the TradingView Pine Script indicator logic.
Generates identical signals without depending on TradingView webhooks.

Modules:
    pivots       — Camarilla H1-H5/L1-L5, CPR, EMAs, ATR
    day_types    — 5 Day Type Blueprints + 4 Trade Sequences
    strategies   — 12 canonical strategy triggers with H4/L4 gating
    trade_manager — Stateful trade lifecycle (limit → fill → trail → close)
    feeds        — Multi-market real-time feed ingestion (Dhan, Binance, Global)
    shadow_pipeline — Supabase shadow database synchronization
    telegram_dispatcher — Market-wise Telegram alert notifications
    engine_daemon — Master background execution daemon
"""

from .pivots import (
    compute_camarilla, compute_cpr, compute_daily_levels,
    ema, compute_atr, compute_adr, OHLC
)
from .day_types import DayTypeClassifier, DayTypeResult
from .strategies import StrategyEngine, StrategySignal, MarketContext
from .trade_manager import TradeManager, Trade, TradeStatus, TradeOutcome
from .feeds import FeedManager, CandleAggregator, Tick
from .shadow_pipeline import ShadowPipeline
from .telegram_dispatcher import TelegramDispatcher
from .engine_daemon import EngineDaemon

__version__ = "2.0.0"

__all__ = [
    "compute_camarilla",
    "compute_cpr",
    "compute_daily_levels",
    "ema",
    "compute_atr",
    "compute_adr",
    "OHLC",
    "DayTypeClassifier",
    "DayTypeResult",
    "StrategyEngine",
    "StrategySignal",
    "MarketContext",
    "TradeManager",
    "Trade",
    "TradeStatus",
    "TradeOutcome",
    "FeedManager",
    "CandleAggregator",
    "Tick",
    "ShadowPipeline",
    "TelegramDispatcher",
    "EngineDaemon",
]
