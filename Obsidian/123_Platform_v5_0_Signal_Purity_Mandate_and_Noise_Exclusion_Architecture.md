# 123: Version 5.0 Signal Purity Mandate & Complete Noise / News Exclusion Architecture

**Date**: November 24, 2026  
**Status**: APPROVED & INSTITUTIONALIZED (v5.0)  
**Modules**: `algo_engine/`, `Tv-Alert-Mobile/src/app/page.tsx`, `RemoteURL/page.tsx`, `page.tsx`, `AGENTS.md`

---

## 1. Executive Summary & Institutional Directive

Per strict institutional user directive:
> *"The Confluence setup (⚡ purple circled icon at the bottom). This is a news icon and not a part of the signal. Request to follow only the signal logics for alerts generation and do not incorporate noise into it as it corrupts. Be pure in thinking and implementation."*
> *"NATURALGAS: Evaluates to [] (0 signals) across the 5 core swing strategies because it only had a standalone Camarilla touch icon on the daily chart, with no Missile, Scalp, Lightning, Extreme Reversal, or Divergence trigger. Make sure Naturalgas is properly excluded from Swing Trading Opportunities because it has no eligible swing strategy trigger. Make sure you do not accept anything artificial over our basic code logics. Push these changes on application version v5.0."*

This document formalizes the **Zero-Noise Purity of Signal Logics Mandate** across all quantitative signal engines, scanners, Pine Script indicators, and database pipelines.

---

## 2. Root Cause Analysis: Platform News Widgets vs Indicator Signals

### 2.1 The Identification of Visual Noise
On TradingView charts, timeline markers along the bottom date axis display platform events:
- **Purple circled `⚡`**: Represents **Dow Jones Newswires** headline updates (e.g. *"U.S. Natural Gas Futures Sink on Milder Weather Outlook — Market Talk"*).
- **Blue circled `->`**: Represents session splits, market rollovers, and corporate dividend events.

These markers are third-party news widgets native to TradingView's timeline axis, entirely independent of the Pine Script charting canvas and quantitative indicator logic. Interpreting them as trading signals or confluence setups corrupts quantitative models with external narrative noise.

### 2.2 Mathematical Signal Evaluation: CRUDEOIL vs NATURALGAS
To prove the purity of our system, both assets were evaluated against the Python BlackBox scanner (`DailyBlackboxScanner(market='mcx')`) using DhanHQ daily historical candles:

1. **`CRUDEOIL` (`CRUDEOIL1!`)**:
   - Evaluates to: **`['DHAN_MCX_CRUDEOIL_2026-11-23_SHORT_MISSILE_1D']`**.
   - Verified on TradingView chart: Clear red downward trend arrow with target limits at `7921`, `7648`, and `6736`.
   - **Status**: Authentically qualifies under **`🚀 MISSILE`** (Count: 1).

2. **`NATURALGAS` (`NATURALGAS1!`)**:
   - Evaluates to: **`[]` (0 signals)** across all 5 core swing execution strategies.
   - On the chart: Only features a standalone Camarilla touch-point green triangle (`▲`) with day type `TYPICAL DAY, TRADING RANGE, SIDEWAYS` and trend `CONFIRMED BEARISH`.
   - **Status**: **Properly and completely excluded** from Swing Trading Opportunities on the INSIGHTS tab.

---

## 3. Database Purge & Integrity Actions

1. **Purge of Noise Record**:
   - Spurious historical webhook record `68e9fe8f-8e81-4872-8e51-dc8216089ecd` (`NATURALGAS1!` short trade triggered by news icon misinterpretation) was permanently deleted from the Supabase `signals` table.
2. **Authentic Active Orders Retained**:
   - `signals`: `CL1!` (NYMEX Crude 15m), `CRUDEOIL1!` (MCX Crude 1D Short Missile).
   - `shadow_signals`: `AXISBANK` (NSE Stocks 1D Long Missile), `ADANIPORTS` (NSE Stocks 1D Long Missile).
   - Zero unverified or noise-generated assets exist in the database.

---

## 4. The 5 Core Swing Execution Strategies (INSIGHTS Tab)

Under `🎯 SWING TRADING OPPORTUNITIES` / `⚡ DAILY TF SIGNALS ( '1D' TIME FRAME)`:
- **Confluence (`⚡ CONFLUENCE` / `FIRE`) is permanently removed**.
- Strictly 5 canonical execution strategies are evaluated and rendered:
  1. **Missile** (`🚀 MISSILE`): `CanBuy` / `CanSell`
  2. **Scalp** (`💎 SCALP`): `ScalpBuy` / `ScalpSell`
  3. **Lightning** (`⚡ LIGHTNING`): `CanBuy and ScalpBuy` / `CanSell and ScalpSell`
  4. **Extreme Reversal** (`🔥 EXT REV`): `Elongsignal` / `Eshortsignal`
  5. **Divergence** (`🎯 REGULAR DIV` / `🔍 HIDDEN DIV`): Quantitative RSI/Price divergence

---

## 5. System-Wide Governance & Repository Sync

- **Rules Enshrined**: Mandate committed to [`AGENTS.md`](file:///Users/vishant/Documents/Project/AGENTS.md) and [`.agents/AGENTS.md`](file:///Users/vishant/Documents/Project/.agents/AGENTS.md).
- **Code Mirrors**: Synchronized across `Tv-Alert-Mobile/src/app/page.tsx`, `RemoteURL/page.tsx`, `page.tsx`, and `Project Backup/`.
- **Release Version**: Standardized at Version 5.0 (`v5.0` / `5.0.0`) across all repositories.
