# Platform Update Note: Version 1.0 Sharpe & Sortino Risk Metrics, BlackBox Weekly Performance Audit, and Autonomous Token Sentinel
**Date**: October 20, 2026  
**Module**: Mobile Terminal (`Tv-Alert-Mobile/src/app/page.tsx`), Algo Engine (`algo_engine/dhan_auth.py`, `algo_engine/sync_weekly_performance.py`), Workflows (`.github/workflows/generate-tearsheet.yml`, `.github/workflows/weekly-performance-cron.yml`), Documentation (`AGENTS.md`)  
**Scope**: Full integration of annualized Sharpe and Sortino ratio metrics across the Simulated Equity Curve (`TLCS_PAPER` and `DHAN_PAPER`), 10-tile institutional KPI grid, root-cause resolution for BlackBox weekly performance aggregation across dual tables (`signals` vs. `shadow_signals`), and autonomous DhanHQ 24h dynamic TOTP token validation.

---

## 1. Executive Summary & Rationale

As part of the Version 1.0 Institutional Quantitative Trading Architecture, this update implements risk-adjusted performance telemetry for simulated portfolio equity curves, addresses weekly performance tearsheet segregation between TradingView webhook signals and BlackBox scanner alerts, and clarifies live versus EOD status behavior across Option Chains and F&O Buildups.

1. **Risk-Adjusted Return Analytics (Sharpe & Sortino Ratios)**:
   - Added mathematically rigorous, annualized Sharpe and Sortino ratio calculations to both the **TLCS Paper Portfolio** (`paperStats`) and the **DhanHQ Paper Portfolio** (`dhanPaperStats`).
   - Expanded the KPI grid from 8 to 10 tiles on both portfolio views, providing instantaneous visibility into return per unit of total risk (Sharpe) and return per unit of downside risk (Sortino).
   - Injected live Sharpe and Sortino status pills into the `SIMULATED EQUITY CURVE` card headers and the interactive touch/drag inspection bars.

2. **BlackBox Weekly Performance & Tearsheet Ingestion Audit**:
   - TradingView webhook signals reside in `public.signals`, while BlackBox DhanHQ 100 scanner executions are logged to `public.shadow_signals` (`source: 'blackbox_dhan'`).
   - Background cron workflows (`weekly-performance-cron.yml` and `generate-tearsheet.yml`) strictly query `sb.table('signals')`.
   - The mobile terminal dynamically synthesizes weekly cards for BlackBox in client memory from `dhanBlackboxSignals` (`engineSource === 'SHADOW'`), explaining why weekly metrics populate inside the application even when static database tearsheet records target webhook signals.

3. **Autonomous DhanHQ Token Sentinel & Market Hours Fidelity**:
   - Re-authenticated the shared DhanHQ access token via dynamic RFC 6238 HMAC-SHA1 TOTP (`client_id: 1100428069`, `pin: 871346`).
   - Validated token persistence across Supabase `dhan_token` and `system_config`.
   - Verified that off-hours requests for Option Chain and F&O Buildups strictly respect exchange market hours (NSE: 09:15–15:30 IST; MCX: 09:00–23:30 IST) and adhere to the Zero-Fictitious Data mandate by serving authentic EOD closing snapshots or institutional empty states rather than simulated estimates.

---

## 2. Mathematical Formulations

### A. Annualized Sharpe Ratio
Measures the excess return per unit of total volatility (both upside and downside variance):
$$\text{Sharpe Ratio} = \frac{\overline{R}_p - R_f}{\sigma_p} \times \sqrt{252}$$
- $\overline{R}_p$: Sample mean of trade returns across all realized closed positions ($\frac{1}{N}\sum_{i=1}^N R_i$).
- $R_f$: Risk-free benchmark rate (assumed $0.0\%$ for active trading evaluation).
- $\sigma_p$: Sample standard deviation of trade percentage returns:
  $$\sigma_p = \sqrt{\frac{1}{N-1} \sum_{i=1}^N (R_i - \overline{R}_p)^2}$$
- $\sqrt{252}$: Annualization factor based on 252 trading sessions per calendar year.

### B. Annualized Sortino Ratio
Measures excess return relative strictly to downside volatility, ensuring profitable trades with high upside variance are not penalized:
$$\text{Sortino Ratio} = \frac{\overline{R}_p - R_f}{\sigma_d} \times \sqrt{252}$$
- $\sigma_d$: Downside semi-deviation (root mean square of negative trade returns):
  $$\sigma_d = \sqrt{\frac{1}{N} \sum_{i=1}^N \min(0, R_i)^2}$$
- When downside deviation is 0 (all trades breakeven or winning), the metric reports as `∞` (unbounded positive edge).

---

## 3. UI Component Architecture (`Tv-Alert-Mobile/src/app/page.tsx`)

### A. 10-Tile Institutional KPI Grid
Both `TLCS_PAPER` (lines 13516–13644) and `DHAN_PAPER` (lines 14261–14364) utilize a 10-card responsive grid (`grid-cols-2 min-[440px]:grid-cols-5 lg:grid-cols-10 gap-1.5`):
1. **Net Worth**: Current portfolio equity with base capital comparison.
2. **Realized P&L**: Cumulative rupee/dollar return with trade count.
3. **Return on Inv. (ROI)**: Exact total percentage yield with directional vector.
4. **Annual CAGR**: Compounded annual growth rate via $((\text{Bal} / \text{Cap})^{(52 / \text{Wks})} - 1) \times 100$.
5. **Win Rate**: Closed trade success percentage (`wins / totalClosed * 100`) with Profit Factor.
6. **Expectancy**: Dollar/rupee edge per execution and R-multiple.
7. **Calmar Ratio**: Compounded return divided by Maximum Drawdown percentage.
8. **Sharpe Ratio**: Cyan-accented card displaying risk-adjusted total volatility efficiency.
9. **Sortino Ratio**: Purple-accented card displaying downside risk-adjusted efficiency.
10. **Avg Win / Avg Loss**: Direct payoff ratio comparison.

### B. Simulated Equity Curve Header Badges
The card header features real-time performance badges:
- `ROI %` (Emerald / Rose)
- `CAGR %` (Blue / Purple)
- `Sharpe Ratio` (Cyan, e.g. `+1.85 Sharpe`)
- `Sortino Ratio` (Purple, e.g. `+2.40 Sortino`)

### C. Interactive Inspection Bar
Hover/touch readouts along the SVG equity trajectory dynamic inspection strip display:
```
START: ₹10,00,000 | PEAK: +₹45,200 | TROUGH: ₹9,82,000 | ROI: +4.52% | CAGR: +24.1% | SHARPE: 1.85 | SORTINO: 2.40
```

---

## 4. Verification & Testing

- **Syntax & Bracket Integrity**: Validated full bracket closure balance ($\Delta = 0$ across `(`, `[`, `{`) across all 15,500+ lines of TypeScript and JSX in `Tv-Alert-Mobile/src/app/page.tsx`.
- **DhanHQ Token Renewal**: Fresh token generated via dynamic TOTP, verified against live Dhan endpoints (Natural Gas spot quote 291.80 matching exchange feed), and saved to Supabase `dhan_token` with validity extending through Oct 21, 2026.
