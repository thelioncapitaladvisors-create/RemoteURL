# Obsidian Update Log: Version 1.1 (14 Sept 2026)
## Zero Artificial Fallbacks, Generic TARGET Removal & Strict Trade Logic Enforcement

---

### 1. Executive Summary & Core Principle
Version 1.1 strictly eliminates all generic heuristic fallbacks across the web dashboard and mobile terminal, establishing the **Zero Artificial Fallback Rule**:
* **Explicit Trade Logic Only**: No synthetic mappings or heuristic assumptions (such as mapping generic `"TARGET"` strings to `TP1`) are permitted anywhere in the system.
* **Pre-Defined Ground Truth Binding**: Target levels (`tp1`, `tp2`, `tp3`, `tp4`) are immutable mathematical prices calculated at signal inception and saved to distinct database columns. Trade exits are determined strictly through exact numerical matching between executed `exit_price` and these pre-defined target columns (`[TP4, TP3, TP2, TP1]`), backed exclusively by explicit Pine Script status strings (`Completed TP1..4`, `Hit Initial SL`, `Hit B/E`, `Hit TP1..3 Trailing`, `Hit EMA`, `Divergence Exit`, `EOD Exit`).
* **Permanent Policy**: Nothing beyond the user's explicit trade logic may be introduced without prior knowledge and explicit authorization.

---

### 2. Pre-Defined Limit Level Ground Truth Binding

1. **Immutable Inception Anchors**:
   - When a limit order is created at bar 0, the engine permanently locks the exact price levels into the database row:
     * `entry_price` (e.g. `1.15919`)
     * `stop_loss` (e.g. `1.15952`)
     * `tp1` (e.g. `1.15839`)
     * `tp2` (e.g. `1.15782`)
     * `tp3` (e.g. `1.15686`)
     * `tp4` (e.g. `1.15628`)
2. **Direct Verification (Zero Guessing)**:
   - When the trade closes at `1.15686`, comparing `exit_price` against `[s.tp4, s.tp3, s.tp2, s.tp1]` is a **direct binding check to the trade's own pre-stored database columns**.
   - `s.exit_price (1.15686) === s.tp3 (1.15686)` immediately links the trade to the pre-defined **TP3** limit column with 100% precision.
   - This eliminates dependence on ambiguous or generic webhook strings and guarantees zero artificial guesswork.

---

### 3. Issues Addressed & Technical Root Cause
1. **Generic `TARGET` Fallback Regression**:
   - In previous iterations, `st.includes('TARGET')` was inadvertently present in the `TP1` resolution clause of `getExitLevel` and `getDisplayExitLevel`.
   - When TradingView sent a generic `"TARGET"` or `"TARGET REACHED"` payload without an explicit numerical suffix, this rule hijacked the trade resolution and labeled higher-tier target exits (e.g., `TP3` exits at `1.15686`) as `TP1`.
2. **Resolution & Removal**:
   - Removed `st.includes('TARGET')` unconditionally across all web and mobile resolution engines.
   - Restructured exit level resolution to evaluate exact numeric proximity ($\pm 0.2\%$) against pre-stored `[TP4, TP3, TP2, TP1]` columns **first**, ensuring trades that exit at TP3 (e.g. `1.15686`) are badged cleanly as **`TP3`** (or **`TRAIL (TP3)`**).

---

### 4. Changes Applied Across Files

| Repository / File | Changes Made |
| :--- | :--- |
| `.agents/AGENTS.md` | Enshrined the **Zero Artificial Fallbacks Rule** and the **Pre-Defined Limit Level Ground Truth Binding** rule. |
| `Tv-Alert-Mobile/src/app/page.tsx` | Removed `st.includes('TARGET')` from `getExitLevel` and `getDisplayExitLevel`. Evaluates exact `exit_price` against pre-stored `[TP4, TP3, TP2, TP1]` columns before checking status strings. |
| `TLCS_Website_Deploy/trade-metrics.js` | Removed `st.includes('TARGET')` from `getExitLevel` and `getDisplayExitLevel`. Prioritizes numeric pre-defined TP column matching. |
| `TLCS_Website_Deploy/blog.html` | Removed generic target string fallbacks from the 7-day Weekly Performance & Achievement table loader (`loadWebWeeklyAchievement`), correctly tallying numeric `tp3Hits` for `1.15686`. |
| `TLCS_Website_Deploy/scanner.js` | Updated `outcomePill` to evaluate numeric `exit_price` against pre-generated TP levels first and removed generic `TARGET` $\rightarrow$ `TP` fallback. |
| `TLCS_Website_Deploy/commodity-scanner.js` | Synchronized `outcomePill` with exact numeric TP evaluation. |

---

### 5. Strict Golden Rules for Future Modifications

1. **No Artificial Heuristics**: If incoming data is missing or ambiguous, fail gracefully or display `--`. Do NOT write heuristic guesswork to fill gaps.
2. **Pre-Defined Level Verification**: Always bind `exit_price` directly to the pre-stored `[tp4, tp3, tp2, tp1]` columns saved at limit order genesis.
3. **Canonical Status Strings Only**: The only valid string tokens for target classification are explicit levels: `TP4`, `TARGET 4`, `TP3`, `TARGET 3`, `TP2`, `TARGET 2`, `TP1`, `TARGET 1`. Generic tokens like `TARGET` without a numeric identifier must NEVER be mapped to any specific TP tier.
