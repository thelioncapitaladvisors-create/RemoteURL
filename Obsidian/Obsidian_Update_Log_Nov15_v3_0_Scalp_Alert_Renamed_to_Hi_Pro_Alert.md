# TLCS Platform Architecture Log: Scalp Alert Renamed to 'Hi-Pro Alert' Across Mobile Terminal & Screener Matrices
**Effective Date:** November 15, 2026  
**Release Target:** TLCS Platform v3.0  
**Classification:** Institutional Screener Precision & Terminology Synchronization  

---

### 1. Executive Summary & Rationale
In the `STOCKS WITH ACTION` unified screener within `Tv-Alert-Mobile/src/app/page.tsx`, the setup corresponding to the `FIRE` / `FIRE_ALERT` trigger was previously designated as "Scalp Alert" / "Scalp Alerts". 

In the canonical algorithmic framework:
- The setup represents high-probability confluence trade signals firing **outside Greenzone and Redzone** (`Anysignal and not (Greenzone or Redzone)`).
- Calling this setup "Scalp Alert" caused naming confusion with standalone momentum scalp entries (`SCALP` / `JustScalpBuy` / `JustScalpSell`).
- To provide crisp institutional clarity and recognize that this signal captures high-probability occurrences of existing signal types operating free from conflicting zone friction, it has been universally renamed to **"Hi-Pro Alert"** / **"Hi-Pro Alerts"** across all user-facing terminal interfaces, screener cards, subfilters, parameter categories, table badges, and detail modal popovers.

---

### 2. Comprehensive Modifications in `Tv-Alert-Mobile/src/app/page.tsx`

1. **Table Row Badge & Bias String Generator (`setupType === 'FIRE'`)**:
   - Badge text updated from `'🔥 SCALP ALERT'` to `'🔥 HI-PRO ALERT'`.
   - Bias description updated to `'CANONICAL HI-PRO CONFLUENCE (OUTSIDE GREEN/RED)'`.

2. **Setup Card Configuration (`dhanBiasActiveTab === 'FIRE'`)**:
   - `label`: `'Bullish Hi-Pro Alert'` / `'Bearish Hi-Pro Alert'` / `'Hi-Pro Alert'`
   - `badgeTitle`: `'Canonical Hi-Pro Alert Confluence Setups'`
   - `subtitle`: `'High-probability canonical trade signals firing outside Greenzone & Redzone boundaries, free from adverse zone friction.'`
   - `educationalChecklist`: Updated framework title to `'Hi-Pro Alert Confluence Framework'` with specific section headers `'BULLISH HI-PRO ALERT:'` and `'BEARISH HI-PRO ALERT:'`.

3. **Setup Navigation Tabs (`setupTabs`)**:
   - `label`: `'Hi-Pro Alert'`, `shortLabel`: `'Hi-Pro Alert'`, icon: `'🔥'`, with live category count.

4. **Category Subfilter Buttons**:
   - Subfilter button updated to `'🔥 ALL HI-PRO ALERTS'`.

5. **Parameter Categories**:
   - Category `{ id: 'FIRE_ALERT', label: 'Hi-Pro Alert' }`.

6. **Matrix Row Badges & Toggles**:
   - Table cell badge rendered as `<span>HI-PRO ALERT</span>`.
   - Toggle button rendered as `'HI-PRO ALERTS'`.
   - Empty state message updated to `'No Hi-Pro Alerts Active'`.

7. **Floating Detail Modal Popover**:
   - Popover header updated to `BULLISH HI-PRO ALERT` / `BEARISH HI-PRO ALERT`.
   - Educational playbook descriptions updated to `Bullish Hi-Pro Alert (Confluence Expansion)` and `Bearish Hi-Pro Alert (Confluence Breakdown)`.

---

### 3. Strict Logic & Backend Preservation
- All underlying database column queries (`setup_type === 'FIRE'`, `FIRE_ALERT`) and algorithmic evaluation logic remain strictly unchanged.
- Standalone `SCALP` momentum signals (`LONG SCALP` / `SHORT SCALP`) remain untouched as canonical momentum strategies.
- 100% backward compatibility maintained with Supabase Realtime WebSocket feeds and DhanHQ scanner outputs.

---

### 4. Verification & Validation
- **Production Next.js Build**: Executed `npm run build` in `Tv-Alert-Mobile` — successfully compiled with code 0 (`Compiled successfully`, zero TypeScript or JSX lint errors).
- **Rulebook Synchronization**: Updated `AGENTS.md` and `.agents/AGENTS.md` to reflect `Hi-Pro Alert` within the 9 screener sections.
