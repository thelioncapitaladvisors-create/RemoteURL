# Platform v1.0: F&O Stock Buildups Zero-Fabrication Purge & Institutional Monetization Standard

**Release Date:** October 10, 2026
**Version:** v1.0.0 (Production Hardened Baseline)
**System Scope:** Next.js Mobile Application (Tv-Alert-Mobile), Netlify Background Functions (TLCS_Website_Deploy), Supabase Database (fno_eod_snapshots), Obsidian Knowledge Base.

---

## 1. Executive Summary

As the platform prepares for commercial monetization and regulatory compliance, a zero-tolerance policy against fabricated or simulated trading metrics has been enforced across the entire architecture.

Prior implementations of the F&O Stock Buildups engine (`/api/fno-buildups` and `dhan-fno-buildups.js`) contained legacy mathematical fallback formulas (`mod = idx % 4`, synthetic percentage adjustments, hardcoded volume/OI shifts) that fabricated stock data when markets were closed or when the DhanHQ live feed was offline.

This update permanently purges all synthetic and fictitious values from F&O stock buildups, standardizing them to the exact institutional **`LIVE` vs `EOD`** dual-status paradigm established for the Option Chain.

---

## 2. Problem Addressed & Root Cause Analysis

1. **The Fictitious Modulo-4 Simulation**:
   - In `Tv-Alert-Mobile/src/app/api/fno-buildups/route.ts` (lines 186–205) and `TLCS_Website_Deploy/netlify/functions/dhan-fno-buildups.js` (lines 118–143), when live quotes were unavailable or markets were closed without an active snapshot, the engine looped through stocks using:
     ```typescript
     const mod = idx % 4;
     if (mod === 0) {
       changePct = +(1.15 + ((idx % 5) * 0.38)).toFixed(2);
       oiChange = Math.round(oi * (+0.042 + ((idx % 4) * 0.012)));
     } // ...
     ```
   - This fabricated false prices (e.g. RELIANCE LTP ₹2,948.5, INFY LTP ₹1,932.1) and fabricated 50% Bullish Neutral Breadth on weekends, completely contradicting actual exchange data.

2. **Monetization & Regulatory Standard**:
   - For a professional, monetized institutional terminal, presenting simulated stock prices or fabricated open interest changes is unacceptable.
   - If genuine exchange data is not available, the platform must display a clean institutional empty state (`MARKET CLOSED • EOD SNAPSHOT PENDING`) with zero stocks rather than misleading users.

---

## 3. Remediation & Implementation Details

### A. Total Purge of Synthetic Math in Next.js API Route
- **File**: `Tv-Alert-Mobile/src/app/api/fno-buildups/route.ts`
- **Actions**:
  - Permanently eradicated lines 186–205 (`idx % 4` math) and lines 291–385 (hardcoded fallback stocks).
  - During market hours (NSE Mon–Fri 09:15–15:30 IST): Only processes authentic quotes received from DhanHQ.
  - During off-hours: Strictly queries authentic snapshots from Supabase table `fno_eod_snapshots`.
  - Zero-Speculation Fallback: If no authentic data or snapshot exists, returns `categories: { LONG_BUILDUP: [], SHORT_BUILDUP: [], LONG_UNWINDING: [], SHORT_UNWINDING: [] }` and `snapshotType: "NONE"`.

### B. Total Purge of Synthetic Math in Netlify Serverless Function
- **File**: `TLCS_Website_Deploy/netlify/functions/dhan-fno-buildups.js`
- **Actions**:
  - Removed all `mod = idx % 4` calculations.
  - Queries DhanHQ `/v2/marketfeed/quote` during live market hours.
  - Serves genuine `fno_eod_snapshots` during closed market hours.
  - Returns empty zero-data payload on off-hours cache misses.

### C. Mobile Terminal User Interface Harmonization
- **File**: `Tv-Alert-Mobile/src/app/page.tsx` (`HubFnoBuildups`)
- **Actions**:
  - Status pill matches Option Chain: `🟣 LIVE F&O • [Time]` when market is open and active, vs `MARKET CLOSED • EOD SNAPSHOT [Time]` when closed.
  - Replaced generic fallback message with institutional empty state card:
    `🌙 MARKET CLOSED • EOD SNAPSHOT PENDING`
    "Live trading is offline outside market hours. Authentic session closing buildups will synchronize at session close."
  - When no stocks exist in category, renders clean empty state rather than fabricated stock cards.

---

## 4. Institutional Mandate Recorded

Added **Version 1.0 F&O Stock Buildups Purge & Zero-Fabrication Mandate (Effective October 10, 2026)** to `AGENTS.md` and `.agents/AGENTS.md`.
