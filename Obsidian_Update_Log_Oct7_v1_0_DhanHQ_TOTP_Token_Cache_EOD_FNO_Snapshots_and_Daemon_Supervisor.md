# Platform v1.0: DhanHQ TOTP Token Cache, Persistent EOD F&O Snapshots & Daemon Supervisor

**Release Date:** October 7, 2026  
**Version:** `v1.0.0` (Production Hardened Baseline)  
**System Scope:** Next.js Mobile Application (`Tv-Alert-Mobile`), Netlify Background Workers (`TLCS_Website_Deploy`), Autonomous Algo Engine (`algo_engine`), Production Mirrors (`RemoteURL`, `Backups`).

---

## 1. Executive Summary

On October 7, 2026, Platform **Version 1.0** implemented a comprehensive 6-part remediation addressing token rate-limiting, off-hours F&O data fidelity, active commodity contracts, and process persistence:

1. **DhanHQ TOTP Credentials Configuration**:
   - Added `DHAN_PIN=871346` and `DHAN_TOTP_SECRET=N5ZUIALJCBGJ63YS2DUB3BLW7EEPBJU2` to `Tv-Alert-Mobile/.env.local`.
   - Harmonized `TLCS_Website_Deploy/.env.local` for local and staging diagnostic execution.
   - Enables programmatic 24-hour access token generation via RFC 6238 HMAC-SHA1.

2. **DhanHQ Shared Token Cache in Supabase (Eliminates `DH-901` Rate Limiter)**:
   - Built `dhan_token` and `system_config` tables on Supabase via direct PostgreSQL connection (port 6543) with Row Level Security (RLS) policies.
   - Established unified `getValidDhanToken` across all three application runtimes: Next.js (`src/lib/dhanAuth.ts`), Netlify (`netlify/functions/dhan-auth.js`), and Python (`algo_engine/dhan_auth.py`).
   - Every execution environment checks the database cache before making outbound requests, permanently preventing "Too many attempts" rate limiting.

3. **Persisted 03:30 PM EOD F&O Snapshots (Modulo-4 Synthetic Formula Eliminated)**:
   - Added `sweepFnoEodSnapshot()` to `cron-eod-close.js` and `cron/eod-close/route.ts` to capture real closing prices, volume, and OI for all 20 F&O universe stocks from DhanHQ at session close (15:30 IST) and persist the snapshot to `fno_eod_snapshots`.
   - Updated `/api/fno-buildups` and `dhan-fno-buildups.js` to serve this authentic EOD data during off-hours with `snapshotType: 'EOD_SNAPSHOT'` and `source: 'dhan_eod_snapshot'`.
   - The synthetic modulo-4 calculation is permanently eliminated when users view the terminal at night.

4. **Refreshed Active MCX Contract Security IDs**:
   - Verified against DhanHQ live scrip master CSV (`api-scrip-master.csv`) and updated active nearest contracts in `dhan-scanner-symbols.json`:
     - `GOLD`: `483079` → **`495213`** (Dec 2026 contract)
     - `GOLDM`: `569003` → **`571445`** (Nov 2026 contract)
     - `ALUMINI`: `571296` → **`574827`** (Oct 2026 contract)

5. **Python Daemon Supervisor Configured**:
   - Configured macOS `launchd` plist `algo_engine/supervisor/com.tlcs.nse100scanner.plist` with automated installer `install_macos_service.sh` for keep-alive background execution.
   - Added PM2 ecosystem config (`ecosystem.config.js`) and Linux systemd service (`tlcs-scanner.service`) for cloud VPS deployments.
   - Validated clean execution of `run_nse100_scanner.py --interval 900`.

---

## 2. Technical Modifications & Files Changed

### A. Environment Configuration
- `Tv-Alert-Mobile/.env.local`: Added `DHAN_PIN` and `DHAN_TOTP_SECRET`.
- `TLCS_Website_Deploy/.env.local`: Created matching environment configuration.

### B. Database Schema Migration
- `TLCS_Website_Deploy/CREATE_DHAN_TOKEN_AND_FNO_SNAPSHOTS.sql`: SQL migration creating `dhan_token`, `system_config`, and `fno_eod_snapshots` tables with RLS and PostgREST schema reload.

### C. Token Caching Engine
- `Tv-Alert-Mobile/src/lib/dhanAuth.ts`: Created shared token authentication service with Supabase persistence.
- `Tv-Alert-Mobile/src/app/api/fno-buildups/route.ts`: Integrated shared `dhanAuth` and off-hours EOD snapshot serving.
- `Tv-Alert-Mobile/src/app/api/option-chain/route.ts`: Integrated shared `dhanAuth`.
- `TLCS_Website_Deploy/netlify/functions/dhan-auth.js`: Added Supabase read/write token caching.
- `algo_engine/dhan_auth.py`: Added Supabase read/write token synchronization.

### D. EOD F&O Sweeper & Nighttime Serving
- `TLCS_Website_Deploy/netlify/functions/cron-eod-close.js`: Added `sweepFnoEodSnapshot()`.
- `TLCS_Website_Deploy/netlify/functions/dhan-fno-buildups.js`: Added EOD snapshot lookup.
- `Tv-Alert-Mobile/src/app/api/cron/eod-close/route.ts`: Added matching `sweepFnoEodSnapshot()`.

### E. MCX Contract Security IDs
- `TLCS_Website_Deploy/netlify/functions/dhan-scanner-symbols.json`: Updated `GOLD`, `GOLDM`, and `ALUMINI`.
- `Project Backup/TLCS_Website_Deploy/netlify/functions/dhan-scanner-symbols.json`: Updated matching symbols.

### F. Daemon Supervisor
- `algo_engine/supervisor/com.tlcs.nse100scanner.plist`: macOS launchd plist.
- `algo_engine/supervisor/install_macos_service.sh`: Automated installer.
- `algo_engine/supervisor/ecosystem.config.js`: PM2 config.
- `algo_engine/supervisor/tlcs-scanner.service`: systemd service.
