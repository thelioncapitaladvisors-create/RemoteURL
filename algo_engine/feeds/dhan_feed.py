"""
algo_engine.feeds.dhan_feed — DhanHQ Live Market Feed Adapter
============================================================

Streams real-time market data for NSE Equities (NIFTY 50) and MCX Commodities
via the DhanHQ WebSocket API. Includes security master lookup and an offline
simulation fallback for testing outside market hours.
"""

from __future__ import annotations
import os
import time
import struct
import json
import asyncio
import threading
import logging
from typing import Dict, List, Optional, Set, Tuple

from .base_feed import BaseFeed, FeedStatus, Tick

logger = logging.getLogger(__name__)

# Default DhanHQ Exchange Segments
EXCHANGE_NSE = 1
EXCHANGE_NSE_FNO = 2
EXCHANGE_MCX = 5

# Common default MCX & NSE mappings for instant lookup
DEFAULT_SYMBOL_MAP: Dict[str, Tuple[int, str]] = {
    # (ExchangeSegment, SecurityID)
    "RELIANCE": (EXCHANGE_NSE, "2885"),
    "HDFCBANK": (EXCHANGE_NSE, "1333"),
    "ICICIBANK": (EXCHANGE_NSE, "4963"),
    "INFY": (EXCHANGE_NSE, "1594"),
    "TCS": (EXCHANGE_NSE, "11536"),
    "SBIN": (EXCHANGE_NSE, "3045"),
    "BHARTIARTL": (EXCHANGE_NSE, "10604"),
    "ITC": (EXCHANGE_NSE, "1660"),
    "KOTAKBANK": (EXCHANGE_NSE, "1922"),
    "LT": (EXCHANGE_NSE, "11483"),
    "CRUDEOIL": (EXCHANGE_MCX, "426307"),
    "GOLD": (EXCHANGE_MCX, "426308"),
    "SILVER": (EXCHANGE_MCX, "426309"),
    "NATURALGAS": (EXCHANGE_MCX, "426310"),
    "COPPER": (EXCHANGE_MCX, "426311"),
    "ZINC": (EXCHANGE_MCX, "426312"),
    "ALUMINIUM": (EXCHANGE_MCX, "426313"),
}


class DhanFeed(BaseFeed):
    """
    DhanHQ WebSocket v2 Market Feed client.
    
    Streams live ticks for NSE equities and MCX commodities.
    Includes offline mock simulation mode when credentials are missing or for testing.
    """

    WSS_URL = "wss://api-feed.dhan.co"

    def __init__(self,
                 client_id: Optional[str] = None,
                 access_token: Optional[str] = None,
                 mock_mode: bool = False):
        super().__init__(name="DhanFeed")
        self.client_id = client_id or os.getenv("DHAN_CLIENT_ID", "")
        self.access_token = access_token or os.getenv("DHAN_ACCESS_TOKEN", "")
        self.mock_mode = mock_mode or (not self.client_id or not self.access_token)

        # {symbol: (exchange_segment, security_id)}
        self.symbol_map: Dict[str, Tuple[int, str]] = dict(DEFAULT_SYMBOL_MAP)
        # {(exchange_segment, security_id): symbol}
        self.reverse_map: Dict[Tuple[int, str], str] = {
            v: k for k, v in self.symbol_map.items()
        }

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._ws = None

    def register_symbol(self, symbol: str, exchange_segment: int, security_id: str) -> None:
        """Register a custom symbol mapping."""
        clean = self._clean_symbol(symbol)
        self.symbol_map[clean] = (exchange_segment, str(security_id))
        self.reverse_map[(exchange_segment, str(security_id))] = clean

    def _clean_symbol(self, sym: str) -> str:
        """Normalize symbol string."""
        s = sym.upper()
        if s.startswith("NSE:"):
            s = s[4:]
        elif s.startswith("MCX:"):
            s = s[4:]
        if s.endswith("1!"):
            s = s[:-2]
        return s

    def start(self) -> None:
        """Start feed thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("[DhanFeed] Feed already running.")
            return

        self._stop_event.clear()
        self._set_status(FeedStatus.CONNECTING, "Starting connection")

        if self.mock_mode:
            logger.info("[DhanFeed] Running in MOCK SIMULATION mode (no live broker credentials).")
            self._thread = threading.Thread(target=self._run_mock_loop, daemon=True)
        else:
            self._thread = threading.Thread(target=self._run_live_loop, daemon=True)

        self._thread.start()

    def stop(self) -> None:
        """Stop feed thread."""
        self._stop_event.set()
        self._set_status(FeedStatus.DISCONNECTED, "Stopped by user")
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def subscribe(self, symbols: List[str]) -> None:
        """Subscribe to live market data for symbols."""
        for s in symbols:
            clean = self._clean_symbol(s)
            self.subscribed_symbols.add(clean)
        logger.info(f"[DhanFeed] Subscribed to {len(self.subscribed_symbols)} symbols: {list(self.subscribed_symbols)[:5]}...")

    def unsubscribe(self, symbols: List[str]) -> None:
        """Unsubscribe symbols."""
        for s in symbols:
            clean = self._clean_symbol(s)
            self.subscribed_symbols.discard(clean)

    # ── Live WebSocket Loop ──────────────────────────────────────

    def _run_live_loop(self) -> None:
        """Asyncio loop running the live Dhan WebSocket."""
        try:
            import websockets
        except ImportError:
            logger.error("[DhanFeed] 'websockets' package not installed. Falling back to mock.")
            self._run_mock_loop()
            return

        async def _connect_and_stream():
            url = f"{self.WSS_URL}?version=2&token={self.access_token}&clientId={self.client_id}&authType=2"
            while not self._stop_event.is_set():
                try:
                    self._set_status(FeedStatus.CONNECTING, "Connecting to DhanHQ")
                    async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                        self._ws = ws
                        self._set_status(FeedStatus.CONNECTED, "DhanHQ WebSocket connected")

                        # Send subscription packet
                        await self._send_subscriptions(ws)

                        # Read binary messages
                        while not self._stop_event.is_set():
                            try:
                                msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                                if isinstance(msg, bytes):
                                    self._parse_binary_packet(msg)
                            except asyncio.TimeoutError:
                                # Normal timeout, send ping
                                await ws.ping()
                except Exception as e:
                    self._emit_error(e, "live_stream")
                    self._set_status(FeedStatus.RECONNECTING, str(e))
                    await asyncio.sleep(2)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_connect_and_stream())
        finally:
            loop.close()

    async def _send_subscriptions(self, ws) -> None:
        """Send DhanHQ v2 subscription request."""
        instruments = []
        for sym in self.subscribed_symbols:
            if sym in self.symbol_map:
                seg, sec_id = self.symbol_map[sym]
                instruments.append({
                    "ExchangeSegment": seg,
                    "SecurityId": str(sec_id),
                })

        if instruments:
            payload = {
                "RequestCode": 15,  # Ticker Request
                "InstrumentCount": len(instruments),
                "InstrumentList": instruments,
            }
            await ws.send(json.dumps(payload))
            logger.info(f"[DhanFeed] Sent subscription request for {len(instruments)} instruments")

    def _parse_binary_packet(self, data: bytes) -> None:
        """Unpack DhanHQ binary packet into a Tick."""
        if len(data) < 16:
            return

        try:
            # Ticker packet: <BHBIfI (16 bytes)
            # ResponseCode (1), MessageLength (2), ExchangeSegment (1), SecurityId (4), LTP (4 float), LTT (4 int)
            header = struct.unpack("<BHBIfI", data[:16])
            exch_seg = header[2]
            sec_id = str(header[3])
            ltp = float(header[4])
            ltt = int(header[5])

            sym = self.reverse_map.get((exch_seg, sec_id))
            if not sym:
                sym = f"SEC_{sec_id}"

            market = "MCX" if exch_seg == EXCHANGE_MCX else "NIFTY"
            tick = Tick(
                symbol=sym,
                price=round(ltp, 4),
                volume=1.0,
                timestamp=float(ltt) if ltt > 0 else time.time(),
                market=market,
            )
            self._emit_tick(tick)
        except Exception as e:
            logger.debug(f"[DhanFeed] Error unpacking binary packet: {e}")

    # ── Offline / Mock Simulation Loop ───────────────────────────

    def _run_mock_loop(self) -> None:
        """Generates realistic synthetic ticks for testing."""
        import random

        self._set_status(FeedStatus.CONNECTED, "Mock simulation started")

        # Base prices for simulated assets
        prices = {
            "RELIANCE": 2850.0,
            "HDFCBANK": 1650.0,
            "INFY": 1820.0,
            "TCS": 4200.0,
            "CRUDEOIL": 6150.0,
            "GOLD": 72500.0,
            "SILVER": 84000.0,
            "NATURALGAS": 195.0,
        }

        # Default symbols to stream if none explicitly subscribed
        active_symbols = list(self.subscribed_symbols) or list(prices.keys())

        while not self._stop_event.is_set():
            for sym in active_symbols:
                base = prices.get(sym, 100.0)
                # Small random walk drift (±0.05%)
                drift = base * random.uniform(-0.0005, 0.0005)
                new_price = round(base + drift, 2)
                prices[sym] = new_price

                market = "MCX" if sym in ["CRUDEOIL", "GOLD", "SILVER", "NATURALGAS"] else "NIFTY"
                tick = Tick(
                    symbol=sym,
                    price=new_price,
                    volume=float(random.randint(1, 50)),
                    timestamp=time.time(),
                    market=market,
                )
                self._emit_tick(tick)

            # Sleep between tick bursts (100ms)
            time.sleep(0.1)

        self._set_status(FeedStatus.DISCONNECTED, "Mock simulation stopped")
