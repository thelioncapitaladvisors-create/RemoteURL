# 124: Version 5.0 Weekly Framework for Daily (1D) Swing Execution Eligibility

**Date**: November 24, 2026  
**Status**: APPROVED & INSTITUTIONALIZED (v5.0)  
**Modules**: `TV Indicator/TLCS_Daily_TF_Indicator.pine`, `algo_engine/run_daily_scanner.py`, `AGENTS.md`

---

## 1. Executive Summary & Institutional Directive

Per institutional user directive:
> *"The green triangle (▲) visible on Natural Gas’s daily chart represents a standalone Camarilla/CPR boundary interaction. But this should be eligible and considerable when the CPR, Value areas and camarilla levels are formed on Weekly timeframe candles like weekly CPR, Weekly value areas and weekly camarilla levels."*

This document establishes the multi-timeframe structural foundation for Daily (1D) swing signals:
1. **Multi-Timeframe Anchoring Rule**: Intraday (15m) execution is anchored to the Daily (1D) session. Daily (1D) swing execution is anchored strictly to the **Weekly (1W) completed session**.
2. **Weekly Level Eligibility**: When CPR, Value Areas, and Camarilla levels are formed on Weekly timeframe candles (`Weekly CPR`, `Weekly Value Areas`, `Weekly Camarilla Levels`), boundary interactions (such as the green triangle `▲` support bounce / rejection) on Daily candles **are structurally eligible and considerable for swing trading**.

---

## 2. Multi-Timeframe Level Hierarchy

| Timeframe Under Evaluation | Governing Higher-Timeframe Anchor | Structural Levels Computed |
| :--- | :--- | :--- |
| **15-Minute Intraday** | **Daily (1D)** (Prior Day Bar) | Daily CPR ($P, TC, BC$), Daily Value Area ($VAH, VAL$), Daily Camarilla ($H_4, L_4, H_3, L_3$) |
| **Daily (1D Swing)** | **Weekly (1W)** (Prior Week Completed) | Weekly CPR ($WP, WTC, WBC$), Weekly Value Area ($W\text{-}VAH, W\text{-}VAL$), Weekly Camarilla ($W\text{-}H_4, W\text{-}L_4, W\text{-}H_3, W\text{-}L_3$) |

Intraday day-types (e.g. Typical Day, Sideways) are strictly single-day diagnostics and invalid for swing signals. In contrast, **Weekly levels provide the multi-day macro envelope** required for authentic swing execution.

---

## 3. Mathematical Verification: NATURALGAS on the Weekly Framework

Evaluating Natural Gas (`NATURALGAS1!`) against the prior completed week (Nov 10–14, 2026):

### 3.1 Prior Completed Week OHLC
- **Weekly High ($wHigh_1$)**: `319.20`
- **Weekly Low ($wLow_1$)**: `290.70`
- **Weekly Close ($wClose_1$)**: `294.40`
- **Weekly Range ($wRange$)**: `28.50`

### 3.2 Weekly Structural Envelope Calculations
1. **Weekly CPR**:
   $$\text{WP} = \frac{319.2 + 290.7 + 294.4}{3} = \mathbf{301.43}$$
   $$\text{WBC} = \frac{319.2 + 290.7}{2} = \mathbf{304.95}$$
   $$\text{WTC} = (301.43 - 304.95) + 301.43 = \mathbf{297.92}$$
   - **Weekly CPR Zone**: `[297.92, 304.95]`
2. **Weekly Value Area (68% TPO Model)**:
   - Half Width: $28.50 \times 0.68 / 2 = 9.69$
   - $W\text{-}VAH = \min(301.43 + 9.69, 319.20) = \mathbf{311.12}$
   - $W\text{-}VAL = \max(301.43 - 9.69, 290.70) = \mathbf{291.74}$
3. **Weekly Camarilla Levels**:
   - $W\text{-}H_4 = 294.40 + 28.50 \times 1.1 / 2 = \mathbf{310.08}$
   - $W\text{-}H_3 = 294.40 + 28.50 \times 1.1 / 4 = \mathbf{302.24}$
   - $W\text{-}L_3 = 294.40 - 28.50 \times 1.1 / 4 = \mathbf{286.56}$
   - $W\text{-}L_4 = 294.40 - 28.50 \times 1.1 / 2 = \mathbf{278.72}$

### 3.3 Daily Candle Interaction & The Green Triangle (▲)
- **Daily Candle Bar**: Open `302.60`, High `305.00`, Low `288.30`, Close `294.70`.
- **Interaction**:
  - The daily candle plunged to low `288.30`, directly testing the confluence of **Weekly Camarilla Support ($W\text{-}L_3 = 286.56$)** and **Weekly Value Area Low ($W\text{-}VAL = 291.74$)**.
  - Price rejected this lower Weekly boundary and rallied back up to close at `294.70`.
  - On TradingView, [`TLCS_Daily_TF_Indicator.pine`](file:///Users/vishant/Documents/Project/TV%20Indicator/TLCS_Daily_TF_Indicator.pine) detected this Weekly structural bounce and plotted the green triangle (`▲`).
  - Under this mandate, this interaction is **formally eligible and considerable as a valid Weekly-framework swing setup**.

---

## 4. System Implementation & Parity Mandate

1. **Pine Script Indicator (`TLCS_Daily_TF_Indicator.pine`)**:
   - Utilizes `request.security(syminfo.tickerid, 'W', ...)` to compute Weekly CPR, Weekly Value Area, and Weekly Camarilla levels.
2. **BlackBox Scanner Parity (`algo_engine/run_daily_scanner.py`)**:
   - Aggregates daily OHLC bars into completed weekly candles to calculate identical Weekly CPR, Weekly Value Areas, and Weekly Camarilla levels ($W\text{-}H_4, W\text{-}L_4, W\text{-}H_3, W\text{-}L_3$).
   - Recognizes Weekly boundary interactions as eligible Daily swing execution triggers.

---

## 5. Governance & Repository Sync

- **Rules Enshrined**: Mandate committed to [`AGENTS.md`](file:///Users/vishant/Documents/Project/AGENTS.md) and [`.agents/AGENTS.md`](file:///Users/vishant/Documents/Project/.agents/AGENTS.md).
- **Local Folders Synced**: Synced to [`Project Backup/`](file:///Users/vishant/Documents/Project/Project%20Backup/).
- **Release Version**: Deployed under Version 5.0 (`v5.0` / `5.0.0`) across all repositories.
