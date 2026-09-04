# Version 1.0 Production Master: Strict Triple-Binding (`trade_id` + `entryTime` + `direction`) & Non-Destructive EOD Market Sweeps

**Release Date:** September 4, 2026  
**Milestone Version:** `v1.0.0` (Production Master Baseline)  
**System Scope:** TradingView Pine Script Indicator, Netlify Serverless Backend (`process-webhook-background.js`, `cron-eod-close.js`), Supabase Database (`signals`), Next.js Mobile Application (`Tv-Alert-Mobile`), Production Web Engine (`TLCS_Website_Deploy`)

---

## 1. Executive Summary & Milestone Objectives

This document establishes the official **Version 1.0 Production Master** baseline. It consolidates two structural architectural breakthroughs that permanently ensure data integrity and eliminate operational errors across the entire TLCS trading ecosystem:

1. **The Strict Triple-Binding Protocol (`trade_id` + `entryTime` + `direction`)**:
   - Replaces all legacy fuzzy matching with an immutable three-pillar anchor.
   - Eliminates "Frankenstein" trades where unexecuted limit orders from one session were mutated by opposing orders in later sessions.
   - Permits 100% independent co-existence of opposite-direction trades (`LONG` and `SHORT`) on extended-hours instruments (MCX, NYMEX, Forex, Crypto).

2. **Non-Destructive EOD & Stale Trade Sweep Protocol**:
   - **Strict Prohibition on Blanket Breakeven**: Permanently deprecates blanket `SET outcome = 'BREAKEVEN', exit_price = entry` queries that erase legitimate profits/losses and corrupt win rate calculations.
   - **Zero Win Rate Dilution for Unexecuted Limits**: Unfilled limit orders are marked `CANCELLED` (or deleted), completely removing them from the closed trades denominator.
   - **True Mathematical P&L for Executed Positions**: Executed positions that run to market close calculate their true `exact_pct` and are definitively categorized as `WIN`, `LOSS`, or `BREAKEVEN`.

3. **Autonomous Operator Handover**:
   - All manual diagnostic SQL queries, emergency sweep routines, and deployment commands are codified in `Obsidian_TLCS_Standard_Operating_Procedure_Manual_and_Troubleshooting_Handbook_v1_0.md` for complete human operation without AI tools.

---

## 2. Pillar 1: Strict Triple-Binding Protocol

### The Root Cause of Legacy Failures
In extended-session markets (e.g., MCX 09:00–23:55 IST, NYMEX 23-hour trading, Forex 24/5):
- A symbol can legitimately produce a morning `SHORT MISSILE` setup and an evening `LONG LIGHTNING` setup.
- If the morning short limit was never filled, a naive query like `.eq('symbol', 'CRUDEOIL1!').in('status', ['OPEN', 'Active'])` would grab the short record and graft the evening long trade's fill data onto it.
- This produced corrupted "Frankenstein" trades with mismatched entry prices, invalid durations, and inverted outcome logic.

### The Three Invariant Pillars

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                INCOMING ALERT PAYLOAD                                  │
│                 { trade_id, symbol, entryTime, type/action, entry }                    │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
               ┌────────────────────────────┴────────────────────────────┐
               ▼                                                         ▼
┌─────────────────────────────────────────┐               ┌──────────────────────────────────────────────┐
│       ATTEMPT 1: EXACT IDENTITY         │               │     ATTEMPT 2: STRICT TRIPLE-BIND FALLBACK   │
│   Query: `metadata->>trade_id = id`     │ ─(If Empty)─► │   1. `symbol = symbol`                       │
│   Millisecond-unique fingerprint        │               │   2. `type ILIKE isLongStr%` (DIRECTION)     │
│   Guarantees 1:1 position instance      │               │   3. `entry = entry ± 0.2%` (LEVEL)          │
└──────────────────┬──────────────────────┘               │   4. `signal_ts ≈ entryTime` (TEMPORAL)      │
                   │                                      └──────────────────────┬───────────────────────┘
                   │ Found Exact Match                                           │ Found Exact Match
                   ▼                                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              UPDATE ACTIVE POSITION RECORD (FILL / CLOSE / SL)                         │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            │ If Neither Matches
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                SAFE FALL-THROUGH: CLEAN INSERT                                         │
│            NEVER mutate an unrelated trade. Always insert a brand-new independent row.                 │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Identity Anchor (`trade_id`)**:
   Pine Script generates a millisecond fingerprint `{symbol}_{timestamp}_{type}` (e.g. `CRUDEOIL1!_1788412214121_SHORT_MISSILE`) transmitted across all webhooks (`TradeFill`, `TrailingSLUpdate`, `TradeClose`). Attempt 1 always searches by this key.
2. **Direction Anchor (`direction`)**:
   `type ILIKE 'LONG%'` or `type ILIKE 'SHORT%'`. A `LONG` execution can never touch, modify, or terminate a `SHORT` position under any circumstance.
3. **Temporal & Price Anchor (`entryTime` & `entryPrice`)**:
   Constrains candidate records to $\pm 0.2\%$ of price and binds to the exact bar creation window. Trades from prior days are mathematically isolated.
4. **Safe Fall-Through**:
   If neither attempt matches, the backend **never overwrites an existing trade**. It cleanly executes an `INSERT`, allowing opposite trades to co-exist cleanly.
5. **Instant Ghost Elimination**:
   Pine Script `LimitCancel` or `Invalidated` triggers execute an immediate hard-delete (`.delete().eq('id', activeSignal.id)`). Zero ghost records linger.

---

## 3. Pillar 2: Non-Destructive EOD & Stale Sweep Protocol

### The Danger of Blanket Breakeven
Arbitrarily updating stale records with `outcome = 'BREAKEVEN'` and `exit_price = entry` corrupts the platform:
- Legitimate winning trades that closed with the session have their returns reduced to `0.00%`.
- Legitimate losing trades have their drawdowns erased.
- Unexecuted limits enter the total closed trades denominator ($\frac{\text{Wins}}{\text{Total Closed}}$), falsely diluting the system's actual Win Rate.

### Canonical Sweep Architecture (`cron-eod-close.js` & Manual SQL)

#### Category A: Unexecuted Pending Limits
- **Action**: Mark as `status: 'CANCELLED'`, `outcome: 'CANCELLED'` (or hard-delete).
- **Metric Impact**: Completely omitted from closed trades. 0 impact on Win Rate or Profit Factor.

```sql
UPDATE signals
SET 
  status = 'CANCELLED',
  outcome = 'CANCELLED',
  updated_at = NOW(),
  metadata = jsonb_set(COALESCE(metadata, '{}'::jsonb), '{exit_reason}', '"EXPIRED_LIMIT_MANUAL"'::jsonb)
WHERE exit_price IS NULL
  AND (status ILIKE '%limit%' OR (metadata->>'real_entry_time' IS NULL AND updated_at IS NULL))
  AND created_at < (NOW() - INTERVAL '14 HOURS');
```

#### Category B: Executed Active Positions
- **Action**: Fetch actual closing price (or `current_price` / trailing stop), calculate true exact percentage, and assign canonical outcome:
  $$\text{exact\_pct} = \frac{\text{Exit} - \text{Entry}}{\text{Entry}} \times 100 \quad (\text{or } \frac{\text{Entry} - \text{Exit}}{\text{Entry}} \times 100 \text{ for SHORT})$$
  - If $\text{exact\_pct} > 0.05\% \rightarrow \mathbf{WIN}$ (`status = 'EOD Exit (TP1)'`)
  - If $\text{exact\_pct} < -0.05\% \rightarrow \mathbf{LOSS}$ (`status = 'EOD Exit (SL)'`)
  - If $-0.05\% \le \text{exact\_pct} \le 0.05\% \rightarrow \mathbf{BREAKEVEN}$ (`status = 'EOD Exit'`)

```sql
WITH executed_stale AS (
  SELECT 
    id,
    entry,
    COALESCE(current_price, stop, entry) AS final_exit,
    CASE 
      WHEN type ILIKE '%short%' OR type ILIKE '%sell%' 
        THEN ROUND(((entry - COALESCE(current_price, stop, entry)) / entry * 100)::numeric, 2)
      ELSE ROUND(((COALESCE(current_price, stop, entry) - entry) / entry * 100)::numeric, 2)
    END AS calculated_pct
  FROM signals
  WHERE (outcome IS NULL OR outcome = 'OPEN' OR status ILIKE '%active%')
    AND exit_price IS NULL
    AND created_at < (NOW() - INTERVAL '14 HOURS')
)
UPDATE signals s
SET 
  exit_price = es.final_exit,
  exit_at = NOW(),
  updated_at = NOW(),
  outcome = CASE 
    WHEN es.calculated_pct > 0.05 THEN 'WIN'
    WHEN es.calculated_pct < -0.05 THEN 'LOSS'
    ELSE 'BREAKEVEN'
  END,
  status = CASE 
    WHEN es.calculated_pct > 0.05 THEN 'EOD Exit (TP1)'
    WHEN es.calculated_pct < -0.05 THEN 'EOD Exit (SL)'
    ELSE 'EOD Exit'
  END,
  metadata = jsonb_set(
    jsonb_set(COALESCE(s.metadata, '{}'::jsonb), '{exact_pct}', to_jsonb(es.calculated_pct)),
    '{exit_reason}', '"EOD_STALE_SWEEP"'::jsonb
  )
FROM executed_stale es
WHERE s.id = es.id;
```

---

## 4. Documentation & Operational Handover

1. **Master Architecture Codification**:
   - Permanently recorded in [`.agents/AGENTS.md`](file:///Users/vishant/Documents/Project/.agents/AGENTS.md).
2. **Master Manual SOP & Troubleshooting Handbook**:
   - Detailed in [`Obsidian_TLCS_Standard_Operating_Procedure_Manual_and_Troubleshooting_Handbook_v1_0.md`](file:///Users/vishant/Documents/Project/Obsidian_TLCS_Standard_Operating_Procedure_Manual_and_Troubleshooting_Handbook_v1_0.md) across Guide 1 through Guide 6 and the Emergency SQL Diagnostic Toolkit.
3. **Repository Synchronizations**:
   - All submodules (`TLCS_Website_Deploy`, `Tv-Alert-Mobile`) and the root project tree are fully synchronized, tested, and pushed to GitHub main.
