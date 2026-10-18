# Platform Update Note: Version 1.0 Power Candle Midpoint Retest-Only Scalp Synchronization
**Date**: October 18, 2026  
**Module**: Strategy Engine (`algo_engine/strategies.py`) & Pine Script Indicators (`TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, `user_code.pine`)  
**Scope**: Decouple Macro S&R Breakout Bounces from Scalp Setups and Enforce Retest-Only Gating.

---

## 1. Executive Summary & Rationale

Under the previous implementation:
```pinescript
bool bouncedOffGrsMid = bouncedOffSR_Up or bouncedOffActualGrsMid
bool bouncedOffResMid = bouncedOffSR_Down or bouncedOffActualResMid
```
The scalp bounce condition was satisfied if EITHER the candle was an initial macro breakout impulse off S&R (`bouncedOffSR_Up`) OR an actual retest of a Power Candle Midpoint (`bouncedOffActualGrsMid`). This allowed initial breakout candles to prematurely trigger `LONG SCALP` or `SHORT SCALP` entries at the impulse extreme rather than waiting for a confirmation pullback.

Under the updated Version 1.0 logic:
1. **Impulse Formation**: When a candle bounces off an S&R level, a Power Candle (`GrS` / `ReS`) is identified and its 50% midpoint `(high + low) / 2` is registered into persistent state (`grsMid` / `resMid`).
2. **Pullback Retest**: Scalp signals exclusively enter on the **50% Midpoint Retest** of a previously established Power Candle.
3. **Midpoint Consumption**: Once a midpoint is touched/retested (`bouncedOffActualGrsMid` / `bouncedOffActualResMid`), it is immediately cleared (`na` / `None`) to prevent duplicate/tick-spam signals.
4. **Clean Decoupling**:
```pinescript
// 6. Final Bounce Flags used for Signals
//    - Replaced raw 'bouncedOffSR_Up' with retest-only bounce logic.
//    - Now exclusively enters on the retest of the Power Candle Midpoint,
//      eliminating the initial breakout candle from qualifying as the bounce.
bool bouncedOffGrsMid = bouncedOffActualGrsMid
bool bouncedOffResMid = bouncedOffActualResMid
```

---

## 2. DhanHQ Signal Engine Synchronization (`algo_engine/strategies.py`)

In the DhanHQ Python Signal Engine (`algo_engine/strategies.py`), the 4-step sequential evaluation lifecycle was implemented:

```python
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
grs = bar.is_green and (
    _bounce_up_from(ctx.val) or _bounce_up_from(ctx.cpr_pivot) or
    _bounce_up_from(ctx.L3) or _bounce_up_from(ctx.L4))

res = bar.is_red and (
    _bounce_down_from(ctx.vah) or _bounce_down_from(ctx.cpr_pivot) or
    _bounce_down_from(ctx.H3) or _bounce_down_from(ctx.H4))

if grs:
    self._grs_mid = bar.midpoint
if res:
    self._res_mid = bar.midpoint

# 4. Final Bounce Flags used for Signals (Retest-only per updated Pine Script)
# Exclusively enters on the retest of the Power Candle Midpoint,
# eliminating raw breakout candles from qualifying as the bounce.
bounced_off_grs_mid = bounced_off_actual_grs_mid
bounced_off_res_mid = bounced_off_actual_res_mid
```

---

## 3. Unit Test Verification & Parity Guarantee

A dedicated test suite `TestMidpointRetestScalp` was added to `algo_engine/tests/test_phase1.py`:
- **Bar 1**: Breakout candle off S&R creates a Power Candle and records its midpoint (`100.5`). Verifies 0 scalp signals are emitted on the breakout candle itself.
- **Bar 2**: Subsequent pullback candle retests `100.5` (`low < 100.5` and `close > 100.5`). Verifies `LONG SCALP` triggers on the retest and `_grs_mid` is consumed/cleared (`None`).
- **Bar 3**: Subsequent bars without fresh power candles do not trigger duplicate scalp signals.

Result: **93 / 93 unit tests passed** in 1.4s.

---

## 4. Production Anchors Updated

- `AGENTS.md` & `.agents/AGENTS.md`: Codified `Version 1.0 Power Candle Midpoint Retest-Only Scalp Synchronization Mandate`.
- `TV Indicator/TLCS_Live_Pivot_Alerts.pine`: Updated lines 3093–3100.
- `TV_Indicator_Full_Code.txt`: Synchronized lines 3093–3100.
- `user_code.pine`: Synchronized lines 3085–3092.
- Local backup archives refreshed and mirrored.
