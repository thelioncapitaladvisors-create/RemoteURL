# Platform v2.0: DhanHQ Autonomous Token Auto-Renewal, VCPR Self-Healing Gating & Daemon Path Alignment
**Date**: November 3, 2026 (11:58 IST)  
**Release Tag**: `v2.0`  
**Components**: `Tv-Alert-Mobile` (Next.js PWA), `TLCS_Website_Deploy` (Netlify Functions), `algo_engine` (Python BlackBox), `.github/workflows/supabase_keep_alive.yml`  
**Status**: 100% Production Ready & Verified Live  

---

## 1. Summary of Changes

### A. Proactive Verification & Token Health Probing
1. **DhanHQ Profile Probe**: Added `verifyDhanToken(token)` across TypeScript (`Tv-Alert-Mobile/src/lib/dhanAuth.ts`), JavaScript (`TLCS_Website_Deploy/netlify/functions/dhan-auth.js`), and Python (`algo_engine/dhan_auth.py`), actively testing `GET https://api.dhan.co/v2/profile` with `client-id: DHAN_CLIENT_ID`.
2. **Invalid Token Auto-Purge (`invalidateDhanToken`)**: If DhanHQ returns `DH-906: Invalid Token` or `DH-901: Expired/Invalid`, the dead token is immediately cleared from in-memory and Supabase caches (`dhan_token` and `system_config.dhan_access_token`) so stale credentials are never re-served.
3. **DhanHQ Rate-Limit Protection**: Enforced a 2.5-minute cooldown guard matching Dhan's server-side "Token can be generated once every 2 minutes" policy.

### B. Autonomous Token Renewal Cron Route & 24/7 Keep-Alive Sentinel
1. **Dedicated Token Renewal Endpoint**: Created `Tv-Alert-Mobile/src/app/api/cron/renew-dhan-token/route.ts` which probes current token authorization and automatically mints a fresh 24h token via dynamic TOTP HMAC-SHA1 whenever expired or invalidated.
2. **Pre-Market 08:30 IST Automation**: Updated `.github/workflows/supabase_keep_alive.yml` with:
   - Daily 6-hour interval (`0 */6 * * *`).
   - Dedicated pre-market scheduled trigger at `03:00 UTC` (08:30 IST, Monday-Friday), ensuring a freshly minted, verified token is active before Indian market pre-open (09:00 IST).
   - Automated health verification and VCPR screener pre-warming step.

### C. Self-Healing Autonomous VCPR Screener (`/api/vcpr/route.ts`)
1. **Automatic Single-Retry on 401/400**: If `fetch('https://api.dhan.co/v2/charts/historical')` returns an authentication error (`DH-901` or `DH-906`), the endpoint force-refreshes the token once (`getValidDhanToken(true)`) and retries historical bar fetching before ever falling back.
2. **Benchmark NIFTY 50 Inclusion**: Added `NIFTY 50` (`secId: '13'`, `exch: 'IDX_I'`, `inst: 'INDEX'`, `basePrice: 24000.0`) to `VCPR_UNIVERSE`.
3. **Active Front-Month Scrip Pinning**: Updated `NATURALGAS` security ID to active November 2026 contract `574319` across `route.ts` and `algo_engine/feeds/dhan_feed.py`.
4. **Live Verification**: Re-scanned all 21 universe assets, verifying authentic DhanHQ market data (e.g., NIFTY at 23,440.8, TCS at 2,501.7, Natural Gas at 277.1 INR) with zero synthetic fallbacks.

### D. Local macOS Daemon Path Alignment
1. **TCC Sandbox Permission Resolution**: Corrected macOS `launchd` supervisor plist and runner script to run from `/Users/vishant/Project/algo_engine/`, bypassing macOS `~/Documents` sandboxing permission denials (`Operation not permitted`).
2. **Live Daemon Re-Activation**: Reloaded `com.tlcs.nse100scanner` with verified live streaming across 113 NSE & MCX symbols.

---

## 2. Verification Checklist
- [x] Dhan token generated via dynamic TOTP and verified against `GET /v2/profile` (HTTP 200).
- [x] Stored token in Supabase `dhan_token` and `system_config` valid until November 4, 2026.
- [x] Live historical daily candles for Reliance, Natural Gas (`574319`), and NIFTY (`13`) fetched successfully.
- [x] Supabase `vcpr_autonomous_snapshot` populated with 100% genuine live market quotes.
- [x] Next.js production build (`npm run build`) succeeded with 0 errors.
- [x] Launchd supervisor service verified scanning live without permission errors.
