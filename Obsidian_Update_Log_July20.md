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

### 4. VAPT Security Hardening & Data Quality Sanity
- **Razorpay Timing Attack Mitigation:** Replaced standard `!==` string comparison in web and mobile payment webhooks with `crypto.timingSafeEqual()` to protect against signature forgery side-channel timing attacks.
- **Razorpay Signature Bypass Fix:** Made webhook signature verification mandatory in the mobile API webhook. The handler now aggressively rejects any request lacking the validation signature.
- **Arbitrary Table Deletion Whitelist:** Hardened `admin-delete-item.js` by introducing a strict whitelist of allowed tables (`signals`, `pivots`, `blogs`, `nuggets`, `feedbacks`). Attempting to delete from any other table returns a `403 Forbidden` response.
- **fix-db Authentication Guard:** Added token validation checking against the `WEBHOOK_SECRET` security key to the `fix-db` route, and switched from the public anon client to `supabaseAdmin` for database writes.
- **Removed Exposed Debug/Dev Tools:** Permanently deleted unauthenticated legacy scripts from `netlify/functions` (`purge_db.js`, `test_db_insert.js`, and `webhook.js.bak`) to prevent exposure of database credentials or unintended data purges.
- **Content Security Policy & HSTS Enforcement:** Hardened HTTP headers in both web (`_headers`) and mobile (`next.config.js`) by upgrading Strict-Transport-Security to `max-age=63072000` (2 years) with `preload`, setting `X-Frame-Options` to `DENY` on mobile, and removing `'unsafe-eval'` from script sources.
- **Rate Limit Reduction:** Lowered the mobile webhook rate limit to a secure threshold of 60 requests per minute per IP to defend against Denial of Service (DoS) and brute-force attempts.
- **XSS Prevention:** Sanitized user-inputted `displayName` in `auth.js` before inserting into the dynamic navigation template using an HTML entity escape routine.
- **Data Quality Alignment:** Standardized `resolveOutcome` across `scanner.js` and `commodity-scanner.js` to catch unexecuted cancellations correctly. Removed the redundant `resolveOutcome` cancel-dead-code block on mobile `page.tsx` that interfered with EOD/EMA outcome math, and added `isNaN` guards for all timestamp conversions to prevent runtime execution halts.

