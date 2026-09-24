# Obsidian Update Log: September 24, 2026 (v4.0.1)
## Strict Trade Lifecycle Timestamping, Anti-Future Datestamp Mandate & GIFT NIFTY Morning EOD Session Protection

---

### 1. Executive Summary & Root Cause Investigation
On the morning of September 24, 2026, an operational anomaly was investigated:
* **User Query**: *"Is trade live or closed at breakeven."* (Presenting a live `NIFTY1!` chart where price had successfully hit TP1 `23,280.00`, hit TP2 `23,250.00`, trailed stop loss to breakeven `23,330.00`, and was actively pressing toward TP3 `23,200.00`, while the mobile terminal displayed `CLOSED TRADE 15:30 IST 24 SEPT | BREAKEVEN 0.00%` at `07:35 AM IST`).
* **Root Cause 1: Static Clock Heuristic in EOD Sweep**:
  The automated Netlify background worker (`cron-eod-close.js`) executes every 15 minutes to sweep stale trades after session close. Line 83 contained an assumption:
  `if (istHours >= 15.5 || istHours < 9.0) return true;`
  The condition `istHours < 9.0` was designed to close yesterday's leftover trades before regular market open. However, `NIFTY1!` is the **GIFT NIFTY / NSE IX continuous futures contract**, which opens and trades starting at **06:30 AM IST**. At 07:15 AM IST, the cron evaluated `istHours < 9.0` as `true`, erroneously deemed the market closed, and force-closed the fresh morning trade.
* **Root Cause 2: Future Exit Timestamp Fabrication**:
  Inside `getSessionCloseIso`, the script fabricated a session close date of `15:30 IST` on the trade's day. Running at 07:15 AM IST, this returned a timestamp **8 hours into the future** (`2026-09-24T10:00:00Z` = 15:30 IST), violating the deterministic laws of causality.
* **Root Cause 3: Ab-Initio Limit Invalidation (DJI Case)**:
  On the DJI chart, a `SHORT SCALP` limit order placed at `51,529.65` with stop loss at `51,582.63` was followed by a bar that opened above `51,600` and wicked to `51,700`. Pine Script evaluated `high >= entry` (`true`) and `high >= sl` (`true`) on the exact same tick, generating `status: "Hit Initial SL"` instead of `"Cancelled"`. The backend logged a false realized loss of `-0.10%` on a limit that never legitimately lived as a filled trade.

---

### 2. Architectural Pillars Codified

#### A. The 6-Stage Deterministic Trade Lifecycle
Every trade must be strictly time- and date-stamped across its chronological progression:
1. **Signal Genesis (`signal_ts`)**: Candle close timestamp from Pine Script `timenow` or quant bar timestamp.
2. **Order Placement (`created_at`)**: Database insertion of the pending limit order.
3. **Execution Fill (`metadata.real_entry_time`)**: Exact timestamp when limit price was reached and filled.
4. **Trailing SL Ratchet (`updated_at` / `metadata.trail_sl_updated_at`)**: Stamped upon every dynamic trailing stop adjustment.
5. **Target Touches (`metadata.tp1_hit_at`, `metadata.tp2_hit_at`)**: Stamped upon each target tier execution.
6. **Realized Exit (`exit_at` / `metadata.closeDate`)**: Exact fill timestamp of trade closure.

#### B. Anti-Future Datestamp Mandate
* An exit timestamp (`exit_at`) or update timestamp must **NEVER** exceed wall-clock time (`Date.now()`).
* In `cron-eod-close.js`:
  ```javascript
  const nowMs = Date.now();
  if (niftySymbols.includes(sym)) {
      const closeDate = new Date(`${yr}-${mo}-${da}T15:30:00+05:30`);
      if (!isNaN(closeDate.getTime()) && closeDate.getTime() <= nowMs) {
          return closeDate.toISOString();
      }
      return new Date().toISOString(); // Strictly capped at current time
  }
  ```

#### C. Early Morning Session Protection (GIFT NIFTY & MCX)
* Any trade created on the current calendar day in local IST (`isCreatedToday`) is **strictly protected** from morning sweeps (`istHours < 9.0`).
* A trade created today may ONLY be closed after its official market session has concluded:
  * NSE Domestic: `istHours >= 15.5` (3:30 PM IST)
  * MCX Commodities: `istHours >= 23.5` (11:30 PM IST)

#### D. Ab-Initio Limit Invalidation Protection
* When a limit order is placed, if price opens or gaps past the stop loss without an execution fill (`TradeFill`, `TradeUpdate`, or `real_entry_time`), the limit is invalidated ab-initio.
* Purged under the ghost-trade cleanup rule, completely preventing false losses from penalizing portfolio win rates.

---

### 3. Immediate Database Corrections & Deployments

1. **NIFTY1! Record (`878ef2bf-e70c-4f71-9741-351c1bef5ecc`)**:
   * Restored to **`Status: ⚡ TRADE ACTIVE`**, **`Outcome: OPEN`**, **`Exit Price: null`**, **`Trail SL: 23,330.00`**.
   * App now correctly reflects the live trade pressing toward TP3.
2. **DJI Ghost Record (`c950f53a-941d-45dc-8ce1-ebb8e5a6c45a`)**:
   * Purged from Supabase `signals` table.
   * Legitimate EOD Exit WIN (`+0.24%`) preserved cleanly.
3. **Repository Deployments**:
   * `TLCS_Website_Deploy`: Commit `508f6aa` pushed to `origin/main`.
   * Root `Project`: Commits `215f4a6` and `9d7690e` pushed to `origin/main`.
   * `.agents/AGENTS.md`: Updated and ratified with lifecycle timestamping and ab-initio protection mandates.
