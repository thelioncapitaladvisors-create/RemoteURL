"""
algo_engine.nse100_scanner — Top 100 Liquid NSE Stocks 15-Minute Black Box Scanner
=================================================================================

Evaluates the canonical Top 100 NSE stocks across all 13 strategy categories
and Day Type Blueprints using 15-minute OHLC candles and daily pivot levels.
Synchronizes detected active signals into Supabase .
"""

import os
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from .data.nse_top100_master import get_all_nse100_symbols, clean_symbol
from .feeds.dhan_feed import DhanFeed
from .pivots import (
    OHLC, compute_daily_levels, compute_emas_from_bars,
    compute_atr, compute_pivot_trend_emas
)
from .day_types import DayTypeClassifier
from .strategies import StrategyEngine, StrategySignal, MarketContext
from .shadow_pipeline import ShadowPipeline

logger = logging.getLogger('NSE100Scanner')


class NSE100Scanner:
    """
    Autonomous 15-minute multi-asset scanner for the Top 100 NSE liquid universe.
    """

    def __init__(self,
                 dhan_feed: Optional[DhanFeed] = None,
                 shadow_pipeline: Optional[ShadowPipeline] = None,
                 mock_mode: bool = False):
        self.dhan_feed = dhan_feed or DhanFeed(mock_mode=mock_mode)
        self.shadow_pipeline = shadow_pipeline or ShadowPipeline()
        self.strategy_engine = StrategyEngine()
        self.day_type_classifiers: Dict[str, DayTypeClassifier] = {}
        self.mock_mode = mock_mode
        self.symbols = get_all_nse100_symbols()

    def scan_symbol(self, sym: str) -> List[dict]:
        """
        Scan an individual symbol on 15m timeframe against all 13 strategies and day types.
        """
        clean = clean_symbol(sym)
        daily = self.dhan_feed.fetch_daily_levels(clean)
        if not daily:
            return []

        # 1. Compute Daily Camarilla and CPR Levels
        levels = compute_daily_levels(daily['high'], daily['low'], daily['close'])

        # 2. Fetch 15-minute candles
        candles = self.dhan_feed.fetch_intraday_candles(clean, interval=15)
        if not candles or len(candles) < 3:
            return []

        bars = [
            OHLC(
                open=c['open'],
                high=c['high'],
                low=c['low'],
                close=c['close'],
                volume=c.get('volume', 0.0),
                timestamp=c.get('timestamp', time.time())
            )
            for c in candles
        ]

        # 3. Compute indicators on 15m bars
        emas = compute_emas_from_bars(bars)
        trend_emas = compute_pivot_trend_emas(bars)
        atr = compute_atr(bars)

        # 4. Classify Day Type
        if clean not in self.day_type_classifiers:
            self.day_type_classifiers[clean] = DayTypeClassifier(levels)
        
        day_type_res = self.day_type_classifiers[clean].update(bars[-1])

        # 5. Build Market Context for Strategy Engine
        context = MarketContext(
            symbol=clean,
            market='NIFTY',
            current_bar=bars[-1],
            previous_bar=bars[-2] if len(bars) >= 2 else bars[-1],
            levels=levels,
            emas=emas,
            trend_emas=trend_emas,
            atr=atr,
            day_type=day_type_res.blueprint.value if day_type_res.blueprint else 'TYPICAL',
            opening_bias=day_type_res.opening_bias.value if day_type_res.opening_bias else 'IN_RANGE_IN_VALUE'
        )

        signals: List[dict] = []

        # Evaluate standard strategies (Missile, Scalp, Lightning, Extreme Reversal, Divergence)
        strat_sigs = self.strategy_engine.evaluate(context)
        for sig in strat_sigs:
            signals.append({
                'symbol': clean,
                'type': sig.signal_type.value,
                'trigger': sig.trigger_reason,
                'market': 'nifty',
                'entry_price': sig.entry_price,
                'stop_loss': sig.stop_loss,
                'tp1': sig.tp1,
                'tp2': sig.tp2,
                'tp3': sig.tp3,
                'tp4': sig.tp4,
                'status': 'ACTIVE',
                'source': 'blackbox_dhan',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'timeframe': '15m',
                    'day_type': day_type_res.blueprint.value if day_type_res.blueprint else '',
                    'opening_bias': day_type_res.opening_bias.value if day_type_res.opening_bias else '',
                    'source_feed': 'DhanHQ',
                    'h4': levels.h4,
                    'l4': levels.l4
                }
            })

        # Also register blueprint and sequence tags if active
        if day_type_res.blueprint:
            bp_val = day_type_res.blueprint.value.upper()
            signals.append({
                'symbol': clean,
                'type': f'BLUEPRINT_{bp_val}',
                'trigger': day_type_res.blueprint.value,
                'market': 'nifty',
                'entry_price': bars[-1].close,
                'status': 'ACTIVE',
                'source': 'blackbox_dhan',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'timeframe': '15m',
                    'day_type': day_type_res.blueprint.value,
                    'opening_bias': day_type_res.opening_bias.value if day_type_res.opening_bias else '',
                    'source_feed': 'DhanHQ'
                }
            })

        return signals

    def run_scan_cycle(self, limit: Optional[int] = None) -> List[dict]:
        """
        Execute one full scan cycle across the Top 100 NSE basket.
        """
        target_symbols = self.symbols[:limit] if limit else self.symbols
        logger.info(f'[NSE100Scanner] Starting 15m scan cycle across {len(target_symbols)} symbols...')
        
        all_signals: List[dict] = []
        start_t = time.time()

        for sym in target_symbols:
            try:
                sigs = self.scan_symbol(sym)
                if sigs:
                    all_signals.extend(sigs)
            except Exception as e:
                logger.debug(f'[NSE100Scanner] Error scanning {sym}: {e}')

        duration = time.time() - start_t
        logger.info(f'[NSE100Scanner] Scan finished in {duration:.2f}s. Detected {len(all_signals)} active signals.')

        # Sync to Supabase shadow_signals if pipeline active
        if self.shadow_pipeline and all_signals:
            try:
                for sig in all_signals:
                    self.shadow_pipeline.sync_signal(sig)
                logger.info(f'[NSE100Scanner] Synced {len(all_signals)} signals to shadow_signals.')
            except Exception as e:
                logger.warning(f'[NSE100Scanner] Failed syncing to shadow_signals: {e}')

        return all_signals
