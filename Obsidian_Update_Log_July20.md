# Version 1.2.2 Update Log - July 20, 2026

## 🚀 Enhancements & Features

### 1. Weekly Trades Accuracy Enforcement
- **Universal Fix:** Updated the UI dashboard metrics and the mobile app (`WEEKLY TRADES`) to accurately reflect only `weeklyClosedSignals.length` rather than artificially inflating the count by including `ACTIVE LIMITS` and open positions. 

### 2. Exact Exit Level Badging Optimization
- **Nomenclature Sync:** Replaced generic "TP HIT" strings in the UI with explicitly mapped filters (e.g., `TP1`, `TP2`, `TRAIL`) across all modal badges and success labels, while preserving the exact numeric exit prices below them. This satisfies strict adherence to legacy nomenclature without violating the rigid mathematical fallback rules.

### 3. End-of-Day (EOD) Unexecuted Limit Filtration
- **Backend API Fix:** Upgraded the EOD-closer API (`src/app/api/cron/eod-close/route.ts`) to aggressively differentiate between executed and unexecuted limit orders after market closure.
- **Ghost Limit Cancellation:** If an active limit order has no `updated_at` timestamp by EOD (meaning the underlying asset never hit the entry limit price during market hours), the engine forcibly sets its status to `CANCELLED` (with metadata `EXPIRED_LIMIT`).
- **Eliminating Fake PnL:** Unexecuted limits are now correctly bypassed, preventing the system from calculating fake EOD PnL math or incorrectly categorizing them as active metrics in perpetuity.
