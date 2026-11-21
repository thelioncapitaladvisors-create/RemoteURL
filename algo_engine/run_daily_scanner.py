#!/usr/bin/env python3
"""
algo_engine.run_daily_scanner — Autonomous Daily (1D Swing) BlackBox Scanner
===========================================================================

Evaluates the approved DhanHQ markets (NSE Top 100 Equities, NIFTY Indices, MCX Commodities)
on Daily (1D) OHLC historical candles against all 14 canonical PivotBoss strategies.
Syncs detected authentic 1D Swing execution signals to Supabase `shadow_signals`.

Approved Markets:
    - NIFTY / BANKNIFTY / FINNIFTY (Indices)
    - STOCKS (Top 100 Liquid NSE Equities)
    - MCX (Commodities: CRUDEOIL, GOLD, SILVER, NATURALGAS, COPPER, ZINC, ALUMINIUM)

Mandate Compliance:
    - Timeframe-Agnostic BlackBox Engine Extensibility (Version 5.0 Mandate)
    - Strict Fact-Backed Verification & Zero Unilateral Strategy Modification
    - H4/L4 Touch-Point Limit Gating: Omitted for Daily (1D) Timeframe (User Mandate Nov 21, 2026)
    - Symmetrical DMI Directional Momentum Gating for Divergences
"""

from __future__ import annotations
import os
import sys
import time
import argparse
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root and algo_engine to sys.path
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent

if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DailyScanner")

from algo_engine.feeds.dhan_feed import DhanFeed, EXCHANGE_NSE, EXCHANGE_MCX
from algo_engine.shadow_pipeline import ShadowPipeline
from algo_engine.data.nse_top100_master import NIFTY_100_SYMBOLS, clean_symbol
from algo_engine.nse100_scanner import MCX_COMMODITIES, CANONICAL_EXECUTION_TRIGGERS, is_mcx_symbol
from algo_engine.pivots import (
    OHLC, compute_daily_levels, compute_emas_from_bars, compute_pivot_trend_emas,
    compute_atr, compute_dmi, compute_m0_m10, compute_rsi, ValueArea, compute_opening_bias,
    compute_divergences, compute_institutional_bias_c1, compute_day_type_mx,
    detect_virgin_cpr_zones, detect_virgin_cpr_touches
)
from algo_engine.strategies import StrategyEngine, MarketContext, StrategySignal


class DailyBlackboxScanner:
    """Autonomous Daily (1D Swing) BlackBox Scanner for Approved Markets."""

    def __init__(self,
                 dhan_feed: Optional[DhanFeed] = None,
                 shadow_pipeline: Optional[ShadowPipeline] = None,
                 mock_mode: bool = False,
                 market: str = "all"):
        self.dhan_feed = dhan_feed or DhanFeed(mock_mode=mock_mode)
        self.shadow_pipeline = shadow_pipeline or ShadowPipeline()
        self.strategy_engine = StrategyEngine()
        self.mock_mode = mock_mode
        self.market = market.lower()

        # Build approved market symbol universe
        # 1. NSE Top 100 stocks
        nse_symbols = list(NIFTY_100_SYMBOLS)
        # 2. MCX Commodities
        mcx_symbols = [
            'CRUDEOIL', 'GOLD', 'SILVER', 'NATURALGAS', 'COPPER', 'ZINC', 'ALUMINIUM',
            'CRUDEOILM', 'GOLDM', 'SILVERM', 'NATURALGASM', 'ZINCM', 'ALUMINI'
        ]

        if self.market == "mcx":
            self.symbols = mcx_symbols
        elif self.market == "nse":
            self.symbols = nse_symbols
        else:
            self.symbols = nse_symbols + mcx_symbols

    def scan_symbol(self, sym: str) -> List[dict]:
        """
        Scan an individual symbol on Daily (1D) timeframe against all 14 canonical strategies.
        """
        clean = clean_symbol(sym)
        daily_candles = self.dhan_feed.fetch_daily_candles(clean, days=90)
        if not daily_candles or len(daily_candles) < 15:
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
            for c in daily_candles
        ]

        # Camarilla & CPR levels calculated from prior completed daily bar
        prev_b = bars[-2]
        levels = compute_daily_levels(prev_b.high, prev_b.low, prev_b.close)

        y_range = max(prev_b.high - prev_b.low, 0.01)
        y_poc = (prev_b.high + prev_b.low + prev_b.close) / 3.0
        va = ValueArea(
            vah=round(min(prev_b.high, y_poc + (y_range * 0.68 / 2.0)), 2),
            val=round(max(prev_b.low, y_poc - (y_range * 0.68 / 2.0)), 2),
            poc=round(y_poc, 2)
        )

        emas = compute_emas_from_bars(bars)
        trend_emas = compute_pivot_trend_emas(bars)
        atr_vals = compute_atr(bars)
        plus_di, minus_di = compute_dmi(bars)
        m0_series, m10_series = compute_m0_m10(bars)
        rsi_series = compute_rsi(bars, period=14)
        reg_bull, reg_bear, hidden_bull, hidden_bear = compute_divergences(bars, rsi_series=rsi_series, lookback=10)

        # Detect Virgin CPR zones on historical daily bars
        history_bars = [
            {'high': b.high, 'low': b.low, 'close': b.close}
            for b in bars[:-1]
        ]
        current_close = bars[-1].close
        vcpr_zones = detect_virgin_cpr_zones(history_bars, current_price=current_close, max_lookback_days=30)
        is_vcpr = len(vcpr_zones) > 0
        nearest_vcpr = vcpr_zones[0] if is_vcpr else None

        cur_bar = bars[-1]
        i = len(bars) - 1

        c1_bias = compute_institutional_bias_c1(
            close_price=cur_bar.close,
            open_price=cur_bar.open,
            dtc=levels.tc,
            dbc=levels.bc,
            ytc=levels.tc,
            ybc=levels.bc,
            h4=levels.H4,
            l4=levels.L4,
            prev_close=prev_b.close,
            dp=levels.pivot,
            tp=levels.pivot
        )

        mx_type = compute_day_type_mx(
            open_price=cur_bar.open,
            close_price=cur_bar.close,
            dDH=prev_b.high,
            dDL=prev_b.low,
            vah=va.vah,
            val=va.val,
            ytf_h=prev_b.high,
            ytf_l=prev_b.low,
            dtc=levels.tc,
            dbc=levels.bc
        )

        market_name = 'mcx' if is_mcx_symbol(clean) else 'nifty'
        market_category = 'MCX' if market_name == 'mcx' else ('NIFTY' if clean in ['NIFTY', 'BANKNIFTY', 'FINNIFTY'] else 'STOCKS')

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
            opening_bias='BULLISH' if cur_bar.open > levels.pivot else 'BEARISH',
            day_type_label=mx_type,
            institutional_bias=c1_bias,
            session_highest=max(b.high for b in bars),
            session_lowest=min(b.low for b in bars),
            prev_bar=prev_b,
            prev_close=prev_b.close,
            prev_open=prev_b.open,
            prev_cpr_top=max(levels.tc, levels.bc),
            prev_cpr_bottom=min(levels.tc, levels.bc),
            bull_regular_div=reg_bull[i - 1] if i > 0 else False,
            bear_regular_div=reg_bear[i - 1] if i > 0 else False,
            bull_hidden_div=hidden_bull[i - 1] if i > 0 else False,
            bear_hidden_div=hidden_bear[i - 1] if i > 0 else False,
            plus=plus_di[i] if i < len(plus_di) else 0.0,
            minus=minus_di[i] if i < len(minus_di) else 0.0,
            m0=m0_series[i] if i < len(m0_series) else 0.0,
            m10=m10_series[i] if i < len(m10_series) else 0.0,
            virgin_cpr_zones=vcpr_zones,
            timeframe='1D'
        )

        strat_sigs = self.strategy_engine.evaluate(ctx)

        # Detect direct Virgin CPR touch on daily bar
        vcpr_touches = detect_virgin_cpr_touches(
            history_bars,
            current_price=cur_bar.close,
            high_price=cur_bar.high,
            low_price=cur_bar.low,
            prev_close=prev_b.close,
            max_lookback_days=30
        )
        for touch in vcpr_touches:
            is_long = touch['is_support']
            sig_name = 'LONG VIRGIN CPR' if is_long else 'SHORT VIRGIN CPR'
            if not any(s.name == sig_name for s in strat_sigs):
                entry_p = touch['entry_price']
                atr_v = atr_vals[i] if i < len(atr_vals) else 1.0
                sl_p = entry_p - 0.75 * atr_v if is_long else entry_p + 0.75 * atr_v
                tp1_p = entry_p + 2.5 * atr_v if is_long else entry_p - 2.5 * atr_v
                tp2_p = entry_p + 4.0 * atr_v if is_long else entry_p - 4.0 * atr_v
                tp3_p = entry_p + 6.5 * atr_v if is_long else entry_p - 6.5 * atr_v
                tp4_p = entry_p + 8.0 * atr_v if is_long else entry_p - 8.0 * atr_v

                touch_sig = StrategySignal(
                    name=sig_name,
                    direction='LONG' if is_long else 'SHORT',
                    entry_price=entry_p,
                    stop_loss=sl_p,
                    tp1=tp1_p, tp2=tp2_p, tp3=tp3_p, tp4=tp4_p,
                    bar_index=i,
                    timestamp=cur_bar.timestamp,
                    zone='LONG ZONE' if is_long else 'SHORT ZONE',
                    opening_bias='BULLISH' if cur_bar.open > levels.pivot else 'BEARISH',
                    day_type=mx_type
                )
                strat_sigs.append(touch_sig)

        signals: List[dict] = []
        now_utc = datetime.now(timezone.utc)
        now_iso = now_utc.isoformat()
        bar_date_ist = datetime.fromtimestamp(cur_bar.timestamp, tz=timezone(timedelta(hours=5, minutes=30)))
        entry_day_str = bar_date_ist.strftime("%Y-%m-%d")

        for sig in strat_sigs:
            if sig.name not in CANONICAL_EXECUTION_TRIGGERS:
                continue

            trade_id = f"DHAN_{market_category}_{clean}_{entry_day_str}_{sig.name.replace(' ', '_')}_1D"

            signals.append({
                'symbol': clean,
                'type': sig.name,
                'trigger': f'{sig.name} Trigger',
                'entry': round(float(sig.entry_price), 2),
                'stop': round(float(sig.stop_loss), 2),
                'target': round(float(sig.tp1), 2),
                'tp2': round(float(sig.tp2), 2),
                'tp3': round(float(sig.tp3), 2),
                'tp4': round(float(sig.tp4), 2),
                'timeframe': '1D',
                'status': 'ACTIVE LIMIT',
                'outcome': 'OPEN',
                'source': 'blackbox_dhan',
                'exchange': 'MCX' if is_mcx_symbol(clean) else 'NSE',
                'fire_alert': sig.fire_alert,
                'fire_zone': sig.fire_zone,
                'signal_ts': now_iso,
                'created_at': now_iso,
                'metadata': {
                    'trade_id': trade_id,
                    'timeframe': '1D',
                    'interval': '1D',
                    'day_type': mx_type,
                    'opening_bias': 'BULLISH' if cur_bar.open > levels.pivot else 'BEARISH',
                    'market_category': market_category,
                    'source_feed': 'DhanHQ',
                    'is_confluence': sig.is_confluence,
                    'confluence_type': sig.confluence_tag,
                    'fire_alert': sig.fire_alert,
                    'fire_zone': sig.fire_zone,
                    'prev_high': round(float(prev_b.high), 2),
                    'prev_low': round(float(prev_b.low), 2),
                    'open_price': round(float(cur_bar.open), 2),
                    'dtc': round(float(levels.tc), 2),
                    'dbc': round(float(levels.bc), 2),
                    'h4': round(float(levels.H4), 2),
                    'l4': round(float(levels.L4), 2),
                    'cmp': round(float(cur_bar.close), 2),
                    'entry_time': now_iso,
                    'entryDate': bar_date_ist.strftime("%d %b, %H:%M IST"),
                    'is_vcpr': is_vcpr or len(vcpr_touches) > 0,
                    'is_vcpr_touch': bool(sig.name in ('LONG VIRGIN CPR', 'SHORT VIRGIN CPR') or len(vcpr_touches) > 0),
                    'engine_version': '5.0.0'
                }
            })

        return signals

    def scan_all(self, limit: Optional[int] = None) -> List[dict]:
        """Scan all approved market symbols on Daily (1D) timeframe and sync to Supabase."""
        symbols = self.symbols[:limit] if limit else self.symbols
        logger.info(f"[DailyScanner] Starting 1D Swing scan across {len(symbols)} approved symbols ({self.market.upper()})...")

        all_signals: List[dict] = []
        start_t = time.time()

        for idx, sym in enumerate(symbols, 1):
            try:
                sigs = self.scan_symbol(sym)
                if sigs:
                    for s in sigs:
                        logger.info(f"  [{idx}/{len(symbols)}] 🚨 1D SWING SIGNAL: {sym} -> {s['type']} @ {s['entry']}")
                    all_signals.extend(sigs)
            except Exception as e:
                logger.debug(f"[DailyScanner] Error scanning {sym}: {e}")

        duration = time.time() - start_t
        logger.info(f"[DailyScanner] Scan finished in {duration:.2f}s. Detected {len(all_signals)} authentic 1D Swing signals.")

        # Sync to Supabase shadow_signals
        if self.shadow_pipeline and all_signals:
            synced_count = 0
            for sig in all_signals:
                try:
                    self.shadow_pipeline.sync_signal(sig)
                    synced_count += 1
                except Exception as e:
                    logger.warning(f"[DailyScanner] Error syncing signal for {sig.get('symbol')}: {e}")
            logger.info(f"[DailyScanner] Successfully synced {synced_count} Daily 1D Swing signals to Supabase shadow_signals.")

        return all_signals


def main():
    parser = argparse.ArgumentParser(description="TLCS Daily (1D Swing) BlackBox Scanner (Approved Markets: NIFTY, STOCKS, MCX)")
    parser.add_argument("--market", type=str, default="all", choices=["all", "nse", "mcx"], help="Approved market universe to scan: 'all' (NSE + MCX), 'nse', or 'mcx'")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of symbols to scan")
    parser.add_argument("--mock", action="store_true", help="Force mock data mode without live API calls")
    args = parser.parse_args()

    scanner = DailyBlackboxScanner(mock_mode=args.mock, market=args.market)
    signals = scanner.scan_all(limit=args.limit)
    print(f"\n[SUMMARY] Daily 1D Swing BlackBox Scan Complete. Total Signals Detected: {len(signals)}")


if __name__ == "__main__":
    main()
