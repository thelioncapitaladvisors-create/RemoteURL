# TLCS Platform Updates - July 2, 2026 (v1.0.2 — Metrics RCA Hotfix)

## Bug Description
When reviewing the MARKET WIDE PERFORMANCE statistics screen around 8:15 AM, three successfully closed trades (two hitting TP3) showed Kelly%, Avg Winner, Avg Loser, Equity Curve, and Realized R:R all flipped into negative values — the exact opposite of what was expected for winning trades.

## Root Cause Analysis (RCA)

### Primary Cause — Backend Direction Guessing
When a TradingView `TradeClose` webhook arrives (e.g., for a Short trade hitting TP3), the backend `route.ts` searches for the active signal in Supabase to read its `type`. If no active signal is found (due to race conditions, duplicate entries, or the lookup failing), the backend defaults to assuming the trade was **Long**. For a winning Short trade (Entry > Exit price), this causes the backend to calculate a **negative** `exact_pct` value (e.g., -0.17%), which is then stored into `metadata.exact_pct` in Supabase.

### Secondary Cause — Legacy `r_multiple` Code Surviving in Mobile App
The Mobile App (`Tv-Alert-Mobile/src/app/page.tsx`) contained a legacy copy of `resolveOutcome` that still parsed `r_multiple` and `profit_pct` to determine trade outcomes, violating the Version 1.0 rule established last week. Because the backend stored a negative `r_multiple` for the Short win, the mobile app classified the winning trade as a **LOSS**, causing a divergence: Website showed 38 trades with 39.5% win rate; Mobile app showed 39 trades with a different win rate.

### Tertiary Cause — No Sign Enforcement in Frontend Calculations
Even on the website, `getExactPct()` was pulling the raw `exact_pct` value from Supabase without enforcing the correct sign based on trade outcome text. So a trade with `status: "TP3"` but `exact_pct: -0.17` was feeding a **negative percentage into all performance metric formulas**, flipping Kelly%, Avg Winner, Sharpe Ratio, Sortino Ratio, and the Equity Curve red.

## Fix Applied

### Website — `TLCS_Website_Deploy`
- **`trade-metrics.js`**: `getExactPct()` now enforces sign: if `status`/`outcome` resolves to WIN → `+Math.abs(pct)`, if LOSS → `-Math.abs(pct)`. No longer trusts the raw sign from Supabase.
- **`scanner.js`**: Same sign enforcement applied to both `getExactPct()` instances. `resolveOutcome()` purged of dead `null != null` r_multiple remnant code. Now uses inline `exact_pct` metadata read as fallback, avoiding circular dependency.
- **`commodity-scanner.js`**: Same sign enforcement and `resolveOutcome` cleanup applied to match the other two files exactly.

### Mobile App — `Tv-Alert-Mobile`
- **`src/app/page.tsx`**: Completely rewrote `resolveOutcome` and `getExactPct` to comply with Version 1.0 rules.
  - Moved `getExactPct` definition **before** `resolveOutcome` (fixes circular dependency risk).
  - `getExactPct` now uses inline outcome text (`TP`/`TARGET` = WIN, `STOP`/`SL` = LOSS) for sign determination.
  - `resolveOutcome` now falls back to `getExactPct` for inferred outcomes — **r_multiple and profit_pct fully purged**.
  - Removed the duplicate stale `getExactPct` definition that existed after `resolveOutcome`.

## Impact of the Fix
- Kelly%, Avg Winner, Avg Loser, Best Trade, Realized R:R, and Equity Curve now all display correctly for Short trades hitting TP levels.
- Sharpe Ratio and Sortino Ratio now reflect true risk-adjusted performance (Short wins no longer counted as downside deviation).
- Website and Mobile App now compute identical values for all metrics down to the decimal place.
- Fix is **retroactive** — all historical closed trades are corrected dynamically on every page load, no database migration required.

## Repositories Updated
| Repository | Commit Hash | Status |
|---|---|---|
| `TLCS_Website_Deploy` | `1a5fab3` | ✅ Pushed to `main` |
| `Tv-Alert-Mobile` | `71259cc` | ✅ Pushed to `main` |
| `RemoteURL` (root) | `421ddae` | ✅ Submodule refs updated |

## Version 1.0 Rule Reinforced
> **NEVER** attempt to extract, parse, or rely on `r_multiple` or `profit_pct` for performance metrics. The correct math is `((Exit - Entry) / Entry) * 100` from `metadata.exact_pct`. This rule now enforced 100% across all files in both codebases.

## Additional Architectural Notes
- The Mobile App had a legacy `resolveOutcome` copy that drifted out of sync with the Website because both codebases are separate physical projects with no shared module system. This is a structural risk that will be mitigated by the planned phased migration to a unified Next.js monorepo.
- Short trade direction should ideally be sent explicitly by TradingView (`type: "Short"`) in the exit webhook to prevent backend guessing, though the frontend fix makes this non-critical for display purposes.
