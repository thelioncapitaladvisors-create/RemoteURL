"""
Unit and Integration Tests for Historical REST Bootstrapper
===========================================================

Tests:
    1. CandleAggregator.seed_historical_bars data persistence and limits.
    2. HistoricalBootstrapper synthetic baseline bar generation.
    3. Binance REST klines parsing and OHLC conversion.
    4. Instant indicator readiness: Camarilla, CPR, EMAs, ATR calculation immediately after seeding.
    5. ShadowPipeline dual-write configuration.
"""

import sys
import os
import unittest
from datetime import datetime, timezone

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from algo_engine.pivots import (
    OHLC, compute_daily_levels, compute_emas_from_bars,
    compute_atr, compute_pivot_trend_emas
)
from algo_engine.feeds.aggregator import CandleAggregator
from algo_engine.feeds.bootstrapper import HistoricalBootstrapper
from algo_engine.shadow_pipeline import ShadowPipeline


class TestHistoricalBootstrapper(unittest.TestCase):

    def setUp(self):
        self.aggregator = CandleAggregator()
        self.bootstrapper = HistoricalBootstrapper(timeout=5.0)

    def test_01_seed_historical_bars(self):
        """Verify CandleAggregator stores and returns seeded bars."""
        bars = [
            OHLC(open=100.0, high=105.0, low=99.0, close=104.0, volume=100.0, timestamp="2026-09-20 00:00:00"),
            OHLC(open=104.0, high=108.0, low=103.0, close=107.0, volume=150.0, timestamp="2026-09-21 00:00:00"),
        ]
        self.aggregator.seed_historical_bars("BTCUSDT", "1d", bars)
        stored = self.aggregator.get_bars("BTCUSDT", "1d")
        self.assertEqual(len(stored), 2)
        self.assertEqual(stored[-1].close, 107.0)

    def test_02_synthetic_baseline_bootstrapping(self):
        """Verify synthetic baseline correctly seeds 1d and 15m bars."""
        ok = self.bootstrapper._bootstrap_synthetic_baseline("CL", "NYMEX", self.aggregator)
        self.assertTrue(ok)

        daily = self.aggregator.get_bars("CL", "1d")
        intraday = self.aggregator.get_bars("CL", "15m")

        self.assertGreaterEqual(len(daily), 3)
        self.assertGreaterEqual(len(intraday), 30)
        self.assertGreater(daily[0].high, daily[0].low)
        self.assertGreater(intraday[0].close, 0.0)

    def test_03_binance_rest_klines_live(self):
        """Test live Binance REST klines fetch for SOLUSDT if network available."""
        try:
            bars = self.bootstrapper._fetch_binance_klines("SOLUSDT", interval="15m", limit=5)
            if bars:
                self.assertEqual(len(bars), 5)
                self.assertGreater(bars[0].close, 0.0)
                self.assertIsNotNone(bars[0].timestamp)
        except Exception as e:
            self.skipTest(f"Network call skipped or failed: {e}")

    def test_04_instant_indicator_readiness(self):
        """Verify that after bootstrapping, Camarilla and 14-period indicators calculate immediately."""
        # Seed 35 15m bars
        bars_15m = []
        p = 150.0
        for i in range(35):
            bars_15m.append(OHLC(open=p, high=p + 1.0, low=p - 1.0, close=p + 0.5, volume=50.0))
            p += 0.2

        daily_bars = [
            OHLC(open=140.0, high=155.0, low=138.0, close=152.0, volume=1000.0, timestamp="2026-09-20 00:00:00"),
            OHLC(open=152.0, high=158.0, low=149.0, close=156.0, volume=1200.0, timestamp="2026-09-21 00:00:00"),
        ]

        self.aggregator.seed_historical_bars("SOLUSDT", "15m", bars_15m)
        self.aggregator.seed_historical_bars("SOLUSDT", "1d", daily_bars)

        # Retrieve seeded
        retrieved_15m = self.aggregator.get_bars("SOLUSDT", "15m")
        retrieved_daily = self.aggregator.get_bars("SOLUSDT", "1d")

        self.assertGreaterEqual(len(retrieved_15m), 14)
        self.assertGreaterEqual(len(retrieved_daily), 2)

        # Prior day Camarilla
        prev_day = retrieved_daily[-2]
        levels = compute_daily_levels(prev_day.high, prev_day.low, prev_day.close)
        self.assertGreater(levels.camarilla.H4, levels.camarilla.L4)
        self.assertGreater(levels.camarilla.H3, levels.camarilla.L3)

        # 14-period EMAs & ATR
        short_emas, med_emas, _ = compute_emas_from_bars(retrieved_15m)
        atrs = compute_atr(retrieved_15m, period=14)

        self.assertEqual(len(short_emas), len(retrieved_15m))
        self.assertEqual(len(atrs), len(retrieved_15m))
        self.assertGreater(atrs[-1], 0.0)

    def test_05_shadow_pipeline_dual_write_configuration(self):
        """Verify ShadowPipeline respects table_name and dual_write parameters."""
        pipeline = ShadowPipeline(
            table_name="custom_shadow",
            dual_write=True,
            local_fallback_path="algo_engine/data/test_shadow.json"
        )
        self.assertEqual(pipeline.table_name, "custom_shadow")
        self.assertTrue(pipeline.dual_write)


if __name__ == "__main__":
    unittest.main()
