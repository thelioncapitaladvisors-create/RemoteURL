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
    compute_atr, compute_pivot_trend_emas, compute_value_area_from_bars,
    compute_opening_bias
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
        atr_vals = compute_atr(bars)
        va = compute_value_area_from_bars(bars)
        opening_bias = compute_opening_bias(bars[0].open, daily['high'], daily['low'], va.vah, va.val)

        # 4. Classify Day Type using daily aggregated bar
        daily_bar = OHLC(
            open=bars[0].open,
            high=max(b.high for b in bars),
            low=min(b.low for b in bars),
            close=bars[-1].close,
            volume=sum(b.volume for b in bars),
            timestamp=bars[-1].timestamp
        )

        if clean not in self.day_type_classifiers:
            self.day_type_classifiers[clean] = DayTypeClassifier()
        
        day_type_res = self.day_type_classifiers[clean].evaluate(daily_bar)
        active_blueprints = day_type_res.get_active_blueprints()
        active_sequences = day_type_res.get_active_sequences()

        primary_day_type = active_blueprints[0] if active_blueprints else 'TYPICAL DAY'

        signals: List[dict] = []

        # 5. Evaluate strategy engine across completed bars of the session
        # Check latest bars for active trading signals
        eval_window = min(len(bars), 10)
        for i in range(len(bars) - eval_window, len(bars)):
            cur_bar = bars[i]
            prev_b = bars[i - 1] if i > 0 else cur_bar

            ctx = MarketContext(
                bar=cur_bar,
                bar_index=i,
                H4=levels.H4,
                L4=levels.L4,
                H3=levels.H3,
                L3=levels.L3,
                cpr_pivot=levels.pivot,
                cpr_tc=levels.tc,
                cpr_bc=levels.bc,
                is_ncpr=levels.is_narrow,
                vah=va.vah,
                val=va.val,
                short_ema=emas[0][i],
                med_ema=emas[1][i],
                pivot_trend_fast=trend_emas[0][i],
                pivot_trend_slow=trend_emas[1][i],
                atr=atr_vals[i],
                opening_bias=opening_bias,
                day_type_label=primary_day_type,
                session_highest=max(b.high for b in bars[:i + 1]),
                session_lowest=min(b.low for b in bars[:i + 1]),
                prev_bar=prev_b,
                plus=1.0 if cur_bar.is_green else 0.0,
                minus=1.0 if cur_bar.is_red else 0.0,
            )

            strat_sigs = self.strategy_engine.evaluate(ctx)
            for sig in strat_sigs:
                signals.append({
                    'symbol': clean,
                    'type': sig.name,
                    'trigger': f'{sig.name} Trigger',
                    'market': 'nifty',
                    'entry_price': round(float(sig.entry_price), 2),
                    'stop_loss': round(float(sig.stop_loss), 2),
                    'tp1': round(float(sig.tp1), 2),
                    'tp2': round(float(sig.tp2), 2),
                    'tp3': round(float(sig.tp3), 2),
                    'tp4': round(float(sig.tp4), 2),
                    'status': 'ACTIVE',
                    'source': 'blackbox_dhan',
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'metadata': {
                        'timeframe': '15m',
                        'day_type': primary_day_type,
                        'opening_bias': opening_bias,
                        'source_feed': 'DhanHQ',
                        'h4': levels.H4,
                        'l4': levels.L4
                    }
                })

        # Also register blueprint signals if active
        for bp in active_blueprints:
            is_bull = 'Bullish' in bp
            bp_type = f'BUY {bp.upper()}' if is_bull else f'SELL {bp.upper()}'
            signals.append({
                'symbol': clean,
                'type': bp_type,
                'trigger': bp,
                'market': 'nifty',
                'entry_price': bars[-1].close,
                'status': 'ACTIVE',
                'source': 'blackbox_dhan',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'timeframe': '15m',
                    'day_type': bp,
                    'opening_bias': opening_bias,
                    'source_feed': 'DhanHQ',
                    'h4': levels.H4,
                    'l4': levels.L4
                }
            })

        for seq in active_sequences:
            signals.append({
                'symbol': clean,
                'type': f'BUY {seq.upper()}',
                'trigger': seq,
                'market': 'nifty',
                'entry_price': bars[-1].close,
                'status': 'ACTIVE',
                'source': 'blackbox_dhan',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'timeframe': '15m',
                    'day_type': seq,
                    'opening_bias': opening_bias,
                    'source_feed': 'DhanHQ',
                    'h4': levels.H4,
                    'l4': levels.L4
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
