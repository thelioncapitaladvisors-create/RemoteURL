"""
algo_engine.feeds.feed_manager — Master Real-Time Feed Orchestrator
==================================================================

Orchestrates multi-market data feeds (DhanHQ, Binance, Global), routes symbols
to their appropriate adapters, normalizes symbol formats, and streams ticks
into the CandleAggregator.
"""

from __future__ import annotations
import re
import logging
from typing import Callable, Dict, List, Optional, Set

from .base_feed import BaseFeed, FeedStatus, Tick
from .aggregator import CandleAggregator, BarCallback
from .dhan_feed import DhanFeed
from .binance_feed import BinanceFeed, CANONICAL_CRYPTO_SYMBOLS
from .global_feed import GlobalFeed, NYMEX_SYMBOLS, FOREX_SYMBOLS, WORLD_INDICES
from ..pivots import OHLC

logger = logging.getLogger(__name__)

# Complete Canonical Market Lists from AGENTS.md
NIFTY_SYMBOLS = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
    "BAJAJ-AUTO", "BAJAJFINSV", "BAJFINANCE", "BHARTIARTL", "BPCL",
    "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY",
    "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE",
    "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK", "INDUSINDBK",
    "INFY", "ITC", "JSWSTEEL", "KOTAKBANK", "LT",
    "LTIMINDTREE", "M&M", "MARUTI", "NESTLEIND", "NTPC",
    "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN",
    "SHRIRAMFIN", "SUNPHARMA", "TATACONSUM", "TATAMOTORS", "TATASTEEL",
    "TCS", "TECHM", "TITAN", "ULTRACEMCO", "WIPRO"
]

MCX_SYMBOLS = [
    "ALUMINIUM", "ALUMINIUMM", "COPPER", "COTTON", "CRUDEOIL",
    "CRUDEOILM", "GOLD", "GOLDM", "GOLDPETAL", "LEAD",
    "LEADMINI", "MENTHAOIL", "NATURALGAS", "NATURALGASM", "NICKEL",
    "NICKELMINI", "SILVER", "SILVERM", "SILVERMIC", "ZINC", "ZINCMINI"
]


def normalize_symbol(symbol: str) -> str:
    """
    Normalize TradingView exchange and contract prefixes.
    
    Examples:
        'NSE:RELIANCE' -> 'RELIANCE'
        'MCX:CRUDEOIL1!' -> 'CRUDEOIL'
        'TVC:GOLD' -> 'GOLD'
        'BINANCE:BTCUSDT' -> 'BTCUSDT'
    """
    s = (symbol or "").strip().upper()
    # Strip exchange prefixes (NSE:, MCX:, TVC:, BINANCE:, FX:, etc.)
    if ":" in s:
        s = s.split(":")[-1]
    # Strip continuous futures contract suffixes (1!, 2!)
    s = re.sub(r"\d+!$", "", s)
    return s


def get_market_category(symbol: str) -> str:
    """
    Resolve a symbol to its single canonical market category.
    
    Follows AGENTS.md definitive truth:
        NIFTY -> MCX -> NYMEX -> CRYPTO -> FOREX -> WORLD
    """
    sym = normalize_symbol(symbol)

    if sym in NIFTY_SYMBOLS:
        return "NIFTY"
    if sym in MCX_SYMBOLS:
        return "MCX"
    if sym in NYMEX_SYMBOLS:
        return "NYMEX"
    if sym in CANONICAL_CRYPTO_SYMBOLS or sym.endswith("USDT"):
        return "CRYPTO"
    if sym in FOREX_SYMBOLS:
        return "FOREX"
    if sym in WORLD_INDICES:
        return "WORLD"

    return "UNKNOWN"


def is_market_open(symbol: str, dt: Optional[datetime] = None) -> bool:
    """
    Determine if the market for a given symbol is currently open for trading.
    Prevents strategy evaluation and trade generation outside market hours.
    
    Rules:
        - CRYPTO: 24/7/365 (Always open)
        - NIFTY: Monday through Friday, 09:15 to 15:30 IST
        - MCX: Monday through Friday, 09:00 to 23:30 IST
        - FOREX: Sunday 22:00 UTC to Friday 22:00 UTC
        - Other: Monday through Friday
    """
    from datetime import datetime, timezone, timedelta

    mkt = get_market_category(symbol)
    if mkt == "CRYPTO":
        return True

    now_utc = datetime.now(timezone.utc) if dt is None else dt
    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = now_utc + ist_offset
    weekday = now_ist.weekday()  # 0 = Monday, 4 = Friday, 5 = Sat, 6 = Sun
    time_minutes = now_ist.hour * 60 + now_ist.minute

    if mkt == "NIFTY":
        if weekday >= 5:
            return False
        return (9 * 60 + 15) <= time_minutes <= (15 * 60 + 30)

    if mkt == "MCX":
        if weekday >= 5:
            return False
        return (9 * 60) <= time_minutes <= (23 * 60 + 30)

    if mkt == "FOREX":
        utc_weekday = now_utc.weekday()
        utc_minutes = now_utc.hour * 60 + now_utc.minute
        if utc_weekday == 5:
            return False
        if utc_weekday == 6:
            return utc_minutes >= 22 * 60
        if utc_weekday == 4:
            return utc_minutes < 22 * 60
        return True

    return weekday < 5


class FeedManager:
    """
    Master Feed Orchestrator.
    
    Coordinates DhanFeed, BinanceFeed, and GlobalFeed, routes incoming ticks
    to the CandleAggregator, and exposes high-level subscription APIs.
    """

    def __init__(self,
                 aggregator: Optional[CandleAggregator] = None,
                 mock_mode: bool = False):
        self.aggregator = aggregator or CandleAggregator()
        self.mock_mode = mock_mode

        # Instantiate adapters
        self.dhan_feed = DhanFeed(mock_mode=mock_mode)
        self.binance_feed = BinanceFeed(mock_mode=mock_mode)
        self.global_feed = GlobalFeed(mock_mode=mock_mode)

        self._all_feeds: List[BaseFeed] = [
            self.dhan_feed,
            self.binance_feed,
            self.global_feed,
        ]

        # Connect all feed ticks to aggregator
        for feed in self._all_feeds:
            feed.on_tick(self._handle_feed_tick)

        # External tick callbacks
        self._user_tick_callbacks: List[Callable[[Tick], None]] = []

    def on_tick(self, callback: Callable[[Tick], None]) -> None:
        """Register a callback for processed ticks."""
        self._user_tick_callbacks.append(callback)

    def on_bar_close(self, callback: BarCallback) -> None:
        """Register a callback for finalized candles."""
        self.aggregator.on_bar_close(callback)

    def _handle_feed_tick(self, tick: Tick) -> None:
        """Internal router passing incoming tick to aggregator."""
        # Ensure symbol is normalized and categorized
        clean_sym = normalize_symbol(tick.symbol)
        if clean_sym != tick.symbol:
            tick.symbol = clean_sym

        if not tick.market:
            tick.market = get_market_category(clean_sym)

        # Push to candle aggregator
        self.aggregator.process_tick(tick)

        # Notify downstream user listeners
        for cb in self._user_tick_callbacks:
            try:
                cb(tick)
            except Exception as e:
                logger.error(f"[FeedManager] Error in user tick callback: {e}", exc_info=True)

    def start(self) -> None:
        """Start all underlying market feeds."""
        logger.info("[FeedManager] Starting all market data feeds...")
        for feed in self._all_feeds:
            try:
                feed.start()
            except Exception as e:
                logger.error(f"[FeedManager] Error starting {feed.name}: {e}")

    def stop(self) -> None:
        """Stop all market data feeds."""
        logger.info("[FeedManager] Stopping all market data feeds...")
        for feed in self._all_feeds:
            try:
                feed.stop()
            except Exception as e:
                logger.error(f"[FeedManager] Error stopping {feed.name}: {e}")

    def subscribe_symbol(self, symbol: str) -> None:
        """Subscribe to a symbol on its appropriate feed."""
        clean = normalize_symbol(symbol)
        mkt = get_market_category(clean)

        if mkt in ["NIFTY", "MCX"]:
            self.dhan_feed.subscribe([clean])
        elif mkt == "CRYPTO":
            self.binance_feed.subscribe([clean])
        else:
            self.global_feed.subscribe([clean])

    def subscribe_market(self, market: str) -> None:
        """Subscribe to an entire canonical market."""
        m = market.upper()
        if m == "NIFTY":
            self.dhan_feed.subscribe(NIFTY_SYMBOLS)
        elif m == "MCX":
            self.dhan_feed.subscribe(MCX_SYMBOLS)
        elif m == "CRYPTO":
            self.binance_feed.subscribe(CANONICAL_CRYPTO_SYMBOLS)
        elif m == "NYMEX":
            self.global_feed.subscribe(NYMEX_SYMBOLS)
        elif m == "FOREX":
            self.global_feed.subscribe(FOREX_SYMBOLS)
        elif m == "WORLD":
            self.global_feed.subscribe(WORLD_INDICES)
        else:
            logger.warning(f"[FeedManager] Unknown market: {market}")

    def get_bars(self, symbol: str, timeframe: str = "15m") -> List[OHLC]:
        """Fetch historical bars from aggregator."""
        clean = normalize_symbol(symbol)
        return self.aggregator.get_bars(clean, timeframe)

    def get_developing_bar(self, symbol: str, timeframe: str = "15m") -> Optional[OHLC]:
        """Fetch current incomplete developing candle."""
        clean = normalize_symbol(symbol)
        return self.aggregator.get_developing_bar(clean, timeframe)

    def get_all_subscribed_symbols(self) -> List[str]:
        """Return a sorted unique list of all subscribed symbols across all feed adapters."""
        symbols: Set[str] = set()
        symbols.update(getattr(self.dhan_feed, "subscribed_symbols", []))
        symbols.update(getattr(self.binance_feed, "subscribed_symbols", []))
        symbols.update(getattr(self.global_feed, "subscribed_symbols", []))
        return sorted(list(symbols))

