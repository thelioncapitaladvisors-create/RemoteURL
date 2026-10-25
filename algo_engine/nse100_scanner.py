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
from datetime import datetime, timezone, timedelta

from .data.nse_top100_master import get_all_nse100_symbols, clean_symbol
from .feeds.dhan_feed import DhanFeed
from .pivots import (
    OHLC, compute_daily_levels, compute_emas_from_bars,
    compute_atr, compute_pivot_trend_emas, compute_value_area_from_bars,
    compute_opening_bias, compute_dmi, compute_m0_m10,
    compute_institutional_bias_c1, compute_day_type_mx
)
from .day_types import DayTypeClassifier
from .strategies import StrategyEngine, StrategySignal, MarketContext
from .shadow_pipeline import ShadowPipeline

logger = logging.getLogger('NSE100Scanner')

# ════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════
# IST TIME & MARKET HOURS HELPERS
# ════════════════════════════════════════════════════════════════════

MCX_COMMODITIES: List[str] = [
    'CRUDEOIL', 'GOLD', 'SILVER', 'NATURALGAS', 'COPPER', 'ZINC', 'ALUMINIUM',
    'CRUDEOILM', 'GOLDM', 'SILVERM', 'NATURALGASM', 'ZINCM', 'ALUMINI'
]

# 12 Canonical Strategy Triggers (Zero Speculation STP 2.0 Execution Rule)
CANONICAL_EXECUTION_TRIGGERS = {
    'LONG MISSILE', 'SHORT MISSILE',
    'LONG SCALP', 'SHORT SCALP',
    'LONG LIGHTNING', 'SHORT LIGHTNING',
    'LONG DIVERGENCE', 'SHORT DIVERGENCE',
    'LONG HIDDEN DIVERGENCE', 'SHORT HIDDEN DIVERGENCE',
    'LONG EXTREME REVERSAL', 'SHORT EXTREME REVERSAL'
}



def clean_symbol(sym: str) -> str:
    """Normalize symbol string."""
    s = sym.upper().strip()
    if s.startswith('NSE:'): s = s[4:]
    if s.startswith('MCX:'): s = s[4:]
    if s.endswith('1!'): s = s[:-2]
    if s.endswith('!'): s = s[:-1]
    return s


def is_mcx_symbol(sym: str) -> bool:
    """Check if symbol belongs to MCX commodity market."""
    clean = clean_symbol(sym)
    return clean in MCX_COMMODITIES or any(
        clean.startswith(c) for c in ['GOLD', 'SILVER', 'CRUDEOIL', 'NATURALGAS', 'COPPER', 'ZINC', 'ALUMINI']
    )


def get_ist_time(dt: Optional[datetime] = None) -> datetime:
    """Return datetime in Indian Standard Time (UTC+5:30)."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=5, minutes=30)))


# Official Indian Exchange Trading Holidays 2026 (NSE & MCX)
NSE_HOLIDAYS_2026 = {
    "2026-01-15", "2026-01-26", "2026-03-03", "2026-03-26", "2026-03-31",
    "2026-04-03", "2026-04-14", "2026-05-01", "2026-05-28", "2026-06-26",
    "2026-09-14", "2026-10-02", "2026-10-20", "2026-11-10", "2026-11-24",
    "2026-12-25"
}

MCX_FULL_HOLIDAYS_2026 = {
    "2026-01-26", "2026-04-03", "2026-10-02", "2026-12-25"
}

MCX_MORNING_HOLIDAYS_2026 = {
    "2026-01-15", "2026-03-03", "2026-03-26", "2026-03-31", "2026-04-14",
    "2026-05-01", "2026-05-28", "2026-06-26", "2026-09-14", "2026-10-20",
    "2026-11-10", "2026-11-24"
}


def is_nse_entry_allowed_now() -> bool:
    """Check if trade entry is allowed for NSE Equities (09:15 to 14:00 IST, excluding holidays)."""
    ist = get_ist_time()
    if ist.weekday() >= 5: return False
    date_str = ist.strftime("%Y-%m-%d")
    if date_str in NSE_HOLIDAYS_2026: return False
    mins = ist.hour * 60 + ist.minute
    return 555 <= mins < 840


def is_mcx_entry_allowed_now() -> bool:
    """Check if trade entry is allowed for MCX Commodities (09:00 to 22:00 IST, respecting holidays)."""
    ist = get_ist_time()
    if ist.weekday() >= 5: return False
    date_str = ist.strftime("%Y-%m-%d")
    if date_str in MCX_FULL_HOLIDAYS_2026: return False
    mins = ist.hour * 60 + ist.minute
    if date_str in MCX_MORNING_HOLIDAYS_2026:
        return 1020 <= mins < 1320
    return 540 <= mins < 1320


def is_trade_entry_allowed_for_bar(sym: str, timestamp: Optional[float] = None) -> bool:
    """
    Check if trade entry is allowed for a specific symbol and candle timestamp.
    - NSE: 09:15 to 14:00 IST (2:00 PM cutoff, excluding holidays)
    - MCX: 09:00 to 22:00 IST (10:00 PM cutoff, respecting morning/full holidays)
    """
    if timestamp is not None:
        t = timestamp / 1000.0 if timestamp > 1e11 else timestamp
        dt_utc = datetime.fromtimestamp(t, tz=timezone.utc)
        ist = get_ist_time(dt_utc)
    else:
        ist = get_ist_time()

    if ist.weekday() >= 5: return False
    date_str = ist.strftime("%Y-%m-%d")
    mins = ist.hour * 60 + ist.minute

    if is_mcx_symbol(sym):
        if date_str in MCX_FULL_HOLIDAYS_2026:
            return False
        if date_str in MCX_MORNING_HOLIDAYS_2026:
            # Evening session entry: 17:00 to 22:00 IST (cutoff)
            return 1020 <= mins < 1320
        return 540 <= mins < 1320

    # NSE Equities
    if date_str in NSE_HOLIDAYS_2026:
        return False
    return 555 <= mins < 840


def is_nse_market_open_now() -> bool:
    """Check if official NSE trading hours are active (09:15 to 15:30 IST, Mon-Fri, excluding holidays)."""
    ist = get_ist_time()
    if ist.weekday() >= 5: return False
    date_str = ist.strftime("%Y-%m-%d")
    if date_str in NSE_HOLIDAYS_2026:
        return False
    mins = ist.hour * 60 + ist.minute
    return 555 <= mins < 930


def is_mcx_market_open_now() -> bool:
    """Check if official MCX trading hours are active (09:00 to 23:30 IST, Mon-Fri, respecting morning/full holidays)."""
    ist = get_ist_time()
    if ist.weekday() >= 5: return False
    date_str = ist.strftime("%Y-%m-%d")
    if date_str in MCX_FULL_HOLIDAYS_2026:
        return False
    mins = ist.hour * 60 + ist.minute
    if date_str in MCX_MORNING_HOLIDAYS_2026:
        # Evening session: 17:00 to 23:30 IST
        return 1020 <= mins < 1410
    return 540 <= mins < 1410


class NSE100Scanner:
    """
    Autonomous 15-minute multi-asset scanner for Top 100 NSE stocks and MCX commodities.
    """

    def __init__(self,
                 dhan_feed: Optional[DhanFeed] = None,
                 shadow_pipeline: Optional[ShadowPipeline] = None,
                 mock_mode: bool = False,
                 market: str = "all"):
        self.dhan_feed = dhan_feed or DhanFeed(mock_mode=mock_mode)
        self.shadow_pipeline = shadow_pipeline or ShadowPipeline()
        self.strategy_engine = StrategyEngine()
        self.day_type_classifiers: Dict[str, DayTypeClassifier] = {}
        self.mock_mode = mock_mode
        self.market = market.lower()

        nse_symbols = get_all_nse100_symbols()
        mcx_symbols = list(MCX_COMMODITIES)

        if self.market == "mcx":
            self.symbols = mcx_symbols
        elif self.market == "nse":
            self.symbols = nse_symbols
        else:
            self.symbols = nse_symbols + mcx_symbols

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
        plus_di, minus_di = compute_dmi(bars)
        m0_series, m10_series = compute_m0_m10(bars)

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

        # Check if trade entry allowed for this symbol right now
        if not self.mock_mode and not is_trade_entry_allowed_for_bar(clean):
            return []

        market_name = 'mcx' if is_mcx_symbol(clean) else 'nifty'
        market_category = 'MCX' if market_name == 'mcx' else 'NIFTY'
        signals: List[dict] = []

        # 5. Evaluate strategy engine across completed bars of the session
        # Check latest bars for active trading signals
        eval_window = min(len(bars), 10)
        for i in range(len(bars) - eval_window, len(bars)):
            cur_bar = bars[i]

            # Rule: Don't generate new trades from bars completed after cutoff
            if not self.mock_mode and not is_trade_entry_allowed_for_bar(clean, cur_bar.timestamp):
                continue

            prev_b = bars[i - 1] if i > 0 else cur_bar

            # Compute institutional bias c1 and day type mX
            c1_bias = compute_institutional_bias_c1(
                close_price=cur_bar.close,
                open_price=cur_bar.open,
                dtc=levels.tc,
                dbc=levels.bc,
                ytc=daily.get('prev_tc', levels.tc),
                ybc=daily.get('prev_bc', levels.bc),
                h4=levels.H4,
                l4=levels.L4,
                prev_close=prev_b.close,
                dp=levels.pivot,
                tp=daily.get('prev_pivot', levels.pivot)
            )

            mx_type = compute_day_type_mx(
                open_price=cur_bar.open,
                close_price=cur_bar.close,
                dDH=daily['high'],
                dDL=daily['low'],
                vah=va.vah,
                val=va.val,
                ytf_h=daily['high'],
                ytf_l=daily['low'],
                dtc=levels.tc,
                dbc=levels.bc
            )

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
                day_type_label=mx_type if mx_type != "DEBUG" else primary_day_type,
                institutional_bias=c1_bias,
                session_highest=max(b.high for b in bars[:i + 1]),
                session_lowest=min(b.low for b in bars[:i + 1]),
                prev_bar=prev_b,
                plus=plus_di[i] if i < len(plus_di) else 0.0,
                minus=minus_di[i] if i < len(minus_di) else 0.0,
                m0=m0_series[i] if i < len(m0_series) else 0.0,
                m10=m10_series[i] if i < len(m10_series) else 0.0,
            )

            strat_sigs = self.strategy_engine.evaluate(ctx)
            for sig in strat_sigs:
                if sig.name not in CANONICAL_EXECUTION_TRIGGERS:
                    continue
                signals.append({
                    'symbol': clean,
                    'type': sig.name,
                    'trigger': f'{sig.name} Trigger',
                    'market': market_name,
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
                        'market_category': market_category,
                        'source_feed': 'DhanHQ',
                        'prev_high': round(float(daily['high']), 2),
                        'prev_low': round(float(daily['low']), 2),
                        'prev_range': round(float(max(daily['high'] - daily['low'], 0.01)), 2),
                        'open_price': round(float(bars[0].open), 2),
                        'dtc': round(float(levels.tc), 2),
                        'dbc': round(float(levels.bc), 2),
                        'cpr_width': round(float(abs(levels.tc - levels.bc)), 2),
                        'cpr_ratio': round(float((abs(levels.tc - levels.bc) / max(daily['high'] - daily['low'], 0.01)) * 100), 2),
                        'ytc': round(float(daily.get('prev_tc', 0.0)), 2),
                        'ybc': round(float(daily.get('prev_bc', 0.0)), 2),
                        'is_inside_cpr': bool(levels.tc < daily.get('prev_tc', 0.0) and levels.bc > daily.get('prev_bc', 0.0)) if (daily.get('prev_tc', 0.0) > 0 and daily.get('prev_bc', 0.0) > 0) else False,
                        'is_outside_cpr': bool(levels.tc > daily.get('prev_tc', 0.0) and levels.bc < daily.get('prev_bc', 0.0)) if (daily.get('prev_tc', 0.0) > 0 and daily.get('prev_bc', 0.0) > 0) else False,
                        'is_inside_day': bool(levels.tc < daily.get('prev_tc', 0.0) and levels.bc > daily.get('prev_bc', 0.0)) if (daily.get('prev_tc', 0.0) > 0 and daily.get('prev_bc', 0.0) > 0) else False,
                        'two_day_relationship': 'INSIDE' if (daily.get('prev_tc', 0.0) > 0 and daily.get('prev_bc', 0.0) > 0 and levels.tc < daily.get('prev_tc', 0.0) and levels.bc > daily.get('prev_bc', 0.0)) else ('OUTSIDE' if (daily.get('prev_tc', 0.0) > 0 and daily.get('prev_bc', 0.0) > 0 and levels.tc > daily.get('prev_tc', 0.0) and levels.bc < daily.get('prev_bc', 0.0)) else ('BULLISH' if (daily.get('prev_tc', 0.0) > 0 and levels.bc > daily.get('prev_tc', 0.0)) else ('BEARISH' if (daily.get('prev_bc', 0.0) > 0 and levels.tc < daily.get('prev_bc', 0.0)) else ('MODERATELY BULLISH' if (daily.get('prev_tc', 0.0) > 0 and levels.tc > daily.get('prev_tc', 0.0) and levels.bc > daily.get('prev_bc', 0.0)) else ('MODERATELY BEARISH' if (daily.get('prev_tc', 0.0) > 0 and levels.tc < daily.get('prev_tc', 0.0) and levels.bc < daily.get('prev_bc', 0.0)) else 'UNCHANGED'))))),
                        'h4': levels.H4,
                        'l4': levels.L4,
                        'vah': round(float(va.vah), 2),
                        'val': round(float(va.val), 2),
                        'is_oor': bool((bars[0].open < daily['low'] and bars[0].open < va.val) or (bars[0].open > daily['high'] and bars[0].open > va.vah)),
                        'is_ncpr': bool((abs(levels.tc - levels.bc) / max(daily['high'] - daily['low'], 0.01)) * 100 < 5.0),
                        'is_nval': bool((abs(levels.tc - levels.bc) / max(daily['high'] - daily['low'], 0.01)) * 100 < 5.0),
                        'is_nva': bool((abs(levels.tc - levels.bc) / max(daily['high'] - daily['low'], 0.01)) * 100 < 5.0),
                        'cpr_pivot': round(float(levels.pivot), 2),
                        'cpr_tc': round(float(levels.tc), 2),
                        'cpr_bc': round(float(levels.bc), 2)
                    }
                })

        return signals

    def exit_all_live_trades_at_market_close(self, target_market: str = 'ALL') -> int:
        """
        Ensure all DhanHQ live trades in shadow_signals are exited at market close.
        - NSE Equities market close: 15:30 IST
        - MCX Commodities market close: 23:30 IST
        - Unexecuted limits (ACTIVE without fill) -> CANCELLED
        - Live active trades (⚡ TRADE ACTIVE or with real entry) -> EOD Exit with realized exact_pct
        """
        if not self.shadow_pipeline or not self.shadow_pipeline._sb:
            logger.info("[NSE100Scanner] No active Supabase client for market close sweep.")
            return 0

        logger.info(f"[NSE100Scanner] Sweeping open DhanHQ trades for market close exit ({target_market})...")
        sb = self.shadow_pipeline._sb
        table = self.shadow_pipeline.table_name

        try:
            query = sb.from_(table).select("*").eq("source", "blackbox_dhan").or_(
                "outcome.eq.OPEN,outcome.eq.Open,outcome.is.null,status.ilike.%active%,status.ilike.%open%"
            )
            if target_market.upper() == 'NSE':
                query = query.eq("exchange", "nifty")
            elif target_market.upper() == 'MCX':
                query = query.eq("exchange", "mcx")
            res = query.execute()
            rows = res.data or []
        except Exception as e:
            logger.error(f"[NSE100Scanner] Failed fetching active DhanHQ signals: {e}")
            return 0

        if not rows:
            logger.info(f"[NSE100Scanner] No open DhanHQ signals to exit for market {target_market}.")
            return 0

        now_iso = datetime.now(timezone.utc).isoformat()
        closed_count = 0

        for r in rows:
            sig_id = r.get("id")
            st = (r.get("status") or "").upper()
            outcome = (r.get("outcome") or "").upper()
            
            if "CANCEL" in st or "CANCEL" in outcome or r.get("exit_price") is not None:
                continue

            meta = r.get("metadata") or {}
            if isinstance(meta, str):
                import json
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}

            sym = r.get("symbol", "")
            clean = clean_symbol(sym)

            # Determine exit price: try LTP, fallback to entry/close
            exit_price = None
            try:
                ltp = self.dhan_feed.fetch_ltp(clean)
                if ltp and ltp > 0:
                    exit_price = float(ltp)
            except Exception:
                pass

            if not exit_price:
                exit_price = float(r.get("entry") or r.get("entry_price") or 0.0)

            is_live_trade = (
                "TRADE ACTIVE" in st or 
                "⚡" in st or 
                meta.get("real_entry_time") is not None or
                r.get("trigger") == "TradeFill"
            )

            if not is_live_trade:
                # Unexecuted limit order -> Immediately delete (TradingView Zero-Ghost Parity)
                try:
                    sb.from_(table).delete().eq("id", sig_id).execute()
                    closed_count += 1
                    logger.info(f"[NSE100Scanner] Deleted expired unexecuted limit at market close: {clean} ({sig_id})")
                except Exception as e:
                    logger.error(f"[NSE100Scanner] Error deleting expired limit {sig_id}: {e}")
                continue
            else:
                # Executed Live trade -> EOD Exit
                entry = float(r.get("entry") or r.get("entry_price") or exit_price)
                sig_type = (r.get("type") or "").upper()
                is_short = "SHORT" in sig_type or "SELL" in sig_type

                if entry > 0 and exit_price > 0:
                    exact_pct = ((entry - exit_price) / entry) * 100 if is_short else ((exit_price - entry) / entry) * 100
                else:
                    exact_pct = 0.0

                exact_pct = round(exact_pct, 2)
                meta["exact_pct"] = exact_pct
                meta["exit_reason"] = "MARKET_CLOSE_EOD_EXIT"
                meta["exit_level"] = "EOD"

                if exact_pct > 0.005:
                    final_outcome = "WIN"
                    status_label = "EOD Exit (TP)"
                elif exact_pct < -0.005:
                    final_outcome = "LOSS"
                    status_label = "EOD Exit (SL)"
                else:
                    final_outcome = "BREAKEVEN"
                    status_label = "EOD Exit (BE)"

                update_payload = {
                    "status": status_label,
                    "outcome": final_outcome,
                    "exit_price": round(exit_price, 2),
                    "exit_at": now_iso,
                    "updated_at": now_iso,
                    "metadata": meta
                }

            try:
                sb.from_(table).update(update_payload).eq("id", sig_id).execute()
                closed_count += 1
                logger.info(f"[NSE100Scanner] Closed DhanHQ trade at market close: {clean} -> {update_payload.get('status')}")
            except Exception as e:
                logger.error(f"[NSE100Scanner] Error closing trade {sig_id}: {e}")

        logger.info(f"[NSE100Scanner] Market close sweep complete. Settled {closed_count} DhanHQ trades ({target_market}).")
        return closed_count

    def run_scan_cycle(self, limit: Optional[int] = None) -> List[dict]:
        """
        Execute one full scan cycle across active assets (NSE stocks and/or MCX commodities).
        Enforces dual-market cutoff hours and dual-market close sweeps:
        - NSE: cutoff 14:00 IST, close sweep 15:30 IST
        - MCX: cutoff 22:00 IST, close sweep 23:30 IST
        """
        ist = get_ist_time()
        mins = ist.hour * 60 + ist.minute

        # Check market close exit sweeps
        if mins >= 930 and mins < 945:
            # At 15:30 IST: Sweep NSE Equities
            self.exit_all_live_trades_at_market_close("NSE")
        if mins >= 1410 or ist.weekday() >= 5:
            # At 23:30 IST or weekend: Sweep MCX Commodities
            self.exit_all_live_trades_at_market_close("MCX")
            if ist.weekday() >= 5:
                logger.info(f'[NSE100Scanner] Weekend detected. Indian markets are closed.')
                return []

        nse_open = is_nse_market_open_now()
        mcx_open = is_mcx_market_open_now()

        # Filter target symbols based on currently open market sessions
        active_symbols = [
            sym for sym in self.symbols
            if (is_mcx_symbol(sym) and mcx_open) or (not is_mcx_symbol(sym) and nse_open)
        ]

        # In mock mode, allow scanning all symbols for offline testing
        if self.mock_mode and not active_symbols:
            active_symbols = self.symbols

        if not active_symbols:
            logger.info(f'[NSE100Scanner] No markets open ({ist.strftime("%H:%M:%S")} IST). Status: NSE={nse_open}, MCX={mcx_open}.')
            return []

        target_symbols = active_symbols[:limit] if limit else active_symbols
        logger.info(f'[NSE100Scanner] Starting 15m scan cycle across {len(target_symbols)} symbols at {ist.strftime("%H:%M:%S")} IST (NSE: {nse_open}, MCX: {mcx_open})...')
        
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
