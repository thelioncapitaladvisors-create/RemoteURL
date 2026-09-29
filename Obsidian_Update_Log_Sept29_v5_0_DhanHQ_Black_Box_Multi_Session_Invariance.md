# Obsidian Operational Update Log: September 29, 2026 (v5.0)
## DhanHQ Black Box Engine Multi-Session Market Hours Invariance, Serverless Background Dispatcher & UI Parity

---

### 1. Executive Summary & Milestone Context
* **Platform Baseline**: Version `v5.0` / `5.0.0`
* **Release Date**: September 29, 2026
* **Target Repositories & Subsystems**:
  - `TLCS_Website_Deploy/` (Netlify background workers, `netlify/functions/cron-dhan-scanner.js`, `netlify/functions/dhan-scanner-background.js`)
  - `Tv-Alert-Mobile/` (Next.js PWA terminal, `src/app/page.tsx`)
  - Database: Supabase PostgreSQL (`public.shadow_signals`)
  - Platform Documentation: `.agents/AGENTS.md`
* **Primary Scope**:
  1. **Serverless Background Dispatcher Connection Preservation**: Resolved Netlify scheduled cron premature exit in `cron-dhan-scanner.js` by introducing an explicit `await`ed Promise with an 8-second timeout guard and validation of HTTP 202 Accepted, preventing premature socket teardown before the background scanner could trigger.
  2. **Multi-Session Market Hours Invariance (`isDhanSignalMarketOpen`)**: Replaced blanket `nseOpen` filters with symbol-aware market hours resolution across all Dhan Black Box metric counters, active feeds, distribution cards, and card outcome mappers in `page.tsx`.
  3. **MCX Commodity Limit & Active Trade Display**: Guaranteed that MCX commodity limit orders and active trades (`CRUDEOILM`, `SILVERM`, `GOLDM`, `NATURALGAS`, `COPPER`, `ZINC`, `ALUMINIUM`, `LEAD`, `NICKEL`) stay active until 23:30 IST without premature `EOD CLOSE` or feed wipeout upon NSE cash equity close at 15:30 IST.

---

### 2. Root Cause Analysis & Technical Solutions

#### A. Backend Netlify Cron Connection Dropping
* **Problem**: In AWS Lambda / Netlify serverless runtimes, returning `200 OK` from the scheduled cron handler immediately destroys or freezes the container environment. The un-awaited `https.request` firing the background worker was terminated before the TLS handshake and payload dispatch could complete.
* **Solution**: Wrapped the HTTP POST request in a Promise, provided explicit headers (`Content-Type: application/json`, `Content-Length: 0`, `User-Agent: TLCS-Dhan-Cron/5.0`), handled timeouts cleanly, and explicitly `await`ed the HTTP 202 Accepted status before exiting the cron handler.

#### B. Frontend Blanket NSE Hours Over-Restriction
* **Problem**: In `Tv-Alert-Mobile/src/app/page.tsx`, over 10 filter ladders checked `if (!nseOpen) return false;`. At 15:30 IST, when Indian cash equities closed, this check wiped out all active MCX commodity trades, reducing active counters to 0 and marking trades as `EOD CLOSE`.
* **Solution**: Implemented `isDhanSignalMarketOpen(signal)` checking:
  - `getMarketCategory(s.symbol) === 'MCX'`
  - `s.market === 'mcx'`
  - `metadata.market_category === 'MCX'`
  - Commodity symbol root matches (`CRUDEOIL`, `GOLD`, `SILVER`, `NATURALGAS`, `COPPER`, `ZINC`, `ALUMINIUM`, `LEAD`, `NICKEL`)
  - Evaluates `isMcxMarketHours()` (09:00 to 23:30 IST) for commodities and `isNseMarketHours()` (09:15 to 15:30 IST) for cash equities.

---

### 3. Verification & Deterministic Mathematical Validation
* **Supabase Live Data**: Verified `public.shadow_signals` table contains active limit orders for `SILVERM` and `CRUDEOILM` with `status: "ACTIVE LIMIT"`, `outcome: "OPEN"`, and `exit_at: null`.
* **Simulation Testing**: Executed simulation in Node.js verifying that under the new logic, `dActiveLimitCount` evaluates to `2` and cards format as `ACTIVE LIMIT` and `LIMIT SIGNAL`.
* **TypeScript Compilation**: `tsc --noEmit -p tsconfig.json` passed with 0 errors across the entire codebase.
* **Git Release Tags**: Released and pushed `v5.0` and `v5.0.0` across both `TLCS_Website_Deploy` and `Tv-Alert-Mobile`.
