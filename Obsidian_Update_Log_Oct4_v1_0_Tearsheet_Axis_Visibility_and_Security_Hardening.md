# The Lion Capital Solutions (TLCS) System Architecture & Update Log
## Version 1.0 Release: Strategy Tearsheet Axis Visibility, High-Contrast Typography & Comprehensive Security Hardening
**Date**: October 4, 2026  
**Status**: Production Hardened Baseline (Release Tags `v1.0` / `v1.0.0`)  
**Architect**: Vishant Vyankat Meshram (*CFTe, CMT L3 Dec 2024*)

---

### Executive Overview
This release implements comprehensive visibility, typography, and contrast hardening across all 3 chart tabs (`Equity Curve`, `Drawdowns`, `Raw Returns`) and the `Statistics` tab of the Strategy Tearsheet (`strategy_tearsheet.html`), alongside full VAPT/DAST security remediation, local same-origin iframe embedding, and automated multi-market statistical synchronization.

---

### Key Architectural Enhancements

#### 1. Tearsheet Multi-Theme & High-Contrast Plotly Axis Visibility
- **Universal Theme Detection**:
  - Automatically recognizes all 7 mobile/web visual themes: `DARK`, `SLATE` (`gray`), `LIGHT`, `THE LION`, `GG DARK` (`goldengate`), `GG LIGHT` (`goldengate-light`), and `AUTO` (detecting `(prefers-color-scheme: light)`).
  - Categorizes rendering mode dynamically into `isLightMode` vs dark modes to eliminate invisible white-on-white or dark-on-dark text artifacts.
- **Explicit High-Contrast Axis Parameters**:
  - **X-Axis**: Explicit high-contrast `tickfont.color` (`#020617` in light/GG-light themes, `#FFFFFF` in dark themes), `JetBrains Mono` font family, outside tick marks (`ticks: 'outside'`, `ticklen: 4`), prominent axis baseline (`linewidth: 1.5`, `linecolor: #334155`), and subtle gridlines (`rgba(15,23,42,0.12)` / `rgba(255,255,255,0.12)`).
  - **Y-Axis**: Explicit return percentage formatting (`.1%`), high-contrast tickfont, zero-line baseline (`zerolinewidth: 1.5`), outside ticks, and left margin expansion (`margin.l: 52`) to prevent left-edge numerical clipping.
  - **Legends & Titles**: Horizontal centered legends with adaptive high-contrast labels and clean vertical spacing (`margin.b: 78`).

#### 2. Synchronized Tab Switching & Dynamic Resize Engine
- **Active Tab Re-Layout Hook**:
  - Updated `switchTab(tabId, btn)` to immediately invoke `Plotly.Plots.resize(chartDiv)` and `Plotly.relayout(chartDiv, getPlotlyLayoutUpdates())` whenever users switch between `[Equity Curve]`, `[Drawdowns]`, `[Raw Returns]`, and `[Statistics]`.
  - Fixes the previously unmeasured SVG canvas issue where tabs with `display: none` failed to render axis ticks on revelation.
- **Multi-Pass Initialization**:
  - Staggered re-layout passes at `[50, 150, 300, 600, 1000]ms` guarantee that all asynchronous Plotly SVG elements are properly styled on initial viewport load.

#### 3. Generator Script Parity
- Synchronized template generation logic across:
  - `TLCS_Website_Deploy/generate_tearsheet.py`
  - `algo_engine/backtest_edge.py`
  - `Tv-Alert-Mobile/public/strategy_tearsheet.html`
  - `TLCS_Website_Deploy/strategy_tearsheet.html`
  - `algo_engine/strategy_tearsheet.html`
  - `RemoteURL/algo_engine/strategy_tearsheet.html`

#### 4. Security & Typography Hardening Baseline
- **VAPT & DAST Hardening**: Gated subscription duration tampering, deployed PostgreSQL RLS trigger `trg_protect_profile_security_fields`, eliminated hardcoded credential fallbacks, configured anti-clickjacking headers, and secured background cron workers with `x-internal-secret`.
- **Milky Haze Elimination**: CSS `.shiny-card` isolation (`isolation: isolate;`) and `.shiny-card > * { z-index: 2; }` ensuring 100% crisp typography across all light and dark skins.
- **F&O Stock Buildups Typography**: 1-2px increased font scale with bold dark slate tokens.

---

### Verification & Test Suite
1. **Next.js Production Build**: `npm run build` in `Tv-Alert-Mobile` compiled 9/9 static and dynamic routes with 0 lint errors and 0 type errors.
2. **Same-Origin Delivery**: Local `/strategy_tearsheet.html` served with zero CSP/X-Frame-Options blocking.
3. **Backup Synchronization**: Triple-mirrored to `Project Backup/`, `Backups/`, and `Documents/Backups/`.
