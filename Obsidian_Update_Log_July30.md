# TLCS Update Log: July 30, 2026

## 1. Supabase CDN Independence & SSO Interception Fix
- **The Issue**: Users were reporting that "None of the login options working on the landing and other pages." This was primarily caused by the `supabase-js-v2` library being loaded via `cdn.jsdelivr.net`. On certain browsers (like Brave with strict shields) or restrictive network firewalls, this CDN request was blocked. 
- **The Consequence**: When the script failed to load, `window.supabase` was left undefined, causing silent JavaScript failures that prevented the `bootAuth()` initialization from finishing. This broke the SSO interceptor for the "Launch App" button and prevented the UI from updating the static "Login" links.
- **The Fix**: Downloaded and permanently vendored the `supabase-js-v2.min.js` file locally within the `TLCS_Website_Deploy` folder. All 11 HTML pages across the website have been updated to point to this local script, fully immunizing the platform against CDN adblocker and firewall restrictions.

## 2. Bulletproof DOMContentLoaded Timing Constraints
- **The Issue**: In both `auth.js` and `main.js`, initialization functions (`bootAuth` and `initMain`) were bound strictly using `document.addEventListener('DOMContentLoaded', ...)`. 
- **The Consequence**: Because these scripts were included at the bottom of the `<body>` tag synchronously, standard browser HTML parsing behavior occasionally meant that the `DOMContentLoaded` event fired *before* the script even executed its event listener. This resulted in the auth loops and mobile navigation logic never initializing.
- **The Fix**: Wrapped all initialization bindings with a robust `document.readyState` fallback. 
  ```javascript
  if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initFn);
  } else {
      initFn();
  }
  ```
  This ensures the initialization functions always run, regardless of asynchronous delays, network conditions, or early HTML parsing completions.

## 3. Automated NYMEX to MCX Live Trading Integration (Dhan)
- **The Feature**: The user requested that NYMEX active limit alerts (`CL`, `NG`, `GC`, `SI`) automatically execute as live trades on Dhan for MCX options (`CRUDEOIL`, `NATURALGAS`, `GOLD`, `SILVER`) without manual intervention.
- **The Execution**: Modified `dhan-engine.js` to automatically intercept incoming NYMEX symbols and gracefully map them to MCX counterparts.
- **The Constraint**: Implemented a robust `isMCXSessionActive()` time-guard (9:00 AM to 11:30 PM IST, Mon-Fri) that ensures NYMEX alerts fired during MCX downtime (e.g. 2:00 AM IST) are intelligently ignored by the Dhan execution engine to prevent order rejections.
- **The Spot Resolution (Option B)**: To accurately calculate the At-The-Money (ATM) Option strike for MCX, the engine directly queries the live Dhan Marketfeed API (`/marketfeed/ltp`) for the active MCX Futures contract at the exact moment the NYMEX alert fires. This perfectly synchronizes the MCX strike price with the live INR spot price, bypassing discrepancies between USD/INR conversions.
- **Mathematical Fallback**: If the Dhan API is slow or unavailable, the engine gracefully falls back to a mathematical conversion, dynamically translating the NYMEX Entry price (in USD) to MCX Spot (in INR) using fixed multipliers (e.g. $83.5 for USD/INR exchange rate, adjusting for Troy Ounce/Gram conversions).

## 4. Live Trades vs Active Limits (Mobile/Web Bug Fix)
- **The Issue**: Live Market Executions trigger initial webhooks with `status: "TRADE ACTIVE"`. Because these are the *first* inserts into the database, they lack an `updated_at` timestamp. The frontend previously bucketed any open trade lacking an `updated_at` as an unexecuted limit order, causing live market executions to mistakenly render as `ACTIVE LIMITS` and completely disappear from the `LIVE` filter view.
- **The Fix**: Rewrote the parser logic in both the mobile app (`page.tsx`) and the web dashboard (`trade-metrics.js`). The engine now safely overrides the missing timestamp and forcefully categorizes any trade containing `ACTIVE` in its string as a valid `LIVE TRADE`, completely restoring the live data feeds.
