"""
Unit Tests for Phase 2: Real-Time Multi-Market Feed Ingestion Layer
===================================================================

Tests:
    1. Tick & Bar data contracts
    2. CandleAggregator multi-timeframe tick grouping and candle completion
    3. Symbol normalization and canonical market categorization
    4. DhanHQ binary packet parsing & symbol resolution
    5. Binance JSON trade message parsing
    6. Global feed & historical candle replay engine
    7. End-to-End pipeline: Ticks -> FeedManager -> Aggregator -> Strategy/Pivots
"""

import sys
import os
import time
import struct
import unittest
from typing import List

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from algo_engine.pivots import OHLC, compute_daily_levels
from algo_engine.feeds import (
    Tick, BaseFeed, FeedStatus,
    CandleAggregator,
    DhanFeed,
    BinanceFeed,
    GlobalFeed,
    FeedManager,
    normalize_symbol,
    get_market_category,
)


# ════════════════════════════════════════════════════════════════════
# TEST 1: TICK & DATA CONTRACTS
# ════════════════════════════════════════════════════════════════════

class TestTickDataContracts(unittest.TestCase):

    def test_tick_creation(self):
        t = Tick(symbol="RELIANCE", price=2850.50, volume=10.0, market="NIFTY")
        self.assertEqual(t.symbol, "RELIANCE")
        self.assertEqual(t.price, 2850.50)
        self.assertEqual(t.volume, 10.0)
        self.assertEqual(t.market, "NIFTY")
        self.assertGreater(t.timestamp, 0)


# ════════════════════════════════════════════════════════════════════
# TEST 2: SYMBOL NORMALIZATION & CANONICAL MARKET ROUTING
# ════════════════════════════════════════════════════════════════════

class TestSymbolNormalization(unittest.TestCase):

    def test_strip_exchange_prefixes(self):
        self.assertEqual(normalize_symbol("NSE:RELIANCE"), "RELIANCE")
        self.assertEqual(normalize_symbol("MCX:CRUDEOIL1!"), "CRUDEOIL")
        self.assertEqual(normalize_symbol("BINANCE:BTCUSDT"), "BTCUSDT")
        self.assertEqual(normalize_symbol("TVC:GOLD"), "GOLD")
        self.assertEqual(normalize_symbol("FX:EURUSD"), "EURUSD")

    def test_strip_futures_contract_numbers(self):
        self.assertEqual(normalize_symbol("CRUDEOIL1!"), "CRUDEOIL")
        self.assertEqual(normalize_symbol("NATURALGAS2!"), "NATURALGAS")
        self.assertEqual(normalize_symbol("SILVERM1!"), "SILVERM")

    def test_canonical_market_categorization(self):
        """Verify symbols match their single canonical market per AGENTS.md."""
        # NIFTY equities
        self.assertEqual(get_market_category("RELIANCE"), "NIFTY")
        self.assertEqual(get_market_category("NSE:HDFCBANK"), "NIFTY")
        self.assertEqual(get_market_category("TCS"), "NIFTY")
        self.assertEqual(get_market_category("INFY"), "NIFTY")

        # MCX commodities
        self.assertEqual(get_market_category("MCX:CRUDEOIL1!"), "MCX")
        self.assertEqual(get_market_category("GOLD"), "MCX")
        self.assertEqual(get_market_category("NATURALGAS"), "MCX")

        # NYMEX commodities
        self.assertEqual(get_market_category("CL"), "NYMEX")
        self.assertEqual(get_market_category("GC"), "NYMEX")
        self.assertEqual(get_market_category("NG"), "NYMEX")

        # CRYPTO
        self.assertEqual(get_market_category("BTCUSDT"), "CRYPTO")
        self.assertEqual(get_market_category("ETHUSDT"), "CRYPTO")
        self.assertEqual(get_market_category("SOLUSDT"), "CRYPTO")

        # FOREX
        self.assertEqual(get_market_category("EURUSD"), "FOREX")
        self.assertEqual(get_market_category("GBPUSD"), "FOREX")
        self.assertEqual(get_market_category("USDJPY"), "FOREX")

        # WORLD INDICES
        self.assertEqual(get_market_category("NAS100"), "WORLD")
        self.assertEqual(get_market_category("SPX500"), "WORLD")
        self.assertEqual(get_market_category("DE40"), "WORLD")


# ════════════════════════════════════════════════════════════════════
# TEST 3: CANDLE AGGREGATOR
# ════════════════════════════════════════════════════════════════════

class TestCandleAggregator(unittest.TestCase):

    def test_single_candle_formation(self):
        """Ticks in the same minute bucket update a developing candle."""
        agg = CandleAggregator(timeframes=["1m"])
        t_base = 1699999800  # Clean 60s & 300s aligned boundary

        agg.process_tick(Tick("RELIANCE", 2850.0, volume=10.0, timestamp=t_base + 5))
        agg.process_tick(Tick("RELIANCE", 2855.0, volume=5.0, timestamp=t_base + 10))
        agg.process_tick(Tick("RELIANCE", 2845.0, volume=15.0, timestamp=t_base + 20))
        agg.process_tick(Tick("RELIANCE", 2852.0, volume=20.0, timestamp=t_base + 30))

        dev = agg.get_developing_bar("RELIANCE", "1m")
        self.assertIsNotNone(dev)
        self.assertEqual(dev.open, 2850.0)
        self.assertEqual(dev.high, 2855.0)
        self.assertEqual(dev.low, 2845.0)
        self.assertEqual(dev.close, 2852.0)
        self.assertEqual(dev.volume, 50.0)

    def test_candle_close_event(self):
        """Crossing the timeframe boundary finalizes the previous candle."""
        agg = CandleAggregator(timeframes=["1m"])
        closed_events: List[OHLC] = []
        agg.on_bar_close(lambda sym, tf, bar: closed_events.append(bar))

        t_base = 1699999800  # Minute 0

        # Minute 0 ticks
        agg.process_tick(Tick("RELIANCE", 100.0, timestamp=t_base + 10))
        agg.process_tick(Tick("RELIANCE", 105.0, timestamp=t_base + 20))
        agg.process_tick(Tick("RELIANCE", 98.0, timestamp=t_base + 30))
        agg.process_tick(Tick("RELIANCE", 102.0, timestamp=t_base + 40))

        self.assertEqual(len(closed_events), 0)

        # Minute 1 tick (boundary cross: t_base + 65)
        agg.process_tick(Tick("RELIANCE", 103.0, timestamp=t_base + 65))

        self.assertEqual(len(closed_events), 1)
        closed = closed_events[0]
        self.assertEqual(closed.open, 100.0)
        self.assertEqual(closed.high, 105.0)
        self.assertEqual(closed.low, 98.0)
        self.assertEqual(closed.close, 102.0)

        # Historical buffer now contains the closed bar
        bars = agg.get_bars("RELIANCE", "1m")
        self.assertEqual(len(bars), 1)
        self.assertEqual(bars[0].close, 102.0)

    def test_multi_timeframe_aggregation(self):
        """Simultaneous aggregation for 1m and 5m."""
        agg = CandleAggregator(timeframes=["1m", "5m"])
        t_base = 1699999800  # Clean aligned timestamp (multiple of 300)

        # Feed 5 full minutes of ticks (minutes 0, 1, 2, 3, 4)
        for minute in range(5):
            for sec in [10, 30, 50]:
                ts = t_base + (minute * 60) + sec
                price = 100.0 + minute * 2.0
                agg.process_tick(Tick("BTCUSDT", price, timestamp=ts))

        # At minute 5 (305s mark), crossing closes the 5th 1m candle AND the 5m candle
        agg.process_tick(Tick("BTCUSDT", 110.0, timestamp=t_base + 305))

        m1_bars = agg.get_bars("BTCUSDT", "1m")
        m5_bars = agg.get_bars("BTCUSDT", "5m")

        self.assertEqual(len(m1_bars), 5)
        self.assertEqual(len(m5_bars), 1)

    def test_buffer_capacity_capping(self):
        """Aggregator truncates history when max_bars is exceeded."""
        agg = CandleAggregator(timeframes=["1m"], max_intraday_bars=3)
        t_base = 1699999800

        # Feed 5 minutes
        for minute in range(6):
            agg.process_tick(Tick("ETHUSDT", 3000.0 + minute, timestamp=t_base + minute * 60 + 10))

        bars = agg.get_bars("ETHUSDT", "1m")
        self.assertLessEqual(len(bars), 3, "Buffer must not exceed max_intraday_bars (3)")


# ════════════════════════════════════════════════════════════════════
# TEST 4: DHANHQ BINARY PARSER & ADAPTER
# ════════════════════════════════════════════════════════════════════

class TestDhanFeed(unittest.TestCase):

    def test_dhan_binary_unpacking(self):
        """Simulate unpacking DhanHQ 16-byte binary packet."""
        dhan = DhanFeed(mock_mode=True)
        ticks_received: List[Tick] = []
        dhan.on_tick(lambda t: ticks_received.append(t))

        # Register mapping: ExchangeSegment=1 (NSE), SecurityId=2885 -> RELIANCE
        dhan.register_symbol("RELIANCE", 1, "2885")

        # Format: <BHBIfI
        # resp_code(1B)=15, msg_len(2H)=16, exch(1B)=1, sec_id(4I)=2885, ltp(4f)=2850.75, ltt(4I)=1700000000
        packet = struct.pack("<BHBIfI", 15, 16, 1, 2885, 2850.75, 1700000000)

        dhan._parse_binary_packet(packet)

        self.assertEqual(len(ticks_received), 1)
        t = ticks_received[0]
        self.assertEqual(t.symbol, "RELIANCE")
        self.assertAlmostEqual(t.price, 2850.75, places=2)
        self.assertEqual(t.market, "NIFTY")

    def test_dhan_mock_stream(self):
        """Mock mode starts, streams ticks, and stops gracefully."""
        dhan = DhanFeed(mock_mode=True)
        ticks: List[Tick] = []
        dhan.on_tick(lambda t: ticks.append(t))
        dhan.subscribe(["RELIANCE", "CRUDEOIL"])

        dhan.start()
        time.sleep(0.3)
        dhan.stop()

        self.assertGreater(len(ticks), 0, "Mock feed must stream ticks")
        self.assertIn(ticks[0].symbol, ["RELIANCE", "CRUDEOIL"])


# ════════════════════════════════════════════════════════════════════
# TEST 5: BINANCE FEED PARSER
# ════════════════════════════════════════════════════════════════════

class TestBinanceFeed(unittest.TestCase):

    def test_binance_trade_json_parsing(self):
        """Parse real Binance trade JSON payload."""
        feed = BinanceFeed(mock_mode=True)
        ticks: List[Tick] = []
        feed.on_tick(lambda t: ticks.append(t))

        raw_payload = (
            '{"stream":"btcusdt@trade","data":'
            '{"e":"trade","E":1690000000000,"s":"BTCUSDT","t":12345,'
            '"p":"65432.10","q":"0.5","b":88,"a":89,"T":1690000000000,"m":true,"M":true}}'
        )

        feed._parse_json_message(raw_payload)

        self.assertEqual(len(ticks), 1)
        t = ticks[0]
        self.assertEqual(t.symbol, "BTCUSDT")
        self.assertEqual(t.price, 65432.10)
        self.assertEqual(t.volume, 0.5)
        self.assertEqual(t.market, "CRYPTO")

    def test_binance_mock_stream(self):
        """Binance mock mode streams crypto pairs."""
        feed = BinanceFeed(symbols=["BTCUSDT", "ETHUSDT"], mock_mode=True)
        ticks: List[Tick] = []
        feed.on_tick(lambda t: ticks.append(t))

        feed.start()
        time.sleep(0.3)
        feed.stop()

        self.assertGreater(len(ticks), 0)
        self.assertIn(ticks[0].symbol, ["BTCUSDT", "ETHUSDT"])


# ════════════════════════════════════════════════════════════════════
# TEST 6: GLOBAL FEED & HISTORICAL REPLAY ENGINE
# ════════════════════════════════════════════════════════════════════

class TestGlobalFeed(unittest.TestCase):

    def test_global_market_categorization(self):
        feed = GlobalFeed(symbols=["CL", "EURUSD", "NAS100"])
        self.assertEqual(feed._get_market_category("CL"), "NYMEX")
        self.assertEqual(feed._get_market_category("EURUSD"), "FOREX")
        self.assertEqual(feed._get_market_category("NAS100"), "WORLD")

    def test_bar_replay_synthesis(self):
        """Synthesize OHLC bar into a 4-tick journey."""
        feed = GlobalFeed()
        ticks: List[Tick] = []
        feed.on_tick(lambda t: ticks.append(t))

        bar = OHLC(open=100.0, high=110.0, low=95.0, close=108.0, volume=100.0)
        synthesized = feed.replay_bar_as_ticks("CL", bar)

        self.assertEqual(len(synthesized), 4)
        self.assertEqual(len(ticks), 4)
        # Green candle: Open -> Low -> High -> Close
        self.assertEqual(ticks[0].price, 100.0)  # Open
        self.assertEqual(ticks[1].price, 95.0)   # Low
        self.assertEqual(ticks[2].price, 110.0)  # High
        self.assertEqual(ticks[3].price, 108.0)  # Close


# ════════════════════════════════════════════════════════════════════
# TEST 7: END-TO-END PIPELINE (FEEDMANAGER -> AGGREGATOR -> ENGINE)
# ════════════════════════════════════════════════════════════════════

class TestEndToEndPipeline(unittest.TestCase):

    def test_feed_manager_tick_routing(self):
        """FeedManager normalizes incoming ticks and aggregates candles."""
        agg = CandleAggregator(timeframes=["1m"])
        fm = FeedManager(aggregator=agg, mock_mode=True)

        received_ticks: List[Tick] = []
        closed_bars: List[OHLC] = []

        fm.on_tick(lambda t: received_ticks.append(t))
        fm.on_bar_close(lambda sym, tf, bar: closed_bars.append(bar))

        t_base = 1700000000

        # Inject raw tick with TradingView prefix 'NSE:RELIANCE'
        raw_tick1 = Tick("NSE:RELIANCE", 2850.0, volume=10.0, timestamp=t_base + 10)
        raw_tick2 = Tick("NSE:RELIANCE", 2860.0, volume=5.0, timestamp=t_base + 20)
        raw_tick3 = Tick("NSE:RELIANCE", 2855.0, volume=15.0, timestamp=t_base + 70)  # Minute 1 (closes min 0)

        fm._handle_feed_tick(raw_tick1)
        fm._handle_feed_tick(raw_tick2)
        fm._handle_feed_tick(raw_tick3)

        # Ticks should be normalized
        self.assertEqual(len(received_ticks), 3)
        self.assertEqual(received_ticks[0].symbol, "RELIANCE")
        self.assertEqual(received_ticks[0].market, "NIFTY")

        # Candle should have closed
        self.assertEqual(len(closed_bars), 1)
        c = closed_bars[0]
        self.assertEqual(c.open, 2850.0)
        self.assertEqual(c.high, 2860.0)
        self.assertEqual(c.low, 2850.0)
        self.assertEqual(c.close, 2860.0)
        self.assertEqual(c.volume, 15.0)

        # Test feeding completed bar into Phase 1 pivots
        daily = compute_daily_levels(c.high, c.low, c.close)
        self.assertAlmostEqual(daily.camarilla.H4, c.close + (c.high - c.low) * 0.55, places=4)


if __name__ == '__main__':
    unittest.main(verbosity=2)
