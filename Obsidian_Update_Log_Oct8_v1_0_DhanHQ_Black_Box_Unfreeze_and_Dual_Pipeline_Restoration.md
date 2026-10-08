# Platform v1.0: DhanHQ Black Box Engine Unfreeze, macOS Daemon Sandbox Remediation & Dual-Pipeline Synchronization

**Release Date:** October 8, 2026  
**Version:** `v1.0.1` (Production Autonomous Hardening)  
**System Scope:** Local Quant Engine (`algo_engine`), macOS LaunchAgent (`com.tlcs.nse100scanner.plist`), Next.js Mobile Application (`Tv-Alert-Mobile`), Netlify Background Workers (`TLCS_Website_Deploy`), Supabase Pipeline (`signals` & `shadow_signals`).

---

## 1. Executive Summary & Root Cause Analysis (RCA)

Following the application freeze on October 7, 2026, an exhaustive diagnostic investigation was conducted to determine why live DhanHQ Black Box trade signals were not received on October 8, 2026:

### A. Root Causes Identified:
1. **macOS TCC Sandbox Blockade on Daemon Service**:
   - The LaunchAgent plist was originally mapped to `/Users/vishant/Documents/Project/algo_engine/run_nse100_scanner.py`.
   - On macOS, `launchd` background services lack TCC permissions to access protected directories like `~/Documents`, causing immediate failures with `[Errno 1] Operation not permitted`.
   - The daemon was repeatedly killed and could not run during today's market hours.
2. **Missing `SHADOW_DUAL_WRITE` Synchronization**:
   - In `algo_engine/.env`, `SHADOW_DUAL_WRITE=false` was configured.
   - The DhanHQ quant scanner was writing exclusively to `public.shadow_signals` and never replicating trades into `public.signals`.
   - The standard mobile app, website overview, and order executors listen to `public.signals`. Consequently, even when signals were generated, they were invisible on default views.
3. **Restricted Client Source Gating**:
   - `Tv-Alert-Mobile/src/app/page.tsx` contained an artificial authorization check that forced non-admin users to `'TV'` (TradingView webhook feed), blocking access to `'SHADOW'` (DhanHQ Black Box).
   - In `dashboard.html`, clicking the Black Box source was blocked for non-admin sessions and preference was not persisted in `localStorage`.
4. **Netlify Rate Limit Retries & Dual-Write Decoupling**:
   - In `dhan-scanner-background.js`, rate limiting (429) was not retrying with exponential backoff and dual-write to `signals` was absent.

---

## 2. Comprehensive Remediation Actions Taken

### 1. Relocated Daemon & Activated macOS LaunchAgent Service
- Synchronized `algo_engine` into the root workspace `/Users/vishant/Project/algo_engine/`, which operates outside the macOS TCC sandboxed directories.
- Updated `supervisor/run_scanner_daemon.sh` and `supervisor/com.tlcs.nse100scanner.plist` with explicit environment variables (`PYTHONPATH`, `PYTHONUNBUFFERED`, `PATH`).
- Installed and loaded `~/Library/LaunchAgents/com.tlcs.nse100scanner.plist` into `launchctl` (`PID 35897`).
- **Live Verification**: The daemon executed a live scan cycle, detected MCX trade signals, authenticated via live TOTP, and successfully synced to Supabase with zero permission errors.

### 2. Enabled Dual-Write Pipeline Across All Engines
- Set `SHADOW_DUAL_WRITE=true` in `algo_engine/.env`.
- Added a 30-minute deduplication guard in `algo_engine/shadow_pipeline.py` to prevent duplicate signals across consecutive 15-minute intervals.
- Integrated `dualUpdateTrade` and `dualDeleteTrade` helpers in `TLCS_Website_Deploy/netlify/functions/dhan-scanner-background.js` so all lifecycle updates (TradeFill, TP1-TP4 progression, EOD exits, cancellations) sync simultaneously to both `public.shadow_signals` and `public.signals`.

### 3. Unfroze Mobile & Dashboard Black Box Selectors
- **`Tv-Alert-Mobile` (`src/app/page.tsx`)**:
  - Initialized `engineSource` to default to `'SHADOW'` (Black Box engine).
  - Persisted user engine preference in `localStorage` (`tlcs_engine_source`).
  - Removed restrictive admin lock that previously reverted user sessions back to TradingView.
- **`TLCS_Website_Deploy` (`dashboard.html`)**:
  - Defaulted to `'SHADOW'` with `localStorage` persistence (`tlcs_dashboard_engine`).
  - Removed admin barrier so any user can monitor live DhanHQ Black Box feeds.

### 4. Continuous Operational Guarantees for Tomorrow Onwards
- **Dual-Market Schedule**:
  - **NSE Equities (Top 100)**: Autonomous scanning activates from 09:15 to 15:30 IST (Entry cutoff at 14:00 IST, EOD sweep at 15:30 IST).
  - **MCX Commodities**: Autonomous scanning active from 09:00 to 23:30 IST (Entry cutoff at 22:00 IST, EOD sweep at 23:30 IST).
- **Dual-Redundancy**:
  - **Primary**: Local macOS background service (`com.tlcs.nse100scanner`) running 24/7.
  - **Secondary**: Netlify scheduled cron (`cron-dhan-scanner.js`) running in cloud infrastructure.
