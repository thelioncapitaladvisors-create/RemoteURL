# Update Log: Version 3.12 — Unified Commodities Dashboard & Dynamic Row Hiding
**Date:** Aug 9, 2026  
**Components:** Pine Script Indicators (`TLCS_Dashboards_4_Commodities_Merged.pine`), Web Application (`thelioncapitalsolutions.com`), Mobile Application (`market-store.online`)

---

## 1. Single Unified Table Architecture (`dash1`)
- **Consolidation:** Merged 3 separate table cards (Signals, Day Type Blueprints, Trade Sequences) into a single, continuous, vertically stacked table card (`dash1`).
- **Right Text Alignment:** Enforced `text_halign = text.align_right` across all cell invocations across all 21 rows for optimal visual structure on charts.
- **Custom Positioning:** Table position is fully configurable via `Table Position` setting (`Bottom Center`, `Top Right`, `Bottom Right`, etc.).

---

## 2. Dynamic Active Row Hiding (Zero-Gap Filtering)
- **Automatic Row Hiding:** Implemented dynamic row indexing (`curR`) that checks if any commodity in the basket has an active signal (`count > 0`). Rows with `0` active signals (showing `- -`) are completely omitted from the table without leaving dark placeholders or empty space.
- **Adaptive Height:** The table dynamically resizes its height to fit only active rows.
- **Clean Fallback:** When 0 signals, blueprints, or sequences are active across all 4 commodities, the dashboard automatically collapses into a single clean 1-row status badge: `NO ACTIVE SIGNALS / BLUEPRINTS`.

---

## 3. Divergence Streamlining & Metric Synchronization
- **Two Categories:** Streamlined Divergence metrics into two clean, non-overlapping categories: **Price Divergences** and **Hidden Divergences**.
- **`exact_pct` Single Source of Truth:** Enforced backend exact percentage math `((Exit - Entry) / Entry) * 100` before keyword string checks across `resolveOutcome` in `metrics.html`, `trade-metrics.js`, and `page.tsx`.

---

## 4. Pine Script Scoping & Syntax Fixes
- **Global Scope Resolution (`CE10272`):** Declared `var table dash1 = na` and `var int curR = 0` at top-level global scope, resolving undeclared identifier compilation errors when referencing `dash1` and `curR` across multiple `if barstate.islast` blocks.
- **Native Switch Blocks (`CE10156`):** Replaced multiline ternary position lookups with native Pine Script v6 `switch` blocks to eliminate line continuation syntax errors.

---

## 5. Automated GitHub & Netlify Deployments
- **TLCS Website (`thelioncapitalsolutions.com`)**: Pushed commit to `TLCS_Website` (`origin/main`), triggering automatic Netlify production build.
- **Mobile Application (`market-store.online`)**: Pushed commit to `thelioncapital-alerts` (`origin/main`), triggering automatic Netlify production build.
- **Root Project Repository (`RemoteURL`)**: Pushed commit to `RemoteURL` (`origin/main`) incorporating indicator sources and submodules.
