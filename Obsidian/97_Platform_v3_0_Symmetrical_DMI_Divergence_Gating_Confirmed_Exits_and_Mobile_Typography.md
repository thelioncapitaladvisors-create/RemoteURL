# 97. Platform v3.0: Symmetrical DMI Directional Momentum Gating for Divergences, Confirmed-Only Divergence Exits & Mobile Metric Pill Layout Optimization

**Date:** November 14, 2026  
**Status:** Canonical Production Baseline & Algorithmic Parity Release  
**Preceding Baseline:** Note 96 (Platform v3.0 Option Chain Close Day Sync, Static Pinned Symbol Headers & Real-Time Supabase WebSocket Feeds)  
**Repositories:** Master Pine Script (`TLCS v3.0`), `algo_engine`, `TLCS_Website_Deploy`, `Tv-Alert-Mobile`, Root Workspace  

---

## 1. Executive Summary

In response to production trading audits and mobile terminal usability reviews, three major algorithmic and UI enhancements were implemented under Platform v3.0 across all execution environments:

1. **Symmetrical DMI Directional Momentum Gating for Regular Divergence ($D$)**:
   - **Long Regular Divergence ($D$)**: Strictly blocked from generating new trade signals when **`minus > plus`** ($DI^- > DI^+$). Prevents counter-trend bottom-fishing entries during dominant bearish momentum selloffs (such as the BTCUSDT 15m downtrend).
   - **Bearish Regular Divergence ($D$)**: Symmetrically blocked from generating new trade signals when **`plus > minus`** ($DI^+ > DI^-$). Prevents counter-trend top-fishing entries during dominant bullish momentum rallies.
   - **Cross-Engine Parity**: Applied identically across Master Pine Script (`TLCS v3.0`), Python BlackBox (`StrategyEngine`), and autonomous DhanHQ Netlify background scanners (`dhan-scanner-background.js`).

2. **Confirmed-Only Divergence Exit Hardening**:
   - Live trades previously exited prematurely on unconfirmed Bar 0 divergences.
   - Excised immediate `isRegularDivExit` triggers; all divergence exits are now strictly gated to `isConfirmedDivExit`, requiring a 1-bar prior divergence (`[1]`) AND subsequent directional confirmation candle close (`(close > open and close > close[1])` for bullish confirmation close, `(close < open and close < close[1])` for bearish confirmation close).

3. **Mobile 5-Column Metric Pill Typography & Missing Sortino Restoration**:
   - Created dedicated responsive typography classes (`.metric-pill-label` and `.metric-pill-val`) in `globals.css` that override the micro-font floor specifically for narrow 5-column metric grids on mobile screens ($\le 430\text{px}$).
   - Enabled graceful two-word wrapping (`white-space: normal !important`, negative tracking) so labels like `PROFIT FACTOR`, `CALMAR RATIO`, `HALF-KELLY %`, and `SORTINO RATIO` fit neatly within ~60px–72px pill boundaries without clipping or text collision.
   - Restored the missing value display `<span>` for `Sortino Ratio` in the Market-Wise sections of the mobile terminal.

---

## 2. Technical Architecture & Implementation

### A. Master Pine Script Indicators (`TLCS v3.0`)
- **Files**:
  - `TV Indicator/TLCS_Live_Pivot_Alerts.pine`
  - `TV_Indicator_Full_Code.txt`
  - `user_code.pine`
- **Directional Gating Logic**:
  ```pinescript
  // Regular Divergence strictly requires subsequent directional confirmation candle close (zero unconfirmed entries)
  // Version 3.0: Symmetrical DMI Directional Filter (Avoid Long D when minus > plus, avoid Short D when plus > minus)
  bool confirmedRegBull = inWindowRegBull and isBullishConfirmCandle and not (minus > plus) and (na(lastFiredRegBullBar) or lastFiredRegBullBar < lastRegBullDivBar)
  bool confirmedRegBear = inWindowRegBear and isBearishConfirmCandle and not (plus > minus) and (na(lastFiredRegBearBar) or lastFiredRegBearBar < lastRegBearDivBar)

  // 2. Regular Divergence Signals (Standalone Strategy - Confirmed on candle close, exempt from day types, NCPR and H4/L4 gating)
  // Version 3.0: Symmetrical DMI Directional Filter
  bool DivergenceBuy  = confirmedRegBull and not (minus > plus)
  bool DivergenceSell = confirmedRegBear and not (plus > minus)
  ```
- **Checksum Parity**:
  All three indicator source files maintain 100% byte-for-byte SHA256 checksum parity:
  `e4caa5a28359a6be56b2d1b51e0936b6cb0d1709c5282046801216bfd04253f2`.

### B. Python BlackBox Engine (`algo_engine/strategies.py`)
- Symmetrically filtered `confirmed_reg_bull` and `confirmed_reg_bear`:
  ```python
  # Confirmed triggers on CLOSE of confirmation candle:
  # Regular Divergence strictly requires subsequent directional confirmation candle close (zero unconfirmed entries)
  # Version 3.0: Symmetrical DMI Directional Filter (Avoid Long D when minus > plus, avoid Short D when plus > minus)
  confirmed_reg_bull = in_win_reg_bull and is_bull_confirm and not (ctx.minus > ctx.plus) and (self._last_fired_reg_bull_bar is None or self._last_fired_reg_bull_bar < self._last_reg_bull_div_bar)
  confirmed_reg_bear = in_win_reg_bear and is_bear_confirm and not (ctx.plus > ctx.minus) and (self._last_fired_reg_bear_bar is None or self._last_fired_reg_bear_bar < self._last_reg_bear_div_bar)

  # 3. Regular Divergence (Standalone Strategy - Confirmed on candle close, exempt from day types, NCPR, and H4/L4 gating)
  # Version 3.0: Symmetrical DMI Directional Filter
  divergence_buy = confirmed_reg_bull and not (ctx.minus > ctx.plus)
  divergence_sell = confirmed_reg_bear and not (ctx.plus > ctx.minus)
  ```

### C. Autonomous DhanHQ Background Scanner (`dhan-scanner-background.js`)
- Enforced DMI directional momentum filter:
  ```javascript
  // Divergence strategies are exempt from dayAllowed and H4/L4 gating (confirmed on candle close)
  // Version 3.0: Symmetrical DMI Directional Filter (Avoid Long D when minus > plus, avoid Short D when plus > minus)
  const DivergenceBuy = Boolean(regBullDiv) && !(minus > plus);
  const DivergenceSell = Boolean(regBearDiv) && !(plus > minus);
  ```

### D. Mobile Typography & Zero Spillover (`globals.css` & `page.tsx`)
- Configured `.metric-pill-label` with responsive font progression (`7.5px` at $<360\text{px}$, `8px` at $\ge 360\text{px}$, `8.5px` at $\ge 400\text{px}$, `10px` at $\ge 640\text{px}$), tight line height (`1.15`), and `white-space: normal !important`.
- Applied across all 10 cards in **Today's Signal Performance** and 10 cards in **Market-Wise Sections**.
- Added the missing `Sortino Ratio` value span:
  ```tsx
  <span className={`font-black font-mono metric-pill-val ${mSortinoNum != null ? (mSortinoNum >= 0 ? 'text-cyan-600 dark:text-cyan-400' : 'text-rose-600 dark:text-rose-400') : 'text-dim'}`}>{mSortinoDisp}</span>
  ```

---

## 3. Automated Test Suite & Verification Results

Executed full pytest discovery across `algo_engine/tests`:
```bash
pytest algo_engine/tests/ -v
================== 135 passed, 1 skipped, 1 warning in 1.58s ===================
```
- `test_regular_divergence_symmetrical_dmi_filter`: PASSED (confirms Long D blocked when `minus > plus`, Short D blocked when `plus > minus`).
- `test_hidden_divergence_symmetrical_dmi_filter`: PASSED (confirms Long H blocked when `minus > plus`, Short H blocked when `plus > minus`).
- `test_regular_divergence_exit_requires_confirmation_bar0_eliminated`: PASSED (confirms Bar 0 regular divergence exit elimination).
- Zero regressions across the entire algorithmic suite.
