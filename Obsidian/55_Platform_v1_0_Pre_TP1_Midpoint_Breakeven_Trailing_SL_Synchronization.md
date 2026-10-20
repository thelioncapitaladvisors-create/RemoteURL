# Platform v1.0 Pre-TP1 Midpoint Breakeven Trailing SL Synchronization Mandate
**Date**: October 20, 2026  
**Status**: Production Ready & Fully Verified

---

## Executive Summary
Per trader specification and direct visual trade analysis, when an active filled trade moves towards Take Profit 1 (TP1) and reaches the halfway point (midpoint) between Entry and TP1, the Stop Loss (SL) is immediately moved to the Entry level (Breakeven). This early capital protection lock prevents winning trades that travel significantly towards TP1 from reversing into losses, while preserving the entire existing TP1, TP2, TP3, TP4, and EMA trailing stop hierarchy.

This logic is synchronized with 100% mathematical parity across both the Pine Script TradingView indicator engines (`TV_Indicator_Full_Code.txt`, `TLCS_Live_Pivot_Alerts.pine`, `user_code.pine`) and the DhanHQ BlackBox Python Signal Engine (`algo_engine/trade_manager.py`).

---

## Architectural & Mathematical Specification

### 1. Midpoint Breakeven Formulation
For any active filled trade where TP1 has not yet triggered (`not trade.tp1Triggered`):

$$\text{Midpoint Level} = \frac{\text{trade.entryLevel} + \text{trade.tp1Level}}{2.0}$$

- **Long Trades (`isLong_`)**:
  - Condition: `high >= midTP1Level`
  - Action: If `trade.slLevel < trade.entryLevel`, update `trade.slLevel := trade.entryLevel` and activate trailing (`trade.trailingSLActivated := true`).
- **Short Trades (`not isLong_`)**:
  - Condition: `low <= midTP1Level`
  - Action: If `trade.slLevel > trade.entryLevel`, update `trade.slLevel := trade.entryLevel` and activate trailing (`trade.trailingSLActivated := true`).

### 2. Trailing SL Lifecycle Invariance
The existing trailing stop hierarchy is strictly preserved:
1. **Pre-TP1 Midpoint**: SL moves from initial risk level to `trade.entryLevel` (Breakeven).
2. **TP1 Trigger**: Realizes TP1 partial profit; SL remains secured at `trade.entryLevel`.
3. **TP2 Trigger**: Realizes TP2 partial profit; SL trails to `trade.tp1Level`.
4. **TP3 Trigger**: Realizes TP3 partial profit; SL trails to `trade.tp2Level`.
5. **TP4 Trigger & EMA Trailing**: Realizes TP4 partial profit; SL trails to `trade.tp3Level` and transitions to medium EMA trailing stops (`fMed_EMA`).

### 3. Telemetry & Webhook Integration
- **Chart Visuals**: When `trade.slLevel` is updated to Entry, `updateTradeVisuals()` immediately shifts the red dotted stop loss line (`visuals.stopLossMarkerLine`) and label (`visuals.stopLossMarkerLabel`) to `trade.entryLevel`.
- **Webhook Dispatch**: In `processTradeArray()`, the delta check `trade.slLevel != prevSL and trade.trailingSLActivated` automatically detects the shift and fires `sendTrailingSLAlert()` with `trigger: 'TrailingSLUpdate'`, keeping Supabase, Telegram alerts, and mobile dashboard in sync.

---

## Verification & Compliance
- **Pine Script Synchronization**: Verified and applied to `TV_Indicator_Full_Code.txt`, `TV Indicator/TLCS_Live_Pivot_Alerts.pine`, and `user_code.pine`.
- **Python DhanHQ Engine Parity**: Applied to `algo_engine/trade_manager.py`. All 103 unit tests in `algo_engine` pass cleanly.
- **Zero Regression**: Preserves zero-unilateral modification boundaries and Version 1.0 exact percentage calculations.
