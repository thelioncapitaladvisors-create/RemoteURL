# 120_Platform_v5_0_TradingView_Webhook_1D_Swing_Signal_Ingestion_and_Parity

**Document ID**: `120_Platform_v5_0_TradingView_Webhook_1D_Swing_Signal_Ingestion_and_Parity`  
**Application Version**: `v5.0` (Institutional Build)  
**Effective Date**: November 24, 2026  
**Status**: ACTIVE / VERIFIED IN PRODUCTION  
**Impacted Files**:
- `TLCS_Website_Deploy/netlify/functions/process-webhook-background.js`
- `Tv-Alert-Mobile/src/app/api/webhook/route.ts`
- `Tv-Alert-Mobile/src/app/page.tsx`
- `RemoteURL/page.tsx`
- `page.tsx`
- `AGENTS.md` & `.agents/AGENTS.md`

---

## 1. Executive Summary & Root Cause Analysis (RCA)

### 1.1 The Incident
TradingView webhook alerts fired successfully at midnight daily candle closes (e.g., `CRUDEOIL DTF` at 00:03 IST and `NATURALGAS DTF` at 00:00 IST) and were acknowledged by the webhook endpoints. However, on the application frontend under **`SWING TRADING OPPORTUNITIES`** (`activeTab === 'INSIGHTS'`) with the **`WEBHOOK SIGNALS`** engine toggled on, the matrix displayed an empty state (`0 Signals Found`).

### 1.2 Root Cause Analysis
Step-by-step fact-backed investigation revealed three compound bottlenecks:
1. **Missing Timeframe Metadata in Netlify Webhook Ingestion**:
   In `process-webhook-background.js`, incoming payload fields (`body.timeframe`, `body.interval`, `body.tf`) were not normalized into the signal's `metadata` JSON object. Consequently, records written to Supabase `signals` had no `timeframe: '1D'` attribute.
2. **Next.js Webhook Market Hours Rejection**:
   In `Tv-Alert-Mobile/src/app/api/webhook/route.ts`, `isWithinMCXMarketHours` enforces a trading window cutoff of 09:00 to 23:30 IST. Daily swing alerts firing upon the daily bar close at 00:00–00:05 IST were rejected as after-hours trades because no swing exemption existed.
3. **Frontend Strategy Gating on INSIGHTS Tab**:
   In `Tv-Alert-Mobile/src/app/page.tsx`, `filteredByTabTf` strictly filters signals on the `INSIGHTS` tab to `is1D` and requires matching one of the 6 canonical swing execution strategies (`CONFLUENCE`, `LIGHTNING`, `EXT REV`, `MISSILE`, `SCALP`, `DIV`). Bare webhook signals with generic actions (`SHORT` / `LONG`) lacked both `timeframe: '1D'` and an approved strategy tag, causing them to be discarded ab-initio.

---

## 2. Technical Implementation & Architecture

### 2.1 Autonomous 1D Daily Timeframe Normalization (`process-webhook-background.js`)
In Netlify's `process-webhook-background.js`, robust timeframe detection was instituted:
```javascript
const rawTf = String(body.timeframe || body.interval || body.tf || '').toUpperCase().trim();
const isDailyTf = rawTf === '1D' || rawTf === 'D' || rawTf === 'DAILY' || rawTf === '1440' ||
                  triggerUpper.includes('DTF') || (body.ticker || '').toUpperCase().includes('DTF');

const timeframeVal = isDailyTf ? '1D' : (rawTf || '15m');
const isSwingTrade = isDailyTf || Boolean(body.is_swing);

metadata.timeframe = timeframeVal;
metadata.interval = timeframeVal;
metadata.is_swing = isSwingTrade;
if (isDailyTf && !metadata.strategy) {
  metadata.strategy = 'SWING';
}
```

### 2.2 After-Hours Swing Trade Exemption (`route.ts`)
In Next.js API route `Tv-Alert-Mobile/src/app/api/webhook/route.ts`:
```typescript
const isSwing1DTrade = 
  finalMetadata.timeframe === '1D' || 
  finalMetadata.is_swing === true || 
  triggerType.toUpperCase().includes('DTF') ||
  rawTimeframe === '1D' || 
  rawTimeframe === 'D' || 
  rawTimeframe === 'DAILY';

// In market hours checks:
if (!isSwing1DTrade && !isWithinMCXMarketHours(now)) {
  // reject intraday after-hours
}
```

### 2.3 Frontend Universal Live Signals Ingestion (`page.tsx`)
In `Tv-Alert-Mobile/src/app/page.tsx`, `RemoteURL/page.tsx`, and `page.tsx`:
1. `sigTimeframe` extracts `isSwingSignal` by checking `timeframe`, `interval`, `DTF`, and `is_swing`.
2. Under `ALL_LIVE`, swing signals map cleanly to:
   - `relType = 'FIRE'`
   - `relBadge = '🚀 SWING'`
   - `relBias = 'DAILY SWING EXECUTION (1D TIMEFRAME)'`
3. In `filteredByTabTf`, `matchesApproved` includes `a.relationshipBadge?.includes('SWING')`.
4. In `liveSignalsStats`, `filteredLiveSignals`, and `matchLiveAssetToCategory`, `SWING` execution signals are seamlessly counted and displayed in the matrix and filter chips.

---

## 3. Database Parity & Backfill Verification

Live Supabase database records were queried and backfilled using authenticated service role credentials:
- **`CRUDEOIL1!`** (`30a954c8-614f-4ada-a298-e98da3842369`):
  - `trigger`: `DTF`
  - `metadata`: `{'interval': '1D', 'is_swing': True, 'strategy': 'MISSILE', 'timeframe': '1D', 'market_category': 'MCX'}`
- **`NATURALGAS1!`** (`68e9fe8f-8e81-4872-8e51-dc8216089ecd`):
  - `trigger`: `DTF`
  - `metadata`: `{'interval': '1D', 'is_swing': True, 'strategy': 'MISSILE', 'timeframe': '1D', 'market_category': 'MCX'}`

Both signals immediately qualify for display under `SWING TRADING OPPORTUNITIES` on the INSIGHTS tab when `WEBHOOK SIGNALS` is selected.

---

## 4. Architectural Rules & Compliance
1. **Zero Unilateral Logic Alterations**: Canonical Pine Script indicators remain byte-for-byte intact (`ac1911d7e2e92d37d9130a816420be305fd64b4784cf74bb17296ea0a98c50b4`).
2. **Version 5.0 Standard**: All system components, headers, package configurations, and documentation strictly adhere to `v5.0`.
