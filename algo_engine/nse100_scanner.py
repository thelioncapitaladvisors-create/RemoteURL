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
    compute_opening_bias
)
from .day_types import DayTypeClassifier
from .strategies import StrategyEngine, StrategySignal, MarketContext
from .shadow_pipeline import ShadowPipeline

logger = logging.getLogger('NSE100Scanner')

# ════════════════════════════════════════════════════════════════════
# IST TIME & MARKET HOURS HELPERS
# ════════════════════════════════════════════════════════════════════

def get_ist_time(dt: Optional[datetime] = None) -> datetime:
    """Return datetime in Indian Standard Time (UTC+5:30)."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=5, minutes=30)))


def is_after_2pm_ist(timestamp: Optional[float] = None) -> bool:
    """
    Check if the given timestamp (or current time if None) is at or after 14:00 (2:00 PM) IST.
    DhanHQ Rule: Do not generate new trades after 2:00 PM IST.
    """
    if timestamp is not None:
        t = timestamp / 1000.0 if timestamp > 1e11 else timestamp
        dt_utc = datetime.fromtimestamp(t, tz=timezone.utc)
        ist = get_ist_time(dt_utc)
    else:
        ist = get_ist_time()
    
    # 2:00 PM IST is 14:00 (840 minutes from midnight IST)
    return (ist.hour > 14) or (ist.hour == 14 and (ist.minute > 0 or ist.second > 0))


def is_dhan_trade_entry_allowed_now() -> bool:
    """
    Check if new trade generation is currently allowed for DhanHQ signals.
    Window: Monday-Friday, 09:15 to 14:00 IST (2:00 PM IST cutoff).
    No new trade generation is permitted after 2:00 PM IST.
    """
    ist = get_ist_time()
    if ist.weekday() >= 5:  # Saturday or Sunday
        return False
    mins = ist.hour * 60 + ist.minute
    # 09:15 is 555 mins, 14:00 (2:00 PM) is 840 mins
    return 555 <= mins < 840


def is_nse_market_open_now() -> bool:
    """
    Check if the current time is within official NSE trading hours (09:15 to 15:30 IST, Mon-Fri).
    """
    ist = get_ist_time()
    if ist.weekday() >= 5:
        return False
    mins = ist.hour * 60 + ist.minute
    return 555 <= mins < 930


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

        # Rule: Do not generate new trades after 2:00 PM IST (14:00)
        if not is_dhan_trade_entry_allowed_now():
            return []

        signals: List[dict] = []

        # 5. Evaluate strategy engine across completed bars of the session
        # Check latest bars for active trading signals
        eval_window = min(len(bars), 10)
        for i in range(len(bars) - eval_window, len(bars)):
            cur_bar = bars[i]

            # Rule: Don't generate new trades from bars completed after 2:00 PM IST (14:00)
            if is_after_2pm_ist(cur_bar.timestamp):
                continue

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

        # Also register blueprint signals if active (only before 2:00 PM IST)
        if not is_after_2pm_ist(bars[-1].timestamp):
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

    def exit_all_live_trades_at_market_close(self) -> int:
        """
        Ensure all DhanHQ live trades in shadow_signals are exited at market close (15:30 IST).
        - Unexecuted limits (ACTIVE without fill) -> CANCELLED
        - Live active trades (⚡ TRADE ACTIVE or with real entry) -> EOD Exit with realized exact_pct
        """
        if not self.shadow_pipeline or not self.shadow_pipeline._sb:
            logger.info("[NSE100Scanner] No active Supabase client for market close sweep.")
            return 0

        logger.info("[NSE100Scanner] Sweeping open DhanHQ trades for market close exit (15:30 IST)...")
        sb = self.shadow_pipeline._sb
        table = self.shadow_pipeline.table_name

        try:
            res = sb.from_(table).select("*").eq("source", "blackbox_dhan").or_(
                "outcome.eq.OPEN,outcome.eq.Open,outcome.is.null,status.ilike.%active%,status.ilike.%open%"
            ).execute()
            rows = res.data or []
        except Exception as e:
            logger.error(f"[NSE100Scanner] Failed fetching active DhanHQ signals: {e}")
            return 0

        if not rows:
            logger.info("[NSE100Scanner] No open DhanHQ signals to exit.")
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
                (r.get("updated_at") and r.get("updated_at") != r.get("created_at")) or 
                meta.get("real_entry_time")
            )

            if not is_live_trade:
                # Unexecuted limit order -> CANCELLED
                meta["exit_reason"] = "MARKET_CLOSE_EXPIRED_LIMIT"
                update_payload = {
                    "status": "CANCELLED",
                    "outcome": "CANCELLED",
                    "updated_at": now_iso,
                    "metadata": meta
                }
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

        logger.info(f"[NSE100Scanner] Market close sweep complete. Settled {closed_count} DhanHQ trades.")
        return closed_count

    def run_scan_cycle(self, limit: Optional[int] = None) -> List[dict]:
        """
        Execute one full scan cycle across the Top 100 NSE basket.
        Enforces 2:00 PM cutoff (no new trades generated after 14:00 IST)
        and market close sweep (all live trades exited at 15:30 IST).
        """
        ist = get_ist_time()

        # If market is closed (>= 15:30 IST or weekend), sweep all live trades to exit
        if (ist.hour > 15) or (ist.hour == 15 and ist.minute >= 30) or ist.weekday() >= 5:
            logger.info(f'[NSE100Scanner] Market is closed ({ist.strftime("%H:%M:%S")} IST). Running market close exit sweep...')
            self.exit_all_live_trades_at_market_close()
            return []

        # If past 2:00 PM IST (14:00), do not generate new trades
        if is_after_2pm_ist():
            logger.info(f'[NSE100Scanner] Past 2:00 PM IST cutoff ({ist.strftime("%H:%M:%S")} IST). No new trades will be generated for DhanHQ signals.')
            return []

        target_symbols = self.symbols[:limit] if limit else self.symbols
        logger.info(f'[NSE100Scanner] Starting 15m scan cycle across {len(target_symbols)} symbols at {ist.strftime("%H:%M:%S")} IST...')
        
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
