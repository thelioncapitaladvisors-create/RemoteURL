# Version 1.2 Production Release: Analytics Performance Tables Optimization & Calmar Ratio Integration

**Release Date:** September 10, 2026  
**Milestone Version:** `v1.2` (Production Master)  
**System Components Affected:** `Tv-Alert-Mobile/src/app/page.tsx`, `Tv-Alert-Mobile`  

---

## 1. Summary of Changes & Architecture Upgrades

This release optimizes the data presentation and analytical depth of the Mobile Application (`Tv-Alert-Mobile`), specifically within the **ANALYTICS** tab, establishing visual parity with the design standards of the **INSIGHTS** and **HUB** modules.

### A. "This Week's Signal Performance" Table Optimization
1. **Removal of Targets Column**:
   - The legacy `Targets` column (previously occupying 20% of horizontal space) was removed from the 7-day day-wise matrix.
   - Subtitle updated to: *"Day-wise signal volume, win rate, and realized percentage return for the last 7 calendar days."*
2. **Spacious 5-Column Geometry (100% Mobile Card Width)**:
   - **`Day` (27%)**: Left-aligned with generous padding, clearly demarcating `TILL DATE Consolidated` and daily rows (`D1`–`D7`).
   - **`Sigs` (27%)**: Centered trade volume with complete breakdown `({Total} ({Wins}W/{Losses}L)` without text truncation or ellipsis (`112 (22W/9...)` completely resolved).
   - **`Win Rate` (18%)**: Dedicated column with high-contrast color coding: Rose (`0.0%`), Amber (`<40%`), Emerald (`≥40%`).
   - **`Net` (14%)**: Realized daily percentage return with proper sign prefixes. Fixed the `+-0.00%` edge case.
   - **`Avg` (14%)**: Average trade return percentage.
3. **Breathing Room & Typography**:
   - Expanded row vertical padding from cramped `py-1.5` to generous `py-2.5`.
   - Crisp column borders (`border-r border-black/5 dark:border-white/5`) and smooth row hover states.

---

### B. "Weekly Performance Edge" Table: Calmar Ratio Integration
1. **Integration of Dedicated Calmar Ratio Column**:
   - Added `Calmar` column to both the `CUMULATIVE` rollup row and individual weekly rows.
2. **Dynamic Mathematical Computation**:
   - **Cumulative Row**: Evaluates cumulative equity run-up, peak-to-trough max drawdown, and calculates $\text{Calmar} = \frac{\text{Net Edge}}{\text{Max Drawdown}}$.
   - **Weekly Rows**: Filters closed signals belonging to each calendar week, computes chronological intra-week drawdown, and derives each week's realized Calmar ratio.
3. **Harmonized 7-Column Layout**:
   - `Wk` (8%) | `Date` (18%) | `Win Rate` (18%) | `Net Edge` (16%) | `PF` (12%) | `Calmar` (14%) | `Kelly` (14%).
4. **Semantic Color Palette**:
   - `Calmar`: Emerald (`≥1.0` or `MAX`), Rose (`<0.0`), Dim (`0.00`).
   - `Profit Factor`: Emerald (`≥1.5`), Amber (`≥1.0`), Rose (`<1.0`).
   - `Win Rate`: Rose (`0.0%`), Amber (`<40%`), Emerald (`≥40%`).
   - `Kelly %`: Amber / Emerald (`>0`), Rose (`<0`).

---

### C. Universal Design System & Cross-Tab Parity
- Verified font family consistency: `font-mono` across all performance numbers, data tables, and metrics.
- Verified visual skin compatibility: Complete dark, light, `theme-lion` (obsidian/gold), and `theme-gray` (slate) support across all tables.
- All table cards employ `.wc-table-card` glassmorphism and `.wc-table-thead` styling.

---

---

### D. Website & Mobile Trade Distribution 100% Mathematical Parity
1. **Root Cause Analysis**:
   - In `Tv-Alert-Mobile/src/app/page.tsx`, `isSignalActiveForMarket` checked entry time `getSignalTime(s)` when filtering closed trades for `todayClosedSignals`. Multi-session trades (Crypto, Forex, NYMEX) entered yesterday that realized P&L and exited today were erroneously excluded from today's closed trades.
   - In `TLCS_Website_Deploy/blog.html`, `filterSignalsByTimeframe` checked realized closure timestamp `s.exit_at || s.signal_ts || s.created_at`.
   - In `dedupeSignals`, the minute key was previously based on `signal_ts` rather than `real_entry_time`, leading to false collision for distinct execution intervals.
2. **Canonical Timestamp Alignment**:
   - For all closed trades (`resolveOutcome(s) !== 'OPEN'`), both `page.tsx`, `blog.html`, `dashboard.html`, and `trade-metrics.js` now strictly evaluate the realized closure timestamp `exit_at || updated_at || signal_ts || created_at >= startOfToday`.
   - In `Tv-Alert-Mobile/src/app/page.tsx`, `dedupeSignals` uses `getSignalTime(s)` prioritizing `metadata.real_entry_time`.
   - In `TLCS_Website_Deploy/blog.html`, `dedupeSignals` and `isRealTrade` are applied to `cachedDistSignals`.
3. **Confirmed Parity across Website & Mobile**:
   - **Total Closed Trades Today**: `24` (`5 Wins · 16 Losses · 3 Breakeven`).
   - **Win Rate**: `20.8%`.
   - **Profit Factor**: `1.81`.
   - **Net Realized %**: `+5.97%`.
   - **Net Realized P&L**: `+₹6.0 k`.
   - **WEEK rolling window (7-day)**: Identical 129 closed trades (`+9.64%` net).

---

## 2. Verification & Validation

- **Client-Side Build**: Verified Next.js compilation in `Tv-Alert-Mobile` (`✓ Compiled successfully`, static pages generated with 0 errors).
- **Parity Verification**: Verified through diagnostic script matching Supabase data across both engines. Both engines yield exact 24 trades, 20.8% win rate, and +5.97% net return.
- **Responsive Layout**: Validated 5-column and 7-column table cards on mobile viewport widths (360px–420px). Zero overflow, zero awkward wrapping.
- **Data Integrity**: Verified that `exact_pct` remains the strict single source of truth for all calculations in accordance with Version 1.0 system rules.

