# TLCS Terminal & Platform — Version 1.0 Architecture & Security Release Notes
**Release Date:** August 30, 2026  
**Infrastructure & Environment:** Netlify Exclusive (`thelioncapitalsolutions.com` / `market-store.online`)  
**GitHub Version Tag:** `v1.0.0` / `v1.0`

---

## Executive Summary
This release implements the definitive **TLCS Application Anomaly Correction Plan**, enforces a strict **3-Tier Access Control Model**, completely eliminates public leaks of the subscriber mobile application (`market-store.online`), achieves zero-data-leakage client gating on premium research and screener surfaces, resolves duplicate lock screens on the Performance Scanner, and restores dynamic real-time **Hold Duration** calculations for live active trades while suppressing elapsed times on unexecuted limit orders.

---

## 1. Discretionary Pivot Signal Messaging Alignment
- **Truth Convergence**: Fixed product copy across the website to reflect discretionary pivot signal generation rather than automated or algorithmic trade execution.
- **Hero Badge**: `"🔥 NOW LIVE — Real-Time Pivot Signal Alerts"`
- **Feature Card**: `"The indicator plots Entry, Stop Loss, and 4 Take Profit levels and fires a webhook alert the moment a setup triggers — you decide when to act."`
- **Section Subtitle**: `"From learning pivots to advanced signal alerts"`
- **Tier Comparison Tables**: Elite webhooks renamed from `"Algorithmic Trade Webhooks"` to `"Alert Webhooks (JSON)"`.
- **Meta Tags**: `og:description` updated across all pages to remove auto-trade phrasing.

---

## 2. Strict 3-Tier Access Control & Zero-Data Leakage Architecture
- **3-Tier Access Matrix**:
  1. **Visitor (Public)**: Full access to Homepage (`/`), Products & Pricing (`products.html`), Blogs & FAQs (`blog.html`), and Dashboard (`dashboard.html`).
  2. **Normal User (Registered Free)**: Visitor pages + account profile management.
  3. **Subscriber (Paid Plan / Owner `owner@tlcs.com`)**: Full access to all Visitor pages PLUS **Research** (`metrics.html`), **Screener Matrix** (`screener.html`), **Performance Scanner** (`scanner.html`), and **TLCS Terminal** (`market-store.online`).
- **Zero-Data Leakage & Network Isolation**:
  - Gated pages (`metrics.html`, `scanner.html`, `screener.html`) wrap all terminal chrome and tables in hidden containers (`style="display:none;"`) until `window.verifyPageAccess()` confirms valid subscriber credentials.
  - Data fetching scripts (`trade-metrics.js`, `scanner.js`, `screener.js`, `loadAnalysisSignals()`) halt execution immediately for unauthenticated visitors and free users, dispatching 0 network queries to Supabase.
- **Single-Layer Paywall**: Removed legacy duplicate auth gates (e.g. `#scanner-auth-gate` in `scanner.html`), ensuring clean presentation of the single branded subscriber modal.

---

## 3. Mobile Terminal Isolation (`market-store.online`)
- **Subscriber-Only Surface**:
  - Removed all public "Download App", "Launch App", and "Mobile App" buttons and links from public navbars, footers, and Products page.
  - The `📲 TLCS Terminal` launch button is surfaced strictly inside the logged-in navbar pill when `isSubscriber === true`.
- **AuthGuard Paywall**: `AuthGuard.tsx` in `Tv-Alert-Mobile` blocks unauthenticated visitors and free users with an "Active Subscription Required" upgrade card linking to `products.html`.
- **Search Engine Indexing Protection**: Enforced `public/robots.txt` (`Disallow: /`) and `<meta name="robots" content="noindex, nofollow" />` in Next.js `layout.tsx`.
- **Unified Branding**: The subscriber application is officially branded **TLCS Terminal**.

---

## 4. Live Hold Duration & Unentered Trade Suppression
- **Live Active Trades**: Hold duration is dynamically computed from when the trade entered/filled (`metadata.real_entry_time` / entry timestamp) up to the current moment (`Date.now() - liveEntryTs`), displaying continuous live held time (e.g. `<1m`, `15m`, `1h 20m`).
- **Unentered / Skipped / Cancelled / Expired Trades**: Hold duration is strictly suppressed and renders `--`. Limit orders that have not filled (`ACTIVE LIMIT`) never display hold duration.
- **Active Trade Exit Timestamps**: The `EXIT` timestamp for live active trades strictly renders `--` instead of intermediate webhook update timestamps.

---

## Files Modified & Created

### Web Platform (`TLCS_Website_Deploy`)
- `index.html`: Updated hero badge, feature box, pricing subtitles, and removed public app links.
- `products.html`: Replaced direct terminal links with internal plan anchors.
- `auth.js`: Implemented 3-tier access controller (`verifyPageAccess`), branded paywall modal, and subscriber-only terminal pill.
- `scanner.html` & `scanner.js`: Removed duplicate legacy lock gate and aligned with `verifyPageAccess`.
- `metrics.html` & `trade-metrics.js`: Wrapped terminal DOM in hidden container and gated data querying engine.
- `screener.html` & `screener.js`: Enforced subscriber paywall and data isolation.
- `commodity-scanner.js`: Added unentered/skipped trade hold duration guards.

### Mobile Terminal (`Tv-Alert-Mobile`)
- `src/components/AuthGuard.tsx`: Added subscriber paywall for non-subscribers attempting terminal access.
- `src/app/layout.tsx` & `public/robots.txt`: Added noindex robots tag and blocking robots.txt.
- `src/app/page.tsx`: Updated live hold duration calculation across HUB and LOGS tabs and suppressed duration on unentered limit orders.

### Documentation & Global Memory
- `.agents/AGENTS.md`: Added 3-Tier Access Control, Terminal Isolation, and Hold Duration rules.
- `Obsidian_Update_Log_Aug30_v1_0_Access_Control_and_Hold_Duration.md` *(NEW)*: Release log.

---

## Git Tagging & Version Control
- **Tag:** `v1.0.0` / `v1.0`
- **Repositories:**
  - `TLCS_Website_Deploy` → `v1.0.0`
  - `Tv-Alert-Mobile` → `v1.0.0`
  - `RemoteURL` → `v1.0.0`
  - Root `Project` → `v1.0.0`

---

## 5. Reverse-Engineering Exit Level & Price Resolution Protocol
When a trade exits and the exit level/price is not registered in the webhook payload, the system applies a 4-tier reverse engineering resolution strategy:
1. **Pine Script Status Keyword Direct Binding**: Automatically binds `exit_price` to `target`, `tp2`, `tp3`, `tp4`, `entry`, `stop`, or `trail_sl` based on definitive status terminology (`Hit TP1-4`, `Hit Initial SL`, `Hit B/E`, `Trailing Stop`).
2. **Exact Percentage Mathematical Inversion**: Inverts `metadata.exact_pct` against `entry` price ($\text{exit} = \text{entry} \times (1 \pm \text{pct}/100)$) and tests for proximity alignment against stored trade levels ($\pm 0.2\%$).
3. **Yahoo Finance Intraday 1m/5m Quote Resolution**: Queries Yahoo Finance for intraday candle data at `exit_at` / `updated_at` timestamps, applying scale-correlated percentage normalization for cross-currency futures.
4. **Automated Supabase Reconciliation**: Automatically writes back resolved exit prices and outcomes to Supabase to keep all performance tearsheets and win/loss analytics 100% synchronized.
