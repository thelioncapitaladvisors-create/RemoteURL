# 134 — Platform v1.0 Canonical Database Purge & Fresh Forward Baseline Mandate

**Date**: November 27, 2026  
**Status**: Canonical Production Release (`v1.0.0`)  
**Target Files**: `page.tsx`, `RemoteURL/page.tsx`, `Tv-Alert-Mobile/src/app/page.tsx`, `AGENTS.md`, `.agents/AGENTS.md`, Supabase (`signals`, `shadow_signals`, `weekly_performance_logs`)

---

## 1. Executive Summary

As instructed by the user, a complete database purge of all historical signal alerts and execution data across all application tabs (`DASHBOARD`, `MARKETS`, `INSIGHTS`, `LOGS`, `PERFORMANCE`, `TERMINAL`) was executed. Simultaneously, the platform's canonical baseline anchor was advanced from November 24, 2026 to **November 27, 2026 00:00:00 IST (`1795717800000` ms)** to allow the system to register signals and track live performance afresh from the next incoming signal alert.

---

## 2. Database Purge Scope & Verifiable Zero State

The purge script connected directly to Supabase production and executed deletions across the primary trading tables:

1. **`signals`**: Purged all TradingView webhook and executed signal records (including open limits, active positions, closed trades). Confirmed remaining rows: **`0`**.
2. **`shadow_signals`**: Purged all DhanHQ BlackBox algorithm shadow trades. Confirmed remaining rows: **`0`**.
3. **`weekly_performance_logs`**: Purged all historical weekly performance aggregation logs. Confirmed remaining rows: **`0`**.

### Database Verification Output
```json
{
  "signals_remaining": 0,
  "shadow_signals_remaining": 0,
  "weekly_logs_remaining": 0,
  "status": "PURGE_COMPLETE_VERIFIED"
}
```

---

## 3. Forward Baseline Synchronization (`BASELINE_START_MS`)

All performance breakdown and analytics matrices in the user interface rely on `BASELINE_START_MS` to anchor forward-looking statistical calculations. The baseline was updated across `RemoteURL/page.tsx`, `page.tsx`, and `Tv-Alert-Mobile/src/app/page.tsx`:

* **Previous Baseline**: `1795458600000` (November 24, 2026 00:00:00 IST)
* **New Canonical Baseline**: **`1795717800000` (November 27, 2026 00:00:00 IST)**

### Affected Analytics Tables
1. **Canonical Signal Family Forward-Performance Scorecard (`canonicalFamilyStats`)**:
   - `BASELINE_START_MS = 1795717800000`
   - UI Pill Badge: `● NOV 27, 2026+ BASELINE`
2. **VectorBT Confluence Benchmark Matrix (`confluenceBenchmarkStats`)**:
   - `BASELINE_START_MS = 1795717800000`
3. **Market Regime & Day Type Performance Breakdown (`dayTypeStats`)**:
   - `BASELINE_START_MS = 1795717800000`
   - UI Pill Badge: `● NOV 27, 2026+ BASELINE`
4. **DhanHQ BlackBox Screener Scorecard (`dhanScreenerSetupStats`)**:
   - `BASELINE_START_MS = 1795717800000`

---

## 4. Operational Behavior

* **All Application Tabs**: Cleared of historical signals, displaying clean zero/waiting states.
* **Next Incoming Signal**: Will be ingested with timestamp >= 1795717800000 and will register as the initial trade of the new baseline cycle.
* **Integrity**: Full parity preserved across web, mobile, local backup repositories, and agent instructions.
