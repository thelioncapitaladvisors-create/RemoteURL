# TLCS Update Log — 02 August 2026 (V2.2.3)

## Summary
Two critical fixes applied across the mobile app (`page.tsx`) and web dashboard (`trade-metrics.js`):
1. **ACTIVE LIMITS / LIVE filter regression fix** — filters were completely broken due to a string-based detection approach
2. **HUB tab exact percentage display** — closed trade cards now show `exact_pct` inline next to outcome badges

---

## 1. ACTIVE LIMITS Filter Fix (Critical Regression)

### The Bug
The ACTIVE LIMITS and LIVE filter buttons on the HUB tab were using a broken string-based approach to classify limit orders vs live trades:

```javascript
// OLD (BROKEN) — V1 approach
const isLimitStatus = (s.status || '').toUpperCase().includes('LIMIT');
const isLimitTrigger = (s.trigger || '').toUpperCase().includes('LIMIT');
const isLive = !!s.updated_at || (!isLimitStatus && !isLimitTrigger);
```

**Why it broke**: When TradingView sent limit signals with `status: "Active"` or `status: "OPEN"` (without the word "LIMIT"), both `isLimitStatus` and `isLimitTrigger` were `false`. This caused `isLive = true` for ALL signals regardless of `updated_at`, because the fallback branch `(!false && !false) = true` always evaluated to `true`.

**Symptoms**:
- ACTIVE LIMITS filter → showed **TOTAL: 0** (all limits misclassified as LIVE)
- LIVE filter → showed **unfilled limit orders** with "ACTIVE LIMIT" badges

### The Fix
Replaced with the canonical definition from AGENTS.md:

```javascript
// NEW (CORRECTED) — V2 approach
// Canonical: A Limit Order is an OPEN trade that lacks an updated_at timestamp
return !s.updated_at ? 'ACTIVE LIMITS' : 'LIVE TRADES';
```

### Files Changed
| File | Locations Fixed |
|------|----------------|
| `Tv-Alert-Mobile/src/app/page.tsx` | `getExitLevel`, `getDisplayExitLevel`, dashboard ACTIVE LIMITS filter, dashboard LIVE filter (4 locations) |
| `TLCS_Website_Deploy/trade-metrics.js` | `getExitLevel`, `getDisplayExitLevel` (2 locations) |

**Note**: `dashboard.html`, `scanner.js`, and `commodity-scanner.js` already used the correct `updated_at`-based approach via `isActiveLimit()` and were NOT affected.

---

## 2. HUB Tab Exact Percentage Display

### The Change
Added `exact_pct` percentage display inline next to the outcome badge on HUB tab signal cards:
- For closed trades (WIN, LOSS, BREAKEVEN), shows the percentage value (e.g., `-0.22%` in red, `+1.35%` in green)
- Uses `getExactPct(signal)` — the same function already used on the LOGS tab
- Active/open trades do NOT show a percentage (no `exact_pct` yet)

### File Changed
| File | Change |
|------|--------|
| `Tv-Alert-Mobile/src/app/page.tsx` | Added percentage rendering in HUB card outcome badge area |

---

## 3. AGENTS.md Updated

- **Replaced**: `Live Trades vs Active Limits Categorization` section → V2 (Corrected)
- **Added**: `HUB Tab Exact Percentage Display` rule
- **Documented**: Deprecated V1 approach as anti-pattern with explicit "MUST NOT" patterns

---

## Anti-Pattern Registry (Do NOT Reintroduce)

| Anti-Pattern | Why It Breaks |
|--------------|--------------|
| `(s.status \|\| '').toUpperCase().includes('LIMIT')` for limit detection | Fails when status is `"Active"` or `"OPEN"` |
| `(s.trigger \|\| '').toUpperCase().includes('LIMIT')` for limit detection | Trigger field is often null or absent |
| `const isLive = !!s.updated_at \|\| (!isLimitStatus && !isLimitTrigger)` | Fallback branch forces `isLive = true` for all signals without "LIMIT" in status |
