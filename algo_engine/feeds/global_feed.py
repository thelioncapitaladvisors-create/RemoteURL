"""
algo_engine.feeds.global_feed — Global Market Feed Adapter & Historical Replay
=============================================================================

Streams and simulates real-time ticks for NYMEX Commodities, Forex Majors,
and World Indices. Includes an integrated historical bar replay engine for
deterministic pipeline testing and weekend development.
"""

from __future__ import annotations
import time
import random
import threading
import logging
from typing import Dict, List, Optional, Set

from .base_feed import BaseFeed, FeedStatus, Tick
from ..pivots import OHLC

logger = logging.getLogger(__name__)

# Canonical symbols from AGENTS.md
NYMEX_SYMBOLS = ["CL", "GC", "HG", "HO", "NG", "PA", "PL", "RB", "SI"]
FOREX_SYMBOLS = [
    "AUDCAD", "AUDINR", "AUDJPY", "AUDNZD", "AUDUSD", "CADJPY",
    "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURINR", "EURJPY",
    "EURUSD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPINR", "GBPJPY",
    "GBPUSD", "JPYINR", "NZDUSD", "USDCAD", "USDCHF", "USDINR", "USDJPY"
]
WORLD_INDICES = [
    "AU200", "DE40", "EU50", "FR40", "HK50", "JP225",
    "NAS100", "SPX500", "UK100", "US2000", "US30"
]

# Baseline prices for realistic market simulation
DEFAULT_GLOBAL_PRICES: Dict[str, float] = {
    # NYMEX
    "CL": 71.50, "GC": 2680.0, "HG": 4.45, "HO": 2.25,
    "NG": 2.85, "PA": 1050.0, "PL": 980.0, "RB": 2.10, "SI": 31.80,
    # Forex
    "EURUSD": 1.0850, "GBPUSD": 1.3020, "USDJPY": 148.50,
    "AUDUSD": 0.6650, "USDCAD": 1.3780, "USDCHF": 0.8650,
    "EURGBP": 0.8330, "EURJPY": 161.20, "GBPJPY": 193.40,
    # World Indices
    "NAS100": 20150.0, "SPX500": 5820.0, "US30": 42800.0,
    "DE40": 19500.0, "UK100": 8250.0, "JP225": 38900.0,
    "HK50": 20600.0, "AU200": 8280.0, "EU50": 4950.0,
}


class GlobalFeed(BaseFeed):
    """
    Global Market Feed Adapter.
    
    Covers NYMEX, Forex, and World Indices. Supports live simulated
    tick generation and historical candle bar replay.
    """

    def __init__(self,
                 symbols: Optional[List[str]] = None,
                 poll_interval: float = 0.1):
        super().__init__(name="GlobalFeed")
        default_all = NYMEX_SYMBOLS + FOREX_SYMBOLS[:5] + WORLD_INDICES[:5]
        self.subscribed_symbols = set(symbols or default_all)
        self.poll_interval = poll_interval

        self._prices = dict(DEFAULT_GLOBAL_PRICES)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Replay mode state
        self._replay_mode = False
        self._replay_bars: Dict[str, List[OHLC]] = {}
        self._replay_speed = 1.0

    def start(self) -> None:
        """Start streaming thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("[GlobalFeed] Feed already running.")
            return

        self._stop_event.clear()
        self._set_status(FeedStatus.CONNECTED, "Global feed active")
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop streaming thread."""
        self._stop_event.set()
        self._set_status(FeedStatus.DISCONNECTED, "Stopped by user")
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def subscribe(self, symbols: List[str]) -> None:
        """Subscribe to additional symbols."""
        for s in symbols:
            self.subscribed_symbols.add(s.upper())

    def unsubscribe(self, symbols: List[str]) -> None:
        """Unsubscribe symbols."""
        for s in symbols:
            self.subscribed_symbols.discard(s.upper())

    def _get_market_category(self, sym: str) -> str:
        """Resolve canonical market category for global symbol."""
        s = sym.upper()
        if s in NYMEX_SYMBOLS:
            return "NYMEX"
        if s in FOREX_SYMBOLS:
            return "FOREX"
        if s in WORLD_INDICES:
            return "WORLD"
        return "GLOBAL"

    def _run_loop(self) -> None:
        """Main tick generation loop."""
        active = list(self.subscribed_symbols)

        while not self._stop_event.is_set():
            for sym in active:
                base = self._prices.get(sym, 100.0)
                # Realistic asset-dependent volatility
                mkt = self._get_market_category(sym)
                vol = 0.0001 if mkt == "FOREX" else 0.0003
                drift = base * random.uniform(-vol, vol)

                decimals = 4 if mkt == "FOREX" else 2
                new_price = round(base + drift, decimals)
                self._prices[sym] = new_price

                tick = Tick(
                    symbol=sym,
                    price=new_price,
                    volume=round(random.uniform(1.0, 20.0), 2),
                    timestamp=time.time(),
                    market=mkt,
                )
                self._emit_tick(tick)

            time.sleep(self.poll_interval)

    # ── Historical Bar Replay Driver ─────────────────────────────

    def load_replay_data(self, symbol: str, bars: List[OHLC]) -> None:
        """Load historical bars for deterministic replay testing."""
        self._replay_bars[symbol] = list(bars)

    def replay_bar_as_ticks(self, symbol: str, bar: OHLC, num_ticks: int = 4) -> List[Tick]:
        """
        Synthesize ticks representing a bar's journey: Open -> High/Low -> Close.
        
        Emits synthesized ticks to subscribers and returns the list.
        """
        mkt = self._get_market_category(symbol)
        t_base = time.time()

        # Typical candle sequence: Open -> Low -> High -> Close (for green candle)
        if bar.is_green:
            seq = [bar.open, bar.low, bar.high, bar.close]
        else:
            seq = [bar.open, bar.high, bar.low, bar.close]

        ticks = []
        for i, p in enumerate(seq):
            tick = Tick(
                symbol=symbol,
                price=p,
                volume=bar.volume / num_ticks if bar.volume > 0 else 1.0,
                timestamp=t_base + (i * 0.05),
                market=mkt,
            )
            ticks.append(tick)
            self._emit_tick(tick)

        return ticks
