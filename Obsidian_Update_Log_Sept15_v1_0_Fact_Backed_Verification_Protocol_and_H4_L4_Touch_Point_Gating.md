# Obsidian Update Log: Version 1.0 (15 Sept 2026)
## Fact-Backed Verification Protocol, H4/L4 Touch-Point Gating & Automated Tearsheet CI/CD Fixes

---

### 1. Overview & Core Enhancements
Version 1.0 establishes strict operational and engineering standards across the TLCS Trading Ecosystem (Pine Script Indicators, Serverless Netlify Pipelines, and GitHub Actions CI/CD):

1. **Strict Fact-Backed Verification Mandate (Zero Speculation Rule)**:
   - Enshrined in `.agents/AGENTS.md`: The AI assistant must never make assertions, diagnose trade executions, or evaluate conditions without first backing claims with verifiable facts (exact source code lines, live database queries, and mathematical calculations).
   - Zero assumptions or verbal generalizations are permitted.

2. **H4 / L4 Limit Touch-Point Gating (`low < H4` / `high > L4`)**:
   - **Problem**: Previously, `longAllowed` and `shortAllowed` evaluated `close < H4` and `close > L4`. On candles where price tested the Camarilla levels or midpoint resistance via wicks but closed beyond the boundary, valid limit orders were improperly blocked on bar close.
   - **Fix**: Linked `longAllowed` & `_buy` strictly to **`low < H4`** and `shortAllowed` & `_sell` strictly to **`high > L4`** across all Pine Script indicator files (`TLCS_Live_Pivot_Alerts.pine`, `TLCS_Dashboards_4_Commodities_Merged.pine`, `TLCS_Dashboards_4_Commodities_Signals.pine`, `raw_input.pine`, and `user_code.pine`).

3. **NCPR Mathematical Proof & Multi-Asset Normalization**:
   - Verified that Narrow CPR (NCPR) is mathematically evaluated using the normalized ratio against yesterday's range ($\text{CPR Width} / \text{PrevDayRange} \times 100 < 5.0\%$) and asset price ($\text{CPR Width} / \text{Pivot} \times 100 < 0.20\%$).
   - On compression days where `NCPR == true`, the sideways day filter is automatically bypassed (`dayAllowed = not isSidewaysDay or NCPR`).

4. **Automated VectorBT Strategy Tearsheet Restoration**:
   - **Fixed Python Template Bug**: Fixed `NameError: name 'html_drawdown' is not defined` in `TLCS_Website_Deploy/generate_tearsheet.py` by restoring correct interpolation of `html_dd` and `html_ret`.
   - **Removed Deployment Suppression**: Removed `[skip ci]` from the commit step in `TLCS_Website_Deploy/.github/workflows/generate_tearsheet_cron.yml` so Netlify automatically rebuilds and deploys updated tearsheets on scheduled cron runs.
   - **Synchronized All 245 Closed Trades**: Recomputed and pushed the multi-market tearsheet through September 15, 2026.

---

### 2. Canonical Code Adjustments

#### H4 / L4 Touch-Point Gating (`initializeAndPushTrade`)
```pine
initializeAndPushTrade(Settings settings, bool buyCond, bool sellCond, string longName, string shortName, array<TradeLogic> sessionsArr, array<TradeVisuals> visualsArr, string z1, string dX, string mX, string d1_message) =>
    // ── H4/L4 HARD GATE (Touch-point verified via wick extremes) ──
    bool _buy  = buyCond  and low < H4
    bool _sell = sellCond and high > L4
    ...
```

#### Strategy-Level Gating:
```pine
bool longAllowed  = low < H4
bool shortAllowed = high > L4
```

---

### 3. Verification & Deployment Status

| Component | Repository | Status | Key Deliverable |
| :--- | :--- | :--- | :--- |
| **`.agents/AGENTS.md`** | `RemoteURL` | `Active` | Strict Fact-Backed Verification Mandate & H4/L4 Touch-Point Rules. |
| **`TV Indicator/`** | `RemoteURL` | `v1.0` | Applied `low < H4` / `high > L4` gating across all 5 Pine scripts. |
| **`generate_tearsheet.py`** | `TLCS_Website` | `v1.0` | Fixed `NameError`, updated VectorBT matrix with 245 closed trades. |
| **`generate_tearsheet_cron.yml`** | `TLCS_Website` | `v1.0` | Removed `[skip ci]` to ensure Netlify auto-publishes on cron. |
