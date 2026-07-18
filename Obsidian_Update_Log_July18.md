# July 18 Update Log: Metrics Parity, Active Limits Badge & Dynamic Fallback Logic

## 1. Metrics Synchronization (Web vs Mobile)
**Issue:** "WEEKLY TRADES" and "CLOSED TRADES" values significantly differed between the AI Dashboard and the Mobile App. The mobile app inadvertently included 'CANCELLED' trades in its closed trade counting variables (`closedSignals` and `weeklyClosedSignals`).
**Fix:** Explicitly filtered out 'CANCELLED' strings alongside 'OPEN' strings within the `page.tsx` array filters to match the strict counting logic found on the Web Dashboard.

## 2. 'ACTIVE LIMITS' Visual Bug Resolution
**Issue:** Cancelled trades were visually rendering as 'ACTIVE LIMIT' on the mobile app's alerts log, distorting the active state awareness.
**Fix:** Reordered the string resolution logic in the badge renderer in `page.tsx`. Introduced a top-level `if (finalOutcome === 'CANCELLED')` override to definitively assign a subdued gray "CANCELLED" pill before any other string matching (like "ACTIVE" or "OPEN") could falsely flag the trade.

## 3. Exit Price Fallback for Legacy Trades
**Issue:** The LOGS tab in the mobile app printed `--` for older trades because the exact `exit_price` wasn't explicitly populated in historical Pine Script webhook JSON payloads, despite the trade being closed.
**Fix:** Implemented mathematical fallback deduction logic directly into the mobile `page.tsx` alerts feed loop. If `signal.exit_price` is strictly null but the trade is closed, the UI layer now mathematically extracts the explicit `trail_sl` or TP boundaries from the database based on the status string and renders the deduced price in the "EXITED AT" slot dynamically.

## 4. 'B/E' Misclassification (Strict Granularity Enforcement)
**Issue:** Trades correctly identified via TradingView webhook string as `"Hit B/E"` were erroneously tagged with a red `❌ LOSS` outcome rather than `BREAKEVEN` across both the Web and Mobile applications.
**Fix:** Modified the `resolveOutcome()` structural hierarchy inside `dashboard.html`, `trade-metrics.js`, and `page.tsx`. Prioritized the granular checking of `st.includes('BREAK EVEN')` or `st.includes('B/E')` to ensure it always overrides a generic `o === 'LOSS'` payload fallback.

## 5. Market Guidance Table Parity
**Issue:** The "Today's Market Guidance" table on the AI Research page (`metrics.html`) rendered blank `--` values for Opening Bias, Day Type, Swing, and Zone, even though those exact values successfully parsed in the Trade Logs view.
**Fix:** Rewrote the `trade-metrics.js` table compiler loop to search the top-level payload structure before falling back to the `metadata` object (e.g., `const ob = s.opening_bias || meta.opening_bias`), instantly restoring the missing data to the table.
