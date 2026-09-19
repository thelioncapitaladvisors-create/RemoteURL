"""
algo_engine.pivots — Camarilla Pivots, CPR, EMAs, and ATR
==========================================================

Port of Pine Script Camarilla H1-H5 / L1-L5, Central Pivot Range (Pivot, TC, BC),
EMA calculations on Typical/Pivot Price, and ATR computations.

Source Reference:
    TLCS_Dashboards_4_Commodities_Merged.pine  lines 38-44, 945-961, 2395-2416
    TV_Indicator_Full_Code.txt                  lines 38-44, 961-977, 2417-2440

Mathematical Formulas:
    Range = High - Low  (of previous completed daily bar)
    
    Camarilla Levels (using previous day Close and Range):
        H5 = High / Low * Close
        H4 = Close + Range * 1.1 / 2    = Close + Range * 0.55
        H3 = Close + Range * 1.1 / 4    = Close + Range * 0.275
        H2 = Close + Range * 1.1 / 6    = Close + Range * 0.18333...
        H1 = Close + Range * 1.1 / 12   = Close + Range * 0.09167...
        L1 = Close - Range * 1.1 / 12   = Close - Range * 0.09167...
        L2 = Close - Range * 1.1 / 6    = Close - Range * 0.18333...
        L3 = Close - Range * 1.1 / 4    = Close - Range * 0.275
        L4 = Close - Range * 1.1 / 2    = Close - Range * 0.55
        L5 = Close - (H5 - Close) = 2 * Close - H5
    
    CPR (Central Pivot Range):
        Pivot = (H + L + C) / 3
        BC (Bottom Central) = (H + L) / 2
        TC (Top Central) = Pivot - BC + Pivot = 2 * Pivot - BC
        Actual_TC = max(TC, BC)
        Actual_BC = min(TC, BC)
    
    EMAs (on Typical/Pivot Price = (H + L + C) / 3):
        Short EMA  = EMA(Pivot, 13)
        Medium EMA = EMA(Pivot, 32)
        Trend EMA  = EMA(Pivot, 21)
    
    ATR = Simple Moving Average of True Range over N periods
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import math


# ════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ════════════════════════════════════════════════════════════════════

@dataclass
class CamarillaLevels:
    """All 10 Camarilla pivot levels for a given day."""
    H5: float
    H4: float
    H3: float
    H2: float
    H1: float
    L1: float
    L2: float
    L3: float
    L4: float
    L5: float


@dataclass
class CPRLevels:
    """Central Pivot Range for a given day."""
    pivot: float       # (H + L + C) / 3
    tc: float          # Top Central (max of raw TC and BC)
    bc: float          # Bottom Central (min of raw TC and BC)
    width: float       # abs(tc - bc)
    is_narrow: bool    # NCPR: width/range < 5% (or 0.2% of pivot)


@dataclass
class DailyLevels:
    """Complete set of daily levels computed from previous day's OHLC."""
    camarilla: CamarillaLevels
    cpr: CPRLevels
    prev_high: float
    prev_low: float
    prev_close: float
    prev_range: float


@dataclass
class OHLC:
    """Single bar OHLC data."""
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    timestamp: Optional[str] = None

    @property
    def typical_price(self) -> float:
        """Pivot/Typical Price = (H + L + C) / 3"""
        return (self.high + self.low + self.close) / 3.0

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low

    @property
    def midpoint(self) -> float:
        return (self.high + self.low) / 2.0

    @property
    def is_green(self) -> bool:
        return self.close > self.open

    @property
    def is_red(self) -> bool:
        return self.close < self.open

    @property
    def close_position(self) -> float:
        """Position of close within the bar's range (0 = at low, 1 = at high)."""
        rng = self.range
        if rng == 0:
            return 0.5
        return (self.close - self.low) / rng


# ════════════════════════════════════════════════════════════════════
# CAMARILLA PIVOT CALCULATIONS
# ════════════════════════════════════════════════════════════════════

def compute_camarilla(prev_high: float, prev_low: float, prev_close: float) -> CamarillaLevels:
    """
    Compute Camarilla H1-H5, L1-L5 from previous day's HLC.
    
    Pine Script Source (lines 952-961 of TLCS_Dashboards_4_Commodities_Merged.pine):
        H5 := highhtf / lowhtf * closehtf
        H4 := closehtf + RANGE * 1.1 / 2
        H3 := closehtf + RANGE * 1.1 / 4
        H2 = closehtf + RANGE * 1.1 / 6
        H1 = closehtf + RANGE * 1.1 / 12
        L1 = closehtf - RANGE * 1.1 / 12
        L2 = closehtf - RANGE * 1.1 / 6
        L3 := closehtf - RANGE * 1.1 / 4
        L4 := closehtf - RANGE * 1.1 / 2
        L5 := closehtf - (H5 - closehtf)
    
    Args:
        prev_high:  Previous completed daily bar's High
        prev_low:   Previous completed daily bar's Low  
        prev_close: Previous completed daily bar's Close
    
    Returns:
        CamarillaLevels with all 10 levels
    """
    range_ = prev_high - prev_low
    c = prev_close

    # Guard against zero division (identical H/L)
    if prev_low == 0:
        h5 = c
    else:
        h5 = (prev_high / prev_low) * c

    h4 = c + range_ * 1.1 / 2.0     # 0.55 * Range
    h3 = c + range_ * 1.1 / 4.0     # 0.275 * Range
    h2 = c + range_ * 1.1 / 6.0     # 0.18333 * Range
    h1 = c + range_ * 1.1 / 12.0    # 0.09167 * Range

    l1 = c - range_ * 1.1 / 12.0
    l2 = c - range_ * 1.1 / 6.0
    l3 = c - range_ * 1.1 / 4.0
    l4 = c - range_ * 1.1 / 2.0
    l5 = c - (h5 - c)               # = 2 * Close - H5

    return CamarillaLevels(
        H5=h5, H4=h4, H3=h3, H2=h2, H1=h1,
        L1=l1, L2=l2, L3=l3, L4=l4, L5=l5
    )


# ════════════════════════════════════════════════════════════════════
# CPR (CENTRAL PIVOT RANGE) CALCULATIONS
# ════════════════════════════════════════════════════════════════════

def compute_cpr(prev_high: float, prev_low: float, prev_close: float) -> CPRLevels:
    """
    Compute Central Pivot Range from previous day's HLC.
    
    Pine Script Source (lines 38-44 of TLCS_Dashboards_4_Commodities_Merged.pine):
        Pi = (dDH_ + dDL_ + CL_) / 3.0
        Bcy = (dDH_ + dDL_) / 2
        Tcy = Pi - Bcy + Pi
        DTC = math.max(Tcy, Bcy)
        DBC = math.min(Tcy, Bcy)
    
    NCPR (Narrow CPR) check:
        CPR width < 5% of previous day range (or < 0.2% of pivot)
    
    Args:
        prev_high:  Previous completed daily bar's High
        prev_low:   Previous completed daily bar's Low
        prev_close: Previous completed daily bar's Close
    
    Returns:
        CPRLevels with pivot, tc, bc, width, and is_narrow flag
    """
    pivot = (prev_high + prev_low + prev_close) / 3.0
    raw_bc = (prev_high + prev_low) / 2.0
    raw_tc = pivot - raw_bc + pivot  # = 2 * pivot - bc

    tc = max(raw_tc, raw_bc)
    bc = min(raw_tc, raw_bc)
    width = abs(tc - bc)

    # NCPR check: width as % of previous day's range < 5%
    prev_range = max(prev_high - prev_low, 1e-10)  # prevent div-by-zero
    is_narrow = (width / prev_range) * 100 < 5.0

    return CPRLevels(
        pivot=pivot,
        tc=tc,
        bc=bc,
        width=width,
        is_narrow=is_narrow
    )


def compute_daily_levels(prev_high: float, prev_low: float, prev_close: float) -> DailyLevels:
    """
    Compute all daily levels (Camarilla + CPR) from previous day's HLC.
    
    Args:
        prev_high:  Previous completed daily bar's High
        prev_low:   Previous completed daily bar's Low
        prev_close: Previous completed daily bar's Close
    
    Returns:
        DailyLevels containing both Camarilla and CPR levels
    """
    return DailyLevels(
        camarilla=compute_camarilla(prev_high, prev_low, prev_close),
        cpr=compute_cpr(prev_high, prev_low, prev_close),
        prev_high=prev_high,
        prev_low=prev_low,
        prev_close=prev_close,
        prev_range=prev_high - prev_low
    )


# ════════════════════════════════════════════════════════════════════
# EMA CALCULATIONS
# ════════════════════════════════════════════════════════════════════

def ema(values: List[float], period: int) -> List[float]:
    """
    Compute Exponential Moving Average.
    
    Pine Script uses standard EMA: multiplier = 2 / (period + 1)
    
    IMPORTANT: In the TLCS indicator, EMAs are calculated on Typical/Pivot Price
    (H+L+C)/3, NOT on raw close. See Pine Script lines 2414-2416:
        FPivot = (high + low + close) / 3
        fShort_EMA = ta.ema(FPivot, Short_EMA)   # 13
        fMed_EMA   = ta.ema(FPivot, Med_EMA)     # 32
    
    Args:
        values: List of input values (typically Typical Price series)
        period: EMA lookback period
    
    Returns:
        List of EMA values (same length as input, first value = first input)
    """
    if not values or period <= 0:
        return []

    result = [0.0] * len(values)
    multiplier = 2.0 / (period + 1)

    # Initialize with first value
    result[0] = values[0]

    for i in range(1, len(values)):
        result[i] = (values[i] - result[i - 1]) * multiplier + result[i - 1]

    return result


def compute_emas_from_bars(bars: List[OHLC],
                           short_period: int = 13,
                           med_period: int = 32,
                           trend_period: int = 21) -> Tuple[List[float], List[float], List[float]]:
    """
    Compute Short, Medium, and Trend EMAs from a list of OHLC bars.
    
    All EMAs are computed on Typical Price = (H+L+C)/3, matching Pine Script.
    
    Pine Script Source (lines 2414-2416):
        fShort_EMA = ta.ema(FPivot, Short_EMA)  // 13
        fMed_EMA   = ta.ema(FPivot, Med_EMA)    // 32
    
    Args:
        bars: List of OHLC bars in chronological order
        short_period: Short EMA period (default 13)
        med_period: Medium EMA period (default 32) 
        trend_period: Trend EMA period (default 21)
    
    Returns:
        Tuple of (short_ema, med_ema, trend_ema) lists
    """
    typical_prices = [bar.typical_price for bar in bars]

    short_ema = ema(typical_prices, short_period)
    med_ema = ema(typical_prices, med_period)
    trend_ema = ema(typical_prices, trend_period)

    return short_ema, med_ema, trend_ema


# ════════════════════════════════════════════════════════════════════
# DOUBLE-SMOOTHED EMA (DEMA) — Pivot Trend Detection
# ════════════════════════════════════════════════════════════════════

def dema(values: List[float], period: int) -> List[float]:
    """
    Compute Double Exponential Moving Average.
    
    Pine Script Source (lines 441-450):
        fPivotEMAF1 = ta.ema(fPivot, fFastEMA1)     // 5
        fPivotEMAF2 = ta.ema(fPivotEMAF1, fFastEMA1) // double-smooth
        PDEMAF = fPivotEMAF1 * 2 - fPivotEMAF2
        fPivotPDEMAF = ta.ema(PDEMAF, fFastEMA1)     // triple-smooth
    
    Formula: DEMA = 2 * EMA(values, period) - EMA(EMA(values, period), period)
    
    Args:
        values: Input price series
        period: Smoothing period
    
    Returns:
        List of DEMA values
    """
    ema1 = ema(values, period)
    ema2 = ema(ema1, period)
    return [2.0 * e1 - e2 for e1, e2 in zip(ema1, ema2)]


def triple_ema(values: List[float], period: int) -> List[float]:
    """
    Compute Triple-Smoothed EMA (Pivot DEMA then smoothed again).
    
    Pine Script: fPivotPDEMAF = ta.ema(PDEMAF, fFastEMA1)
    This is: EMA(DEMA(values, period), period)
    
    Used for:
        fPivotPDEMAF (fast pivot trend, period=5) — used in emaCanBuy/emaCanSell
        fPivotPDEMAS (slow pivot trend, period=13) — used in emaCanBuy/emaCanSell
    """
    dema_vals = dema(values, period)
    return ema(dema_vals, period)


def compute_pivot_trend_emas(bars: List[OHLC],
                              fast_period: int = 5,
                              slow_period: int = 13) -> Tuple[List[float], List[float]]:
    """
    Compute the Pivot Trend DEMA indicators used for emaCanBuy / emaCanSell.
    
    Pine Script Source (lines 437-450):
        fPivotPDEMAF = triple-smooth EMA on Pivot with fast period (5)
        fPivotPDEMAS = triple-smooth EMA on Pivot with slow period (13)
    
    The Greenzone / Redzone conditions (line 895-899):
        Greenzone = (plus > minus) and (fShortEMA > fMedEMA) and (fPivotPDEMAF > fPivotPDEMAS)
        Redzone   = (minus > plus) and (fShortEMA < fMedEMA) and (fPivotPDEMAF < fPivotPDEMAS)
        emaCanBuy  = Greenzone or not Redzone
        emaCanSell = Redzone   or not Greenzone
    
    Args:
        bars: List of OHLC bars
        fast_period: Fast pivot DEMA period (default 5)
        slow_period: Slow pivot DEMA period (default 13)
    
    Returns:
        Tuple of (fast_pivot_trend, slow_pivot_trend) — fPivotPDEMAF, fPivotPDEMAS
    """
    typical_prices = [bar.typical_price for bar in bars]
    
    fast_trend = triple_ema(typical_prices, fast_period)
    slow_trend = triple_ema(typical_prices, slow_period)
    
    return fast_trend, slow_trend


# ════════════════════════════════════════════════════════════════════
# ATR (AVERAGE TRUE RANGE) CALCULATIONS
# ════════════════════════════════════════════════════════════════════

def true_range(bar: OHLC, prev_close: Optional[float] = None) -> float:
    """
    Compute True Range for a single bar.
    
    Pine Script: ta.tr(true)  — handles gaps
    TR = max(H - L, abs(H - prev_close), abs(L - prev_close))
    
    If prev_close is None (first bar), TR = H - L.
    """
    hl = bar.high - bar.low
    if prev_close is None:
        return hl
    return max(hl, abs(bar.high - prev_close), abs(bar.low - prev_close))


def compute_true_range_series(bars: List[OHLC]) -> List[float]:
    """Compute True Range for a series of bars."""
    if not bars:
        return []
    
    tr_values = [bars[0].range]  # First bar: H - L
    for i in range(1, len(bars)):
        tr_values.append(true_range(bars[i], bars[i - 1].close))
    
    return tr_values


def sma(values: List[float], period: int) -> List[float]:
    """
    Compute Simple Moving Average.
    
    For indices < period, uses available values (partial window).
    
    Args:
        values: Input series
        period: Lookback period
    
    Returns:
        List of SMA values (same length as input)
    """
    if not values:
        return []
    
    result = []
    for i in range(len(values)):
        start = max(0, i - period + 1)
        window = values[start:i + 1]
        result.append(sum(window) / len(window))
    
    return result


def compute_atr(bars: List[OHLC], period: int = 14) -> List[float]:
    """
    Compute ATR (Average True Range) using SMA of True Range.
    
    Pine Script Source (line 2367):
        atrValue = ta.atr(atrLengthInput)  // atrLengthInput = 14
    
    Note: ta.atr uses SMA (not EMA) of True Range in Pine Script v6.
    
    Args:
        bars: List of OHLC bars
        period: ATR lookback (default 14)
    
    Returns:
        List of ATR values (same length as bars)
    """
    tr_series = compute_true_range_series(bars)
    return sma(tr_series, period)


def compute_adr(bars: List[OHLC], period: int = 10) -> List[float]:
    """
    Compute Average Daily Range (ADR) using SMA of True Range, shifted by 1 bar.
    
    Pine Script Source (line 143 of TLCS_Sequence_Dashboard.pine):
        avgRange = ta.sma(ta.tr(true), adrLen)[1]
    
    The [1] shift means today's avgRange uses yesterday's completed SMA value.
    This prevents today's developing candle from affecting the reference range.
    
    Args:
        bars: Daily OHLC bars
        period: ADR lookback (default 10)
    
    Returns:
        List of ADR values. Index i contains the ADR as of bar i,
        computed from bars[0..i-1] (excluding bar i itself due to [1] shift).
    """
    tr_series = compute_true_range_series(bars)
    raw_sma = sma(tr_series, period)
    
    # Apply [1] shift: today's ADR = yesterday's SMA value
    shifted = [0.0] + raw_sma[:-1]  # Shift right by 1
    return shifted


# ════════════════════════════════════════════════════════════════════
# VALUE AREA CALCULATIONS
# ════════════════════════════════════════════════════════════════════

@dataclass
class ValueArea:
    """Value Area High (VAH), Value Area Low (VAL), POC."""
    vah: float
    val: float
    poc: float


def compute_value_area_from_bars(session_bars: List[OHLC],
                                  percent_of_tpo: float = 0.68) -> ValueArea:
    """
    Approximate Value Area from intraday bars using TPO distribution.
    
    This is a simplified implementation. The Pine Script uses a sophisticated
    TPO counting mechanism with bucket-based histograms. For the Black Box
    engine, we approximate using a price-weighted distribution.
    
    Args:
        session_bars: Intraday bars for the session
        percent_of_tpo: Percentage of TPOs for Value Area (default 68%)
    
    Returns:
        ValueArea with VAH, VAL, POC
    """
    if not session_bars:
        return ValueArea(vah=0, val=0, poc=0)
    
    # Simple approximation: POC at highest-volume price, VA at 68% of range
    session_high = max(b.high for b in session_bars)
    session_low = min(b.low for b in session_bars)
    session_range = session_high - session_low
    
    # POC: approximate as the most common price area (volume-weighted midpoint)
    total_vol = sum(b.volume for b in session_bars) or 1.0
    poc = sum(b.typical_price * b.volume for b in session_bars) / total_vol
    
    # Value Area: centered around POC, covering percent_of_tpo of range
    va_half_width = session_range * percent_of_tpo / 2.0
    vah = poc + va_half_width
    val = poc - va_half_width
    
    # Clamp to session bounds
    vah = min(vah, session_high)
    val = max(val, session_low)
    
    return ValueArea(vah=vah, val=val, poc=poc)


# ════════════════════════════════════════════════════════════════════
# OPENING BIAS / DAY TYPE CLASSIFICATION (dX / mX)
# ════════════════════════════════════════════════════════════════════

def compute_opening_bias(open_price: float,
                          prev_high: float, prev_low: float,
                          vah: float, val: float) -> str:
    """
    Compute Opening Bias (dX) — where the session opened relative to 
    previous day's range and value area.
    
    Pine Script Source (lines 742-744, 801):
        INRANGEINVALUE = OO_ > dDL_ and OO_ < dDH_ and OO_ > VAL and OO_ < VAH
        INRANGEOUTOFVALUE = OO_ > dDL_ and OO_ < dDH_ and (OO_ < VAL or OO_ > VAH)
        OUTOFRANGEVALUE = OO_ < dDL_ and OO_ < VAL or OO_ > dDH_ and OO_ > VAH
        
        dX = INRANGEINVALUE ? 'IN RANGE IN VALUE' 
           : INRANGEOUTOFVALUE ? 'IN RANGE OUT OF VALUE'
           : OUTOFRANGEVALUE ? 'OUT OF RANGE OUT OF VALUE' : 'DEBUG'
    
    Args:
        open_price: Today's session open
        prev_high:  Previous day's high
        prev_low:   Previous day's low
        vah:        Value Area High
        val:        Value Area Low
    
    Returns:
        Opening bias string
    """
    in_range = prev_low < open_price < prev_high
    in_value = val < open_price < vah

    if in_range and in_value:
        return "IN RANGE IN VALUE"
    elif in_range and not in_value:
        return "IN RANGE OUT OF VALUE"
    elif not in_range:
        return "OUT OF RANGE OUT OF VALUE"
    else:
        return "DEBUG"


# ════════════════════════════════════════════════════════════════════
# UTILITY: HIGHEST / LOWEST LOOKBACK
# ════════════════════════════════════════════════════════════════════

def highest(values: List[float], period: int, index: int) -> float:
    """
    Equivalent of Pine Script ta.highest(values, period) at a given index.
    Returns the highest value in the lookback window ending at `index`.
    """
    start = max(0, index - period + 1)
    window = values[start:index + 1]
    return max(window) if window else float('-inf')


def lowest(values: List[float], period: int, index: int) -> float:
    """
    Equivalent of Pine Script ta.lowest(values, period) at a given index.
    Returns the lowest value in the lookback window ending at `index`.
    """
    start = max(0, index - period + 1)
    window = values[start:index + 1]
    return min(window) if window else float('inf')


def bars_since(condition_series: List[bool], index: int) -> Optional[int]:
    """
    Equivalent of Pine Script ta.barssince(condition).
    Returns the number of bars since the condition was last True.
    Returns None if condition was never True.
    """
    for offset in range(index, -1, -1):
        if condition_series[offset]:
            return index - offset
    return None
