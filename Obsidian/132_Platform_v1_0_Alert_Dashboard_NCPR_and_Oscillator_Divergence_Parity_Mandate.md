# 132. Platform v1.0: Alert Dashboard Narrow CPR (NCPR) & Oscillator Divergence Parity Mandate

**Effective Date**: November 26, 2026  
**Status**: ACTIVE PRODUCTION MANDATE & ARCHITECTURAL RELEASE  
**Canonical Version**: v1.0 (`v1.0.0`)  
**Scope**: Pine Script Alert Dashboard (`TV Indicator/TLCS_Main_Dashboard_7Day_Matrix.pine`, `RemoteURL/TV Indicator/TLCS_Main_Dashboard_7Day_Matrix.pine`), Webhook Alert Payloads (`SessionOpenMatrix`), Oscillator Mathematical Parity (`TLCS_Native_Oscillator.pine`).

---

## 1. Executive Summary & Problem Definition

In Version 1.0, the **TLCS ALERTS DASHBOARD** (`TLCS_Main_Dashboard_7Day_Matrix.pine`) serves as the core 7-day multi-asset intelligence matrix monitoring 9 high-liquidity instruments:
1. `NSE:NIFTY`
2. `NSE:BANKNIFTY`
3. `NSE:FINNIFTY`
4. `NSE:MIDCPNIFTY`
5. `MCX:CRUDEOIL1!`
6. `MCX:NATURALGAS1!`
7. `MCX:GOLD1!`
8. `MCX:SILVER1!`
9. `MCX:COPPER1!`

Two critical enhancements were mandated:
1. **Daily CPR & Narrow CPR (NCPR) Integration**:
   - Provide an autonomous daily calculation of the Central Pivot Range ($\text{TC}, \text{BC}, \text{Pivot}$) from the completed Daily bar for all 9 symbols.
   - Detect Narrow CPR days ($\text{CPR Width} < 0.50 \times \text{SMA}(\text{CPR Width}, 14)$) and render them directly in a dedicated 28th row in the 7-day visual matrix.
   - Inject the structured `"cpr"` dictionary into the `SessionOpenMatrix` alert JSON payload to broadcast exact pivot levels directly to webhook handlers and cloud screeners.
2. **Divergence Engine Parity with Oscillator Geometry**:
   - Resolve discrepancies between chart indicator divergence calculations and the native oscillator indicator (`TLCS_Native_Oscillator.pine`).
   - Standardize price pivot evaluation to swing highs and swing lows (`array.from(high, close, low)` instead of close-only arrays) and unconstrain the sentiment divergence formula.

---

## 2. Mathematical Logic & Implementation

### 2.1 Daily Central Pivot Range & Narrow CPR (NCPR) Formulation
For each instrument, CPR levels are computed from the prior completed daily bar (`high[1]`, `low[1]`, `close[1]`):

$$\text{Pivot } (P) = \frac{\text{High}_{t-1} + \text{Low}_{t-1} + \text{Close}_{t-1}}{3.0}$$

$$\text{Bottom Central } (BC) = \frac{\text{High}_{t-1} + \text{Low}_{t-1}}{2.0}$$

$$\text{Top Central } (TC) = (2.0 \times P) - BC$$

$$\text{CPR Width} = |TC - BC|$$

$$\text{AvgWidth}_{14} = \text{SMA}(\text{CPR Width}, 14)$$

A symbol is identified as having a **Narrow CPR** on any day when:
$$\text{isNarrowCPR} = (\text{CPR Width} < 0.50 \times \text{AvgWidth}_{14})$$

### 2.2 Table UI Matrix Row 28
The table is expanded to 28 rows (1 Header + 8 Intraday Strategies + 10 Day-Type Blueprints + 8 Trade Sequences + 1 Narrow CPR Row):
```pinescript
setRow(matrixTable, 27, "📏 Narrow CPR (NCPR)", ncprMatrix, color.orange, color.white)
```

### 2.3 Webhook Alert Payload (`SessionOpenMatrix`)
The `alertPayload` JSON string is enriched with the `"cpr"` dictionary for all 9 universe assets:
```pinescript
string cprJson = "{" +
     '"u1":{"sym":"' + u1 + '","ncpr":' + (u1_ncpr > 0.5 ? "true" : "false") + ',"dtc":' + str.tostring(u1_dtc, format.mintick) + ',"dbc":' + str.tostring(u1_dbc, format.mintick) + ',"dp":' + str.tostring(u1_dp, format.mintick) + ',"cpr_width":' + str.tostring(u1_cpr_w, format.mintick) + '},' +
     ...
     '"u9":{"sym":"' + u9 + '","ncpr":' + (u9_ncpr > 0.5 ? "true" : "false") + ',"dtc":' + str.tostring(u9_dtc, format.mintick) + ',"dbc":' + str.tostring(u9_dbc, format.mintick) + ',"dp":' + str.tostring(u9_dp, format.mintick) + ',"cpr_width":' + str.tostring(u9_cpr_w, format.mintick) + '}' +
     "}"
```

### 2.4 Divergence Engine Parity with `TLCS_Native_Oscillator.pine`
In `f_calc_sigs_impl(...)`:
1. **Price Matrix Input**:
   - Prior code: `divIndicators.add_row(0, array.from(close, close, close))` (evaluated closes, missing wick pivots).
   - Standardized: `divIndicators.add_row(0, array.from(high, close, low))` (swing high for peaks, swing low for troughs).
2. **Sentiment Formula**:
   - `sentiment = math.sign(oscRatio - priceRatio)`
   - `divergence = sentiment < 0 ? 1 : trend != dir and sentiment > 0 ? -1 : 0`

---

## 3. Verification & Parity Audit

1. **Table Rendering**:
   - Table initialized cleanly with dimensions `table.new(pos, 8, 28)`.
   - All 7 historical rolling columns shift seamlessly at `isNewDay`.
2. **Payload Completeness**:
   - Broadcast triggers on daily close (`isDailyClose or barstate.islast`).
   - JSON keys include `matrix_days`, `signals`, and the new `cpr` dictionary.
3. **Repository Sync**:
   - Synchronized across `RemoteURL/TV Indicator/TLCS_Main_Dashboard_7Day_Matrix.pine` and local backup archives.
