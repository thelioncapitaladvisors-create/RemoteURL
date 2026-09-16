# Obsidian Update Log: Version 2.0 (16 Sept 2026)
## Extreme Reversal Screener Filter Integration & Platform Version 2.0 Golden Release

---

### 1. Overview & Core Enhancements
Version 2.0 brings full multi-platform visibility and filtering for the **Extreme Reversal** strategy across the mobile app, web dashboard, 7-day screener matrix, and serverless webhook pipeline:

1. **Extreme Reversal Screener Filter Integration**:
   - **Web Screener Matrix (`screener.js` & `dashboard.html`)**: Added `EXTREME_REV` category to `signalCategories` in both the standalone screener page and the unified Dashboard 7-Day Screener Matrix.
   - **Mobile Terminal (`page.tsx`)**: Added `EXTREME_REV` to the 7-day screener matrix, `EXTREME_REVERSAL`, `DIVERGENCE`, and `HIDDEN_DIVERGENCE` to the ANALYTICS parameter matrix, and registered StrategyBadges (🔥 Fuchsia Flame for Extreme Reversal, 👁 Teal Eye for Hidden Divergence, and 🔀 Violet GitBranch for Divergence).

2. **Backend Webhook Scan Data Extraction (`process-webhook-background.js`)**:
   - Added support for extracting `bExt`/`sExt` (Format 1 - 7-day scans) and `bullExt`/`bearExt` / `bullExtRev`/`bearExtRev` (Format 2 - SessionOpenMatrix) into the `extRev` column for real-time and historical screener matrix rendering.

3. **Platform-Wide Version 2.0 Release**:
   - **Mobile Terminal**: Updated header to `TLCS TERMINAL v2.0`, SIEM initialization log to `Terminal V2.0`, and bumped `package.json` to `2.0.0`.
   - **Web Platform**: Updated footers across `dashboard.html`, `metrics.html`, and `scanner.html` to `v2.0`, script cachebusters to `?v=2.0`, login debug badge to `v2.0`, and bumped `package.json` to `2.0.0`.

---

### 2. Files Updated
- `Tv-Alert-Mobile/src/app/page.tsx`
- `Tv-Alert-Mobile/package.json`
- `TLCS_Website_Deploy/dashboard.html`
- `TLCS_Website_Deploy/screener.js`
- `TLCS_Website_Deploy/scanner.html`
- `TLCS_Website_Deploy/metrics.html`
- `TLCS_Website_Deploy/login.html`
- `TLCS_Website_Deploy/package.json`
- `TLCS_Website_Deploy/netlify/functions/process-webhook-background.js`
