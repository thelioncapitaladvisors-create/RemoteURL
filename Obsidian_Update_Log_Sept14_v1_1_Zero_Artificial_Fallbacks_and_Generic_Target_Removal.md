# Obsidian Update Log: Version 1.1 (14 Sept 2026)
## Zero Artificial Fallbacks, Generic TARGET Removal & Strict Trade Logic Enforcement

---

### 1. Executive Summary & Core Principle
Version 1.1 strictly eliminates all generic heuristic fallbacks across the web dashboard and mobile terminal, establishing the **Zero Artificial Fallback Rule**:
* **Explicit Trade Logic Only**: No synthetic mappings or heuristic assumptions (such as mapping generic `"TARGET"` strings to `TP1`) are permitted anywhere in the system.
* **Exact Mathematical Evaluation Priority**: Trade exits are determined strictly through exact numerical matching between `exit_price` and pre-generated target levels (`[TP4, TP3, TP2, TP1]`), backed exclusively by explicit Pine Script status strings (`Completed TP1..4`, `Hit Initial SL`, `Hit B/E`, `Hit TP1..3 Trailing`, `Hit EMA`, `Divergence Exit`, `EOD Exit`).
* **Permanent Policy**: Nothing beyond the user's explicit trade logic may be introduced without prior knowledge and explicit authorization.

---

### 2. Issues Addressed & Technical Root Cause
1. **Generic `TARGET` Fallback Regression**:
   - In previous iterations, `st.includes('TARGET')` was inadvertently present in the `TP1` resolution clause of `getExitLevel` and `getDisplayExitLevel`.
   - When TradingView sent a generic `"TARGET"` or `"TARGET REACHED"` payload without an explicit numerical suffix, this rule hijacked the trade resolution and labeled higher-tier target exits (e.g., `TP3` exits at `1.15686`) as `TP1`.
2. **Resolution & Removal**:
   - Removed `st.includes('TARGET')` unconditionally across all web and mobile resolution engines.
   - Restructured exit level resolution to evaluate exact numeric proximity ($\pm 0.2\%$) against `[TP4, TP3, TP2, TP1]` **first**, ensuring trades that exit at TP3 (e.g. `1.15686`) are badged cleanly as **`TP3`** (or **`TRAIL (TP3)`**).

---

### 3. Changes Applied Across Files

| Repository / File | Changes Made |
| :--- | :--- |
| `.agents/AGENTS.md` | Enshrined the **Zero Artificial Fallbacks Rule**: strict prohibition on uninstructed heuristics, synthetic string fallbacks, or artificial guessing. |
| `Tv-Alert-Mobile/src/app/page.tsx` | Removed `st.includes('TARGET')` from `getExitLevel` and `getDisplayExitLevel`. Evaluates exact `exit_price` against `[TP4, TP3, TP2, TP1]` before evaluating status strings. |
| `TLCS_Website_Deploy/trade-metrics.js` | Removed `st.includes('TARGET')` from `getExitLevel` and `getDisplayExitLevel`. Prioritizes numeric exit price matching. |
| `TLCS_Website_Deploy/blog.html` | Removed generic target string fallbacks from the 7-day Weekly Performance & Achievement table loader (`loadWebWeeklyAchievement`), correctly tallying numeric `tp3Hits` for `1.15686`. |
| `TLCS_Website_Deploy/scanner.js` | Updated `outcomePill` to evaluate numeric `exit_price` against pre-generated TP levels first and removed generic `TARGET` $\rightarrow$ `TP` fallback. |
| `TLCS_Website_Deploy/commodity-scanner.js` | Synchronized `outcomePill` with exact numeric TP evaluation. |

---

### 4. Strict Golden Rules for Future Modifications

1. **No Artificial Heuristics**: If incoming data is missing or ambiguous, fail gracefully or display `--`. Do NOT write heuristic guesswork to fill gaps.
2. **Exact Mathematical Level Matching**: Always evaluate `exit_price` directly against the true mathematical target levels (`tp4`, `tp3`, `tp2`, `tp1`) rather than relying on loose string tokens.
3. **Canonical Status Strings Only**: The only valid string tokens for target classification are explicit levels: `TP4`, `TARGET 4`, `TP3`, `TARGET 3`, `TP2`, `TARGET 2`, `TP1`, `TARGET 1`. Generic tokens like `TARGET` without a numeric identifier must NEVER be mapped to any specific TP tier.
