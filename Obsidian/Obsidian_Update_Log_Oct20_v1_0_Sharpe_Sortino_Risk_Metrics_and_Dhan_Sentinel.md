# Obsidian Update Log: Version 1.0 Sharpe & Sortino Risk Metrics, BlackBox Weekly Performance Audit, and Dhan Sentinel
**Date**: October 20, 2026  
**Author**: Antigravity AI Quantitative Engineer  
**Status**: Complete & Verified (v1.0 Production)  

---

### Key Accomplishments & Modifications

1. **Virtual Paper Portfolio Sharpe & Sortino Risk Metrics**:
   - Implemented exact annualized Sharpe Ratio ($\sqrt{252} \times \overline{R}_p / \sigma_p$) and Sortino Ratio ($\sqrt{252} \times \overline{R}_p / \sigma_d$) calculations in `paperStats` and `dhanPaperStats` in `Tv-Alert-Mobile/src/app/page.tsx`.
   - Expanded the Realized Paper Performance KPI grid from 8 to 10 tiles on both `TLCS_PAPER` and `DHAN_PAPER`.
   - Added dynamic `Sharpe` and `Sortino` performance status pills to the `SIMULATED EQUITY CURVE` card header.
   - Enhanced the interactive SVG inspection readout bar with `| SHARPE: ... | SORTINO: ...` values.

2. **BlackBox Weekly Performance Ingestion Audit**:
   - Fact-backed investigation into why BlackBox tearsheets were not automatically logged in GitHub Actions cron runs:
     - TV webhook trades populate `public.signals`.
     - BlackBox scanner trades populate `public.shadow_signals` (`source: 'blackbox_dhan'`).
     - GitHub Actions workflows (`weekly-performance-cron.yml`, `generate-tearsheet.yml`) strictly query `signals`.
     - App synthesizes weekly performance dynamically in client memory from `dhanBlackboxSignals` when `engineSource === 'SHADOW'`.

3. **DhanHQ Autonomous Token Sentinel & Live State Validation**:
   - Authenticated fresh 24h DhanHQ access token via RFC 6238 HMAC-SHA1 TOTP.
   - Persisted token to Supabase `dhan_token` and `system_config`.
   - Validated live marketfeed quotes during active trading hours and clarified EOD behavior during off-hours under the Zero-Fictitious Data mandate.

4. **Agent Rules & Architecture Update**:
   - Added **Version 1.0 Virtual Paper Portfolio Sharpe & Sortino Ratio Institutional Risk Metrics Mandate (Effective October 20, 2026)** to `AGENTS.md` and `.agents/AGENTS.md`.
