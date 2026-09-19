"""
algo_engine.day_types — Day Type Blueprints & Trade Sequences
=============================================================

Port of Pine Script TLCS_Sequence_Dashboard.pine (793 lines).
Implements 5 Day Type Blueprints and 4 Trade Sequences with exact
mathematical conditions matching the Pine Script f_calc() function.

Source Reference:
    TV Indicator/TLCS_Sequence_Dashboard.pine  lines 136-321

Day Type Blueprints (Canonical Names — DO NOT ALTER):
    1. Rejection Day Blueprint
    2. Absorption Day Blueprint
    3. Failed New Low Blueprint
    4. Outside Day Blueprint
    5. Stop Run Day Blueprint

Trade Sequences (Canonical Names — DO NOT ALTER):
    1. Rejection Day Sequence
    2. Stop Run Sequence
    3. Failed Absorption Sequence
    4. Accumulation / Distribution Sequence
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from .pivots import OHLC, compute_adr, highest, lowest, bars_since


# ════════════════════════════════════════════════════════════════════
# CONFIGURATION (Default Pine Script Input Parameters)
# ════════════════════════════════════════════════════════════════════

@dataclass
class DayTypeConfig:
    """
    Configuration parameters matching Pine Script inputs (lines 22-77).
    All values here are the Pine Script defaults.
    """
    # Shared: ADR Lookback
    adr_len: int = 10                    # line 23: adrLen

    # Accumulation / Distribution
    acc_len: int = 20                    # line 27: accLen
    acc_max_range_mult: float = 3.0      # line 28: accMaxRangeMult

    # Rejection Day — Range
    adr_mult_min: float = 1.25           # line 32: adrMultMin

    # Rejection Day — Tail / Body
    tail_body_mult: float = 2.5          # line 35: tailBodyMult

    # Rejection Day — Close Location
    close_zone_pct: float = 0.35         # line 38: closeZonePct (35 / 100)

    # Rejection Day — Location / Structure
    use_structure: bool = True           # line 41: useStructure
    struct_len: int = 20                 # line 42: structLen
    struct_tol_pct: float = 0.01         # line 43: structTolPct (1.0 / 100)

    # Outside Day — Range
    od_adr_mult_min: float = 1.05        # line 47: odAdrMultMin

    # FNL/FNH — Range
    adr_min_pct: float = 0.75            # line 51: adrMinPct (75 / 100)

    # FNL/FNH — Sweep
    sweep_lookback: int = 1              # line 54: sweepLookback

    # FNL/FNH — Close Location
    require_above_y_mid: bool = True     # line 57: requireAboveYMid

    # Absorption Day — Range
    abs_adr_max_mult: float = 0.75       # line 61: absAdrMaxMult

    # Absorption Day — Location
    abs_mid_tol_pct: float = 0.01        # line 64: absMidTolPct (1.0 / 100)

    # Absorption Day — Close Confirmation
    require_body_confirm: bool = True    # line 67: requireBodyConfirm

    # Stop Run Day — Range
    srd_adr_mult_min: float = 2.0        # line 71: srdAdrMultMin

    # Stop Run Day — Close Location
    srd_close_zone_pct: float = 0.15     # line 74: srdCloseZonePct (15 / 100)

    # Stop Run Day — Structure
    srd_struct_len: int = 5              # line 77: srdStructLen


# ════════════════════════════════════════════════════════════════════
# RESULT DATA STRUCTURES
# ════════════════════════════════════════════════════════════════════

@dataclass
class DayTypeResult:
    """Result of Day Type Blueprint classification for a single bar."""
    # Day Type Blueprints (canonical names)
    bull_rejection: bool = False
    bear_rejection: bool = False
    bull_absorption: bool = False
    bear_absorption: bool = False
    bull_fnl: bool = False           # Failed New Low
    bear_fnh: bool = False           # Failed New High
    bull_outside_day: bool = False
    bear_outside_day: bool = False
    bull_stop_run: bool = False
    bear_stop_run: bool = False

    # Trade Sequences
    bull_acc: bool = False            # Accumulation
    bear_dist: bool = False           # Distribution
    bull_fade: bool = False           # Fade after Stop Run
    bear_fade: bool = False
    bull_failed_breakout: bool = False
    bear_failed_breakout: bool = False
    bull_retest_srd: bool = False     # Retest after Stop Run
    bear_retest_srd: bool = False
    bull_continuation: bool = False
    bear_continuation: bool = False

    def get_active_blueprints(self) -> List[str]:
        """Return list of active Day Type Blueprint names."""
        result = []
        if self.bull_rejection:
            result.append("Rejection Day Blueprint (Bullish)")
        if self.bear_rejection:
            result.append("Rejection Day Blueprint (Bearish)")
        if self.bull_absorption:
            result.append("Absorption Day Blueprint (Bullish)")
        if self.bear_absorption:
            result.append("Absorption Day Blueprint (Bearish)")
        if self.bull_fnl:
            result.append("Failed New Low Blueprint (Bullish)")
        if self.bear_fnh:
            result.append("Failed New Low Blueprint (Bearish)")
        if self.bull_outside_day:
            result.append("Outside Day Blueprint (Bullish)")
        if self.bear_outside_day:
            result.append("Outside Day Blueprint (Bearish)")
        if self.bull_stop_run:
            result.append("Stop Run Day Blueprint (Bullish)")
        if self.bear_stop_run:
            result.append("Stop Run Day Blueprint (Bearish)")
        return result

    def get_active_sequences(self) -> List[str]:
        """Return list of active Trade Sequence names."""
        result = []
        if self.bull_rejection or self.bear_rejection:
            result.append("Rejection Day Sequence")
        if self.bull_stop_run or self.bear_stop_run:
            result.append("Stop Run Sequence")
        if self.bull_failed_breakout or self.bear_failed_breakout or \
           self.bull_retest_srd or self.bear_retest_srd:
            result.append("Failed Absorption Sequence")
        if self.bull_acc or self.bear_dist:
            result.append("Accumulation / Distribution Sequence")
        return result

    def has_any_signal(self) -> bool:
        """True if any Day Type or Sequence is active."""
        return any([
            self.bull_rejection, self.bear_rejection,
            self.bull_absorption, self.bear_absorption,
            self.bull_fnl, self.bear_fnh,
            self.bull_outside_day, self.bear_outside_day,
            self.bull_stop_run, self.bear_stop_run,
            self.bull_acc, self.bear_dist,
            self.bull_fade, self.bear_fade,
            self.bull_failed_breakout, self.bear_failed_breakout,
            self.bull_retest_srd, self.bear_retest_srd,
            self.bull_continuation, self.bear_continuation,
        ])

    def to_webhook_dict(self) -> Dict[str, str]:
        """Convert to webhook JSON format matching Pine Script f_build_json_row."""
        def _dir(bull, bear):
            if bull:
                return "Bullish"
            if bear:
                return "Bearish"
            return "NONE"

        return {
            "acc":  _dir(self.bull_acc, self.bear_dist),
            "rej":  _dir(self.bull_rejection, self.bear_rejection),
            "srd":  _dir(self.bull_stop_run, self.bear_stop_run),
            "out":  _dir(self.bull_outside_day, self.bear_outside_day),
            "fade": _dir(self.bull_fade, self.bear_fade),
            "abs":  _dir(self.bull_absorption, self.bear_absorption),
            "fnl":  _dir(self.bull_fnl, self.bear_fnh),
            "fb":   _dir(self.bull_failed_breakout, self.bear_failed_breakout),
            "rt":   _dir(self.bull_retest_srd, self.bear_retest_srd),
            "cont": _dir(self.bull_continuation, self.bear_continuation),
        }


# ════════════════════════════════════════════════════════════════════
# STATEFUL SEQUENCE TRACKER
# ════════════════════════════════════════════════════════════════════

@dataclass
class SequenceState:
    """
    Tracks persistent state across bars for Trade Sequences.
    
    Mirrors the `var` variables in Pine Script's f_calc() (lines 186-232).
    Must be maintained across daily bars for each symbol independently.
    """
    # Rejection Day Sequence State (lines 186-193)
    rej_active_mid: Optional[float] = None
    rej_active_high: Optional[float] = None
    rej_active_low: Optional[float] = None
    bull_rej_active: bool = False
    bear_rej_active: bool = False

    # Failed Absorption Context (lines 192-193)
    bull_failed_abs_active: bool = False
    bear_failed_abs_active: bool = False

    # Stop Run Day Sequence State (lines 229-232)
    srd_active_mid: Optional[float] = None
    srd_active_ext: Optional[float] = None
    bull_srd_active: bool = False
    bear_srd_active: bool = False

    # Continuation Day Tracking (lines 310-311)
    prev_active_day_bull: bool = False
    prev_active_day_bear: bool = False


# ════════════════════════════════════════════════════════════════════
# CORE CLASSIFIER ENGINE
# ════════════════════════════════════════════════════════════════════

class DayTypeClassifier:
    """
    Stateful Day Type Blueprint and Trade Sequence classifier.
    
    Replicates Pine Script f_calc() function (lines 136-321) bar-by-bar.
    Must be instantiated per-symbol and updated with each daily bar.
    
    Usage:
        classifier = DayTypeClassifier()
        for bar in daily_bars:
            result = classifier.evaluate(bar)
            if result.has_any_signal():
                print(f"{bar.timestamp}: {result.get_active_blueprints()}")
    """

    def __init__(self, config: Optional[DayTypeConfig] = None):
        self.config = config or DayTypeConfig()
        self.state = SequenceState()

        # Historical data for lookback calculations
        self._bars: List[OHLC] = []
        self._highs: List[float] = []
        self._lows: List[float] = []
        self._closes: List[float] = []
        self._opens: List[float] = []
        self._adr_values: List[float] = []

        # Track which bars triggered rejection / stop run for barsSince
        self._rej_triggered: List[bool] = []
        self._srd_triggered: List[bool] = []
        self._fa_triggered: List[bool] = []  # Failed absorption context activation

    def evaluate(self, bar: OHLC) -> DayTypeResult:
        """
        Evaluate a single daily bar and return all Day Type / Sequence signals.
        
        This is the Python port of Pine Script f_calc() (lines 136-321).
        Must be called with daily bars in chronological order.
        
        Args:
            bar: Daily OHLC bar to evaluate
        
        Returns:
            DayTypeResult with all 20 boolean signal flags
        """
        cfg = self.config
        result = DayTypeResult()

        # ── Append bar to history ──
        idx = len(self._bars)
        self._bars.append(bar)
        self._highs.append(bar.high)
        self._lows.append(bar.low)
        self._closes.append(bar.close)
        self._opens.append(bar.open)

        # ── Base Pre-Calculations (lines 137-144) ──
        rng = bar.range
        body = bar.body
        up_wick = bar.upper_wick
        dn_wick = bar.lower_wick
        mid = bar.midpoint
        close_pos = bar.close_position

        # ── ADR: ta.sma(ta.tr(true), adrLen)[1] (line 143) ──
        # Compute True Range for this bar
        prev_close = self._closes[idx - 1] if idx > 0 else None
        tr = max(rng, abs(bar.high - prev_close), abs(bar.low - prev_close)) \
            if prev_close is not None else rng

        # Maintain running ADR using SMA of TR with [1] shift
        # For simplicity, we'll recompute on the fly
        self._adr_values.append(tr)
        if idx > 0:
            start = max(0, idx - cfg.adr_len)
            # [1] shift: use window ending at idx-1
            adr_window = self._adr_values[start:idx]
            avg_range = sum(adr_window) / len(adr_window) if adr_window else 0.0
        else:
            avg_range = 0.0

        # ════════════════════════════════════════════════════════
        # 0. ACCUMULATION / DISTRIBUTION PHASE (lines 146-153)
        # ════════════════════════════════════════════════════════
        if idx >= cfg.acc_len - 1:
            acc_high = highest(self._highs, cfg.acc_len, idx)
            acc_low = lowest(self._lows, cfg.acc_len, idx)
            acc_range = acc_high - acc_low
            is_compressing = avg_range > 0 and acc_range <= cfg.acc_max_range_mult * avg_range
            acc_mid = (acc_high + acc_low) / 2.0

            result.bull_acc = is_compressing and bar.close >= acc_mid
            result.bear_dist = is_compressing and bar.close < acc_mid
        
        # ════════════════════════════════════════════════════════
        # 1. REJECTION DAY TRIGGER (lines 155-170)
        # ════════════════════════════════════════════════════════
        rej_range_ok = avg_range > 0 and rng > cfg.adr_mult_min * avg_range

        # Tail/Body ratio
        bull_tail_ok = (dn_wick > cfg.tail_body_mult * body) if body > 0 else (dn_wick > 0)
        bear_tail_ok = (up_wick > cfg.tail_body_mult * body) if body > 0 else (up_wick > 0)

        # Close location
        bull_close_ok = close_pos >= (1 - cfg.close_zone_pct)
        bear_close_ok = close_pos <= cfg.close_zone_pct

        # Structural extreme check
        if cfg.use_structure and idx >= cfg.struct_len:
            prior_low_struct = lowest(self._lows, cfg.struct_len, idx - 1)
            prior_high_struct = highest(self._highs, cfg.struct_len, idx - 1)
            near_prior_low = bar.low <= prior_low_struct * (1 + cfg.struct_tol_pct)
            near_prior_high = bar.high >= prior_high_struct * (1 - cfg.struct_tol_pct)
        else:
            near_prior_low = True   # No structure check
            near_prior_high = True

        struct_bull_ok = not cfg.use_structure or near_prior_low
        struct_bear_ok = not cfg.use_structure or near_prior_high

        bull_rej = rej_range_ok and bull_tail_ok and bull_close_ok and struct_bull_ok
        bear_rej = rej_range_ok and bear_tail_ok and bear_close_ok and struct_bear_ok

        result.bull_rejection = bull_rej
        result.bear_rejection = bear_rej

        # ════════════════════════════════════════════════════════
        # 2. STOP RUN DAY TRIGGER (lines 172-183)
        # ════════════════════════════════════════════════════════
        srd_range_ok = avg_range > 0 and rng > cfg.srd_adr_mult_min * avg_range

        bull_srd_close_pos_ok = close_pos >= (1 - cfg.srd_close_zone_pct)
        bear_srd_close_pos_ok = close_pos <= cfg.srd_close_zone_pct

        bull_srd_close_ext = idx > 0 and bar.close > self._highs[idx - 1]
        bear_srd_close_ext = idx > 0 and bar.close < self._lows[idx - 1]

        if idx >= cfg.srd_struct_len:
            bull_srd_mid_ext = mid >= highest(self._highs, cfg.srd_struct_len, idx - 1)
            bear_srd_mid_ext = mid <= lowest(self._lows, cfg.srd_struct_len, idx - 1)
        else:
            bull_srd_mid_ext = True
            bear_srd_mid_ext = True

        bull_srd_signal = srd_range_ok and bull_srd_close_pos_ok and bull_srd_close_ext and bull_srd_mid_ext
        bear_srd_signal = srd_range_ok and bear_srd_close_pos_ok and bear_srd_close_ext and bear_srd_mid_ext

        result.bull_stop_run = bull_srd_signal
        result.bear_stop_run = bear_srd_signal

        # Track triggers for barsSince
        self._rej_triggered.append(bull_rej or bear_rej)
        self._srd_triggered.append(bull_srd_signal or bear_srd_signal)

        # ════════════════════════════════════════════════════════
        # STATE TRACKING: REJECTION SEQUENCE (lines 185-226)
        # ════════════════════════════════════════════════════════
        bars_since_rej = bars_since(self._rej_triggered, idx)

        if bull_rej:
            self.state.rej_active_mid = mid
            self.state.rej_active_high = bar.high
            self.state.rej_active_low = bar.low
            self.state.bull_rej_active = True
            self.state.bear_rej_active = False
            self.state.bull_failed_abs_active = False
            self.state.bear_failed_abs_active = False
        elif bear_rej:
            self.state.rej_active_mid = mid
            self.state.rej_active_high = bar.high
            self.state.rej_active_low = bar.low
            self.state.bear_rej_active = True
            self.state.bull_rej_active = False
            self.state.bull_failed_abs_active = False
            self.state.bear_failed_abs_active = False

        # Check Rejection Failure → triggers Failed Absorption Context (lines 214-220)
        if self.state.bull_rej_active and self.state.rej_active_mid is not None:
            if bar.close < self.state.rej_active_mid:
                self.state.bull_rej_active = False
                self.state.bear_failed_abs_active = True

        if self.state.bear_rej_active and self.state.rej_active_mid is not None:
            if bar.close > self.state.rej_active_mid:
                self.state.bear_rej_active = False
                self.state.bull_failed_abs_active = True

        # Invalidate Failed Absorption Context (lines 222-226)
        if self.state.bear_failed_abs_active and self.state.rej_active_high is not None:
            if bar.close > self.state.rej_active_high:
                self.state.bear_failed_abs_active = False

        if self.state.bull_failed_abs_active and self.state.rej_active_low is not None:
            if bar.close < self.state.rej_active_low:
                self.state.bull_failed_abs_active = False

        # ════════════════════════════════════════════════════════
        # STATE TRACKING: STOP RUN SEQUENCE (lines 228-250)
        # ════════════════════════════════════════════════════════
        bars_since_srd = bars_since(self._srd_triggered, idx)

        if bull_srd_signal:
            self.state.srd_active_mid = mid
            self.state.srd_active_ext = bar.high
            self.state.bull_srd_active = True
            self.state.bear_srd_active = False
        elif bear_srd_signal:
            self.state.srd_active_mid = mid
            self.state.srd_active_ext = bar.low
            self.state.bear_srd_active = True
            self.state.bull_srd_active = False

        if self.state.bull_srd_active and self.state.srd_active_mid is not None:
            if bar.close < self.state.srd_active_mid:
                self.state.bull_srd_active = False

        if self.state.bear_srd_active and self.state.srd_active_mid is not None:
            if bar.close > self.state.srd_active_mid:
                self.state.bear_srd_active = False

        # ════════════════════════════════════════════════════════
        # 3. FADE AFTER STOP RUN (lines 252-254)
        # ════════════════════════════════════════════════════════
        bull_fade = (self.state.bull_srd_active
                     and bars_since_srd is not None
                     and bars_since_srd > 0
                     and self.state.srd_active_ext is not None
                     and bar.high >= self.state.srd_active_ext * 0.995
                     and bar.close < bar.open)

        bear_fade = (self.state.bear_srd_active
                     and bars_since_srd is not None
                     and bars_since_srd > 0
                     and self.state.srd_active_ext is not None
                     and bar.low <= self.state.srd_active_ext * 1.005
                     and bar.close > bar.open)

        # ════════════════════════════════════════════════════════
        # 4. ABSORPTION DAY (lines 256-263)
        # ════════════════════════════════════════════════════════
        abs_range_ok = avg_range > 0 and rng < cfg.abs_adr_max_mult * avg_range

        # Absorption in Rejection context
        bull_abs_rej = (self.state.bull_rej_active
                        and bars_since_rej is not None
                        and bars_since_rej > 0
                        and abs_range_ok
                        and self.state.rej_active_mid is not None
                        and bar.close > self.state.rej_active_mid
                        and (not cfg.require_body_confirm or bar.close > bar.open)
                        and abs(bar.low - self.state.rej_active_mid) <= self.state.rej_active_mid * cfg.abs_mid_tol_pct)

        bear_abs_rej = (self.state.bear_rej_active
                        and bars_since_rej is not None
                        and bars_since_rej > 0
                        and abs_range_ok
                        and self.state.rej_active_mid is not None
                        and bar.close < self.state.rej_active_mid
                        and (not cfg.require_body_confirm or bar.close < bar.open)
                        and abs(bar.high - self.state.rej_active_mid) <= self.state.rej_active_mid * cfg.abs_mid_tol_pct)

        # Absorption in Stop Run context
        bull_abs_srd = (self.state.bull_srd_active
                        and bars_since_srd is not None
                        and bars_since_srd > 0
                        and abs_range_ok
                        and self.state.srd_active_mid is not None
                        and bar.close > self.state.srd_active_mid
                        and (not cfg.require_body_confirm or bar.close > bar.open)
                        and abs(bar.low - self.state.srd_active_mid) <= self.state.srd_active_mid * cfg.abs_mid_tol_pct)

        bear_abs_srd = (self.state.bear_srd_active
                        and bars_since_srd is not None
                        and bars_since_srd > 0
                        and abs_range_ok
                        and self.state.srd_active_mid is not None
                        and bar.close < self.state.srd_active_mid
                        and (not cfg.require_body_confirm or bar.close < bar.open)
                        and abs(bar.high - self.state.srd_active_mid) <= self.state.srd_active_mid * cfg.abs_mid_tol_pct)

        # ════════════════════════════════════════════════════════
        # X. OUTSIDE DAY (lines 265-268)
        # ════════════════════════════════════════════════════════
        od_range_ok = avg_range > 0 and rng > cfg.od_adr_mult_min * avg_range

        if idx > 0:
            result.bull_outside_day = (od_range_ok
                                       and bar.low < self._lows[idx - 1]
                                       and bar.close > self._highs[idx - 1])
            result.bear_outside_day = (od_range_ok
                                       and bar.high > self._highs[idx - 1]
                                       and bar.close < self._lows[idx - 1])

        # ════════════════════════════════════════════════════════
        # 5. FNL / FNH — Failed New Low / Failed New High (lines 270-291)
        # ════════════════════════════════════════════════════════
        fnl_range_ok = avg_range > 0 and rng >= cfg.adr_min_pct * avg_range

        if idx >= cfg.sweep_lookback:
            prior_low_sweep = lowest(self._lows, cfg.sweep_lookback, idx - 1)
            prior_high_sweep = highest(self._highs, cfg.sweep_lookback, idx - 1)
            y_mid = (self._highs[idx - 1] + self._lows[idx - 1]) / 2.0

            fnl_sweep = bar.low < prior_low_sweep
            fnl_close = bar.close > y_mid if cfg.require_above_y_mid else bar.close > mid
            fnl_signal = fnl_range_ok and fnl_sweep and fnl_close

            fnh_sweep = bar.high > prior_high_sweep
            fnh_close = bar.close < y_mid if cfg.require_above_y_mid else bar.close < mid
            fnh_signal = fnl_range_ok and fnh_sweep and fnh_close
        else:
            fnl_signal = False
            fnh_signal = False

        # FNL/FNH in context of active sequences (lines 284-291)
        bull_fnl_rej = (self.state.bull_rej_active and bars_since_rej is not None
                        and bars_since_rej > 0 and fnl_signal)
        bear_fnh_rej = (self.state.bear_rej_active and bars_since_rej is not None
                        and bars_since_rej > 0 and fnh_signal)

        bull_fnl_srd = (self.state.bull_srd_active and bars_since_srd is not None
                        and bars_since_srd > 0 and fnl_signal)
        bear_fnh_srd = (self.state.bear_srd_active and bars_since_srd is not None
                        and bars_since_srd > 0 and fnh_signal)

        # Unified FNL (standalone blueprint uses the raw signal)
        result.bull_fnl = fnl_signal
        result.bear_fnh = fnh_signal

        # ════════════════════════════════════════════════════════
        # 6. FAILED BREAKOUT (lines 293-296)
        # ════════════════════════════════════════════════════════
        self._fa_triggered.append(
            self.state.bull_failed_abs_active or self.state.bear_failed_abs_active
        )
        bars_since_fa = bars_since(self._fa_triggered, idx)

        bull_failed_breakout = (self.state.bull_failed_abs_active
                                 and bars_since_fa is not None
                                 and bars_since_fa > 0
                                 and idx > 0
                                 and bar.low <= self._lows[idx - 1]
                                 and bar.close > bar.open)

        bear_failed_breakout = (self.state.bear_failed_abs_active
                                 and bars_since_fa is not None
                                 and bars_since_fa > 0
                                 and idx > 0
                                 and bar.high >= self._highs[idx - 1]
                                 and bar.close < bar.open)

        result.bull_failed_breakout = bull_failed_breakout
        result.bear_failed_breakout = bear_failed_breakout

        # ════════════════════════════════════════════════════════
        # 7. RETEST AFTER STOP RUN (lines 298-300)
        # ════════════════════════════════════════════════════════
        bull_retest_srd = self.state.bull_failed_abs_active and (bull_fade or bull_abs_srd)
        bear_retest_srd = self.state.bear_failed_abs_active and (bear_fade or bear_abs_srd)

        result.bull_retest_srd = bull_retest_srd
        result.bear_retest_srd = bear_retest_srd

        # ── Masking: Remove retests from Fade/Abs rows (lines 302-307) ──
        bull_fade_final = bull_fade and not bull_retest_srd
        bear_fade_final = bear_fade and not bear_retest_srd

        unified_bull_abs = bull_abs_rej or (bull_abs_srd and not bull_retest_srd)
        unified_bear_abs = bear_abs_rej or (bear_abs_srd and not bear_retest_srd)

        result.bull_fade = bull_fade_final
        result.bear_fade = bear_fade_final
        result.bull_absorption = unified_bull_abs
        result.bear_absorption = unified_bear_abs

        # ════════════════════════════════════════════════════════
        # 8. CONTINUATION DAY (lines 309-317)
        # ════════════════════════════════════════════════════════
        result.bull_continuation = (self.state.prev_active_day_bull
                                     and idx > 0
                                     and bar.close > self._closes[idx - 1])
        result.bear_continuation = (self.state.prev_active_day_bear
                                     and idx > 0
                                     and bar.close < self._closes[idx - 1])

        # Update prevActiveDayBull/Bear for NEXT bar (lines 316-317)
        self.state.prev_active_day_bull = (
            bull_rej or bull_srd_signal or unified_bull_abs or
            fnl_signal or bull_failed_breakout or bull_retest_srd
        )
        self.state.prev_active_day_bear = (
            bear_rej or bear_srd_signal or unified_bear_abs or
            fnh_signal or bear_failed_breakout or bear_retest_srd
        )

        return result

    def reset(self):
        """Reset all state for a fresh evaluation."""
        self.state = SequenceState()
        self._bars.clear()
        self._highs.clear()
        self._lows.clear()
        self._closes.clear()
        self._opens.clear()
        self._adr_values.clear()
        self._rej_triggered.clear()
        self._srd_triggered.clear()
        self._fa_triggered.clear()


# ════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ════════════════════════════════════════════════════════════════════

def classify_day_types(daily_bars: List[OHLC],
                        config: Optional[DayTypeConfig] = None) -> List[DayTypeResult]:
    """
    Classify day types for a complete series of daily bars.
    
    Args:
        daily_bars: List of daily OHLC bars in chronological order
        config: Optional configuration overrides
    
    Returns:
        List of DayTypeResult, one per bar
    """
    classifier = DayTypeClassifier(config)
    return [classifier.evaluate(bar) for bar in daily_bars]


def classify_single_day(daily_bars: List[OHLC],
                         config: Optional[DayTypeConfig] = None) -> DayTypeResult:
    """
    Classify only the LAST bar's day type, using all prior bars for context.
    
    This is the most common use case: you have historical daily bars and
    want to know today's classification.
    
    Args:
        daily_bars: List of daily OHLC bars ending with the bar to classify
        config: Optional configuration overrides
    
    Returns:
        DayTypeResult for the last bar
    """
    results = classify_day_types(daily_bars, config)
    return results[-1] if results else DayTypeResult()
