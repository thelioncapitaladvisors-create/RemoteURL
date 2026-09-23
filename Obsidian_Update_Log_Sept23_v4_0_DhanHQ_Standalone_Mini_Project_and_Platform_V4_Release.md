# Obsidian Update Log: Version 4.0 (23 Sept 2026)
## DhanHQ Top 100 NSE Black Box Standalone Mini-Project & Platform Version 4.0 Golden Release

---

### 1. Overview & Core Enhancements
Version 4.0 establishes a strict multi-layer architectural boundary, introducing the **DhanHQ Top 100 Liquid NSE Stocks Quantitative Scanner** as a dedicated **Standalone Mini-Project** visible exclusively within the **HUB Tab** of the mobile application. All other mobile application tabs (`MARKETS`, `ANALYTICS`, `LOGS`, `ADMIN`, `RESEARCH`) and the web application (`TLCS_Website_Deploy`) remain 100% isolated, preserving production TradingView webhook alerts and execution KPIs with absolute mathematical fidelity.

1. **Strict Multi-Layer Isolation Mandate**:
   - **Zero Web Application Bleed**: The web application (`thelioncapitalsolutions.com`) remains dedicated to production TradingView webhook alerts and never ingests or renders DhanHQ blackbox signals.
   - **Zero Cross-Tab Bleed in Mobile App**: Detections from the Python Black Box engine (`shadow_signals` with `source: 'blackbox_dhan'`) are strictly excluded from calculations in `MARKETS`, `ANALYTICS`, `LOGS`, and `ADMIN`. Portfolio win rates, profit factor, consecutive streaks, and trade cards remain 100% bound to TradingView webhooks.
   - **Standalone Mini-Project Container**: Functions as an independent experimental quantitative sandbox confined strictly to the HUB tab.

2. **Interactive HUB Filter Toggle Button**:
   - Integrated directly above the `TRADE GUIDANCE` section:
     - `[ 📡 WEBHOOK SIGNALS | ⚡ DHANHQ 100 (BLACK BOX ⚡) ]`
   - Allows traders to seamlessly switch between the canonical live TradingView webhook telemetry and the autonomous 15-minute DhanHQ Black Box evaluation.
   - Active status indicator dynamically displays `● Live Webhook Engine` or `⚡ Standalone 15m Mini-Project`.

3. **Dynamic TRADE GUIDANCE 10-KPI Performance Grid**:
   - When `WEBHOOK SIGNALS` is active (Default):
     - Displays standard production webhook KPIs (Active Limits, Live Trades, Closed Trades, Today's Success %, Today's Profit Factor, Weekly Trades, Weekly Success %, Weekly Profit Factor, Weekly Expectancy %, Weekly Calmar).
   - When `DHANHQ 100 (BLACK BOX ⚡)` is active:
     - The 10 KPI cards dynamically compute and display isolated performance for the 100 liquid stocks:
       - **Row 1 (Today & Live)**: Dhan Active Limits, Dhan Live Trades, Dhan Today Closed Trades, Dhan Today Success Rate %, Dhan Today Profit Factor.
       - **Row 2 (Current Week & Scope)**: Dhan Weekly Trades, Dhan Weekly Success Rate %, Dhan Weekly Profit Factor, Dhan Weekly Expectancy (Average Return %), Universe Size (`100 STOCKS`).
     - Features distinct Fuchsia/Violet themed glow styling to reinforce the standalone engine mode.

4. **Dedicated Standalone Mini-Project Status Card**:
   - When DhanHQ mode is active on the HUB tab, a high-visibility parameter card renders above the grid:
     - **Universe**: Top 100 Liquid NSE Stocks (`NSE:EQ`)
     - **Timeframe**: 15-Minute Completed Intervals
     - **Touchpoint Gating**: Strictly H4 (Buys) / L4 (Sells)
     - **Isolation Status**: Confined strictly to Hub Tab

5. **Source-Gated TLCS ALERTS DASHBOARD**:
   - When `DHAN` mode is selected: the 13 strategy parameter rows (Missile, Scalp, Lightning, Extreme Reversal, Divergence, 5 Day Type Blueprints, 2 Sequences) filter strictly active signals detected by the DhanHQ 15m engine.
   - When `WEBHOOK` mode is selected: the matrix filters strictly active TradingView webhook alerts.

6. **Platform-Wide Version 4.0 Standardization**:
   - **Mobile Terminal (`Tv-Alert-Mobile`)**:
     - Terminal header: `TLCS TERMINAL v4.0`.
     - SIEM app initialization log: `Terminal V4.0 initialized`.
     - Daemon verification pill: `Active Daemon v4.0`.
     - `package.json`: Version bumped to `4.0.0`.
   - **Web Application (`TLCS_Website_Deploy`)**:
     - `dashboard.html`: Engine badge `Deterministic Engine v4.0` and footer `v4.0`.
     - `metrics.html`: Footer `v4.0`.
     - `scanner.html`: Footer `v4.0`.
     - `login.html`: Debug badge `v4.0`.
     - `localization.js`: Version header `v4.0.0`.
     - `scanner.js`: Version header `v4.0.0`.
     - `sw.js`: Cache name bumped to `tlcs-website-cache-v4.0.0`.
     - `package.json`: Version bumped to `4.0.0`.
   - **System Architecture (`.agents/AGENTS.md`)**:
     - Formally ratified Version 4.0 Platform Baseline and Strict Isolation Mandate.

---

### 2. Code Modifications & Repositories
- **Mobile Terminal (`Tv-Alert-Mobile`)**:
  - `src/app/page.tsx`:
    - Added `hubDataSource` state (`'WEBHOOK' | 'DHAN'`).
    - Added memoized isolated DhanHQ 100 performance metrics (`dhanActiveLimitsCount`, `dhanLiveTradesCount`, `dhanTodayClosed`, `dhanTodaySuccessRate`, `dhanTodayPFVal`, `dhanWeeklyClosed`, `dhanWeeklySuccessRate`, `dhanWeeklyPFVal`, `dhanWeeklyExpectancy`).
    - Implemented filter toggle button and DhanHQ parameter status card.
    - Wired dynamic KPI switching into `TRADE GUIDANCE` 10-stat grid.
    - Source-gated `TLCS ALERTS DASHBOARD` matrix filtering.
    - Updated branding to `v4.0`.
  - `package.json`: Bumped version to `4.0.0`.
- **Web Application (`TLCS_Website_Deploy`)**:
  - `dashboard.html`, `metrics.html`, `scanner.html`, `login.html`, `localization.js`, `scanner.js`, `sw.js`: Standardized to `v4.0` / `v4.0.0`.
  - `package.json`: Bumped version to `4.0.0`.
- **System Memory (`.agents/AGENTS.md`)**:
  - Documented Version 4.0 Platform Baseline and Standalone DhanHQ Mini-Project rules.

---

### 3. Verification & Validation
- **TypeScript & Next.js Build**:
  - `next build` compiled cleanly with 0 type errors or warnings across all 8 static and dynamic routes.
- **Python DhanHQ Scanner Runner**:
  - `python3 algo_engine/run_nse100_scanner.py --limit 10 --mock --once` executed and verified.
