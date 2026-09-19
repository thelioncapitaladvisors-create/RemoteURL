"""
algo_engine.trade_manager — Stateful Trade Lifecycle Manager
============================================================

Port of Pine Script trade execution engine from
TLCS_Dashboards_4_Commodities_Merged.pine (lines 2516-2700, 3158-3180).

Trade Lifecycle:
    1. LIMIT ORDER CREATION — Signal generated, entry/SL/TP levels locked
    2. LIMIT FILL DETECTION — Price reaches entry level on subsequent bar
    3. INVALIDATION — SL hit before limit fills → cancel order
    4. TP PROGRESSION — Step-based trailing stop on TP1→TP2→TP3→TP4
    5. TRAILING STOP — Standard ATR-based trailing after activation
    6. EMA TRAILING — Post-TP4, stop tracks max(TP3, EMA-32)
    7. DIVERGENCE EXIT — Regular/confirmed divergence exits
    8. EOD EXIT — Force close at end of day for intraday trades

Trailing Stop Progression (lines 2538-2585):
    TP1 hit → SL moves to Entry (Breakeven)
    TP2 hit → SL moves to TP1
    TP3 hit → SL moves to TP2
    TP4 hit → SL moves to TP3
    Post-TP4 → SL = max(TP3, EMA-32)  [for longs]
             → SL = min(TP3, EMA-32)  [for shorts]

Exit Categories:
    - TP1, TP2, TP3, TP4: Exact pre-defined take profit levels
    - TRAIL: Trailing stop between levels (arbitrary exit)
    - SL: Initial stop loss
    - B/E: Breakeven stop
    - EMA: Dynamic EMA exit post-TP4
    - DIV: Divergence exit
    - EOD: End of Day forced close

Exact Percentage Calculation:
    exact_pct = ((exit_price - entry_price) / entry_price) * 100
    (For shorts: ((entry_price - exit_price) / entry_price) * 100)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from .pivots import OHLC
from .strategies import StrategySignal


# ════════════════════════════════════════════════════════════════════
# ENUMS
# ════════════════════════════════════════════════════════════════════

class TradeStatus(Enum):
    """Trade lifecycle states."""
    ACTIVE_LIMIT = "ACTIVE LIMIT"      # Limit order placed, not yet filled
    ACTIVE = "ACTIVE"                   # Limit filled, trade is live
    CLOSED_SL = "SL"                    # Hit initial stop loss
    CLOSED_BE = "B/E"                   # Hit breakeven stop
    CLOSED_TP1 = "TP1"                  # Closed at TP1
    CLOSED_TP2 = "TP2"                  # Closed at TP2
    CLOSED_TP3 = "TP3"                  # Closed at TP3
    CLOSED_TP4 = "TP4"                  # Closed at TP4
    CLOSED_TRAIL = "TRAIL"             # Trailing stop hit (between levels)
    CLOSED_EMA = "EMA"                 # Post-TP4 EMA exit
    CLOSED_DIV = "DIV"                 # Divergence exit
    CLOSED_EOD = "EOD"                 # End of Day exit
    CANCELLED = "CANCELLED"            # Invalidated before fill
    EXPIRED = "EXPIRED"                # Expired without fill (24h)


class TradeOutcome(Enum):
    """Trade outcome classification."""
    OPEN = "OPEN"
    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"
    CANCELLED = "CANCELLED"


# ════════════════════════════════════════════════════════════════════
# TRADE DATA STRUCTURE
# ════════════════════════════════════════════════════════════════════

@dataclass
class Trade:
    """
    Complete trade state, mirroring Pine Script's TradeLogic UDT.
    
    Immutable at creation: entry_price, stop_loss, tp1-tp4, direction, name.
    Mutable during lifecycle: current_sl, status, exit_price, etc.
    """
    # ── Identity ──
    trade_id: str                     # Unique identifier
    name: str                         # e.g., "LONG LIGHTNING"
    direction: str                    # "LONG" or "SHORT"
    symbol: str = ""

    # ── Immutable Pre-Defined Levels (locked at signal genesis) ──
    entry_price: float = 0.0         # Limit order entry level
    initial_sl: float = 0.0          # Original stop loss level
    tp1: float = 0.0                 # Pre-defined TP1 level
    tp2: float = 0.0                 # Pre-defined TP2 level
    tp3: float = 0.0                 # Pre-defined TP3 level
    tp4: float = 0.0                 # Pre-defined TP4 level

    # ── Mutable Trade State ──
    current_sl: float = 0.0          # Current stop loss (moves during lifecycle)
    breakeven_level: float = 0.0     # Breakeven level (= entry after TP1)
    status: TradeStatus = TradeStatus.ACTIVE_LIMIT
    exit_price: Optional[float] = None
    exit_level: str = ""             # Exit level label (SL, TP1, TRAIL, etc.)
    exact_pct: Optional[float] = None  # ((Exit-Entry)/Entry) * 100

    # ── TP Progression Flags ──
    has_hit_entry: bool = False
    tp1_triggered: bool = False
    tp2_triggered: bool = False
    tp3_triggered: bool = False
    tp4_triggered: bool = False
    sl_triggered: bool = False
    is_closed: bool = False

    # ── Trailing Stop State ──
    trailing_sl_activated: bool = False
    trailing_sl_level: Optional[float] = None
    ema_exit_triggered: bool = False
    div_exit_triggered: bool = False
    force_closed: bool = False

    # ── Timing ──
    signal_bar_index: int = 0        # Bar index when signal was generated
    entry_bar_index: Optional[int] = None  # Bar index when limit was filled
    exit_bar_index: Optional[int] = None
    signal_timestamp: Optional[str] = None
    entry_timestamp: Optional[str] = None
    exit_timestamp: Optional[str] = None

    # ── Position (for partial TP) ──
    position_remaining: float = 100.0  # % of position still open

    @property
    def is_long(self) -> bool:
        return self.direction == "LONG"

    @property
    def outcome(self) -> TradeOutcome:
        """
        Determine trade outcome using EXACT PERCENTAGE as single source of truth.
        
        CRITICAL: exact_pct is checked FIRST, before any keyword matching.
        This prevents the "Hit B/E" + exact_pct=+1.35% regression.
        """
        if self.status == TradeStatus.CANCELLED or self.status == TradeStatus.EXPIRED:
            return TradeOutcome.CANCELLED

        if self.exact_pct is not None:
            if self.exact_pct > 0:
                return TradeOutcome.WIN
            elif self.exact_pct < 0:
                return TradeOutcome.LOSS
            else:
                return TradeOutcome.BREAKEVEN

        if not self.is_closed:
            return TradeOutcome.OPEN

        return TradeOutcome.OPEN

    def compute_exact_pct(self) -> Optional[float]:
        """
        Compute exact percentage: ((Exit - Entry) / Entry) * 100.
        
        For shorts: direction is inverted.
        This is the SINGLE SOURCE OF TRUTH for P/L calculation.
        
        NEVER use r_multiple or TradingView outcome_pct.
        """
        if self.exit_price is None or self.entry_price == 0:
            return None

        if self.is_long:
            pct = ((self.exit_price - self.entry_price) / self.entry_price) * 100
        else:
            pct = ((self.entry_price - self.exit_price) / self.entry_price) * 100

        return round(pct, 6)


# ════════════════════════════════════════════════════════════════════
# TRADE MANAGER ENGINE
# ════════════════════════════════════════════════════════════════════

@dataclass
class TradeManagerConfig:
    """Configuration for the trade manager."""
    break_even_enabled: bool = True     # Move SL to BE after TP1
    max_trade_duration_bars: int = 0    # 0 = no limit (use EOD instead)
    max_trade_duration_ms: int = 86400000  # 24 hours in milliseconds
    trailing_atr_multiplier: float = 1.0  # Trailing stop distance in ATR
    div_exit_enabled: bool = True       # Enable divergence exits


class TradeManager:
    """
    Stateful Trade Lifecycle Manager.
    
    Replicates Pine Script evaluateTradeProgress() (lines 2516-2700)
    and the master execution engine (lines 3158-3180).
    
    Usage:
        manager = TradeManager()
        trade = manager.create_trade(signal)
        
        for bar in subsequent_bars:
            manager.update(trade, bar, bar_index, ema_value)
            if trade.is_closed:
                print(f"Trade closed: {trade.exit_level} at {trade.exact_pct}%")
    """

    def __init__(self, config: Optional[TradeManagerConfig] = None):
        self.config = config or TradeManagerConfig()
        self._active_trades: List[Trade] = []

    def create_trade(self, signal: StrategySignal, symbol: str = "") -> Trade:
        """
        Create a new Trade from a StrategySignal.
        
        Pine Script Source (initializeTradeSession, lines 2865-2900):
            - Entry at trendLine (session midpoint)
            - SL/TP computed from ATR multipliers
            - All levels locked immutably at creation
        
        Args:
            signal: StrategySignal from the strategy engine
            symbol: Trading symbol
        
        Returns:
            New Trade object in ACTIVE_LIMIT status
        """
        trade_id = f"{symbol}_{signal.timestamp or signal.bar_index}_{signal.name}"

        trade = Trade(
            trade_id=trade_id,
            name=signal.name,
            direction=signal.direction,
            symbol=symbol,
            entry_price=signal.entry_price,
            initial_sl=signal.stop_loss,
            current_sl=signal.stop_loss,
            breakeven_level=signal.entry_price,
            tp1=signal.tp1,
            tp2=signal.tp2,
            tp3=signal.tp3,
            tp4=signal.tp4,
            status=TradeStatus.ACTIVE_LIMIT,
            signal_bar_index=signal.bar_index,
            signal_timestamp=signal.timestamp,
        )

        self._active_trades.append(trade)
        return trade

    def update(self, trade: Trade, bar: OHLC, bar_index: int,
               med_ema: Optional[float] = None,
               bull_regular_div: bool = False,
               bear_regular_div: bool = False,
               bull_hidden_div: bool = False,
               bear_hidden_div: bool = False,
               is_session_last_bar: bool = False,
               trail_range: Optional[float] = None) -> None:
        """
        Update a trade's state with a new bar.
        
        Port of evaluateTradeProgress() (lines 2516-2700).
        
        Args:
            trade: Trade to update
            bar: Current OHLC bar
            bar_index: Current bar index
            med_ema: Medium EMA value (32-period on Typical Price)
            bull_regular_div: Regular bullish divergence on current bar
            bear_regular_div: Regular bearish divergence on current bar
            bull_hidden_div: Hidden bullish divergence on current bar
            bear_hidden_div: Hidden bearish divergence on current bar
            is_session_last_bar: True if this is the last bar of the session
            trail_range: Trailing stop distance (ATR-based)
        """
        if trade.is_closed:
            return

        is_long = trade.is_long

        # ═══════════════════════════════════════════════════════
        # 1. LIMIT FILL DETECTION (lines 2523-2528)
        # Cannot fill on signal candle (bar_index > startBarIndex)
        # ═══════════════════════════════════════════════════════
        if not trade.has_hit_entry and bar_index > trade.signal_bar_index:
            entry_hit = (bar.low <= trade.entry_price if is_long
                         else bar.high >= trade.entry_price)
            if entry_hit:
                trade.has_hit_entry = True
                trade.entry_bar_index = bar_index
                trade.entry_timestamp = bar.timestamp
                trade.status = TradeStatus.ACTIVE

        # ═══════════════════════════════════════════════════════
        # 2. INVALIDATION (lines 2530-2536)
        # SL hit before limit fills → cancel
        # ═══════════════════════════════════════════════════════
        if not trade.has_hit_entry and not trade.is_closed and bar_index > trade.signal_bar_index:
            is_invalidated = (bar.low <= trade.current_sl if is_long
                              else bar.high >= trade.current_sl)
            if is_invalidated:
                trade.is_closed = True
                trade.force_closed = True
                trade.status = TradeStatus.CANCELLED
                trade.exit_bar_index = bar_index
                trade.exit_timestamp = bar.timestamp
                return

        # Skip further processing if trade hasn't filled yet
        if not trade.has_hit_entry:
            return

        just_hit_tp = False

        # ═══════════════════════════════════════════════════════
        # 3. TP EVALUATIONS (lines 2538-2585)
        # ═══════════════════════════════════════════════════════

        # TP1 (lines 2539-2549)
        if not trade.tp1_triggered:
            tp1_hit = (bar.high >= trade.tp1 if is_long
                       else bar.low <= trade.tp1)
            if tp1_hit:
                trade.tp1_triggered = True
                just_hit_tp = True
                if self.config.break_even_enabled:
                    trade.breakeven_level = trade.entry_price
                    if is_long:
                        if trade.current_sl < trade.breakeven_level:
                            trade.current_sl = trade.breakeven_level
                    else:
                        if trade.current_sl > trade.breakeven_level:
                            trade.current_sl = trade.breakeven_level

        # TP2 (lines 2551-2561)
        if not trade.tp2_triggered and trade.tp1_triggered:
            tp2_hit = (bar.high >= trade.tp2 if is_long
                       else bar.low <= trade.tp2)
            if tp2_hit:
                trade.tp2_triggered = True
                just_hit_tp = True
                if self.config.break_even_enabled:
                    trade.breakeven_level = trade.tp1
                    if is_long:
                        if trade.current_sl < trade.breakeven_level:
                            trade.current_sl = trade.breakeven_level
                    else:
                        if trade.current_sl > trade.breakeven_level:
                            trade.current_sl = trade.breakeven_level

        # TP3 (lines 2563-2573)
        if not trade.tp3_triggered and trade.tp2_triggered:
            tp3_hit = (bar.high >= trade.tp3 if is_long
                       else bar.low <= trade.tp3)
            if tp3_hit:
                trade.tp3_triggered = True
                just_hit_tp = True
                if self.config.break_even_enabled:
                    trade.breakeven_level = trade.tp2
                    if is_long:
                        if trade.current_sl < trade.breakeven_level:
                            trade.current_sl = trade.breakeven_level
                    else:
                        if trade.current_sl > trade.breakeven_level:
                            trade.current_sl = trade.breakeven_level

        # TP4 (lines 2575-2585)
        if not trade.tp4_triggered and trade.tp3_triggered:
            tp4_hit = (bar.high >= trade.tp4 if is_long
                       else bar.low <= trade.tp4)
            if tp4_hit:
                trade.tp4_triggered = True
                just_hit_tp = True
                if self.config.break_even_enabled:
                    trade.breakeven_level = trade.tp3
                    if is_long:
                        if trade.current_sl < trade.breakeven_level:
                            trade.current_sl = trade.breakeven_level
                    else:
                        if trade.current_sl > trade.breakeven_level:
                            trade.current_sl = trade.breakeven_level

        # ═══════════════════════════════════════════════════════
        # 4. STANDARD TRAILING STOP (lines 2587-2601)
        # ═══════════════════════════════════════════════════════
        if trail_range is not None and not trade.tp4_triggered:
            if (trade.trailing_sl_activated or trade.tp1_triggered) and not just_hit_tp:
                if is_long:
                    trail_level = bar.high - trail_range
                    if trail_level > trade.current_sl:
                        trade.current_sl = trail_level
                        trade.trailing_sl_level = trail_level
                        trade.trailing_sl_activated = True
                else:
                    trail_level = bar.low + trail_range
                    if trail_level < trade.current_sl:
                        trade.current_sl = trail_level
                        trade.trailing_sl_level = trail_level
                        trade.trailing_sl_activated = True

        # ═══════════════════════════════════════════════════════
        # 5. STOP LOSS CHECK (lines 2603-2615)
        # ═══════════════════════════════════════════════════════
        if not trade.sl_triggered and not trade.is_closed:
            if just_hit_tp:
                # On TP hit bar, check close instead of low/high
                is_sl_hit = (bar.close <= trade.current_sl if is_long
                             else bar.close >= trade.current_sl)
            else:
                is_sl_hit = (bar.low <= trade.current_sl if is_long
                             else bar.high >= trade.current_sl)

            if is_sl_hit:
                trade.sl_triggered = True
                trade.is_closed = True
                trade.exit_price = trade.current_sl
                trade.exit_bar_index = bar_index
                trade.exit_timestamp = bar.timestamp
                trade.exact_pct = trade.compute_exact_pct()

                # Determine exit level label
                trade.exit_level = self._resolve_exit_level(trade)
                trade.status = self._resolve_exit_status(trade)
                return

        # ═══════════════════════════════════════════════════════
        # 6. EMA TRAILING (Post-TP4, lines 2617-2635)
        # ═══════════════════════════════════════════════════════
        if trade.tp4_triggered and not trade.is_closed and med_ema is not None:
            # Post-TP4: SL = max(TP3, EMA) for longs, min(TP3, EMA) for shorts
            if is_long:
                trade.current_sl = max(trade.tp3, med_ema)
            else:
                trade.current_sl = min(trade.tp3, med_ema)

            trade.trailing_sl_level = trade.current_sl
            trade.trailing_sl_activated = False  # Standard trailing disabled

            # EMA cross check (line 2625)
            is_ema_cross = (bar.close < trade.current_sl if is_long
                            else bar.close > trade.current_sl)

            if is_ema_cross:
                trade.is_closed = True
                trade.exit_price = bar.close
                trade.exit_bar_index = bar_index
                trade.exit_timestamp = bar.timestamp
                trade.exact_pct = trade.compute_exact_pct()

                # Check if EMA advanced beyond TP3 (lines 2628-2632)
                if is_long:
                    is_ema_advanced = med_ema > trade.tp3
                else:
                    is_ema_advanced = med_ema < trade.tp3

                if is_ema_advanced:
                    trade.ema_exit_triggered = True
                    trade.exit_level = "EMA"
                    trade.status = TradeStatus.CLOSED_EMA
                else:
                    trade.sl_triggered = True
                    trade.exit_level = self._resolve_exit_level(trade)
                    trade.status = self._resolve_exit_status(trade)
                return

        # ═══════════════════════════════════════════════════════
        # 7. DIVERGENCE EXIT (lines 2637-2680)
        # ═══════════════════════════════════════════════════════
        if self.config.div_exit_enabled and not trade.is_closed:
            # Rule 1: Regular divergence fires NOW → immediate exit
            is_reg_div_exit = ((is_long and bear_regular_div) or
                               (not is_long and bull_regular_div))

            # Rule 2: Confirmed divergence (requires price action confirmation)
            # Simplified: just check if divergence + price confirms
            is_confirmed_div_exit = False  # Would need bar[1] divergence tracking

            if is_reg_div_exit or is_confirmed_div_exit:
                trade.is_closed = True
                trade.div_exit_triggered = True
                trade.exit_price = bar.close
                trade.exit_bar_index = bar_index
                trade.exit_timestamp = bar.timestamp
                trade.exact_pct = trade.compute_exact_pct()
                trade.exit_level = "DIV"
                trade.status = TradeStatus.CLOSED_DIV
                return

        # ═══════════════════════════════════════════════════════
        # 8. EOD EXIT (lines 3177-3178)
        # ═══════════════════════════════════════════════════════
        if is_session_last_bar and not trade.is_closed:
            trade.is_closed = True
            trade.force_closed = True
            trade.exit_price = bar.close
            trade.exit_bar_index = bar_index
            trade.exit_timestamp = bar.timestamp
            trade.exact_pct = trade.compute_exact_pct()
            trade.exit_level = "EOD"
            trade.status = TradeStatus.CLOSED_EOD
            return

    def _resolve_exit_level(self, trade: Trade) -> str:
        """
        Resolve the exit level label based on current SL position.
        
        Uses Pre-Defined Limit Level Binding:
        Compare exit_price against the trade's own pre-defined TP columns.
        
        Rules:
            - If exact_pct < 0: level MUST be SL (or EMA/DIV/EOD)
            - If exact_pct > 0: level MUST NOT be SL or B/E
            - Check TP levels with ±0.2% proximity window
        """
        if trade.exit_price is None:
            return "UNKNOWN"

        exit_p = trade.exit_price
        pct = trade.exact_pct

        # If loss, must be SL
        if pct is not None and pct < 0:
            return "SL"

        # If breakeven (pct == 0)
        if pct is not None and pct == 0:
            return "B/E"

        # If win, check pre-defined TP levels with ±0.2% proximity
        tolerance = 0.002  # 0.2%

        for level_name, level_val in [("TP4", trade.tp4), ("TP3", trade.tp3),
                                       ("TP2", trade.tp2), ("TP1", trade.tp1)]:
            if level_val != 0 and abs(exit_p - level_val) / max(abs(level_val), 1e-10) <= tolerance:
                return level_name

        # Win but between levels → TRAIL
        if pct is not None and pct > 0:
            if trade.trailing_sl_activated or trade.tp1_triggered:
                # Check which TP level the trailing stop was near
                if trade.tp4_triggered:
                    return "TRAIL"
                elif trade.tp3_triggered:
                    return "TRAIL"
                elif trade.tp2_triggered:
                    return "TRAIL"
                elif trade.tp1_triggered:
                    return "TRAIL"
            return "TRAIL"

        return "SL"

    def _resolve_exit_status(self, trade: Trade) -> TradeStatus:
        """Map exit level label to TradeStatus enum."""
        level = trade.exit_level
        status_map = {
            "SL": TradeStatus.CLOSED_SL,
            "B/E": TradeStatus.CLOSED_BE,
            "TP1": TradeStatus.CLOSED_TP1,
            "TP2": TradeStatus.CLOSED_TP2,
            "TP3": TradeStatus.CLOSED_TP3,
            "TP4": TradeStatus.CLOSED_TP4,
            "TRAIL": TradeStatus.CLOSED_TRAIL,
            "EMA": TradeStatus.CLOSED_EMA,
            "DIV": TradeStatus.CLOSED_DIV,
            "EOD": TradeStatus.CLOSED_EOD,
        }
        return status_map.get(level, TradeStatus.CLOSED_SL)

    @property
    def active_trades(self) -> List[Trade]:
        """Return all currently active (not closed) trades."""
        return [t for t in self._active_trades if not t.is_closed]

    @property
    def closed_trades(self) -> List[Trade]:
        """Return all closed trades."""
        return [t for t in self._active_trades if t.is_closed]

    @property
    def all_trades(self) -> List[Trade]:
        """Return all trades."""
        return list(self._active_trades)

    def get_trade_by_id(self, trade_id: str) -> Optional[Trade]:
        """Find a trade by its ID."""
        for trade in self._active_trades:
            return trade if trade.trade_id == trade_id else None
        return None
