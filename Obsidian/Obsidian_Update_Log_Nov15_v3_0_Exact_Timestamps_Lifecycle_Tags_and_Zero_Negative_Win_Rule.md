# Obsidian Update Log: Version 3.0 Platform Architecture Release
**Date:** November 15, 2026  
**Designation:** Version 3.0 (`v3.0`)  
**Scope:** `Tv-Alert-Mobile` (Next.js 14) & System Documentation  

---

## 1. Executive Summary
On November 15, 2026, three major enhancements and bug fixes were committed and deployed to Version 3.0 of the TLCS Mobile Terminal:
1. **Trade Signal Exact Chart Candle Timestamps**: Integrated multi-zone formatted timestamps (`timeIST`, `dateIST`, `fullTimeIST`, `timeUTC`) across table row headers, metadata sub-rows, and modal inspection popovers.
2. **Trade Lifecycle Flashy Badges & Duration Spent**: Real-time trade state pills (`⏳ ACTIVE LIMIT` pulsing amber with ping dot, `⚡ LIVE` pulsing emerald with ping dot, and `🔒 CLOSED` outcome-coded with WIN/LOSS tags) and hold duration computation (`timeSpentStr`).
3. **Strict Outcome-Consistent Move & Return (%) Mandate (Zero Negative Win Rule)**: Fixed critical sign inversion bug where short winning trades (e.g., `BTCUSDT [CRYPTO] • WIN`) rendered as `-1.20%` in red instead of `+1.20%` in emerald green.

---

## 2. Technical Details & Root Cause Analysis

### A. Root Cause Analysis: Short Trade Return Sign Inversion
In `extractDhanScreenerAssets`:
- Raw price delta `dayMovePts = exitP - entryP` was previously computed without taking trade direction (`isShort`) into account. For short trades, when the asset price dropped (a winning trade), `exitP < entryP`, resulting in a negative points delta and negative percentage.
- Metadata `meta.exact_pct` fallback explicitly negated short trade returns (`dayMovePct = isShortTrade ? -trPct : trPct;`).
- General fallback forced all bearish trades to be negative (`dayMovePct = direction === 'BULLISH' ? Math.abs(exactPctVal) : -Math.abs(exactPctVal);`).
- Consequently, `BTCUSDT • WIN` was paired with `-1.20%` in a rose/red badge.

### B. The Dual-Layer Fix
1. **Engine Layer (`extractDhanScreenerAssets`)**:
   - Wired `getExactPct(s)` and `canonicalOutcome` directly to `dayMovePct`.
   - Short trade returns calculated as `(entryP - exitP) / entryP * 100`.
   - Enforced mathematical invariant:
     - If `outcome === 'WIN'`, `dayMovePct = Math.abs(dayMovePct)`.
     - If `outcome === 'LOSS'`, `dayMovePct = -Math.abs(dayMovePct)`.
2. **UI Layer (`page.tsx`)**:
   - In both `Col 3: Move (%)` and the asset inspection modal popover, wrapped percentage display in defensive clamp: any winning trade is structurally prevented from rendering with a minus sign or rose styling, and strictly renders `+X.XX%` in emerald green (`bg-emerald-500/15 text-emerald-800 border-emerald-500/35`).

### C. Flashy Trade Lifecycle Tags
Integrated dynamic status pills:
- `⏳ ACTIVE LIMIT`: Pulsing amber tag (`animate-pulse`) with ping dot (`animate-ping`).
- `⚡ LIVE`: Pulsing emerald tag (`animate-pulse`) with ping dot and glowing drop shadow.
- `🔒 CLOSED`: High-contrast badge tagged with outcome status `(WIN)` green, `(LOSS)` red, or `(B/E)` slate.

---

## 3. Verification & Compliance
- **Application Version**: Retained strictly as `v3.0` (`package.json` version `3.0.0`, UI headers `TLCS TERMINAL v3.0`).
- **TypeScript**: `npx tsc --noEmit` passed with 0 errors.
- **Production Build**: `npm run build` compiled 8/8 routes with 0 errors.
- **Pine Script Parity**: Maintained 100% SHA256 checksum parity (`e4caa5a28359a6be56b2d1b51e0936b6cb0d1709c5282046801216bfd04253f2`).
- **Git Push**: Both `Tv-Alert-Mobile` and root repository pushed cleanly to `origin/main`.
