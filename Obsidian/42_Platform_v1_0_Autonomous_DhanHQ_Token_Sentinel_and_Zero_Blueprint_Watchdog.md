# Platform V1.0: Autonomous DhanHQ Token Sentinel & Zero-Blueprint Watchdog Architecture

**Document Version:** 1.0  
**Effective Date:** October 15, 2026 (22:25 IST)  
**Status:** COMPLETE PRODUCTION ARCHITECTURE & REPOSITORY ANCHOR  
**Infrastructure & Environment:** Next.js 14 Mobile Terminal (`Tv-Alert-Mobile`), Netlify Background Serverless Functions (`cron-keep-alive.js`, `dhan-scanner-background.js`, `dhan-option-chain.js`), Supabase Real-Time Engine (`dwepduvhzuhzeehbeaaz`), macOS `launchd` Daemon (`com.tlcs.nse100scanner`), GitHub Actions Workflow (`supabase_keep_alive.yml`)  
**Architect:** *Vishant Vyankat Meshram, CFTe, CMT L3 Dec 2024*  

---

## 1. Executive Summary & Root Cause Resolution

Following production telemetry anomalies observed on October 15, 2026—namely non-canonical Day Type Blueprint alerts appearing on the terminal feed and an erroneous "MARKET CLOSED • EOD" display on MCX commodities during active trading hours—an exhaustive institutional audit was conducted. Two critical architectural root causes were identified and eliminated through autonomous, self-healing sentinel automation requiring zero human reminders:

1. **Stale Daemon Directory Separation & Rogue Blueprint Elimination**:
   - *Root Cause*: The macOS `launchd` persistent background daemon (`com.tlcs.nse100scanner`) was executing from `/Users/vishant/Project` (configured during initial setup to bypass macOS TCC security constraints on `~/Documents`). When the codebase in `/Users/vishant/Documents/Project` was hardened on October 13 (removing blueprint signal loops), the running background daemon process (PID 872) continued executing the pre-October 13 unhardened code, emitting `BUY REJECTION DAY BLUEPRINT (BULLISH)` and `BUY FAILED NEW HIGH/LOW BLUEPRINT (BULLISH)` trades every 15 minutes.
   - *Resolution*:
     - Purged all 15 non-canonical blueprint rows from Supabase `shadow_signals`.
     - Synchronized the complete hardened `algo_engine` codebase into the daemon runtime directory (`/Users/vishant/Project/algo_engine`).
     - Installed a multi-layer **Autonomous Rogue Signal Watchdog** in `algo_engine/shadow_pipeline.py` (`_execute_insert()` hard filter and `purge_non_canonical_signals()`), `run_nse100_scanner.py` (cycle cleaner), and Netlify `dhan-scanner-background.js` / `cron-keep-alive.js` (autonomous 6-hour sweeper).
     - Created PostgreSQL trigger specification (`algo_engine/sql/block_non_canonical_triggers.sql`) rejecting non-canonical inserts at the database level.
     - Reloaded `launchd` daemon (`com.tlcs.nse100scanner`, PID 3539), actively executing clean cycles with 0 blueprint emissions.

2. **Autonomous DhanHQ Token Sentinel & Option Chain Real-Time Resilience**:
   - *Root Cause*: When the 24-hour DhanHQ access token expired, outbound requests from `/api/option-chain` failed. In [`api/option-chain/route.ts`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/api/option-chain/route.ts), the fallback handler hardcoded `isMarketOpen: false` and `marketStatus: 'EOD'`, overriding the actual exchange trading hours (MCX 09:00 to 23:30 IST) and misleading the client UI into displaying "MARKET CLOSED • EOD SNAPSHOT PENDING" with 0 strikes.
   - *Resolution*:
     - Proactive Token Keep-Alive: Integrated autonomous pre-warming into `TLCS_Website_Deploy/netlify/functions/cron-keep-alive.js` and GitHub Actions (`.github/workflows/supabase_keep_alive.yml`), renewing tokens automatically via RFC 6238 TOTP HMAC-SHA1 before expiration.
     - Accurate Market Status Fallback: Corrected `route.ts` and `dhan-option-chain.js` so `cleanFallbackPayload` strictly preserves the true calculated exchange status (`isMarketOpen`, `marketStatus`), never falsely declaring an open exchange closed.
     - Resilient Snapshot Fallback: Integrated fallback to persisted authentic Supabase snapshots (`system_config` table `option_chain_eod_${symbol}`) if DhanHQ API exhibits momentary network latency, guaranteeing strikes are never blanked out during open market sessions.
     - Extended Timeouts: Relaxed aggressive 2000ms timeouts to 4500ms/5000ms with per-candidate exception isolation.

---

## 2. Architectural Blueprint & Self-Healing Pipeline

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               TLCS AUTONOMOUS KEEP-ALIVE & WATCHDOG ARCHITECTURE                       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [GitHub Actions Keep-Alive] (Every 6h) ───► Ping Supabase & Netlify Keep-Alive        │
│                                                     │                                  │
│                                                     ▼                                  │
│                                      [Netlify cron-keep-alive.js]                      │
│                                                     │                                  │
│                       ┌─────────────────────────────┼────────────────────────────┐     │
│                       ▼                             ▼                            ▼     │
│             [Dhan Token Sentinel]         [Rogue Signal Watchdog]    [Option Chain Prewarm]
│             Auto-renews 24h JWT           Purges %BLUEPRINT% &       Refreshes NIFTY,      │
│             via dynamic TOTP              %SEQUENCE% from DB         CRUDE, NG, GOLD, SI   │
│             into Supabase Cache           (Zero Human Reminders)     into system_config    │
│                                                                                        │
│  [Local launchd Daemon (com.tlcs.nse100scanner)] ──► Scans 113 Assets Every 15 Mins   │
│                       │                                                                │
│                       ▼                                                                │
│             [ShadowPipeline Hard Gate]                                                 │
│             Strictly 12 Canonical Strategy Triggers Only                               │
│             Auto-rejects any non-canonical trigger ab-initio                           │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Code Modifications & Production Verification

| Repository | Component | Changes Made |
| :--- | :--- | :--- |
| **`algo_engine`** | `shadow_pipeline.py` | Added hard canonical trigger gate in `_execute_insert()`, added `purge_non_canonical_signals()`. |
| **`algo_engine`** | `run_nse100_scanner.py` | Added automatic post-cycle watchdog sweep to clean any stray non-canonical rows. |
| **`algo_engine`** | `supervisor/` | Updated `com.tlcs.nse100scanner.plist`, `run_scanner_daemon.sh`, and `install_macos_service.sh`; reloaded launchd daemon (PID 3539). |
| **`algo_engine`** | `sql/block_non_canonical_triggers.sql` | [NEW] PostgreSQL trigger to block non-canonical trigger inserts at database level. |
| **`Tv-Alert-Mobile`** | `src/app/api/option-chain/route.ts` | Corrected `cleanFallbackPayload` to preserve `isMarketOpen` / `marketStatus`, increased timeouts to 4500ms/5000ms, added snapshot fallback. |
| **`TLCS_Website_Deploy`** | `netlify/functions/dhan-scanner-background.js` | Added canonical trigger gate and autonomous watchdog sweep. |
| **`TLCS_Website_Deploy`** | `netlify/functions/dhan-option-chain.js` | Fixed `cleanPayload` to preserve true `isMarketOpen` and `marketStatus`. |
| **`TLCS_Website_Deploy`** | `netlify/functions/cron-keep-alive.js` | Added autonomous rogue signal purge and option chain pre-warm for all 5 assets. |
| **Root Repository** | `.github/workflows/supabase_keep_alive.yml` | Added Netlify Sentinel ping step; verified 100% valid YAML with `yaml.safe_load`. |

---

## 4. Verification & Validation Metrics

1. **Supabase Database Clean State**:
   - Purged all 15 rogue blueprint rows (`BUY REJECTION DAY BLUEPRINT (BULLISH)`, `BUY FAILED NEW HIGH/LOW BLUEPRINT (BULLISH)`, `BUY REJECTION DAY SEQUENCE`, etc.).
   - Verified 0 non-canonical rows in `shadow_signals` and `signals`.
2. **Daemon Verification**:
   - Terminated stale daemon PID 872.
   - Started new persistent daemon PID 3539 via launchd. Verified clean execution of 15-minute scan across 13 commodity symbols with 0 blueprint emissions.
3. **Live Option Chain Telemetry**:
   - Authenticated against live DhanHQ feed across all 4 commodities:
     - `CRUDE OIL`: Spot ₹9,037, PCR 1.12, Max Pain 9,000, 207 strikes (`dhan_live`).
     - `NATURAL GAS`: Spot ₹303.9, PCR 0.89, Max Pain 305, 90 strikes (`dhan_live`).
     - `GOLD`: Spot ₹1,45,511, PCR 0.80, Max Pain 1,50,000, 181 strikes (`dhan_live`).
     - `SILVER`: Spot ₹2,08,424, PCR 0.53, Max Pain 2,20,000, 188 strikes (`dhan_live`).
4. **TypeScript & Python Suite**:
   - `npx tsc --noEmit` exited code 0 with 0 errors.
   - `python3 -m unittest algo_engine/tests/test_phase3.py` passed 9/9 tests in 0.48s.
   - `yaml.safe_load` on `.github/workflows/supabase_keep_alive.yml` exited code 0.
