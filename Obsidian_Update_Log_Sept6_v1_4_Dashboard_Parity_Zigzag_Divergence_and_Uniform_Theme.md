# Version 1.4 Release: Full Dashboard Parity, Zigzag Divergence Engine & Uniform Matrix Aesthetics

**Release Date:** September 6, 2026  
**Milestone Version:** `v1.4` (Production Release)  
**Components Affected:** `TV Indicator/TLCS_Main_Dashboard_7Day_Matrix.pine`, `TV Indicator/TLCS_Debug_Dashboard.pine`

---

## 1. Release Overview & Objectives

Version 1.4 brings the 7-Day Session Matrix Dashboard and Debug Dashboard to complete 1:1 mathematical and structural agreement, incorporates the authentic multi-swing Zigzag Divergence Engine directly into the dashboard matrices across all monitored symbols, and upgrades the visual presentation with uniform, high-contrast table styling.

---

## 2. Key Architectural Enhancements

### A. 1:1 Main vs. Debug Dashboard Engine Parity
- **Unified Engine Calculations**: Aligned all signal definitions (Candlestick Reversals, Day Type Blueprints, Trade Sequences, and Divergences) between `TLCS_Main_Dashboard_7Day_Matrix.pine` and `TLCS_Debug_Dashboard.pine`.
- **Zero Ambiguity Across Tools**: When a signal or blueprint triggers on any symbol (e.g. `▲ NG`, `▼ SI`), both the Main 7-Day Matrix and the Debug Dashboard display the exact same detection output without discrepancies.

### B. Authentic Zigzag Divergence Engine Integration
- Integrated the authentic Zigzag Divergence Engine directly into both dashboard scripts.
- **Oscillator Selection**: Full support for RSI, CCI, CMO, COG, MFI, ROC, Stochastics, and WPR.
- **Price & Hidden Divergences**: Both Regular Price Divergences (`bullDiv`, `bearDiv`) and Hidden Divergences (`bullHDiv`, `bearHDiv`) are evaluated across the lookback horizon and properly packed into signal bitmasks.

### C. Isolated Per-Symbol Security Executors
- Wrapped signal and sequence logic into 9 dedicated per-symbol calculation pipelines (`f_calc_sigs_1..9` and `f_calc_dt_1..9`).
- **Eliminated State Contamination**: Pine Script series functions and state machine variables (`SeqState`) are strictly partitioned per symbol context, preventing cross-symbol state bleeding across multi-day sequences.

### D. Uniform Left-to-Right Row Background Styling
- **Removal of Pitch-Black Data Cells**: Extended the left-side label background color (`c_label_bg`) uniformly across all 7 daily matrix columns (`cellBg = c_label_bg`).
- **High-Contrast Typography**:
  - **Bullish Signals (`▲`)**: Crisp dark emerald green (`color.rgb(0, 130, 0)`), providing >4.8:1 WCAG contrast on cream/light backgrounds.
  - **Bearish Signals (`▼`)**: Deep bold crimson red (`color.rgb(204, 0, 0)`).
  - **Mixed Signals (`▲▼`)**: Bold dark amber (`color.rgb(190, 85, 0)`).
  - **Empty Cells (`-`)**: Clean, muted slate gray (`color.rgb(120, 120, 120)`).

---

## 3. Verification & Validation

- Both indicators compiled and verified in Pine Script v6.
- Tested on live charts across NYMEX/COMEX symbols (`GC1!`, `SI1!`, `CL1!`, `NG1!`) and domestic indices (`NIFTY1!`).
- Confirmed full table rendering with uniform row backgrounds and accurate historical cell population.
