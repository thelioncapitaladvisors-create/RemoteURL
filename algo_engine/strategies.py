"""
algo_engine.strategies — 14 Canonical Strategy Triggers
=======================================================

Port of Pine Script strategy trigger conditions from
TLCS_Dashboards_4_Commodities_Merged.pine (lines 2990-3156) & PivotBoss STP 2.0.

All 14 Canonical Execution Strategies (7 Long + 7 Short):
    1. LONG MISSILE / SHORT MISSILE
    2. LONG SCALP / SHORT SCALP
    3. LONG LIGHTNING / SHORT LIGHTNING
    4. LONG DIVERGENCE / SHORT DIVERGENCE
    5. LONG HIDDEN DIVERGENCE / SHORT HIDDEN DIVERGENCE
    6. LONG EXTREME REVERSAL / SHORT EXTREME REVERSAL
    7. LONG VIRGIN CPR / SHORT VIRGIN CPR

H4/L4 Touch-Point Gating (CRITICAL — MUST NEVER USE CLOSE):
    Long trades:  qualified strictly on low < H4
    Short trades: qualified strictly on high > L4

Strategy Priority (Higher priority suppresses lower):
    Lightning > Extreme Reversal > Divergence > Hidden Divergence > Missile > Scalp
    (Missile and Scalp fire ONLY if none of the higher-priority strategies fire)

Day Type Filter (dayAllowed):
    Blocks Missile, Scalp, Lightning, and Extreme Reversal on sideways days
    unless Narrow CPR (NCPR) compression is met.
    Divergence and Hidden Divergence are EXEMPT from day type filtering.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from .pivots import (
    OHLC, CamarillaLevels, CPRLevels, DailyLevels, ValueArea, VirginCPRZone,
    ema, compute_pivot_trend_emas
)


# ════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ════════════════════════════════════════════════════════════════════

@dataclass
class StrategySignal:
    """A single strategy trigger signal."""
    name: str                # e.g., "LONG MISSILE", "SHORT LIGHTNING"
    direction: str           # "LONG" or "SHORT"
    entry_price: float       # Limit order entry level (trendLine midpoint)
    stop_loss: float         # Initial SL = entry ± SL_ATR_MULT * ATR
    tp1: float               # TP1 = entry ± TP1_ATR_MULT * ATR
    tp2: float               # TP2 = entry ± TP2_ATR_MULT * ATR
    tp3: float               # TP3 = entry ± TP3_ATR_MULT * ATR
    tp4: float               # TP4 = entry ± TP4_ATR_MULT * ATR
    bar_index: int           # Index of the bar that generated this signal
    timestamp: Optional[str] = None
    zone: str = ""           # z1: LONG ZONE / SHORT ZONE / WAITING
    opening_bias: str = ""   # dX: Opening bias string
    day_type: str = ""       # mX: Market type / day type string


@dataclass
class StrategyConfig:
    """
    Configuration for strategy triggers.
    Default values match Pine Script inputs.
    """
    # ATR-Based SL/TP Multipliers (lines 2360-2365)
    atr_length: int = 14
    sl_atr_mult: float = 0.75      # SL = 0.75 * ATR from entry
    tp1_atr_mult: float = 2.5      # TP1 = 2.5 * ATR from entry
    tp2_atr_mult: float = 4.0      # TP2 = 4.0 * ATR from entry
    tp3_atr_mult: float = 6.5      # TP3 = 6.5 * ATR from entry
    tp4_atr_mult: float = 8.0      # TP4 = 8.0 * ATR from entry

    # EMA Periods for trend/zone detection
    short_ema_period: int = 13      # fShort_EMA (lines 2399, 2414)
    med_ema_period: int = 32        # fMed_EMA (lines 2403, 2415)
    fast_pivot_period: int = 5      # fFastEMA1 for pivot DEMA (line 430)
    slow_pivot_period: int = 13     # fSlowEMA1 for pivot DEMA (line 431)

    # Wick Reversal parameters
    wick_body_size: float = 0.40
    wick_candle_mult: float = 0.9

    # Extreme Reversal parameters (lines 608-614)
    bodysize: float = 0.75          # Body must be >= 75% of candle range
    body_multiplier: float = 2.0    # Range must be > 2x avg candle size
    avg_candle_len: int = 50        # Lookback for average candle/body size

    # Doji Reversal parameters
    doji_body_size: float = 0.05
    doji_candle_mult: float = 0.9

    # Divergence lookback window
    div_lookback: int = 6           # Check divergence within last 6 bars


# ════════════════════════════════════════════════════════════════════
# MARKET CONTEXT
# ════════════════════════════════════════════════════════════════════

@dataclass
class MarketContext:
    """
    Aggregated market context for strategy evaluation on a single bar.
    Encapsulates all the pre-computed indicators that strategies need.
    """
    bar: OHLC                       # Current bar
    bar_index: int                  # Position in series

    # Camarilla levels for H4/L4 gating
    H4: float
    L4: float
    H3: float
    L3: float

    # CPR levels
    cpr_pivot: float
    cpr_tc: float
    cpr_bc: float
    is_ncpr: bool = False           # Narrow CPR

    # Value Area
    vah: float = 0.0
    val: float = 0.0

    # EMAs (on Typical/Pivot Price)
    short_ema: float = 0.0          # 13 EMA
    med_ema: float = 0.0            # 32 EMA

    # Pivot Trend EMAs (triple-smoothed DEMA)
    pivot_trend_fast: float = 0.0   # fPivotPDEMAF (period 5)
    pivot_trend_slow: float = 0.0   # fPivotPDEMAS (period 13)

    # ATR at current bar
    atr: float = 0.0

    # Opening bias & day type
    opening_bias: str = ""          # dX
    day_type_label: str = ""        # mX
    institutional_bias: str = ""    # c1 (CONFIRMED BULLISH, CONFIRMED BEARISH, WATCH, etc.)

    # Previous bar data (for session range / trendLine)
    session_highest: float = 0.0    # Highest high of current session
    session_lowest: float = 0.0     # Lowest low of current session

    # Divergence signals (from external oscillator)
    bull_regular_div: bool = False   # Regular bullish divergence on bar[1]
    bear_regular_div: bool = False   # Regular bearish divergence on bar[1]
    bull_hidden_div: bool = False    # Hidden bullish divergence on bar[1]
    bear_hidden_div: bool = False    # Hidden bearish divergence on bar[1]

    # Extreme reversal input signals
    extreme_long_signal: bool = False   # Elongsignal
    extreme_short_signal: bool = False  # Eshortsignal

    # Previous bar close for trend confirmation
    prev_close: float = 0.0
    prev_open: float = 0.0
    prev_bar: Optional[OHLC] = None

    # Previous CPR boundaries for Hidden Divergence inside-CPR check
    prev_cpr_top: float = 0.0
    prev_cpr_bottom: float = 0.0

    # Oscillator values (for Greenzone/Redzone)
    plus: float = 0.0               # DI+ or bullish momentum
    minus: float = 0.0              # DI- or bearish momentum

    # m0 / m10 for ranging detection
    m0: float = 0.0
    m10: float = 0.0

    # Virgin CPR Zones (active untouched zones over past 1 month)
    virgin_cpr_zones: List[VirginCPRZone] = field(default_factory=list)


# ════════════════════════════════════════════════════════════════════
# CORE STRATEGY ENGINE
# ════════════════════════════════════════════════════════════════════

class StrategyEngine:
    """
    Evaluates all 12 strategy triggers for a given market context.
    
    Implements the exact boolean logic from Pine Script lines 2990-3156.
    """

    def __init__(self, config: Optional[StrategyConfig] = None):
        self.config = config or StrategyConfig()

        # Power Candle Midpoint Tracking (lines 2951-2957)
        self._grs_mid: Optional[float] = None   # Green candle bounce midpoint
        self._res_mid: Optional[float] = None   # Red candle bounce midpoint
        self._clean_trend_bullish: bool = False
        self._clean_trend_bearish: bool = False

        # Divergence 6-bar Lookback Buffers (lines 3152-3157)
        self._bull_div_history: List[bool] = []
        self._bear_div_history: List[bool] = []
        self._hidden_bull_history: List[bool] = []
        self._hidden_bear_history: List[bool] = []

        # Track which bars have already generated signals (tick-spam protection)
        self._last_signal_bar: Dict[str, int] = {}

    def evaluate(self, ctx: MarketContext) -> List[StrategySignal]:
        """
        Evaluate all 12 strategy triggers for the current bar.
        
        Args:
            ctx: MarketContext with all pre-computed indicators
        
        Returns:
            List of StrategySignal objects for signals that triggered
        """
        signals: List[StrategySignal] = []
        bar = ctx.bar
        cfg = self.config

        # ═══════════════════════════════════════════════════════
        # H4/L4 TOUCH-POINT GATING (CRITICAL — lines 3071-3072)
        # ═══════════════════════════════════════════════════════
        # MUST use low < H4 for longs, high > L4 for shorts
        # NEVER use close for limit entry qualification
        long_allowed = bar.low < ctx.H4
        short_allowed = bar.high > ctx.L4

        # ═══════════════════════════════════════════════════════
        # ZONE/TREND DETECTION (lines 895-899, 2995-3010)
        # ═══════════════════════════════════════════════════════
        greenzone = (ctx.plus > ctx.minus and
                     ctx.short_ema > ctx.med_ema and
                     ctx.pivot_trend_fast > ctx.pivot_trend_slow)

        redzone = (ctx.minus > ctx.plus and
                   ctx.short_ema < ctx.med_ema and
                   ctx.pivot_trend_fast < ctx.pivot_trend_slow)

        ema_can_buy = greenzone or not redzone
        ema_can_sell = redzone or not greenzone

        # ═══════════════════════════════════════════════════════
        # RISING/FALLING CONDITIONS (lines 2995-3016)
        # ═══════════════════════════════════════════════════════
        dt = ctx.day_type_label.upper() if ctx.day_type_label else ""
        ob = ctx.opening_bias.upper() if ctx.opening_bias else ""
        c1 = ctx.institutional_bias.upper().replace("\n", "").replace("  ", " ") if ctx.institutional_bias else ""

        # CPR Institutional Day Types & Rejection Day (Pine Script lines 771-792, 3054-3066, 3129)
        dtc = ctx.cpr_tc
        dbc = ctx.cpr_bc
        ytc = ctx.prev_cpr_top if ctx.prev_cpr_top > 0 else dtc
        ybc = ctx.prev_cpr_bottom if ctx.prev_cpr_bottom > 0 else dbc
        op = bar.open
        cc = ctx.prev_close

        bullish = (dtc > ytc) and (dbc > ytc)
        bearish = (dtc < ybc) and (dbc < ybc)
        mod_bullish = (dtc > ytc) and (dbc > ybc)
        mod_bearish = (dtc < ytc) and (dbc < ybc)
        inside = (dtc < ytc) and (dbc > ybc)
        outside = (dtc > ytc) and (dbc < ybc)
        unchanged = (dbc == ybc) and (dtc == ytc)

        breakoutday = inside or unchanged
        otherdays = outside or breakoutday

        cc_cond_bull = (cc != ytc) if (cc != 0.0 and ytc != 0.0) else True
        cc_cond_bear = (cc != ybc) if (cc != 0.0 and ybc != 0.0) else True

        confirmed_bullish = (bullish or mod_bullish or otherdays) and cc_cond_bull and (op > dbc)
        confirmed_bearish = (bearish or mod_bearish or otherdays) and cc_cond_bear and (op < dtc)
        rejected_bullish = (bullish or mod_bullish or otherdays) and cc_cond_bull and (op < dbc)
        rejected_bearish = (bearish or mod_bearish or otherdays) and cc_cond_bear and (op > dtc)

        rejection_day = (
            (confirmed_bullish and bar.close < dbc) or
            (confirmed_bearish and bar.close > dtc) or
            (rejected_bullish and bar.close < dbc) or
            (rejected_bullish and bar.close > dtc) or
            (rejected_bearish and bar.close > dtc) or
            (rejected_bearish and bar.close < dbc)
        )

        bull_conds = (
            ("BIG MOVE" in dt) or
            ("TREND DAY" in dt and "DOUBLE DISTRIBUTION" in dt) or
            ("OUT OF RANGE" in ob and "OUT OF VALUE" in ob) or
            ("CONFIRMED BULLISH" in c1) or
            ("BULLISH CONTINUATION" in c1) or
            ("BEARISH REJECTION" in c1) or
            ("REJECTED BEARISH" in c1) or
            ("WATCH" in c1) or
            (
                rejected_bearish or
                (confirmed_bearish and bar.close > dtc) or
                (rejected_bullish and bar.close > dtc) or
                (rejected_bearish and bar.close > dtc)
            )
        )

        bear_conds = (
            ("BIG MOVE" in dt) or
            ("TREND DAY" in dt and "DOUBLE DISTRIBUTION" in dt) or
            ("OUT OF RANGE" in ob and "OUT OF VALUE" in ob) or
            ("CONFIRMED BEARISH" in c1) or
            ("BEARISH CONTINUATION" in c1) or
            ("BULLISH REJECTION" in c1) or
            ("REJECTED BULLISH" in c1) or
            ("WATCH" in c1) or
            (
                rejected_bullish or
                (confirmed_bullish and bar.close < dbc) or
                (rejected_bullish and bar.close < dbc) or
                (rejected_bearish and bar.close < dbc)
            )
        )

        rising_up = (ctx.plus >= ctx.minus and
                     ctx.pivot_trend_fast >= ctx.pivot_trend_slow and
                     bull_conds)

        falling_down = (ctx.minus >= ctx.plus and
                        ctx.pivot_trend_fast <= ctx.pivot_trend_slow and
                        bear_conds)

        r_up = rising_up and bar.close > bar.open
        r_dn = falling_down and bar.close < bar.open

        # ═══════════════════════════════════════════════════════
        # MISS / BOUNCE CONDITIONS (lines 3018-3040)
        # ═══════════════════════════════════════════════════════
        def _bounce_up_from(level):
            """Bar touches down to level and closes above it (green)."""
            return (bar.low < level and bar.open > level and
                    bar.high > level and bar.close > level)

        def _bounce_down_from(level):
            """Bar touches up to level and closes below it (red)."""
            return (bar.high > level and bar.open < level and
                    bar.low < level and bar.close < level)

        miss_up = ((rising_up or bull_conds) and bar.is_green and
                   _bounce_up_from(ctx.vah))

        miss_u = miss_up or (r_up and (
            _bounce_up_from(ctx.vah) or
            _bounce_up_from(ctx.med_ema) or
            _bounce_up_from(ctx.cpr_pivot)))

        miss_down = ((falling_down or bear_conds) and bar.is_red and
                     _bounce_down_from(ctx.val))

        miss_d = miss_down or (r_dn and (
            _bounce_down_from(ctx.val) or
            _bounce_down_from(ctx.med_ema) or
            _bounce_down_from(ctx.cpr_pivot)))

        # Ranging conditions (lines 3030-3040)
        is_sideways = ("INRANGE" in ob.replace(" ", "") or
                       "TRADING RANGE" in dt or "SIDEWAYS" in dt or
                       "TYPICAL DAY" in dt or
                       "IN RANGE" in ob and "IN VALUE" in ob)

        ranging_up = (ctx.plus >= ctx.minus and
                      ctx.pivot_trend_fast >= ctx.pivot_trend_slow and
                      ctx.m0 >= ctx.m10 and is_sideways)

        ranging_down = (ctx.minus >= ctx.plus and
                        ctx.pivot_trend_fast <= ctx.pivot_trend_slow and
                        ctx.m0 <= ctx.m10 and is_sideways)

        bounce_up = (ranging_up and bar.is_green and
                     (_bounce_up_from(ctx.val) or _bounce_up_from(ctx.cpr_pivot)))

        bounce_down = (ranging_down and bar.is_red and
                       (_bounce_down_from(ctx.vah) or _bounce_down_from(ctx.cpr_pivot)))

        # ═══════════════════════════════════════════════════════
        # CANBUY / CANSELL (lines 3047-3048)
        # ═══════════════════════════════════════════════════════
        can_buy = (ema_can_buy and miss_u) or (ema_can_buy and bounce_up)
        can_sell = (ema_can_sell and miss_d) or (ema_can_sell and bounce_down)

        # Update clean trend (lines 3052-3053)
        if can_buy:
            self._clean_trend_bullish = True
        elif can_sell:
            self._clean_trend_bullish = False
        elif rising_up:
            self._clean_trend_bullish = True
        else:
            self._clean_trend_bullish = False

        if can_sell:
            self._clean_trend_bearish = True
        elif can_buy:
            self._clean_trend_bearish = False
        elif falling_down:
            self._clean_trend_bearish = True
        else:
            self._clean_trend_bearish = False

        # ═══════════════════════════════════════════════════════
        # POWER CANDLE / S&R BOUNCE DETECTION (lines 2958-2987)
        # ═══════════════════════════════════════════════════════
        has_dmi = (ctx.plus != 0.0 or ctx.minus != 0.0)
        has_m = (ctx.m0 != 0.0 or ctx.m10 != 0.0)
        if has_dmi or has_m:
            dmi_green = (ctx.plus > ctx.minus) if has_dmi else True
            dmi_red = (ctx.minus > ctx.plus) if has_dmi else True
            m_green = (ctx.m0 > ctx.m10) if has_m else True
            m_red = (ctx.m0 < ctx.m10) if has_m else True
            green1 = dmi_green and m_green
            red1 = dmi_red and m_red
        else:
            green1 = bar.is_green
            red1 = bar.is_red

        # 1. Evaluate midpoint retest on existing midpoint from prior bars
        bounced_off_actual_grs_mid = (
            self._grs_mid is not None and _bounce_up_from(self._grs_mid)
        )
        bounced_off_actual_res_mid = (
            self._res_mid is not None and _bounce_down_from(self._res_mid)
        )

        # 2. Clear midpoints immediately upon bounce consumption
        if bounced_off_actual_grs_mid:
            self._grs_mid = None
        if bounced_off_actual_res_mid:
            self._res_mid = None

        # 3. Detect green/red power candles at S&R levels and establish new midpoints
        # Pine Script: GrS = GREEN1 and (bouncedOffSR_Up), ReS = RED1 and (bouncedOffSR_Down)
        bounced_sr_up = (
            _bounce_up_from(ctx.val) or _bounce_up_from(ctx.cpr_pivot) or
            _bounce_up_from(ctx.L3) or _bounce_up_from(ctx.L4)
        )
        bounced_sr_down = (
            _bounce_down_from(ctx.vah) or _bounce_down_from(ctx.cpr_pivot) or
            _bounce_down_from(ctx.H3) or _bounce_down_from(ctx.H4)
        )

        grs = green1 and bounced_sr_up
        res = red1 and bounced_sr_down

        if grs:
            self._grs_mid = bar.midpoint
        if res:
            self._res_mid = bar.midpoint

        # 4. Final Bounce Flags used for Signals (Retest-only per updated Pine Script)
        # Exclusively enters on the retest of the Power Candle Midpoint,
        # eliminating raw breakout candles from qualifying as the bounce.
        bounced_off_grs_mid = bounced_off_actual_grs_mid
        bounced_off_res_mid = bounced_off_actual_res_mid

        # ═══════════════════════════════════════════════════════
        # SCALP SIGNALS (lines 3060-3064)
        # ═══════════════════════════════════════════════════════
        # Pine Script: StepUp = (cleanTrendBullish or GREEN1) and bouncedOffGrsMid
        #              StepDn = (cleanTrendBearish or RED1) and bouncedOffResMid
        step_up = (self._clean_trend_bullish or green1) and bounced_off_grs_mid
        step_dn = (self._clean_trend_bearish or red1) and bounced_off_res_mid

        scalp_buy = ema_can_buy and step_up
        scalp_sell = ema_can_sell and step_dn

        # ═══════════════════════════════════════════════════════
        # DAY ALLOWED FILTER (lines 3129-3140)
        # ═══════════════════════════════════════════════════════
        # Pine Script:
        #   bool isRejectionDay = REJECTIONDAY
        #   bool dayAllowed = not isSidewaysDay or isRejectionDay
        is_rejection_day = rejection_day
        day_allowed = not is_sideways or is_rejection_day

        # ═══════════════════════════════════════════════════════
        # HIDDEN DIVERGENCE CONFIRMATION (lines 3082-3093 / 3130-3141)
        # ═══════════════════════════════════════════════════════
        # Check if bar[1]'s hidden divergence was inside previous CPR
        h_bull_inside_cpr = False
        h_bear_inside_cpr = False

        if ctx.prev_bar is not None:
            pb = ctx.prev_bar
            inside_cpr_body = (
                (min(pb.open, pb.close) <= ctx.prev_cpr_top and
                 max(pb.open, pb.close) >= ctx.prev_cpr_bottom) or
                (pb.close >= ctx.prev_cpr_bottom and pb.close <= ctx.prev_cpr_top))

            h_bull_inside_cpr = ctx.bull_hidden_div and inside_cpr_body
            h_bear_inside_cpr = ctx.bear_hidden_div and inside_cpr_body

        hidden_bull_confirmed = (h_bull_inside_cpr and bar.is_green and
                                  bar.close > ctx.prev_close)
        hidden_bear_confirmed = (h_bear_inside_cpr and bar.is_red and
                                  bar.close < ctx.prev_close)

        # Update sliding 6-bar history buffers for divergences (matching Pine Script lines 3152-3157)
        self._bull_div_history.append(bool(ctx.bull_regular_div))
        self._bear_div_history.append(bool(ctx.bear_regular_div))
        if len(self._bull_div_history) > self.config.div_lookback:
            self._bull_div_history.pop(0)
        if len(self._bear_div_history) > self.config.div_lookback:
            self._bear_div_history.pop(0)

        self._hidden_bull_history.append(bool(hidden_bull_confirmed))
        self._hidden_bear_history.append(bool(hidden_bear_confirmed))
        if len(self._hidden_bull_history) > self.config.div_lookback:
            self._hidden_bull_history.pop(0)
        if len(self._hidden_bear_history) > self.config.div_lookback:
            self._hidden_bear_history.pop(0)

        recent_bull_div = any(self._bull_div_history)
        recent_bear_div = any(self._bear_div_history)
        recent_hidden_bull = any(self._hidden_bull_history)
        recent_hidden_bear = any(self._hidden_bear_history)

        # ═══════════════════════════════════════════════════════
        # COMPUTE ALL 12 STRATEGY TRIGGERS (Pine Script v7.0 lines 3147-3176)
        # ═══════════════════════════════════════════════════════

        # 1. Standard Lightning (Pure Native Missile + Scalp Confluence, lines 3148-3161)
        standard_lightning_buy = can_buy and scalp_buy and long_allowed and day_allowed
        standard_lightning_sell = can_sell and scalp_sell and short_allowed and day_allowed
        lightning_buy = standard_lightning_buy
        lightning_sell = standard_lightning_sell

        # 2. Hidden Divergence (Standalone Strategy - Exempt from day types and NCPR, lines 3155-3157)
        hidden_div_buy = recent_hidden_bull and grs and long_allowed
        hidden_div_sell = recent_hidden_bear and res and short_allowed

        # 3. Regular Divergence (Standalone Strategy - Exempt from day types and NCPR, lines 3152-3153)
        divergence_buy = recent_bull_div and grs and long_allowed
        divergence_sell = recent_bear_div and res and short_allowed

        # 4. Extreme Reversal (Independent signal, standard dayAllowed gate, lines 3166-3168)
        extreme_rev_buy = ctx.extreme_long_signal and long_allowed and day_allowed
        extreme_rev_sell = ctx.extreme_short_signal and short_allowed and day_allowed

        # 5. Missile (Decoupled, lines 3171-3172)
        just_missile_buy = (can_buy and not lightning_buy and not extreme_rev_buy
                            and not divergence_buy and not hidden_div_buy
                            and long_allowed and day_allowed)
        just_missile_sell = (can_sell and not lightning_sell and not extreme_rev_sell
                             and not divergence_sell and not hidden_div_sell
                             and short_allowed and day_allowed)

        # 6. Scalp (Decoupled, lines 3174-3175)
        just_scalp_buy = (scalp_buy and not lightning_buy and not extreme_rev_buy
                          and not divergence_buy and not hidden_div_buy
                          and long_allowed and day_allowed)
        just_scalp_sell = (scalp_sell and not lightning_sell and not extreme_rev_sell
                           and not divergence_sell and not hidden_div_sell
                           and short_allowed and day_allowed)

        # 7. Virgin CPR (VCPR) Retest / Touch (PivotBoss STP 2.0, 1-Month Lookback)
        matching_buy_z = next(
            (z for z in ctx.virgin_cpr_zones if bar.low <= z.top and bar.high >= z.bottom and (ctx.prev_close > z.top or bar.open > z.top)),
            None
        )
        vcpr_buy = (matching_buy_z is not None) and long_allowed and day_allowed

        matching_sell_z = next(
            (z for z in ctx.virgin_cpr_zones if bar.high >= z.bottom and bar.low <= z.top and (ctx.prev_close < z.bottom or bar.open < z.bottom)),
            None
        )
        vcpr_sell = (matching_sell_z is not None) and short_allowed and day_allowed

        # ═══════════════════════════════════════════════════════
        # COMPUTE ENTRY / SL / TP LEVELS (lines 2865-2893)
        # ═══════════════════════════════════════════════════════
        # Entry = trendLine = midpoint of session range (lines 2418-2423)
        entry_price = (ctx.session_highest + ctx.session_lowest) / 2.0
        atr_val = ctx.atr

        # Generate signals for each triggered strategy
        trigger_map = [
            (just_missile_buy,  "LONG MISSILE"),
            (just_missile_sell, "SHORT MISSILE"),
            (just_scalp_buy,    "LONG SCALP"),
            (just_scalp_sell,   "SHORT SCALP"),
            (lightning_buy,     "LONG LIGHTNING"),
            (lightning_sell,    "SHORT LIGHTNING"),
            (divergence_buy,    "LONG DIVERGENCE"),
            (divergence_sell,   "SHORT DIVERGENCE"),
            (hidden_div_buy,    "LONG HIDDEN DIVERGENCE"),
            (hidden_div_sell,   "SHORT HIDDEN DIVERGENCE"),
            (extreme_rev_buy,   "LONG EXTREME REVERSAL"),
            (extreme_rev_sell,  "SHORT EXTREME REVERSAL"),
            (vcpr_buy,          "LONG VIRGIN CPR"),
            (vcpr_sell,         "SHORT VIRGIN CPR"),
        ]

        for triggered, name in trigger_map:
            if not triggered:
                continue

            # Tick-spam protection: 1 signal per bar per strategy
            if self._last_signal_bar.get(name) == ctx.bar_index:
                continue
            self._last_signal_bar[name] = ctx.bar_index

            is_long = name.startswith("LONG")
            sig_entry = entry_price
            if name == "LONG VIRGIN CPR" and matching_buy_z:
                sig_entry = matching_buy_z.top
            elif name == "SHORT VIRGIN CPR" and matching_sell_z:
                sig_entry = matching_sell_z.bottom

            signal = self._build_signal(
                name=name,
                is_long=is_long,
                entry_price=sig_entry,
                atr_val=atr_val,
                bar_index=ctx.bar_index,
                timestamp=bar.timestamp,
                zone=self._compute_zone(bar, ctx),
                opening_bias=ctx.opening_bias,
                day_type=ctx.day_type_label,
            )
            signals.append(signal)

        return signals

    def _build_signal(self, name: str, is_long: bool, entry_price: float,
                      atr_val: float, bar_index: int, timestamp: Optional[str],
                      zone: str, opening_bias: str, day_type: str) -> StrategySignal:
        """
        Build a StrategySignal with computed SL/TP levels.
        
        Pine Script Source (lines 2880-2893):
            SL  = entry ± slAtrMultInput * atrValue     (0.75)
            TP1 = entry ± tp1AtrMultInput * atrValue    (2.5)
            TP2 = entry ± tp2AtrMultInput * atrValue    (4.0)
            TP3 = entry ± tp3AtrMultInput * atrValue    (6.5)
            TP4 = entry ± tp4AtrMultInput * atrValue    (8.0)
        """
        cfg = self.config
        direction = "LONG" if is_long else "SHORT"

        if is_long:
            sl  = entry_price - cfg.sl_atr_mult * atr_val
            tp1 = entry_price + cfg.tp1_atr_mult * atr_val
            tp2 = entry_price + cfg.tp2_atr_mult * atr_val
            tp3 = entry_price + cfg.tp3_atr_mult * atr_val
            tp4 = entry_price + cfg.tp4_atr_mult * atr_val
        else:
            sl  = entry_price + cfg.sl_atr_mult * atr_val
            tp1 = entry_price - cfg.tp1_atr_mult * atr_val
            tp2 = entry_price - cfg.tp2_atr_mult * atr_val
            tp3 = entry_price - cfg.tp3_atr_mult * atr_val
            tp4 = entry_price - cfg.tp4_atr_mult * atr_val

        return StrategySignal(
            name=name,
            direction=direction,
            entry_price=entry_price,
            stop_loss=sl,
            tp1=tp1, tp2=tp2, tp3=tp3, tp4=tp4,
            bar_index=bar_index,
            timestamp=timestamp,
            zone=zone,
            opening_bias=opening_bias,
            day_type=day_type,
        )

    def _compute_zone(self, bar: OHLC, ctx: MarketContext) -> str:
        """
        Compute zone status (z1) for webhook payload.
        
        Pine Script Source (line 3076):
            z1 = close > h3 ? 'LONG ZONE' : close < l3 ? 'SHORT ZONE' : ...
        """
        if bar.close > ctx.H3:
            return "LONG ZONE"
        elif bar.close < ctx.L3:
            return "SHORT ZONE"
        elif ctx.cpr_bc < bar.close < ctx.cpr_tc:
            return "WAIT FOR SIGNAL"
        else:
            return "WAITING"


# ════════════════════════════════════════════════════════════════════
# EXTREME REVERSAL DETECTION (lines 613-617)
# ════════════════════════════════════════════════════════════════════

def detect_extreme_reversal(bars: List[OHLC],
                             config: Optional[StrategyConfig] = None,
                             pivot_trend_slow: Optional[List[float]] = None,
                             green_zone: Optional[List[bool]] = None,
                             red_zone: Optional[List[bool]] = None
                             ) -> Tuple[List[bool], List[bool]]:
    """
    Detect Extreme Reversal signals across a series of bars.
    
    Pine Script Source (lines 613-617):
        Elongsig = GREENZONE and O[1] - C[1] >= bodysize * (H[1] - L[1]) 
                   and H[1] - L[1] > AverageCandle * bodymultiplier 
                   and O[1] - C[1] > AverageBody and C > O
        Eshortsig = REDZONE and C[1] - O[1] >= bodysize * (H[1] - L[1])
                    and H[1] - L[1] > AverageCandle * bodymultiplier
                    and C[1] - O[1] > AverageBody and O > C
        Elongsignal = ta.rising(fPivotPDEMAS, 1) and Elongsig
        Eshortsignal = ta.falling(fPivotPDEMAS, 1) and Eshortsig
    
    Args:
        bars: List of OHLC bars
        config: Strategy configuration
        pivot_trend_slow: fPivotPDEMAS values (optional, for slope check)
        green_zone: List of booleans indicating GREENZONE
        red_zone: List of booleans indicating REDZONE
    
    Returns:
        Tuple of (long_signals, short_signals) boolean lists
    """
    cfg = config or StrategyConfig()
    n = len(bars)
    long_signals = [False] * n
    short_signals = [False] * n

    for i in range(1, n):
        prev = bars[i - 1]
        curr = bars[i]

        # Average candle size and body over lookback
        start = max(0, i - cfg.avg_candle_len)
        candle_sizes = [bars[j].range for j in range(start, i)]
        body_sizes = [bars[j].body for j in range(start, i)]
        avg_candle = sum(candle_sizes) / len(candle_sizes) if candle_sizes else 0
        avg_body = sum(body_sizes) / len(body_sizes) if body_sizes else 0

        prev_range = prev.range
        prev_body = prev.body

        # Body >= 75% of range (exhaustion candle)
        body_ratio_ok = prev_body >= cfg.bodysize * prev_range if prev_range > 0 else False
        # Range > 2x average candle
        range_ok = prev_range > avg_candle * cfg.body_multiplier if avg_candle > 0 else False
        # Body > average body
        body_ok = prev_body > avg_body

        # Bullish: prev was bearish exhaustion (O > C), current is green
        is_prev_bearish_exhaust = prev.open > prev.close  # Red candle
        is_prev_bullish_exhaust = prev.close > prev.open  # Green candle

        # Pivot trend slope check
        ema_rising = True
        ema_falling = True
        if pivot_trend_slow is not None and i < len(pivot_trend_slow) and i > 0:
            ema_rising = pivot_trend_slow[i] > pivot_trend_slow[i - 1]
            ema_falling = pivot_trend_slow[i] < pivot_trend_slow[i - 1]

        gz_ok = green_zone[i] if green_zone is not None and i < len(green_zone) else True
        rz_ok = red_zone[i] if red_zone is not None and i < len(red_zone) else True

        # Elongsignal = rising slope + bearish exhaustion prev + green current + GREENZONE
        if (body_ratio_ok and range_ok and body_ok and
                is_prev_bearish_exhaust and curr.is_green and ema_rising and gz_ok):
            long_signals[i] = True

        # Eshortsignal = falling slope + bullish exhaustion prev + red current + REDZONE
        if (body_ratio_ok and range_ok and body_ok and
                is_prev_bullish_exhaust and curr.is_red and ema_falling and rz_ok):
            short_signals[i] = True

    return long_signals, short_signals


# ════════════════════════════════════════════════════════════════════
# WICK REVERSAL DETECTION (lines 571-597)
# ════════════════════════════════════════════════════════════════════

def detect_wick_reversal(bars: List[OHLC],
                         config: Optional[StrategyConfig] = None,
                         pivot_trend_slow: Optional[List[float]] = None,
                         green_zone: Optional[List[bool]] = None,
                         red_zone: Optional[List[bool]] = None
                         ) -> Tuple[List[bool], List[bool]]:
    """
    Detect Wick Reversal signals across a series of bars.

    Pine Script Source:
        Wbodysize = 0.40
        Wlongsig = GREENZONE and ((high - low) > (AverageCandle * 0.9)) and
                   (open - low) >= (Wbodysize * (high - low)) and
                   (close - low) >= (Wbodysize * (high - low)) and (close > open)
        Wshortsig = REDZONE and ((high - low) > (AverageCandle * 0.9)) and
                    (high - open) >= (Wbodysize * (high - low)) and
                    (high - close) >= (Wbodysize * (high - low)) and (close < open)
        Wlongsignal = ta.rising(fPivotPDEMAS, 1) and Wlongsig
        Wshortsignal = ta.falling(fPivotPDEMAS, 1) and Wshortsig
    """
    cfg = config or StrategyConfig()
    n = len(bars)
    long_signals = [False] * n
    short_signals = [False] * n

    for i in range(n):
        curr = bars[i]
        start = max(0, i - cfg.avg_candle_len)
        candle_sizes = [bars[j].range for j in range(start, i)] if i > 0 else []
        avg_candle = sum(candle_sizes) / len(candle_sizes) if candle_sizes else curr.range

        rng = curr.range
        wbodysize = cfg.wick_body_size
        large_enough = rng > avg_candle * cfg.wick_candle_mult if avg_candle > 0 else True

        gz = green_zone[i] if green_zone is not None and i < len(green_zone) else True
        rz = red_zone[i] if red_zone is not None and i < len(red_zone) else True

        wlongsig = (gz and large_enough and
                    (curr.open - curr.low >= wbodysize * rng) and
                    (curr.close - curr.low >= wbodysize * rng) and
                    (curr.close > curr.open))

        wshortsig = (rz and large_enough and
                     (curr.high - curr.open >= wbodysize * rng) and
                     (curr.high - curr.close >= wbodysize * rng) and
                     (curr.close < curr.open))

        ema_rising = True
        ema_falling = True
        if pivot_trend_slow is not None and i < len(pivot_trend_slow) and i > 0:
            ema_rising = pivot_trend_slow[i] > pivot_trend_slow[i - 1]
            ema_falling = pivot_trend_slow[i] < pivot_trend_slow[i - 1]

        long_signals[i] = ema_rising and wlongsig
        short_signals[i] = ema_falling and wshortsig

    return long_signals, short_signals


# ════════════════════════════════════════════════════════════════════
# OUTSIDE REVERSAL DETECTION (lines 601-616)
# ════════════════════════════════════════════════════════════════════

def detect_outside_reversal(bars: List[OHLC],
                           config: Optional[StrategyConfig] = None,
                           pivot_trend_slow: Optional[List[float]] = None,
                           green_zone: Optional[List[bool]] = None,
                           red_zone: Optional[List[bool]] = None
                           ) -> Tuple[List[bool], List[bool]]:
    """
    Detect Outside Reversal signals across a series of bars.

    Pine Script Source:
        Olongsig = GREENZONE and (close > high[1]) and (low < low[1]) and (close > open)
        Oshortsig = REDZONE and (close < low[1]) and (high > high[1]) and (close < open)
        Olongsignal = ta.rising(fPivotPDEMAS, 1) and Olongsig
        Oshortsignal = ta.falling(fPivotPDEMAS, 1) and Oshortsig
    """
    cfg = config or StrategyConfig()
    n = len(bars)
    long_signals = [False] * n
    short_signals = [False] * n

    for i in range(1, n):
        prev = bars[i - 1]
        curr = bars[i]

        gz = green_zone[i] if green_zone is not None and i < len(green_zone) else True
        rz = red_zone[i] if red_zone is not None and i < len(red_zone) else True

        olongsig = gz and (curr.close > prev.high) and (curr.low < prev.low) and (curr.close > curr.open)
        oshortsig = rz and (curr.close < prev.low) and (curr.high > prev.high) and (curr.close < curr.open)

        ema_rising = True
        ema_falling = True
        if pivot_trend_slow is not None and i < len(pivot_trend_slow):
            ema_rising = pivot_trend_slow[i] > pivot_trend_slow[i - 1]
            ema_falling = pivot_trend_slow[i] < pivot_trend_slow[i - 1]

        long_signals[i] = ema_rising and olongsig
        short_signals[i] = ema_falling and oshortsig

    return long_signals, short_signals


# ════════════════════════════════════════════════════════════════════
# DOJI REVERSAL DETECTION (lines 638-661)
# ════════════════════════════════════════════════════════════════════

def detect_doji_reversal(bars: List[OHLC],
                         config: Optional[StrategyConfig] = None,
                         pivot_trend_slow: Optional[List[float]] = None,
                         green_zone: Optional[List[bool]] = None,
                         red_zone: Optional[List[bool]] = None
                         ) -> Tuple[List[bool], List[bool]]:
    """
    Detect Doji Reversal signals across a series of bars.

    Pine Script Source:
        Dbodysize = 0.05
        Dlongsig = GREENZONE and ((high[1] - low[1]) > (AverageCandle * 0.9)) and
                   (abs(open[1] - close[1]) <= (Dbodysize * (high[1] - low[1]))) and (close > open)
        Dshortsig = REDZONE and ((high[1] - low[1]) > (AverageCandle * 0.9)) and
                    (abs(open[1] - close[1]) <= (Dbodysize * (high[1] - low[1]))) and (close < open)
        Dlongsignal = ta.rising(fPivotPDEMAS, 1) and Dlongsig
        Dshortsignal = ta.falling(fPivotPDEMAS, 1) and Dshortsig
    """
    cfg = config or StrategyConfig()
    n = len(bars)
    long_signals = [False] * n
    short_signals = [False] * n

    for i in range(1, n):
        prev = bars[i - 1]
        curr = bars[i]

        start = max(0, (i - 1) - cfg.avg_candle_len)
        candle_sizes = [bars[j].range for j in range(start, i - 1)] if (i - 1) > 0 else []
        avg_candle = sum(candle_sizes) / len(candle_sizes) if candle_sizes else prev.range

        prev_rng = prev.range
        prev_body = prev.body
        dbodysize = cfg.doji_body_size
        large_enough = prev_rng > avg_candle * cfg.doji_candle_mult if avg_candle > 0 else True

        gz = green_zone[i] if green_zone is not None and i < len(green_zone) else True
        rz = red_zone[i] if red_zone is not None and i < len(red_zone) else True

        dlongsig = (gz and large_enough and
                    (prev_body <= dbodysize * prev_rng) and
                    (curr.close > curr.open))

        dshortsig = (rz and large_enough and
                     (prev_body <= dbodysize * prev_rng) and
                     (curr.close < curr.open))

        ema_rising = True
        ema_falling = True
        if pivot_trend_slow is not None and i < len(pivot_trend_slow):
            ema_rising = pivot_trend_slow[i] > pivot_trend_slow[i - 1]
            ema_falling = pivot_trend_slow[i] < pivot_trend_slow[i - 1]

        long_signals[i] = ema_rising and dlongsig
        short_signals[i] = ema_falling and dshortsig

    return long_signals, short_signals


# ════════════════════════════════════════════════════════════════════
# REVERSAL CANDLES (GreenCandle, RedCandle) (lines 667-668)
# ════════════════════════════════════════════════════════════════════

def compute_reversal_candles(bars: List[OHLC],
                             green_zone: Optional[List[bool]] = None,
                             red_zone: Optional[List[bool]] = None,
                             config: Optional[StrategyConfig] = None
                             ) -> Tuple[List[bool], List[bool]]:
    """
    Compute GreenCandle and RedCandle matching Pine Script lines 667-668:
        GreenCandle = Wlongsig[1] or Olongsig[1] or Elongsig[1] or Dlongsig[1]
        RedCandle = Wshortsig[1] or Oshortsig[1] or Eshortsig[1] or Dshortsig[1]
    """
    cfg = config or StrategyConfig()
    n = len(bars)
    green_candles = [False] * n
    red_candles = [False] * n
    if n < 2:
        return green_candles, red_candles

    # Raw signals without slope gating (representing Wlongsig, Olongsig, Elongsig, Dlongsig)
    w_long, w_short = detect_wick_reversal(bars, cfg, green_zone=green_zone, red_zone=red_zone)
    o_long, o_short = detect_outside_reversal(bars, cfg, green_zone=green_zone, red_zone=red_zone)
    e_long, e_short = detect_extreme_reversal(bars, cfg, green_zone=green_zone, red_zone=red_zone)
    d_long, d_short = detect_doji_reversal(bars, cfg, green_zone=green_zone, red_zone=red_zone)

    for i in range(1, n):
        green_candles[i] = w_long[i - 1] or o_long[i - 1] or e_long[i - 1] or d_long[i - 1]
        red_candles[i] = w_short[i - 1] or o_short[i - 1] or e_short[i - 1] or d_short[i - 1]

    return green_candles, red_candles
