# Obsidian Update Log: Version 1.0 (14 Sept 2026)
## Exit Classification Hierarchy, Post-TP4 Trailing/EMA Resolution & EOD Finalization

---

### 1. Overview & Key Goals
Version 1.0 delivers precise exit level resolution, post-TP4 trailing stop hierarchy fixes, and canonical trade outcome classification across the TradingView Pine Script indicators, Web Dashboard, and Mobile Terminal:

1. **Post-TP4 Trailing SL & EMA Resolution**:
   - **Trailing Stop Hierarchy**: Once TP4 is tagged, the trailing stop loss is locked at **TP3** (`trade.tp3Level`). When price retraces and hits this stop loss, it is now correctly evaluated and dispatched as **`'Hit TP3 Trailing'`** (previously misassigned to `'Hit EMA'`).
   - **EMA Trailing Engine Advance Guard**: In the EMA trailing engine, an exit at `trade.slLevel` while locked at TP3 is cleanly categorized as a TP3 trailing stop hit (`trade.slTriggered := true`). Only when the active EMA has advanced past TP3 and price crosses the EMA does it evaluate as **`'Hit EMA'`**.

2. **Pre-Generated Take Profit Proximity Matching**:
   - **Priority Over EMA Exits for Winning Trades**: In `getDisplayExitLevel`, `getExitLevel`, and scanner outcome pills, pre-generated Take Profit levels (`TP4`, `TP3`, `TP2`, `TP1`) are evaluated **before** applying `EMA` fallback labeling.
   - **Relative Proximity Engine**: If a winning trade's `exit_price` matches a pre-generated TP level within the standard $\pm 0.2\%$ tolerance window, the exact level is denoted (e.g., **`TP3`**, **`TRAIL (TP3)`**).
   - Only winning trades that exit on dynamic moving average boundaries between levels without matching any pre-generated TP level are badged as **`EMA`**.

3. **End of Day (EOD) Finalization Alignment**:
   - Trades closed at the end of the regular market session by the intraday engine are definitively categorized as **`'EOD Exit'`**.
   - Unfilled limit orders that expire or invalidate before entry evaluate cleanly to **`'Cancelled'`**.

4. **Synchronized `finalizeTrade` Code Block**:
   - Regenerated and applied the canonical `finalizeTrade` logic across all primary Pine Script indicator files in the repository.

---

### 2. Canonical `finalizeTrade` Code Block

```pine
finalizeTrade(Settings settings, TradeLogic trade, string z1_zone, string dX, string mX, string d1_message) =>
    string _outcome = 'Unknown'
    if not trade.hasHitEntry
        _outcome := 'Cancelled'
    else if trade.slTriggered
        if trade.tp4Triggered
            _outcome := 'Hit TP3 Trailing'
        else if trade.tp3Triggered
            _outcome := 'Hit TP2 Trailing'
        else if trade.tp2Triggered
            _outcome := 'Hit TP1 Trailing'
        else if trade.tp1Triggered
            _outcome := 'Hit B/E'
        else
            _outcome := 'Hit Initial SL'
    else if trade.divExitTriggered
        _outcome := 'Divergence Exit'
    else if trade.emaExitTriggered
        _outcome := 'Hit EMA'
    else if trade.forceClosed
        _outcome := 'EOD Exit'
    else if trade.tp4Triggered
        _outcome := 'Completed TP4'
    else if trade.tp3Triggered
        _outcome := 'Completed TP3'
    else if trade.tp2Triggered
        _outcome := 'Completed TP2'
    else if trade.tp1Triggered
        _outcome := 'Completed TP1'
```

---

### 3. Files Modified

| File | Changes Made |
| :--- | :--- |
| `TV Indicator/TLCS_Dashboards_4_Commodities_Merged.pine` | Fixed `finalizeTrade` outcome hierarchy, TP3 trailing assignment, and EMA advance guard. |
| `TV Indicator/TLCS_Dashboards_4_Commodities_Signals.pine` | Synchronized `finalizeTrade` hierarchy and EMA trailing logic. |
| `TV Indicator/TLCS_Live_Pivot_Alerts.pine` | Synchronized `finalizeTrade` hierarchy and EMA trailing logic. |
| `user_code.pine` | Synchronized `finalizeTrade` hierarchy and EMA trailing logic. |
| `TV Indicator/raw_input.pine` | Synchronized `finalizeTrade` outcome mapping. |
| `backup.pine` | Synchronized `finalizeTrade` outcome mapping. |
| `TLCS_Website_Deploy/trade-metrics.js` | Updated `getExitLevel` and `getDisplayExitLevel` to prioritize pre-generated TP level matches ($\pm 0.2\%$ proximity) before applying EMA labels on winning trades. |
| `Tv-Alert-Mobile/src/app/page.tsx` | Updated `getExitLevel` and `getDisplayExitLevel` to prioritize pre-generated TP level matches before applying EMA labels. |
| `TLCS_Website_Deploy/scanner.js` | Updated `outcomePill` to check pre-generated TP matches before applying `(EMA)` status to winning trades. |
| `TLCS_Website_Deploy/commodity-scanner.js` | Updated `outcomePill` to check pre-generated TP matches before applying `(EMA)` status to winning trades. |

---

### 4. Verification & Quality Assurance
- **Single Source of Truth**: All trade metrics continue strictly deriving from `metadata.exact_pct` math (`((Exit - Entry) / Entry) * 100`).
- **Canonical Outcome Evaluation**: Math-based outcome evaluation (`exact_pct > 0` $\rightarrow$ `WIN`) is always preserved prior to level resolution.
- **Proximity Tolerance**: Pre-generated target matching rigorously checks `s.tp4`, `s.tp3`, `s.tp2`, `s.target`/`s.tp1` across root and `metadata` objects using the canonical $\pm 0.2\%$ / mintick window.
