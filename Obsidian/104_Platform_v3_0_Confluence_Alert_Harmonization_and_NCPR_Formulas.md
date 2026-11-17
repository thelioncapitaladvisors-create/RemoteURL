# Platform v3.0: Universal Confluence Alert Harmonization & NCPR Formula Architecture

**Document ID**: 104  
**Date**: November 17, 2026  
**Status**: Production Locked (v3.0)  
**Author**: Antigravity Quantitative AI Architecture Team  

---

## 1. Executive Summary

Per direct user instruction under Version 3.0:
1. **Universal Naming Harmonization**: Renamed all user-facing and backend references of **"Fire" / "FIRE" / "Hi-Pro Alert"** to **"Confluence" / "CONFLUENCE" / "Confluence Alert"** across the mobile terminal frontend, serverless webhook dispatchers, Python BlackBox algo engine, Telegram notification channels, and TradingView Pine Script indicators.
2. **Historical NCPR Formula Retrieval**: Audited the Obsidian architectural knowledge base to locate earlier implementations of Narrow Central Pivot Range (NCPR) and analyzed their mathematical behavior against asset price variations.

---

## 2. Historical NCPR Formulas Retrieved from Obsidian

### 2.1 Formula 1: Legacy Absolute Price Percentage
- **Source**: `Obsidian/16_Master_TradingView_Indicator_TLCS_PivotBoss.md` (Line 733)
- **Mathematical Definition**:
  $$\text{Width} = |\text{TC} - \text{BC}| = |2P - 2\text{BC}| = 2 \cdot |DPi - DBcf|$$
  $$\text{NCPR} = \left(\frac{2 \cdot |DPi - DBcf|}{DPi} \times 100\right) < 0.2\%$$
- **Mechanism**: Required the absolute CPR width to be strictly less than 0.2% of the pivot price.
- **Why It Failed**: As noted in the codebase, dividing by the absolute pivot price DPi causes severe distortion across different asset classes. For high-priced assets (like Bitcoin or Nifty), a normal daily oscillation produces a large absolute point spread that easily exceeds 0.2%, while for low-priced assets (like Penny Stocks or Natural Gas futures), the threshold behaves inconsistently.

### 2.2 Formula 2: Normalized Previous-Day-Range Ratio
- **Source**: `Obsidian/12_Platform_V5_0_DhanHQ_BlackBox_Master_PineScript_Engine_and_ZeroGhost_Parity.md` (Line 29)
- **Mathematical Definition**:
  $$\text{PrevDayRange} = \max(\text{DH} - \text{DL}, \text{mintick})$$
  $$\text{CPR Width} = |\text{DTC} - \text{DBC}|$$
  $$\text{NCPR} = \left(\frac{\text{CPR Width}}{\text{PrevDayRange}} \times 100\right) < 5.0\%$$
- **Mechanism**: Expresses CPR width as a percentage of the prior day high-to-low range (DH - DL). When CPR width is under 5% (or an adaptable threshold like 10%) of the prior day range, the day is classified as an NCPR day.

### 2.3 Mathematical Analysis of Proposed $|(2C - H - L)/3|$ & 14-Day Rolling Relative Average
- **Algebraic Derivation**:
  $$P = \frac{H + L + C}{3}, \quad BC = \frac{H + L}{2}, \quad TC = 2P - BC$$
  $$\text{Width} = |TC - BC| = |2P - 2BC| = \left| 2\left(\frac{H+L+C}{3}\right) - (H+L) \right| = \left| \frac{2C - H - L}{3} \right|$$
- **Key Insight**: The CPR width is strictly a function of the distance between the close ($C$) and the midpoint of the range ($\frac{H+L}{2}$). When $C = \frac{H+L}{2}$, CPR width is mathematically zero (a Single Line CPR).
- **The Rolling 14-Day Average Solution**:
  $$\text{CPR\_Width}_{14\text{-EMA}} = \text{ta.sma}(\text{cprWidth}, 14)$$
  $$\text{NCPR} = \text{cprWidth} \le 0.5 \times \text{CPR\_Width}_{14\text{-EMA}}$$
  Comparing today CPR width against the asset own trailing 14-day average dynamically normalizes across all asset classes (Equities, Forex, Crypto, MCX commodities) without arbitrary hardcoded percentage cliffs.

### 2.4 Implementation of Recommended 14-Day Trailing Relative Normalized NCPR Formula
- **Adopted Formula**:
  $$\text{cprWidth} = |\text{TC} - \text{BC}| = \left| \frac{2C - H - L}{3} \right|$$
  $$\text{cprWidthAvg14} = \text{SMA}_{14}(\text{cprWidth})$$
  $$\text{NCPR} = \text{cprWidth} \le (0.50 \times \text{cprWidthAvg14})$$
- **Cross-Asset Dynamic Normalization**:
  Comparing each asset's CPR width against its own trailing 14-day historical mean completely eliminates hardcoded arbitrary point or percentage thresholds. Low-volatility equities, crypto pairs, and commodities are each measured against their own intrinsic volatility baseline.
- **Pine Script Daily SMA Security Architecture**:
  Calling `ta.sma(cprWidth, 14)` directly on an intraday 5m or 15m chart averages 14 intraday candles of the same session (`cprWidthAvg14 == cprWidth`). Passing `math.abs((2.0 * close[1] - high[1] - low[1]) / 3.0)` to `request.security(syminfo.tickerid, 'D', ta.sma(...), lookahead = barmerge.lookahead_on)` guarantees that the 14-day rolling average is computed across 14 completed daily sessions.
- **Python BlackBox Engine (`pivots.py`)**:
  `compute_cpr` and `compute_daily_levels` updated in both `algo_engine/pivots.py` and `RemoteURL/algo_engine/pivots.py` to accept `cpr_width_avg14: Optional[float] = None` and evaluate `is_narrow = width <= (0.50 * cpr_width_avg14)`.
- **DhanHQ Background Scanner (`dhan-scanner-background.js`)**:
  Updated `fetchDailyLevels` to compute `cprWidthAvg14` across the trailing 14 daily candles, and updated `computeCPR` / `computeDualCPR` to evaluate `isNarrow = (avg14 && avg14 > 0) ? (cprWidth <= 0.50 * avg14) : (ncprPct < 5.0)`.

---

## 3. Confluence Alert Harmonization: Implementation Details

### 3.1 Mobile Terminal Frontend (`Tv-Alert-Mobile/src/app/page.tsx`)
- **Table Row Badges**: Standardized to `CONFLUENCE BULL` / `CONFLUENCE BEAR` (formerly `FIRE BULL` / `FIRE BEAR`).
- **Setup Cards & Chips**: Updated sub-tab chip to `⚡ Confluence Alert` / `Confluence` and filter button to `⚡ ALL CONFLUENCE`.
- **Setup Matrix**: Category renamed to `Confluence Alert` with badge `CONF` / `CONFLUENCE ALERT`.
- **Detail Modal**: Updated header and playbooks to `BULLISH CONFLUENCE ALERT (CANONICAL CONFLUENCE OUTSIDE GREEN/RED)`.
- **Dual Compatibility**: `isFireAlertSignal()` enhanced to recognize both legacy `fire_alert` / `FIREZONE` tags and new `confluence` / `CONFLUENCE` triggers.
- **Default Live Expanded State**:
  - `isDhanLiveActionOnly` initialized to `true` by default, presenting live and active limit orders on terminal load.
  - `defaultSetupTab` dynamically resolves the first setup tab containing active live or active limit signals (prioritizing `FIRE` -> `DIV` -> `OOR` -> `NCPR` -> ...).
  - `effectiveActiveTab` auto-expands the live setup table while permitting manual collapse via `'COLLAPSED'`.

### 3.2 Backend Webhooks & Telegram Notifications
- **`Tv-Alert-Mobile/src/app/api/webhook/route.ts`**:
  - Header: `⚡ *TLCS CONFLUENCE ALERT* — *${marketName}*`
  - Field: `⚡ *Confluence Zone*: ${zoneStr} (Neutral / Outside Green & Red)`
- **`TLCS_Website_Deploy/netlify/functions/process-webhook-background.js`**:
  - Header: `⚡ *TLCS CONFLUENCE ALERT* — *${marketName}*`
- **`algo_engine/telegram_dispatcher.py`**:
  - Header: `<b>⚡ TLCS CONFLUENCE ALERT ({mkt})</b>`
  - Field: `<b>Confluence Zone:</b> <code>{fire_zone}</code>`
- **`algo_engine/shadow_pipeline.py` & `RemoteURL/algo_engine/shadow_pipeline.py`**:
  - Allowed execution triggers expanded to include `CONFLUENCE_ALERT` and `CONFLUENCE`.
- **`algo_engine/engine_daemon.py` & `RemoteURL/algo_engine/engine_daemon.py`**:
  - Live log badge updated to `| ⚡ CONFLUENCE_ALERT ({sig.fire_zone})`.

### 3.3 Master Pine Script Indicators
- **Files**:
  - `TV Indicator/TLCS_Live_Pivot_Alerts.pine`
  - `TV_Indicator_Full_Code.txt`
  - `user_code.pine`
- **Changes**:
  - Section 10 title: `10. CONFLUENCE ALERT & DEDICATED WEBHOOK DISPATCHER`
  - Plotshape title: `title = 'Confluence Alert'`
  - Alert condition title: `alertcondition(Fire_Alert, title = 'TLCS Confluence Alert (Any Signal + Zone)', ...)`
  - NCPR implementation:
    ```pine
    daily_cpr_avg14 = request.security(syminfo.tickerid, 'D', ta.sma(math.abs((2.0 * close[1] - high[1] - low[1]) / 3.0), 14), lookahead = barmerge.lookahead_on)
    float prevDayRange = math.max(DH - DL, syminfo.mintick)
    float cprWidth     = math.abs(DTcf - DBcf)
    bool  NCPR         = (daily_cpr_avg14 > 0) ? (cprWidth <= (0.50 * daily_cpr_avg14)) : (5.0 > (cprWidth / prevDayRange) * 100)
    ```
- **Checksum Parity**:
  All three indicator files maintain 100% byte-for-byte SHA256 checksum parity:
  `80bda52bb9b65edb7eb31710ac681bb29d51d767b3dd8d21604e63163afad2dc`

---

## 4. Verification & Testing

- **Unit Tests**: 136 tests ran (`python3 -m unittest discover algo_engine/tests`) -> 135 passed, 1 skipped, 0 failures.
- **Production Build**: Next.js 14 production build (`npm run build` in `Tv-Alert-Mobile`) compiled with 0 errors and generated 8 static routes.
- **Checksum Parity**: SHA256 `80bda52bb9b65edb7eb31710ac681bb29d51d767b3dd8d21604e63163afad2dc` confirmed identical across all indicator files.
- **Backup Parity**: Local mirrors synced to `Project Backup/` and snapshot preserved in `Backups/TLCS_v3.0_Complete_Backup_20261117_223000/`.\n