# 133 — Platform v1.0 Realized P&L Parity & Performance Header Win Rate Synchronization Mandate

**Date**: November 26, 2026  
**Status**: Canonical Production Release (`v1.0.0`)  
**Target Files**: `page.tsx`, `RemoteURL/page.tsx`, `Tv-Alert-Mobile/src/app/page.tsx`, `AGENTS.md`, `.agents/AGENTS.md`

---

## 1. Executive Summary & Problem Diagnosis

### The Issue
A mathematical discrepancy was identified between the top **PERFORMANCE** KPI header card (`TODAY'S SUCCESS`) and the granular **Trade Distribution** chart:
* **Trade Distribution Chart**: Displayed **`3 WINS`**, **`9 LOSSES`**, **`1 B/E`** out of **`13 TOTAL`** trades (+₹1.9k max win, +₹374 min win). Actual win rate:
  7056\frac{3 \text{ Wins}}{13 \text{ Total}} \times 100 = \mathbf{23.08\% \approx 23.1\%} \quad \left(\frac{3}{12} \times 100 = \mathbf{25.0\%} \text{ excluding B/E}\right)7056
* **Performance Header Card**: Displayed **`TODAY'S SUCCESS: 7.7%`**.
  Notice that:
  7056\frac{\mathbf{1}}{\mathbf{13}} \times 100 = 7.692\% \approx \mathbf{7.7\%}7056
  The top card was counting **only 1 WIN** out of 13 trades, undercounting wins by 2 trades.

---

## 2. Root Cause Analysis

In `page.tsx`, `todayWinCount` was defined as:
```typescript
const todayWinCount = todayClosedSignals.filter(s => resolveOutcome(s) === 'WIN').length;
```
Inside `resolveOutcome(s)`:
1. Strategy exits like `DIVERGENCE EXIT` or trades lacking an explicit database `'WIN'` tag were prematurely routed to `'LOSS'` or `'BREAKEVEN'` before their positive realized P&L (`exact_pct > 0`) was evaluated.
2. Conversely, the Trade Distribution chart evaluated trades by realized P&L (`t.value > 0`), recognizing all 3 profitable trades.

---

## 3. Mathematical Implementation & Parity Resolution

### A. Prioritization of Realized P&L in `resolveOutcome(s)`
In `resolveOutcome(s)`, the `exact_pct` evaluation is strictly prioritized ahead of default loss routing:
```typescript
// Step 2: exact_pct is the SINGLE SOURCE OF TRUTH — check it for closed trades
if (meta && meta.exact_pct != null && (s.exit_price != null || s.exit_at != null || st.includes('EXIT') || st.includes('HIT') || st.includes('CLOSED') || o !== 'OPEN')) {
    const pct = parseFloat(meta.exact_pct);
    if (!isNaN(pct)) {
        if (pct > 0)  return 'WIN';
        if (pct < 0)  return 'LOSS';
        return 'BREAKEVEN';
    }
}
```
For `DIVERGENCE EXIT`, price delta is explicitly evaluated:
```typescript
if (st.includes('DIVERGENCE EXIT')) {
    const entryP = Number(s.entry || 0);
    const exitP = Number(s.exit_price || 0);
    if (entryP > 0 && exitP > 0) {
        const isLong = (s.type || '').toUpperCase().includes('LONG') || (s.type || '').toUpperCase().includes('BUY');
        const diff = isLong ? (exitP - entryP) : (entryP - exitP);
        if (diff > 0.00001) return 'WIN';
        if (diff < -0.00001) return 'LOSS';
        return 'BREAKEVEN';
    }
    return 'LOSS';
}
```

### B. Synchronization of `todayWinCount` and `weeklyWinCount`
`todayWinCount` and `weeklyWinCount` now inspect both canonical `resolveOutcome(s) === 'WIN'` and positive realized gain (`exact_pct > 0` or rupee P&L $> 0$):
```typescript
const todayWinCount = todayClosedSignals.filter(s => {
    const o = resolveOutcome(s);
    if (o === 'WIN') return true;
    const pct = getExactPct(s);
    if (pct != null && pct > 0) return true;
    const rupee = getTradeRupeePnL(s, usdInrRate);
    return rupee > 0;
}).length;

const todayLossCount = todayClosedSignals.filter(s => {
    const o = resolveOutcome(s);
    if (o === 'LOSS') return true;
    const pct = getExactPct(s);
    if (pct != null && pct < 0) return true;
    const rupee = getTradeRupeePnL(s, usdInrRate);
    return rupee < 0;
}).length;

const todaySuccessRate = todayClosedSignals.length > 0 
    ? ((todayWinCount / todayClosedSignals.length) * 100).toFixed(1) 
    : '0.0';
```

---

## 4. Verification & Consistency Audit
* Top Performance card `TODAY'S SUCCESS` now evaluates to **`23.1%`** ( / 13$), matching the 3 WINS shown in Trade Distribution.
* 100% mathematical parity across `RemoteURL`, `Tv-Alert-Mobile`, and root repositories.
