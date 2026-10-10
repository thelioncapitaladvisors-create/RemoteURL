# Platform v1.0: Option Chain Purge & Strict Live / EOD Status

**Release Date:** October 10, 2026
**Version:** v1.0.0 (Production Hardened Baseline)
**System Scope:** Next.js Mobile Application (Tv-Alert-Mobile), Netlify Background Workers (TLCS_Website_Deploy), Autonomous Algo Engine (algo_engine), Obsidian Knowledge Base.

---

## 1. Executive Summary

On October 10, 2026, Platform **Version 1.0** completed the full purge of synthetic option chain fallback calculations and instituted strict dual status (LIVE vs EOD) display on the mobile application:

1. **Purge of Synthetic / Fabricated Fallbacks**:
   - Permanently eradicated synthetic mathematical formulas (`Math.sin()`, mock IV/greeks, fabricated strike prices, artificial open interest) across both Next.js (`/api/option-chain`) and Netlify (`dhan-option-chain.js`).
   - Zero-speculation mandate: The system will NEVER generate mock option chains when markets are closed or when live feeds are unavailable.

2. **Strict Dual Status on Mobile (`LIVE` vs `EOD`)**:
   - **`LIVE`**: Displayed only when the market is actively open (NSE Mon-Fri 09:15-15:30 IST / MCX Mon-Fri 09:00-23:30 IST) AND receiving live ticks from DhanHQ (`LIVE OPTION CHAIN`, pulsing green spot LTP dot, active auto-refresh every 15 seconds).
   - **`EOD`**: Displayed when markets are closed (weekends, off-hours, holidays, or EOD snapshot). Spot LTP displays as `EOD CLOSE` with a `SETTLED` badge, calm non-pulsing status pills, and relaxed 60-second auto-refresh.
   - **Empty State Card**: When market is closed and no snapshot has been captured, renders institutional empty card `MARKET CLOSED - EOD SNAPSHOT PENDING` with zero strikes (`strikes: []`), never simulated numbers.

3. **DhanHQ TOTP Dynamic Renewal Circuit Breaker**:
   - Implemented a 10-minute renewal cooldown (`RENEWAL_COOLDOWN_MS = 600,000`) across `Tv-Alert-Mobile/src/lib/dhanAuth.ts`, `TLCS_Website_Deploy/netlify/functions/dhan-auth.js`, and `algo_engine/dhan_auth.py`.
   - Protects against Dhan rate-limiting (`DH-901` - Too many attempts) by suppressing rapid TOTP requests during client auto-refresh loops.

4. **Persistent Authentic EOD Option Chain Snapshots**:
   - Added automated EOD sweeper functions in `cron/eod-close/route.ts` and `cron-eod-close.js` to capture authentic closing option chains for `NIFTY`, `CRUDEOIL`, `NATURALGAS`, `GOLD`, and `SILVER`.
   - Snapshots are saved directly to Supabase (`system_config` table under `option_chain_eod_${symbol}` and dedicated `option_chain_eod_snapshots` table) at 03:30 PM (NSE) and 11:30 PM (MCX).

---

## 2. Technical Modifications & Files Changed

### A. Authentication & Circuit Breakers
- `Tv-Alert-Mobile/src/lib/dhanAuth.ts`: Added `lastFailedRenewalTime` and 10-minute cooldown on token generation failures.
- `TLCS_Website_Deploy/netlify/functions/dhan-auth.js`: Added 10-minute renewal circuit breaker on `fetchFreshToken()`.
- `algo_engine/dhan_auth.py`: Added `_last_failed_renewal` with 600s cooldown.

### B. Option Chain Backend APIs
- `Tv-Alert-Mobile/src/app/api/option-chain/route.ts`:
  - Added strict `getMarketStatus()` evaluating NSE (09:15-15:30 IST) and MCX (09:00-23:30 IST).
  - Purged synthetic fallback.
  - Added Supabase `system_config` EOD snapshot lookup when market is closed.
  - Automatically caches fresh authentic DhanHQ responses to `option_chain_eod_${symbol}`.
  - Returns empty strikes (`strikes: []`) with `marketStatus: EOD` when no authentic snapshot exists.
- `TLCS_Website_Deploy/netlify/functions/dhan-option-chain.js`:
  - Integrated `getMarketStatus()`, Supabase EOD snapshot lookup, and purged synthetic calculations.

### C. Mobile Terminal User Interface
- `Tv-Alert-Mobile/src/app/page.tsx` (`HubOptionChain`):
  - Derives `isMarketOpenNow()` and `isLive` dynamically from API `data.marketStatus`.
  - Header pill renders `LIVE OPTION CHAIN` vs `MARKET CLOSED - EOD`.
  - Spot LTP card renders `SPOT LTP` (with pulsing dot) vs `EOD CLOSE` (with `SETTLED` badge).
  - Table header renders `(LIVE)` vs `(EOD SNAPSHOT)`.
  - Empty state displays `MARKET CLOSED - EOD SNAPSHOT PENDING`.
  - Auto-refresh adjusts dynamically: 15s during live market hours, 60s when market is closed.

### D. Automated EOD Sweeper & Database Migration
- `Tv-Alert-Mobile/src/app/api/cron/eod-close/route.ts`: Sweeps DhanHQ option chains for NIFTY, CRUDEOIL, NATURALGAS, GOLD, SILVER into `system_config`.
- `TLCS_Website_Deploy/netlify/functions/cron-eod-close.js`: Added `sweepOptionChainEodSnapshot()`.
- `TLCS_Website_Deploy/CREATE_DHAN_TOKEN_AND_FNO_SNAPSHOTS.sql`: Added `option_chain_eod_snapshots` table definition and RLS policies.
- `AGENTS.md` and `.agents/AGENTS.md`: Documented Version 1.0 Option Chain Purge & Strict Live / EOD Status Mandate.
