# TLCS Ecosystem Update Log: July 15

## Webhook Bug Fixes & Architecture Restoration
- **Root Cause Analysis (RCA)**: Investigated the 0% win-rate bug where closed trades were manifesting as duplicate ghost entries (`Hit SL`, `EXITED AT ---`). Identified that the global deprecation of `outcome_pct` and `r_multiple` (enforced during the V1.0 transition) was never fully purged from the `route.ts` `.update()` payload. This collision caused the Supabase PostgREST transaction to crash with a 500 error every time TradingView fired a Trade Close alert, inadvertently causing the system to insert a brand new open trade instead of updating the existing one.
- **Webhook Payload Patch**: Permanently stripped the legacy `outcome_pct` and `r_multiple` references from the `route.ts` payload so database updates successfully complete without crashing.
- **Dynamic Close Detection (`route.ts`)**: Re-programmed the webhook to seamlessly identify exact exit levels (`TP1`, `TP2`, `TP3`, `TP4`, `Trailing Stop`) based on dynamic status string extraction rather than relying solely on the rigid `activeSignal.target` fallback. Exact close levels are now flawlessly registered in the database, preserving all precise UI filters.
- **Database Retroactive Repair**: Wrote and executed a Python script to surgically wipe out the duplicate "ghost" entries generated over the last week and natively recalculate the `outcome`, `exit_price`, and `exact_pct` directly back onto the original active signals.

## Frontend Enhancements
- **Active Filter Engine**: Upgraded `trade-metrics.js` to explicitly support the `ACTIVE` UI filter bucket within the "TODAY'S BEST MARKETS" section. Carefully decoupled these open signals from the core denominator so `ACTIVE` trades accurately render within their own isolated tab without dragging down or skewing the global Win Rate % on the `ALL` tab.

## Core Agent Protocols (`AGENTS.md`)
- **Strict Prohibition on Unilateral Fallbacks**: Enshrined a rigid constraint within the agent instructions explicitly prohibiting the unprompted injection of artificial fallback logic (e.g., mathematically guessing missing exit prices) and the arbitrary alteration of established business configurations (e.g., moving `NIFTY` out of the `WORLD` index during optimization passes). Future agents are hardcoded to halt execution and seek explicit user permission before attempting these architectural shifts.

## UI Crash & Missing Exact Percentage Resolution
- **Webhook Exit Fallback Enhancements**: Upgraded both the Web (`process-webhook-background.js`) and Mobile (`route.ts`) webhooks to intelligently parse non-standard exits (`Loss`, `Win`, `Trail`) for missing `close_price` scenarios. Exact performance metrics are now flawlessly calculated and injected as `exact_pct` regardless of how the trade exits.
- **Defensive Metadata Parsing Guardrails**: Patched `dashboard.html`, `scanner.js`, and `commodity-scanner.js` with defensive `null` parsing guardrails (`if (!meta) meta = {};`) to completely eliminate silent UI crashes and `AVG PROFIT` calculation failures caused by stringified `"null"` values in the `metadata` column.
- **Mathematical DB Backfill (`exact_pct`)**: Updated `fix_missing_exact_pct.py` to extract `trail_sl` for trailing stop closures and executed it directly on the Supabase database. Successfully backfilled the missing `exact_pct` for 81 historically corrupt closed trades. 
- **Mobile TP/Target UI Badges**: Fixed regex rules inside `page.tsx` (`tpMatch`) to dynamically accommodate both `TP` and `TARGET` label strings, completely restoring UI label reflection across the mobile alert log.

### Real Trade vs Limit Trade Hold Duration Fix (July 15 - Session 2)
- Fixed an issue where the Hold Duration on the Web and Mobile UIs was calculating based on the limit hit time (`signal_ts`) rather than the true execution time of the webhook (`created_at`).
- Prioritized `created_at` for entry timestamp and `exit_at` / `updated_at` / `created_at` for exit timestamp across `Tv-Alert-Mobile/src/app/page.tsx` and `TLCS_Website_Deploy/scanner.js` to ensure hold times accurately reflect the duration held in real-time execution.
- Ensured missing `exit_at` values (e.g. from same-bar completed trades via TradeClose webhook) gracefully fall back to the execution timestamps so that valid durations and exit dates are rendered instead of `--`.
