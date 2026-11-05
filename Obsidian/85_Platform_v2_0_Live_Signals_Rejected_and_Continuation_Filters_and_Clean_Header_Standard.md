# Platform v2.0: Live Signals Rejected & Continuation Filter Tabs and Clean Header Standard

**Effective Date:** November 5, 2026  
**Component:** `Tv-Alert-Mobile/src/app/page.tsx` (`HUB` Tab • `🚨 LIVE SIGNALS` & `TRADE FILTERS`)  
**Status:** Complete & Production Ready  

---

## 1. Executive Summary

In accordance with user instructions, the **Live Signals** matrix and **Trade Filters** on the HUB tab have been enhanced with dedicated institutional filter tabs to isolate **Rejected Bullish / Rejected Bearish** setups and **Bullish / Bearish Continuation** setups. Furthermore, the redundant top-right `RSI 14 + SWING PIVOTS` label has been completely excised to provide clean horizontal clearance across mobile viewports.

---

## 2. Architectural Changes

### 2.1 Clean Header Standard
- Excised the legacy text `<div className="hidden sm:flex items-center gap-1 text-[9px] font-mono font-bold text-dim uppercase"><span>RSI 14 + SWING PIVOTS</span></div>` from the Live Signals filter bar header.
- Preserved the clean `● REAL-TIME SCAN` badge alongside the flashing `🚨 LIVE SIGNALS` badge.

### 2.2 Live Signals Switcher Bar (`hubLiveTab`)
The state was expanded from binary mode to a 4-mode institutional switcher:
```typescript
const [hubLiveTab, setHubLiveTab] = useState<'ALL' | 'DIVERGENCE' | 'REJECTED' | 'CONTINUATION'>('ALL');
```

The filter bar now features 4 styled buttons:
1. `[🌐 ALL SIGNALS]` (Rose `#e11d48`) — Consolidated active parameter matrix.
2. `[⚡ LIVE DIVERGENCE SIGNALS]` (Royal Violet `#9333ea`) — Regular & Hidden Divergences with `[DIV]` badges.
3. `[🛡️ LIVE REJECTED SIGNALS]` (Institutional Amber `#d97706`) — Rejected Bullish & Rejected Bearish with `[REJ]` badges.
4. `[🚀 LIVE CONTINUATION SIGNALS]` (Institutional Teal `#0d9488`) — Bullish Continuation & Bearish Continuation with `[CONT]` badges.

### 2.3 Strict Directional Column Isolation
In accordance with Swing Trade Pro 2.0 / PivotBoss CPR opening relationships:
- **Rejected Bullish** and **Bullish Continuation** are locked strictly to the **Bullish (▲)** column (`bulls = matching; bears = [];`).
- **Rejected Bearish** and **Bearish Continuation** are locked strictly to the **Bearish (▼)** column (`bulls = []; bears = matching;`).

### 2.4 Canonical Classifiers
Six deterministic helper functions were integrated:
- `isRejectedSignal(s)`
- `isRejectedBullishSignal(s)`
- `isRejectedBearishSignal(s)`
- `isContinuationSignal(s)`
- `isBullishContinuationSignal(s)`
- `isBearishContinuationSignal(s)`

Evaluating `s.type`, `s.trigger`, and `s.metadata` (`opening_bias`, `day_type`, `c1`, `setup_family`, `tradeMessage`).

### 2.5 Trade Filters Synchronization (Section 2)
In Section 2 `TRADE FILTERS`:
- Added `[🛡️ LIVE REJECTED]` (Amber active pill with pulse dot and count badge).
- Added `[🚀 LIVE CONTINUATION]` (Teal active pill with pulse dot and count badge).
- Connected directly to `filteredTrades` for both Webhook and DhanHQ BlackBox engines.

---

## 3. Dedicated Empty States

When no active setups match the selected filter in the current market session:
- **`REJECTED` Mode**:
  `🛡️ NO LIVE REJECTED BULLISH / BEARISH SIGNALS ACTIVE`
  Scanning all active markets for Rejected Bullish & Rejected Bearish CPR opening bias / rejection setups.
- **`CONTINUATION` Mode**:
  `🚀 NO LIVE BULLISH / BEARISH CONTINUATION SIGNALS ACTIVE`
  Scanning all active markets for Bullish & Bearish Continuation CPR bias expansion setups.

---

## 4. Verification & Integrity
- Zero alterations to Pine Script strategy triggers.
- Verified JSX tag closure and bracket balance.
- Verified WCAG AAA color contrast across dark, light, gray, and goldengate theme skins.
