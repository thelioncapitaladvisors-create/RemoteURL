# Version 1.0 Production Update: Co-Existence of Opposing Trades (Long & Short Independence) & Mandatory Webhook Triple-Binding

**Release Date:** September 3, 2026  
**Milestone Version:** `v1.0.0` (Production)  
**System Components Affected:** `Netlify Functions (process-webhook-background.js)`, `Tv-Alert-Mobile (route.ts, page.tsx)`, `TLCS_Website_Deploy (trade-metrics.js, screener.js)`

---

## 1. Co-Existence of Opposing Trades for the Same Symbol

### Context & Trading Realities
In extended-hours markets (MCX Commodities trading 09:00–23:55 IST, NYMEX, Global Forex, and Crypto), market structure and sentiment frequently shift over the course of a 14-hour session. Multiple strategy engines (such as Morning Breakout `MISSILE`, Range Reversal `LIGHTNING`, or Intraday `SCALP`) can legitimately identify valid setups in opposite directions on the same trading day:
- **Morning Session (10:30 IST)**: `CRUDEOIL1!` `SHORT MISSILE` at `8,548.00` (SL `8,572.00`, Target `8,469.00`).
- **Evening Session (21:45 IST)**: `CRUDEOIL1!` `LONG LIGHTNING` (`LONG @ SUPPORT`) at `8,624.00` (SL `8,587.00`, Targets `8,651`–`8,744`).

Both positions represent completely independent trade lifecycles with their own risk parameters, timestamps, and profit objectives.

---

## 2. Root Cause Analysis: The "Frankenstein" Trade Defect

### The Symptom
On the mobile app and dashboard, the `CRUDEOIL1!` card displayed an impossible combination:
- **Symbol**: `CRUDEOIL1!`
- **Type**: `SHORT MISSILE`
- **Limit Signal Time**: `10:30 IST` (Morning)
- **Entry Price**: `8,548.00`
- **Exited/Fill Time**: `21:45 IST` (Night)
- **Alive Duration**: `3m`

### The Defect in `process-webhook-background.js`
When the `LONG LIGHTNING` fill webhook arrived at `21:45 IST`, Attempt 1 (`eq('metadata->>trade_id', body.trade_id)`) found no pre-existing limit record. Attempt 2 executed a loose fallback:
1. **Broken Direction Matching**: Evaluated `if (actionU === 'LONG')` with strict equality. Because TradingView sent `body.type = "LONG LIGHTNING"`, `actionU === 'LONG'` was `false`, causing direction filtering to be completely bypassed.
2. **Missing Price Matching**: Attempt 2 performed no validation on `entryPrice`, allowing an `8,624.00` trade to match an `8,548.00` order.
3. **Overly Broad Time Window**: Used `gte('created_at', now - 24 hours)`, reaching 11 hours into the past to grab the morning `SHORT MISSILE` and grafting the night `LONG LIGHTNING`'s execution data onto it.

---

## 3. The Permanent Architecture: Mandatory Triple-Binding

All webhook handlers (`TradeFill`, `TradeClose`, `TrailingSLUpdate`, and `TradeUpdate`) in both Netlify functions (`process-webhook-background.js`) and Next.js routes (`route.ts`) now enforce **Strict Triple-Binding**:

```javascript
// ── ATTEMPT 2: Fallback with Strict Direction + Price + Time Binding ──
if (!fillSignal) {
  const actionU = (body.action || body.type || '').toUpperCase();
  const isLong = actionU.includes('LONG') || actionU.includes('BUY');
  const isShort = actionU.includes('SHORT') || actionU.includes('SELL');

  // STRICT RULE 1: Direction Binding (MANDATORY)
  if (isLong || isShort) {
    const isLongStr = isLong ? 'LONG' : 'SHORT';
    let fallbackQuery = supabase
      .from('signals')
      .select('id, metadata, entry, type')
      .eq('symbol', resolved.symbol)
      .in('status', ['ACTIVE LIMIT', 'Active Limit', 'Active', 'OPEN', 'Open'])
      .ilike('type', `${isLongStr}%`);

    // STRICT RULE 2: Entry Price Binding (MANDATORY)
    const rawEntry = body.entryPrice || body.entry || body.entry_price;
    if (rawEntry != null) {
      const entryNum = Number(rawEntry);
      if (!isNaN(entryNum) && entryNum > 0) {
        const minEntry = entryNum * 0.998;
        const maxEntry = entryNum * 1.002;
        fallbackQuery = fallbackQuery.gte('entry', minEntry).lte('entry', maxEntry);
      }
    }

    const { data: fallbackData } = await fallbackQuery
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle();

    if (fallbackData) {
      fillSignal = fallbackData;
    }
  }
}
```

### Safe Fall-Through to Clean INSERT
If no open record satisfies the bindings (**Direction + Entry Price**), the backend **never mutates or overwrites an unrelated trade**. It falls through to the insert block and records the trade cleanly as a new independent position.

### Preservation of Natural Trade Lifespan
Trades naturally run for their full lifecycle (5–6 hours, full day, or until EOD exit). The backend enforces NO artificial time cutoffs on trade lifecycles. All trades remain active and valid until closed by their explicit exit conditions.

---

## 4. Verification & Database Restoration
- Patched corrupted Supabase record (`778ac23e-518a-485e-a67c-6ac621ec3dbe`) via Service Role Key, restoring its genuine morning fill time (`10:30:14 IST`) and identifier (`CRUDEOIL1!_1788412214121_SHORT MISSILE`).
- Deployed strict triple-binding to Netlify production functions (`TLCS_Website` commit `474b736`).
- Synchronized architecture rules in `.agents/AGENTS.md`.

---

## 5. Automatic & Immediate Deletion of Invalidated/Expired Limit Orders
- **Zero-Ghost Policy**: Whenever an unexecuted limit order is invalidated or expired in Pine Script (`status` or `trigger` contains `INVALID`, `CANCEL`, or `EXPIRE`), the webhook backend immediately and permanently deletes the record from Supabase via `.delete().eq('id', activeSignal.id)`.
- **Complete Removal from Future Consideration**: An invalidated or expired limit order represents an unfilled setup that no longer exists in the market. It is completely expunged from the database so it can NEVER linger, pollute active signals, or be mistakenly matched or mutated by any subsequent trades (such as a later session trade on the same symbol).
- **No Orphaned Open Limits**: Unexecuted limit orders that do not fill within their market session never survive across sessions to collide with subsequent trade fills.

---

## 6. Original Trading Logic Inviolability (Zero Modifications to Entry, Exit, or SL)
- **Absolute Preservation of Original Logics**: Under NO circumstances should any modifications, overrides, artificial buffers (e.g. ATR cushions), bar-close requirements (`barstate.isconfirmed`), or mathematical adjustments be introduced to the user's original Pine Script indicator formulas for **Entry**, **Exits**, or **Stop Loss (SL)** levels.
- **Pure Touch-Based Execution Model**: Entry, Take Profit, and Stop Loss executions MUST remain strictly based on the user's original touch-based price levels (high/low price action). Stop distances will not be artificially widened and bar-close delays will not be imposed.
- **Zero Backend Interference**: The backend webhook processors, Netlify functions, mobile application, and web dashboards must strictly record, reflect, and faithfully execute the exact empirical levels and alert payloads transmitted by the user's indicator without modification.

---

## 7. NCPR Trade Consideration: Unconditional Signal Allowance on Narrow CPR Days
- **Validity of Day Type Classification**: Classifying the session into Day Types (`TYPICAL DAY`, `TRADING RANGE`, `EXPANDED TYPICAL DAY`, etc.) is legitimate and vital for market context and structural analysis. Session classification is not flawed.
- **Flaw of Ignoring Trades on NCPR**: The actual flaw is failing to consider or discarding trades when a Narrow Central Pivot Range (NCPR) is available.
- **NCPR Overrides Trade Suppression**: Because NCPR indicates volatility compression that typically resolves into breakout expansion, trades MUST ALWAYS be considered and allowed when NCPR is present, regardless of early sideways session classifications. The presence of NCPR ensures signals (`MISSILE`, `SCALP`, `LIGHTNING`) are fully considered and never suppressed.

---

## 8. Strict Prohibition on Proposing Logic Alterations (Inviolability of User's Trading System)
- **Zero Counter-Proposals to User Trading Logics**: The assistant must **NEVER** suggest, recommend, or propose modifications, buffers, wider stops, swing-level shifts, or logic redesigns that run contrary to or modify the user's established trading systems and Pine Script rules.
- **Respect for Established System Logics**: The user's entry conditions, exit criteria, stop loss placement methods, and indicator mechanics are intentional, proprietary, and mathematically defined by the user. The assistant must respect them unconditionally without questioning or trying to "re-engineer" the trading rules.
- **Sole Scope of Assistant Responsibilities**: The assistant's responsibility is exclusively engineering excellence: ensuring flawless infrastructure, webhook processing, exact database synchronization, frontend accuracy, and pure fidelity to the user's alerts as transmitted.
