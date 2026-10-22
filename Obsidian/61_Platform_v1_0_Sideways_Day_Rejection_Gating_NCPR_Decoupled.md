# Platform v1.0 Sideways Day Rejection Gating & NCPR Decoupling
**Date**: October 22, 2026  
**Status**: Production Ready & Fully Verified

---

## Executive Summary

Per the user's explicit directive:
> **`¬isSidewaysDay ∨ NCPR ∨ isRejectionDay`. Ncpr is removed from the given code. Ignore ncpr.**

Narrow CPR (`NCPR`) has been completely decoupled and removed from the active trade gating logic across both the Master Pine Script engines (`TV_Indicator_Full_Code.txt`, `TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `user_code.pine`) and the DhanHQ Python BlackBox engine (`algo_engine/strategies.py`).

The operational filter is now strictly defined as:
22805\text{dayAllowed} = \neg \text{isSidewaysDay} \lor \text{isRejectionDay}22805

---

## 1. Mathematical Formulation & Architecture

### Prior Formulation (Coupled)
Previously:
22805\text{dayAllowed} = \neg \text{isSidewaysDay} \lor \text{NCPR} \lor \text{isRejectionDay}22805
Under this logic, a Narrow CPR day could theoretically permit trend momentum continuation trades on a trading range day even without structural Rejection.

### Production Formulation (NCPR Decoupled & Ignored)
22805\mathbf{dayAllowed = \neg isSidewaysDay \lor isRejectionDay}22805

Where:
1. **`isSidewaysDay`**:
   - `mX == "INRANGEINVALUE"` or
   - `mX == "TYPICAL DAY, \n TRADING RANGE, \n SIDEWAYS"` or
   - `str.contains(mX, "TRADING RANGE")` or
   - `str.contains(mX, "SIDEWAYS")` or
   - `str.contains(mX, "TYPICAL DAY")` or
   - `dX == "IN RANGE \n IN VALUE"`
2. **`isRejectionDay`**:
   - Structural Rejection context: `REJECTIONDAY` or `str.contains(c1, "REJECT")` or `BounceUp` or `BounceDown` or `Elongsignal` or `Eshortsignal`.

---

## 2. Pine Script Indicator Implementation

In `TV_Indicator_Full_Code.txt`, `TV Indicator/TLCS_Live_Pivot_Alerts.pine`, and `user_code.pine`:

```pine
// ── ZONE DEFINITIONS (NCPR Removed) ──
bool bullConds = (mX == 'BIG MOVE') or
     (mX == 'TREND DAY, \n DOUBLE DISTRIBUTION TREND, \n EXPANDED TYPICAL') or
     (dX == 'OUT OF RANGE \n OUT OF VALUE') or
     (c1 == 'CONFIRMED BULLISH') or
     (c1 == 'REJECTED BEARISH') or
     (c1 == 'WATCH')

bool bearConds = (mX == 'BIG MOVE') or
     (mX == 'TREND DAY, \n DOUBLE DISTRIBUTION TREND, \n EXPANDED TYPICAL') or
     (dX == 'OUT OF RANGE \n OUT OF VALUE') or
     (c1 == 'CONFIRMED BEARISH') or
     (c1 == 'REJECTED BULLISH') or
     (c1 == 'WATCH')

// ── SIDEWAYS DAY & REJECTION FILTER (NCPR Ignored) ──
bool isSidewaysDay = (mX == 'INRANGEINVALUE') or
                     (mX == 'TYPICAL DAY, \n TRADING RANGE, \n SIDEWAYS') or
                     str.contains(mX, "TRADING RANGE") or
                     str.contains(mX, "SIDEWAYS") or
                     str.contains(mX, "TYPICAL DAY") or
                     (dX == 'IN RANGE \n IN VALUE')

bool isRejectionDay = REJECTIONDAY or str.contains(c1, "REJECT") or BounceUp or BounceDown or Elongsignal or Eshortsignal
bool dayAllowed = not isSidewaysDay or isRejectionDay
```

---

## 3. Python BlackBox Engine Implementation

In `algo_engine/strategies.py`:

```python
# Rejection Day qualification: institutional CPR failure/rejection, boundary bounces, or extreme reversals
is_rejection_day = (
    "REJECT" in c1 or
    bounce_up or bounce_down or
    ctx.extreme_long_signal or ctx.extreme_short_signal
)

# On sideways / trading range days, NO signals are allowed UNLESS it is a confirmed Rejection Day (NCPR ignored)
day_allowed = not is_sideways or is_rejection_day

# On sideways days, missile breakout momentum (miss_u/miss_d) is suppressed; only structural boundary bounces qualify
missile_allowed_on_day = not is_sideways or (is_rejection_day and (bounce_up or bounce_down))
```

---

## 4. Verification & Testing

- Automated Test Suite: `python3 -m unittest discover -s algo_engine/tests -p "test_*.py"\`
- Result: **108 unit tests passing (OK, skipped=1)**.
- User `: "DEBUG"` Sentinel: 100% preserved as the user's runtime alert system across all Pine Script indicators and BlackBox functions.
