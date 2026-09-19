"""
algo_engine.feeds.base_feed — Abstract Feed Base Class & Data Contracts
======================================================================

Defines the standard tick and bar data structures, feed lifecycle,
and event subscription interfaces used across all market adapters.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Any
import time
import logging

logger = logging.getLogger(__name__)


class FeedStatus(Enum):
    """Lifecycle status of a market data feed."""
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    ERROR = "ERROR"


@dataclass
class Tick:
    """
    Standardized real-time market tick.
    
    Attributes:
        symbol: Normalized symbol name (e.g. 'RELIANCE', 'CRUDEOIL', 'BTCUSDT')
        price: Last Traded Price (LTP)
        volume: Last Traded Quantity / Volume
        timestamp: Epoch timestamp in seconds (float)
        market: Canonical market category ('NIFTY', 'MCX', 'CRYPTO', 'NYMEX', 'FOREX', 'WORLD')
        bid: Best bid price if available
        ask: Best ask price if available
        raw: Underlying raw packet dictionary for debugging
    """
    symbol: str
    price: float
    volume: float = 0.0
    timestamp: float = field(default_factory=time.time)
    market: str = ""
    bid: Optional[float] = None
    ask: Optional[float] = None
    raw: Optional[Dict[str, Any]] = None


# Callback type definitions
TickCallback = Callable[[Tick], None]
StatusCallback = Callable[[FeedStatus, str], None]
ErrorCallback = Callable[[Exception, str], None]


class BaseFeed(ABC):
    """
    Abstract Base Class for all market data feeds.
    
    Subclasses must implement:
        - `_start_connection()`
        - `_stop_connection()`
        - `_subscribe_symbols(symbols)`
        - `_unsubscribe_symbols(symbols)`
    """

    def __init__(self, name: str):
        self.name = name
        self.status = FeedStatus.DISCONNECTED
        self.subscribed_symbols: Set[str] = set()
        
        # Callbacks
        self._tick_callbacks: List[TickCallback] = []
        self._status_callbacks: List[StatusCallback] = []
        self._error_callbacks: List[ErrorCallback] = []

    def on_tick(self, callback: TickCallback) -> None:
        """Register a callback for incoming ticks."""
        self._tick_callbacks.append(callback)

    def on_status_change(self, callback: StatusCallback) -> None:
        """Register a callback for feed connection status changes."""
        self._status_callbacks.append(callback)

    def on_error(self, callback: ErrorCallback) -> None:
        """Register a callback for feed errors."""
        self._error_callbacks.append(callback)

    def _emit_tick(self, tick: Tick) -> None:
        """Dispatch tick to all registered listeners."""
        for cb in self._tick_callbacks:
            try:
                cb(tick)
            except Exception as e:
                logger.error(f"[{self.name}] Error in tick callback: {e}", exc_info=True)

    def _set_status(self, new_status: FeedStatus, reason: str = "") -> None:
        """Update feed status and notify listeners."""
        if self.status != new_status:
            self.status = new_status
            logger.info(f"[{self.name}] Feed status: {new_status.value} ({reason})")
            for cb in self._status_callbacks:
                try:
                    cb(new_status, reason)
                except Exception as e:
                    logger.error(f"[{self.name}] Error in status callback: {e}", exc_info=True)

    def _emit_error(self, error: Exception, context: str = "") -> None:
        """Dispatch error to listeners."""
        logger.error(f"[{self.name}] Error in {context}: {error}")
        for cb in self._error_callbacks:
            try:
                cb(error, context)
            except Exception as e:
                logger.error(f"[{self.name}] Error in error callback: {e}", exc_info=True)

    @property
    def is_connected(self) -> bool:
        """True if the feed is actively streaming."""
        return self.status == FeedStatus.CONNECTED

    @abstractmethod
    def start(self) -> None:
        """Initiate connection to the data feed."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Terminate connection and release resources."""
        pass

    @abstractmethod
    def subscribe(self, symbols: List[str]) -> None:
        """Subscribe to real-time market data for specified symbols."""
        pass

    @abstractmethod
    def unsubscribe(self, symbols: List[str]) -> None:
        """Unsubscribe from market data for specified symbols."""
        pass
