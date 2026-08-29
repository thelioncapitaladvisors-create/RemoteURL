# TLCS Terminal & Mobile Suite — Version 3.19 Release Notes
**Release Date:** August 29, 2026  
**Infrastructure & Environment:** Netlify Exclusive (`thelioncapitalsolutions.com` / `market-store.online`)  
**GitHub Version Tag:** `v3.19.0` / `v3.19`

---

## Executive Summary (Version 3.19)
Version 3.19 introduces the **Global 7-Day Screener Matrix** across both the Web platform and Mobile application, implements the **ALL FILTERS DEBUG** real-time matrix on the Mobile Insights tab, rebrands the Scanner page to **Performance**, and establishes an automated **GitHub Actions CI/CD cron pipeline** for VectorBT strategy tearsheet generation.

---

## Key Enhancements & Architectural Updates (V3.19)

### 1. Global 7-Day Screener Matrix (`screener.html` & Mobile `SCREENER` Tab)
- **3 Canonical Strategy Sections**:
  1. **TLCS SIGNALS**: *Missile*, *Price Divergences*, *Scalp*, *Lightning*
  2. **DAY TYPE BLUEPRINTS**: *Failed New High/Low Blueprint*, *Outside Day Blueprint*, *Rejection Day Blueprint*, *Absorption Day Blueprint*, *Stop Run Day Blueprint*
  3. **TRADE SEQUENCES**: *Rejection Day Sequence*, *Stop Run Sequence*, *Failed Absorption Sequence*, *Accumulation / Distribution Sequence*
- **7-Day Rolling Horizon**: Spanning Day 7 down to Day 1 (Today) with interactive market filtering (`ALL MARKETS`, `NIFTY 50`, `MCX`, `NYMEX`, `CRYPTO`, `FOREX`, `WORLD`).
- **High-Contrast Theme-Adaptive Styling**:
  - **Light/Gray Mode**: Clean white/slate table background, royal sky headers, deep-navy category labels, and bright, high-contrast badges.
  - **Dark Mode**: Deep navy/slate table background with luminous cyan category labels and glowing directional pills.
- **Sticky First Column**: Sticky `FILTER TYPE` column (`position: sticky; left: 0; z-index: 20`) ensuring row headers remain permanently visible during horizontal scrolling.
- **Directional Symbol Pills**: Clean pill badges with explicit directional arrows (`▲ SYMBOL` in emerald green, `▼ SYMBOL` in rose red, `-` for inactive days).

### 2. Mobile App Insights Tab: `ALL FILTERS DEBUG (Today, All Symbols)`
- **Live Strategy Verification**: Dynamic symbol-by-filter matrix table rendered at the top of the **INSIGHTS** tab.
- **Real-Time Synthesis**: Automatically synthesizes signals from `todaySignals` and `pivotBossScans` to display active bullish (`▲`), bearish (`▼`), and inactive (`-`) states across all active symbols.

### 3. Website Navigation & Rebranding (Scanner → Performance)
- **Page Re-branding**: Renamed `scanner.html` header, page title, and navigation labels to **Performance**.
- **Global Navigation Synchronization**: Added **Screener** link and updated **Performance** link across all 11 website templates (`index.html`, `dashboard.html`, `metrics.html`, `products.html`, `blog.html`, `admin.html`, `article.html`, `terms.html`, `privacy.html`, `refund.html`, and `auth.js`).
- **Access Guard**: Included `screener.html` in `auth.js` active subscriber protection list.

### 4. Automated VectorBT Strategy Tearsheet CI/CD Pipeline
- **Stand-alone Generator (`generate_tearsheet.py`)**: VectorBT empirical backtest script computing cumulative equity, drawdown, raw returns, and statistics across all closed trades.
- **Numba Cache Conflict Safeguard**: Disabled caching (`vbt.settings.caching['enabled'] = False` and `NUMBA_DISABLE_CACHING=1`) to prevent Python 3.11 JIT cache corruption.
- **GitHub Actions Cron Workflow (`generate_tearsheet_cron.yml`)**: Automatically triggers at market closes (16:00 IST for Indian Equities, 00:00 IST for MCX, 22:30 UTC for US/NYMEX, and 00:30 UTC for Global Daily) to regenerate `strategy_tearsheet.html` and commit/deploy to Netlify.

---

## Files Modified & Created

### Mobile Application (`Tv-Alert-Mobile`)
- `src/app/page.tsx`: Added `ALL FILTERS DEBUG` in Insights tab, created `SCREENER` tab with 7-Day matrix, added `SCREENER` to bottom navigation bar, updated theme contrast & sticky column styling.
- `package.json`: Version bumped to `1.2.0`.

### Web Platform (`TLCS_Website_Deploy`)
- `screener.html` *(NEW)*: Standalone 7-Day Screener matrix page with auth gate and responsive market tabs.
- `screener.js` *(NEW)*: Real-time and REST Supabase data fetcher and renderer for 7-day signals and scans.
- `scanner.html`: Rebranded to Performance (title, header, badges, footer links).
- `generate_tearsheet.py` *(NEW)*: VectorBT tearsheet generation script.
- `.github/workflows/generate_tearsheet_cron.yml` *(NEW)*: Scheduled GitHub Actions workflow for automated tearsheet generation.
- `strategy_tearsheet.html`: Freshly generated tearsheet with latest 175 closed trades.
- `index.html`, `dashboard.html`, `metrics.html`, `products.html`, `blog.html`, `admin.html`, `article.html`, `terms.html`, `privacy.html`, `refund.html`, `auth.js`: Updated navigation and footer menus.

---

## Git Tagging & Version Control
- **Tag:** `v3.19.0` / `v3.19`
- **Repos:**
  - `Tv-Alert-Mobile` → `v3.19.0`
  - `TLCS_Website_Deploy` → `v3.19.0`
  - `Project` (Root) → `v3.19.0`

---
*Official Version 3.19 Sealed on August 29, 2026.*
