"""
algo_engine.feeds.aggregator — Real-Time Multi-Timeframe Candle Aggregator
========================================================================

Aggregates raw market ticks into 1m, 5m, 15m, and Daily OHLC bars.
Maintains a rolling window of historical bars for indicator and strategy execution.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple
import threading
import logging

from ..pivots import OHLC
from .base_feed import Tick

logger = logging.getLogger(__name__)

# Callback type for closed bar events
BarCallback = Callable[[str, str, OHLC], None]  # (symbol, timeframe, bar)


# Standard timeframe intervals in seconds
TIMEFRAME_SECONDS: Dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "1d": 86400,
}


@dataclass
class DevelopingCandle:
    """An active candle being constructed from streaming ticks."""
    bucket_start: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    tick_count: int = 0

    def update(self, price: float, volume: float = 0.0) -> None:
        """Update candle with a new tick."""
        if price > self.high:
            self.high = price
        if price < self.low:
            self.low = price
        self.close = price
        self.volume += volume
        self.tick_count += 1

    def to_ohlc(self, timestamp_str: Optional[str] = None) -> OHLC:
        """Convert to standard OHLC object."""
        if timestamp_str is None:
            dt = datetime.fromtimestamp(self.bucket_start, tz=timezone.utc)
            timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")

        return OHLC(
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
            timestamp=timestamp_str,
        )


class CandleAggregator:
    """
    Thread-safe tick-to-candle aggregator.
    
    Supports:
        - Multiple timeframes concurrently (default: '1m', '5m', '15m', '1d')
        - Emits callbacks when a candle closes
        - Maintains rolling historical bar buffers
    """

    def __init__(self,
                 timeframes: Optional[List[str]] = None,
                 max_intraday_bars: int = 200,
                 max_daily_bars: int = 60):
        self.timeframes = timeframes or ["1m", "5m", "15m", "1d"]
        self.max_intraday_bars = max_intraday_bars
        self.max_daily_bars = max_daily_bars

        self._lock = threading.Lock()

        # {symbol: {timeframe: DevelopingCandle}}
        self._developing: Dict[str, Dict[str, DevelopingCandle]] = {}

        # {symbol: {timeframe: [OHLC, ...]}}
        self._history: Dict[str, Dict[str, List[OHLC]]] = {}

        # Callbacks
        self._bar_callbacks: List[BarCallback] = []

    def on_bar_close(self, callback: BarCallback) -> None:
        """Register a callback invoked whenever a candle closes."""
        self._bar_callbacks.append(callback)

    def process_tick(self, tick: Tick) -> List[Tuple[str, OHLC]]:
        """
        Ingest a tick, update developing candles, and return any newly closed bars.
        
        Args:
            tick: Live Tick object
            
        Returns:
            List of (timeframe, closed_bar) for candles that finalized on this tick
        """
        closed_bars: List[Tuple[str, OHLC]] = []
        sym = tick.symbol
        ts = int(tick.timestamp)
        p = tick.price
        v = tick.volume

        with self._lock:
            if sym not in self._developing:
                self._developing[sym] = {}
                self._history[sym] = {tf: [] for tf in self.timeframes}

            for tf in self.timeframes:
                sec = TIMEFRAME_SECONDS.get(tf, 60)
                bucket_start = (ts // sec) * sec

                current = self._developing[sym].get(tf)

                if current is None:
                    # First tick for this symbol/timeframe
                    self._developing[sym][tf] = DevelopingCandle(
                        bucket_start=bucket_start,
                        open=p, high=p, low=p, close=p, volume=v, tick_count=1
                    )
                elif bucket_start > current.bucket_start:
                    # Previous candle finalized!
                    closed_bar = current.to_ohlc()
                    closed_bars.append((tf, closed_bar))

                    # Append to history cache
                    max_len = self.max_daily_bars if tf == "1d" else self.max_intraday_bars
                    hist = self._history[sym][tf]
                    hist.append(closed_bar)
                    if len(hist) > max_len:
                        hist.pop(0)

                    # Start new developing candle
                    self._developing[sym][tf] = DevelopingCandle(
                        bucket_start=bucket_start,
                        open=p, high=p, low=p, close=p, volume=v, tick_count=1
                    )
                else:
                    # Same candle continues developing
                    current.update(p, v)

        # Notify callbacks outside the lock to prevent deadlock
        for tf, bar in closed_bars:
            for cb in self._bar_callbacks:
                try:
                    cb(sym, tf, bar)
                except Exception as e:
                    logger.error(f"Error in bar callback for {sym} {tf}: {e}", exc_info=True)

        return closed_bars

    def get_bars(self, symbol: str, timeframe: str = "15m") -> List[OHLC]:
        """
        Get completed historical bars for a symbol and timeframe.
        
        Args:
            symbol: Normalized symbol name
            timeframe: Timeframe identifier ('1m', '5m', '15m', '1d')
            
        Returns:
            List of OHLC bars in chronological order (shallow copy)
        """
        with self._lock:
            if symbol in self._history and timeframe in self._history[symbol]:
                return list(self._history[symbol][timeframe])
            return []

    def get_developing_bar(self, symbol: str, timeframe: str = "15m") -> Optional[OHLC]:
        """Get the current incomplete developing candle as an OHLC snapshot."""
        with self._lock:
            dev = self._developing.get(symbol, {}).get(timeframe)
            if dev:
                return dev.to_ohlc()
            return None

    def seed_historical_bars(self, symbol: str, timeframe: str, bars: List[OHLC]) -> None:
        """
        Pre-populate historical bars (e.g. from historical data fetch).
        
        Args:
            symbol: Normalized symbol name
            timeframe: Timeframe identifier
            bars: Historical OHLC bars in chronological order
        """
        with self._lock:
            if symbol not in self._history:
                self._developing[symbol] = {}
                self._history[symbol] = {tf: [] for tf in self.timeframes}
            elif timeframe not in self._history[symbol]:
                self._history[symbol][timeframe] = []
            
            max_len = self.max_daily_bars if timeframe == "1d" else self.max_intraday_bars
            self._history[symbol][timeframe] = list(bars[-max_len:])
            logger.info(f"Seeded {len(self._history[symbol][timeframe])} historical {timeframe} bars for {symbol}")

    def clear(self) -> None:
        """Reset all aggregations."""
        with self._lock:
            self._developing.clear()
            self._history.clear()
