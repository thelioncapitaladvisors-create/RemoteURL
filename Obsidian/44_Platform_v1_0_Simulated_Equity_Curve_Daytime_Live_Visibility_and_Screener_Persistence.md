# Platform v1.0: Virtual Paper Portfolio Simulated Equity Curve Daytime Live Market Visibility & Screener Tab Persistence

- **Document ID**: 44_Platform_v1_0_Simulated_Equity_Curve_Daytime_Live_Visibility_and_Screener_Persistence.md
- **Release Version**: v1.0.0 / v1.0
- **Effective Date**: October 16, 2026
- **Classification**: Quantitative Architecture, Frontend Resilience & Trade Simulation Integrity

---

## 1. Executive Summary & Problem Diagnosis

During live daytime trading hours (Indian market 09:15 to 15:30 IST), users observed that the **Virtual Paper Portfolio Simulated Equity Curve** (SIMULATED EQUITY CURVE and RECENT SIMULATED PAPER SIGNALS) remained completely hidden or blanked out on the mobile terminal (SCREENER tab).

Following the **Strict Fact-Backed Verification Mandate (Zero Speculation & Zero Unilateral Logic Alterations)**, step-by-step source code auditing of Tv-Alert-Mobile/src/app/page.tsx and Supabase live trade data identified two distinct deterministic root causes:

### Root Cause 1: Intraday Signal Outcome Lifecycle & < 2 Points Guard Collapse
- **Intraday Trade State**: During live daytime hours, incoming trade signals triggered by both TradingView webhooks (signals) and DhanHQ Black Box (shadow_signals) start in outcome === 'OPEN' status with exit_price: null.
- **Closed Trades Filtering**: Both paperStats (line 3711) and dhanPaperStats (line 5121) historically computed the equity curve series exclusively from closed trades:
  ```typescript
  const closed = (paperSimulatedTrades || []).filter(t => t && t.isClosed);
  // where isClosed = s.exit_price != null || (outcome !== 'OPEN')
  ```
- **Fallback Destruction**: During morning and intraday market hours prior to targets or EOD settlement:
  closed.length === 0, causing equitySeries to contain only the single initial point [{ index: 0, equity: 1000000 }].
  This triggered the hardcoded guard:
  ```tsx
  {(!paperStats.equityPoints || paperStats.equityPoints.length < 2) ? (
    <div className="...">Awaiting Closed Simulated Trades</div>
  ) : ...}
  ```
  completely destroying and hiding the interactive SVG equity curve during daytime.
- **Nighttime Reappearance**: After market close (15:30 IST for NSE / 23:30 IST for MCX), the automated EOD closing sweeper (cron/eod-close/route.ts) resolves open trades to WIN / LOSS (EOD Exit), causing closed.length to increase and the equity curve to suddenly appear at night, giving the illusion that the simulator only functions outside market hours.

### Root Cause 2: Screener Subtab Separation & Non-Persistent State
- The SCREENER tab was split into 4 mutually exclusive subtabs: TLCS_SCREENER, DHAN_SCREENER, TLCS_PAPER, DHAN_PAPER.
- screenerViewTab defaulted to 'TLCS_SCREENER' in memory without localStorage persistence, causing page reloads or session restarts during daytime market hours to reset to the 7-day matrix table, completely burying the Virtual Paper Portfolio behind an extra click.
- An aggressive useEffect synchronizing engineSource continuously flipped screenerViewTab between TLCS_SCREENER and DHAN_SCREENER, hijacking user navigation.

---

## 2. Quantitative & Architectural Remediation

### A. Intraday Active Trade Trajectory Inclusion & 2-Point Resilience Guarantee
Both paperStats and dhanPaperStats now combine realized closed trades AND active open trades into chronological trajectory series:
```typescript
const chronoTrades = [...closed, ...active].sort((a, b) => {
  const tA = new Date(a.signal_ts || a.created_at || 0).getTime();
  const tB = new Date(b.signal_ts || b.created_at || 0).getTime();
  return tA - tB;
});
```
- Active open trades dynamically track running P&L (ptsDiff * mult), allowing users to inspect real-time trajectory as explicitly promised by the card title: PORTFOLIO TRAJECTORY • REAL-TIME RUN-UP & DRAWDOWN.
- **Resilience Guarantee**: If 0 trades are present in a filtered view or on a fresh day (equitySeries.length === 1), the engine automatically injects a live baseline anchor at current capital (₹10,00,000). This ensures equityPoints.length >= 2 at all times, permanently preventing the canvas from collapsing.

### B. Persistent Live Baseline & Informative Intraday Status
Rather than destroying the SVG canvas and showing a broken dashed empty box when 0 trades exist:
- The SVG canvas renders a clean horizontal baseline at starting capital (BASELINE ₹10L) with full touch and hover crosshair inspection.
- When closedCount === 0 && activeCount === 0, an elegant live badge overlay informs the user:
  🟢 LIVE INTRADAY MONITORING ACTIVE • Baseline established at ₹10,00,000. Trajectory plots in real-time as signals fire.

### C. Persistent Screener View Selection & Non-Clobbering Engine Sync
- screenerViewTab is now initialized from and saved to localStorage key 'tlcs_screener_view_tab'.
- The synchronization effect utilizes prevEngineSourceRef.current to guarantee it ONLY responds when the user explicitly changes engineSource in the header/menu, never clobbering user selection on mount or live data refreshes.
- Defaults to 'TLCS_PAPER' so the Virtual Paper Portfolio and simulated signals are immediately front and center.

### D. Seamless Matrix-to-Paper Quick Navigation
Both TLCS_SCREENER and DHAN_SCREENER now feature a dedicated quick navigation action card directly below each 7-day matrix table:
📊 Virtual Paper Portfolio Simulator • [OPEN SIMULATOR ↗]
guaranteeing 1-tap transition between the 7-day Day Type Matrix and the Virtual Paper Trading Simulator.

---

## 3. Verification & CI/CD Validation
- **TypeScript Compiler (tsc --noEmit)**: Passed with 0 errors (Exit code 0).
- **Next.js Production Build (npm run build)**: Compiled successfully with all 8 static pages generated and optimized chunks.
- **Repository Alignment**: Verified clean build across Tv-Alert-Mobile.
