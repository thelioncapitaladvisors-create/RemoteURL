"""
algo_engine.feeds.binance_feed — Binance Live Crypto Feed Adapter
================================================================

Public multi-stream WebSocket client streaming real-time trades and 1-minute
klines for the 25 canonical cryptocurrency pairs. Zero authentication needed.
"""

from __future__ import annotations
import time
import json
import asyncio
import threading
import logging
from typing import Dict, List, Optional, Set

from .base_feed import BaseFeed, FeedStatus, Tick

logger = logging.getLogger(__name__)

# The 25 canonical cryptocurrency pairs from AGENTS.md
CANONICAL_CRYPTO_SYMBOLS: List[str] = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT",
    "NEARUSDT", "TONUSDT", "TRXUSDT", "UNIUSDT", "ICPUSDT",
    "APTUSDT", "ARBUSDT", "ATOMUSDT", "BCHUSDT", "FILUSDT",
    "LTCUSDT", "POLUSDT", "SHIBUSDT", "STXUSDT", "XLMUSDT",
]


class BinanceFeed(BaseFeed):
    """
    Binance Public WebSocket Client.
    
    Subscribes to multi-stream endpoints for live trade ticks and klines.
    Zero authentication required.
    """

    WSS_BASE_URL = "wss://stream.binance.com:9443/stream"

    def __init__(self,
                 symbols: Optional[List[str]] = None,
                 mock_mode: bool = False):
        super().__init__(name="BinanceFeed")
        self.mock_mode = mock_mode
        self.subscribed_symbols = set(symbols or CANONICAL_CRYPTO_SYMBOLS)

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._ws = None

    def start(self) -> None:
        """Start streaming thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("[BinanceFeed] Feed already running.")
            return

        self._stop_event.clear()
        self._set_status(FeedStatus.CONNECTING, "Starting Binance stream")

        if self.mock_mode:
            logger.info("[BinanceFeed] Running in MOCK SIMULATION mode.")
            self._thread = threading.Thread(target=self._run_mock_loop, daemon=True)
        else:
            self._thread = threading.Thread(target=self._run_live_loop, daemon=True)

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
        logger.info(f"[BinanceFeed] Subscribed to {len(self.subscribed_symbols)} crypto pairs.")

    def unsubscribe(self, symbols: List[str]) -> None:
        """Unsubscribe symbols."""
        for s in symbols:
            self.subscribed_symbols.discard(s.upper())

    # ── Live WebSocket Loop ──────────────────────────────────────

    def _build_stream_url(self) -> str:
        """Construct multi-stream URL for all subscribed symbols."""
        streams = []
        # Limit to 30 streams per connection to respect Binance connection guidelines
        for sym in list(self.subscribed_symbols)[:30]:
            lower = sym.lower()
            streams.append(f"{lower}@trade")
        return f"{self.WSS_BASE_URL}?streams={'/'.join(streams)}"

    def _run_live_loop(self) -> None:
        """Asyncio loop running the live Binance WebSocket."""
        try:
            import websockets
        except ImportError:
            logger.error("[BinanceFeed] 'websockets' package not installed. Falling back to mock.")
            self._run_mock_loop()
            return

        async def _connect_and_stream():
            backoff = 1.0
            while not self._stop_event.is_set():
                url = self._build_stream_url()
                try:
                    self._set_status(FeedStatus.CONNECTING, "Connecting to Binance")
                    async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                        self._ws = ws
                        self._set_status(FeedStatus.CONNECTED, "Binance WebSocket connected")
                        backoff = 1.0  # Reset on successful connection

                        while not self._stop_event.is_set():
                            try:
                                msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                                self._parse_json_message(msg)
                            except asyncio.TimeoutError:
                                # Keepalive ping
                                await ws.ping()
                except Exception as e:
                    self._emit_error(e, "binance_stream")
                    self._set_status(FeedStatus.RECONNECTING, str(e))
                    await asyncio.sleep(min(backoff, 30.0))
                    backoff *= 1.5

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_connect_and_stream())
        finally:
            loop.close()

    def _parse_json_message(self, raw_msg: str) -> None:
        """Parse Binance multi-stream JSON packet."""
        try:
            data = json.loads(raw_msg)
            stream_data = data.get("data", {})
            event_type = stream_data.get("e")

            if event_type == "trade":
                sym = stream_data.get("s", "").upper()
                price = float(stream_data.get("p", 0.0))
                qty = float(stream_data.get("q", 0.0))
                ts = float(stream_data.get("T", 0.0)) / 1000.0  # ms to seconds

                tick = Tick(
                    symbol=sym,
                    price=price,
                    volume=qty,
                    timestamp=ts if ts > 0 else time.time(),
                    market="CRYPTO",
                    raw=stream_data,
                )
                self._emit_tick(tick)
        except Exception as e:
            logger.debug(f"[BinanceFeed] Error parsing JSON message: {e}")

    # ── Offline / Mock Simulation Loop ───────────────────────────

    def _run_mock_loop(self) -> None:
        """Generates realistic synthetic crypto ticks."""
        import random

        self._set_status(FeedStatus.CONNECTED, "Mock simulation started")

        prices = {
            "BTCUSDT": 65000.0,
            "ETHUSDT": 3450.0,
            "SOLUSDT": 145.0,
            "BNBUSDT": 570.0,
            "XRPUSDT": 0.58,
            "DOGEUSDT": 0.12,
            "ADAUSDT": 0.38,
            "AVAXUSDT": 27.5,
            "LINKUSDT": 11.8,
            "DOTUSDT": 4.5,
        }

        active_symbols = list(self.subscribed_symbols) or list(prices.keys())

        while not self._stop_event.is_set():
            for sym in active_symbols:
                base = prices.get(sym, 1.0)
                # Small crypto volatility (±0.04%)
                drift = base * random.uniform(-0.0004, 0.0004)
                new_price = round(base + drift, 4 if base < 10 else 2)
                prices[sym] = new_price

                tick = Tick(
                    symbol=sym,
                    price=new_price,
                    volume=round(random.uniform(0.1, 5.0), 4),
                    timestamp=time.time(),
                    market="CRYPTO",
                )
                self._emit_tick(tick)

            time.sleep(0.08)

        self._set_status(FeedStatus.DISCONNECTED, "Mock simulation stopped")
