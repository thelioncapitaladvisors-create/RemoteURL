# TLCS Platform Updates - July 2, 2026 (v1.3 — Cross-Platform Discrepancy Fix)

## Summary
Second hotfix pass after the v1.2 RCA. Identified and permanently resolved all remaining
discrepancies between the Website and Mobile App performance statistics screens.
Verification confirmed both platforms now produce identical values for all metrics.

## Discrepancies Found (Website vs Mobile — Before Fix)

| Metric | Website | Mobile | Root Cause |
|---|---|---|---|
| Equity Curve | +1.56% | +0.88% | `index.html` getExactPct missing sign enforcement |
| Sharpe Ratio | 0.08 | 0.05 | Same — corrupted avgRNum fed into formula |
| Sortino Ratio | 0.08 | 0.05 | Same — inflated downside deviation from bad signs |
| Avg Profit | +0.04% | +0.03% | Same — corrupted sum / different effective divider |
| Kelly % | 4.2% | 4.6% | Same + website clamps negative Kelly to 0 |
| Novice Mode Equity Pts | N/A | Inflated | Double-negation in page.tsx equity curve pts |

**Matching correctly (no changes needed):**
Total Trades 41 ✅ | Profit Factor 1.13 ✅ | Best Trade +1.06% ✅ | Avg Winner +0.51% ✅
Avg Loser -0.40% ✅ | Max Drawdown -2.38% ✅ | Consec. Losses 4 ✅ | Wins/Losses/B/E 15/17/9 ✅

## Bug 1 — `index.html` `getExactPct` Missing Sign Enforcement

### Root Cause
`index.html` was the **only file in the ecosystem** that hadn't received the v1.2 sign
enforcement fix. Its `getExactPct` function read raw `exact_pct` from Supabase without
enforcing sign based on outcome text:

```javascript
// BEFORE (broken) — trusts raw DB value, negative for Short wins
if (meta && meta.exact_pct != null) return Number(meta.exact_pct);

// AFTER (fixed) — enforces correct sign from status/outcome text
const isWin  = st.includes('TP') || st.includes('TARGET') || o === 'WIN';
const isLoss = (st.includes('STOP') && ...) || o === 'LOSS' || st.includes('SL');
if (isWin)  return  Math.abs(pctVal);
if (isLoss) return -Math.abs(pctVal);
```

### Impact
A Short trade hitting TP3 had `exact_pct = -0.X%` in Supabase (backend direction guessing bug).
`index.html` fed this negative value directly into:
- Equity Curve cumulative sum (artificially lowered)
- avgRNum for Sharpe/Sortino (made mean return smaller → ratios collapsed)
- Avg Profit calculation (dragged down by negative short wins)
- Kelly % (loss rate inflated artificially)

### Fix Applied
`index.html` getExactPct now uses identical logic to all other files:
WIN status → `+Math.abs(pct)` | LOSS status → `-Math.abs(pct)` | else → raw value

## Bug 2 — `index.html` `resolveOutcome` Dead Code Cleanup

Dead r_multiple remnant from v1.0 cleanup:
```javascript
// REMOVED (never executed, harmless but misleading)
let r = null;
if (r !== null) {   // always false
    if (r > 0) return 'WIN';
    if (r < 0) return 'LOSS';
}
```

## Bug 3 — `page.tsx` Double-Negation in Novice Mode Equity Curve Pts

### Root Cause
`getExactPct` was updated in v1.2 to return already-signed values:
- WIN → `+Math.abs(pct)`
- LOSS → `-Math.abs(pct)`

However, the `equityCurvePts` loop in `page.tsx` still had old code that re-applied
the sign manually:
```javascript
// BEFORE (double-negation bug)
const ptVal = resolveOutcome(s) === 'LOSS' ? -pt : pt;
// For a LOSS: pt = -0.40 → ptVal = -(-0.40) = +0.40 ← LOSS appears as GAIN

// AFTER (correct — use signed value directly)
equityCurvePts += pt;   // pt is already -0.40 for LOSS
```

### Impact
Only affected **Novice Mode** (Points-based equity curve). Pro Mode `equityCurveR`
was already correct (used `+= r` directly). In Novice Mode, every loss was being
counted as a gain in the equity curve, making the Points equity curve artificially bullish.

## Exact % Architecture Verification

Confirmed: TP1, TP2, TP3 and Trailing Stop are **NOT treated equally**.

The backend (`webhook/route.ts` lines 343–354) computes `exact_pct` as:
```javascript
let exitPrice = payload.close_price || payload.exit_price  // ACTUAL exit from TV
let computedEntry = activeSignal.entry || payload.entry    // ACTUAL entry from DB
const profitAmount = isLong ? (exitPrice - computedEntry) : (computedEntry - exitPrice);
const calculatedPct = (profitAmount / computedEntry) * 100;
finalOutcomePct = Number(calculatedPct.toFixed(3));        // stored as metadata.exact_pct
```

This means:
- A TP3 trade stores the **real % from entry to TP3 price** — not a flat assumption
- A Trailing Stop stores the **real % from entry to wherever the trail fired**
- B/E stores **~0.00%**
- Every metric (Kelly%, Avg Winner, Sharpe, Sortino, Equity Curve) uses this real number

The `status` field (TP1/TP2/TP3/TRAIL) is purely cosmetic for UI bucketing.
The `exact_pct` is always mathematically precise and trade-specific.

## Files Changed

| File | Repo | Commit | Change |
|---|---|---|---|
| `index.html` | `TLCS_Website_Deploy` | `d0a0903` | getExactPct sign enforcement + resolveOutcome dead code removal |
| `src/app/page.tsx` | `Tv-Alert-Mobile` | `afd01c6` | Remove double-negation in Novice Mode equity curve pts |
| Root submodules | `RemoteURL` | `cb4cf66` | Submodule pointer updates |

## Architecture Rule Reinforced

All 5 central files (`index.html`, `scanner.js`, `commodity-scanner.js`, `trade-metrics.js`, `page.tsx`)
now use **identical** `getExactPct` and `resolveOutcome` logic. Any future changes to
calculation logic MUST be applied to ALL 5 files simultaneously to prevent recurrence.

> **Canonical Rule**: `getExactPct` always enforces: WIN text → `+Math.abs(pct)`, LOSS text → `-Math.abs(pct)`.
> Never trust the raw sign of `metadata.exact_pct` from Supabase directly.
