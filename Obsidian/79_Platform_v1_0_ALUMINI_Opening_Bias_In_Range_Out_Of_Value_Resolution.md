# Platform v1.0: ALUMINI Opening Bias In Range / Out Of Value Resolution & Parser Collision Fix

**Date:** October 26, 2026  
**Status:** COMPLETE & PRODUCTION-VERIFIED  
**Release Tag:** `v1.0`  
**Related Commits:** Tag `v1.0`  

---

## 1. Issue Overview & User Verification

The user raised the following verification query regarding MCX commodity symbol **ALUMINI**:
> *"ALUMINI is not opened as a outside day outside range today."*  
> (Accompanied by a 15-minute TradingView chart screenshot of `ALUMINI1!` on October 26, 2026).

---

## 2. Fact-Backed Data & Mathematical Ground-Truth

### 2.1 Raw Market Levels (October 23, 2026 vs October 26, 2026)
From Supabase `public.shadow_signals` and DhanHQ marketfeed:
- **Prior Day Range (Friday, Oct 23, 2026)**:
  - Previous High (`prev_high` / `dDH_`): **328.40**
  - Previous Low (`prev_low` / `dDL_`): **323.80**
- **Prior Day Value Area (Friday, Oct 23, 2026)**:
  - Value Area High (`vah` / `VAH`): **327.175** (approx. 326.90 - 327.18 on TV)
  - Value Area Low (`val` / `VAL`): **323.875**
- **Current Day Open (Monday, Oct 26, 2026)**:
  - Open Price (`open_price` / `OO_`): **327.80** (fill price: 329.35)

### 2.2 Mathematical Evaluation Against Frank Ochoa STP 2.0
Under Frank Ochoa's *Swing Trade Pro 2.0* opening relationship taxonomy:
1. **Out of Range / Out of Value (OOR / OOV)**:
   $$\text{Open} > \text{Prev High} \quad \text{OR} \quad \text{Open} < \text{Prev Low}$$
   - Here: $\text{Open} = 327.80 \le \text{Prev High} (328.40)$ and $\text{Open} = 327.80 \ge \text{Prev Low} (323.80)$.
   - Condition evaluates to: **FALSE**. The asset opened **INSIDE** Friday's range.

2. **In Range / Out of Value (IR / OOV)**:
   $$\text{Prev Low} \le \text{Open} \le \text{Prev High} \quad \text{AND} \quad (\text{Open} > \text{VAH} \;\lor\; \text{Open} < \text{VAL})$$
   - Here: $323.80 \le 327.80 \le 328.40$ (**Inside Range**)
   - And: $327.80 > 327.175$ (**Outside Value Area, above VAH**)
   - Condition evaluates to: **TRUE**.

3. **TradingView Chart Visual Inspection**:
   - The user's uploaded TradingView chart screenshot (`media_1793029789585.png`) explicitly displays on-screen:
     `"IN RANGE OUT OF VALUE"` at the top of the session.
   - The Pine Script indicator calculated: `"IN RANGE OUT OF VALUE"`.
   - The Python BlackBox engine (`algo_engine/pivots.py`) recorded: `"IN RANGE OUT OF VALUE"`.

---

## 3. Root Cause Analysis

While the Pine Script and Python engines computed the bias correctly, the mobile web dashboard (`Tv-Alert-Mobile/src/app/page.tsx`) classified ALUMINI under **"Out of Range / Out of Value"** due to a string parser collision in helper functions:

```typescript
// Legacy flawed implementation in page.tsx:
if (s.includes('OUT OF RANGE') || (s.includes('OUT') && s.includes('RANGE'))) {
  return 'OUT OF RANGE / OUT OF VALUE';
}
```

Because the raw string was `"IN RANGE OUT OF VALUE"`:
- `s.includes('OUT')` matched `"OUT"` from `"OUT OF VALUE"`.
- `s.includes('RANGE')` matched `"RANGE"` from `"IN RANGE"`.
- Therefore, `(s.includes('OUT') && s.includes('RANGE'))` evaluated to `true`, erroneously converting `"IN RANGE OUT OF VALUE"` into `'OUT OF RANGE / OUT OF VALUE'`.
- Furthermore, in Section 2 `blueprintCategories`:
  `scanKey: (r: any) => (r.bias && (r.bias.includes('OUT OF RANGE') || r.bias.includes('OUT OF VALUE'))) ? 'Out of Range' : 'NONE'`
  caused any asset with `OUT OF VALUE` to be labeled `'Out of Range'`.

---

## 4. Code Modifications

### 4.1 Strict `resolveCanonicalBias` in `Tv-Alert-Mobile/src/app/page.tsx`
Guarded `OUT OF RANGE` to strictly check for explicit `'OUT OF RANGE'`, `'OUTSIDE RANGE'`, `'OOR'`, and excluded `'IN RANGE'`:
```typescript
if (s.includes('OUT OF RANGE') || s.includes('OUTSIDE RANGE') || s.includes('OOR') || (s.startsWith('OUT') && s.includes('RANGE') && !s.includes('IN RANGE'))) {
  return 'OUT OF RANGE / OUT OF VALUE';
}
if (s.includes('OUT OF VALUE') || s.includes('OUTSIDE VALUE') || s.includes('OOV')) {
  return 'IN RANGE / OUT OF VALUE';
}
```

### 4.2 Screener Filter Gating (`extractDhanScreenerAssets` & `dhanScreenerSetupStats`)
Added explicit rejection:
```typescript
if (bias === 'IN RANGE / OUT OF VALUE' || bias === 'IN RANGE / IN VALUE' || rawBias.includes('IN RANGE')) {
  return false;
}
```

### 4.3 Section 2 `blueprintCategories` Clean Up
Updated line 14025 and line 14746 in `page.tsx`:
```typescript
{ 
  id: 'OOR_OOV', 
  label: 'Out of Range / Out of Value', 
  scanKey: (r: any) => (r.oor && r.oor !== 'NONE') ? r.oor : (r.bias && r.bias.includes('OUT OF RANGE') && !r.bias.includes('IN RANGE')) ? 'Out of Range' : 'NONE', 
  dtMatch: (dt: string) => dt.includes('OUT OF RANGE') && !dt.includes('IN RANGE') 
}
```

---

## 5. Verification & Test Results
1. **Node Unit Evaluation**:
   - `'IN RANGE OUT OF VALUE'` -> `'IN RANGE / OUT OF VALUE'` (Verified)
   - `'OUT OF RANGE / OUT OF VALUE'` -> `'OUT OF RANGE / OUT OF VALUE'` (Verified)
2. **Next.js Production Build**:
   - `npm run build` completed with code `0`, generating all static and dynamic routes cleanly.
3. **Python BlackBox Unit Tests**:
   - All 114 test cases in `algo_engine/tests` passed with code `0`.
