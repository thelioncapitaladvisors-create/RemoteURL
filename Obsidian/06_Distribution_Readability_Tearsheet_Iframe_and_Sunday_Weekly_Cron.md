# Obsidian Update Log: September 21, 2026 (v2.0)
## Trade Distribution Readability, Strategy Tearsheet Iframe Embedding & Sunday 18:30 UTC Weekly Cron Aggregation

---

### 1. Executive Summary & Version 2.0 Baseline
This production release standardizes and seals the platform at **Version 2.0 (`v2.0` / `2.0.0`)** across the **Next.js Mobile PWA (`Tv-Alert-Mobile`)**, the **Static Web Dashboard (`TLCS_Website_Deploy`)**, and the **Root Engine Architecture (`RemoteURL`)**. 

Key enhancements delivered in this release:
1. **Trade Distribution Chart Readability**: Complete visual overhaul of `Min Loss` and `Min Win` metrics in both dark and light modes, eliminating low-contrast text and guaranteeing instant readability.
2. **Strategy Tearsheet Iframe Restoration**: Eliminated `X-Frame-Options: SAMEORIGIN` collision on public tearsheet pages in Netlify `_headers`, establishing full `frame-ancestors *` compatibility for seamless embedding inside the mobile terminal.
3. **Weekly Performance Cron Aggregation Calendar Alignment**: Calibrated GitHub Actions and Netlify scheduled background functions to fire strictly on **Sunday 18:30 UTC** (Monday 00:00 IST / Sunday Midnight IST), capturing the full 7-day market week (including continuous 24/7 Crypto trades) and preventing missing weekly performance log rows.

---

### 2. Detailed Technical Fixes

#### A. Trade Distribution Chart Contrast & Readability Upgrade
* **Affected Files**:
  - `Tv-Alert-Mobile/src/app/page.tsx`
  - `TLCS_Website_Deploy/blog.html`
* **Problem**:
  In the Trade Distribution bell curve / bucket visualizations, the `Min Loss` and `Min Win` pills suffered from washed-out colors (`text-rose-500/80` and `text-emerald-500/80`) on subtle background tints, causing poor contrast and making numbers difficult to read against both dark and light backgrounds.
* **Solution**:
  - Upgraded badges with high-contrast, theme-aware CSS classes:
    - **Min Loss**:
      - Light mode: Deep crimson `text-rose-800 bg-rose-100 border-rose-300` with `font-black`.
      - Dark mode: Crisp bright rose `text-rose-400 bg-rose-500/15 border-rose-500/30` with `font-black`.
    - **Min Win**:
      - Light mode: Deep forest emerald `text-emerald-800 bg-emerald-100 border-emerald-300` with `font-black`.
      - Dark mode: Crisp bright emerald `text-emerald-400 bg-emerald-500/15 border-emerald-500/30` with `font-black`.
  - Upgraded label typography to uppercase tracking with high-contrast neutral muted text (`text-slate-500 dark:text-slate-400 font-bold tracking-wider`).

#### B. Strategy Tearsheet Iframe Embedding Resolution
* **Affected Files**:
  - `TLCS_Website_Deploy/_headers`
* **Problem**:
  When users opened the Strategy Tearsheet within the Mobile PWA modal or embedded dashboard iframe, the browser returned an error:
  `"thelioncapitalsolutions.com refused to connect"`.
* **Root Cause**:
  In `TLCS_Website_Deploy/_headers`, the top-level catch-all security rules `/*` and `/*.html` included the rigid HTTP header:
  `X-Frame-Options: SAMEORIGIN`.
  When loaded inside an embedded PWA container, standalone web application, or alternative origin context, the browser security engine strictly rejected the iframe.
* **Solution**:
  - Removed `X-Frame-Options: SAMEORIGIN` from public presentation paths `/*` and `/*.html`.
  - Configured explicit Content-Security-Policy:
    ```http
    Content-Security-Policy: frame-ancestors *;
    ```
  - Preserved strict `X-Frame-Options: DENY` on sensitive internal paths (`/admin/*`, `/api/*`).
  - Verified live deployment with HTTP `curl -I https://thelioncapitalsolutions.com/strategy_tearsheet.html` returning HTTP 200 with proper `frame-ancestors *` header.

#### C. Weekly Performance Edge Cron Calendar Realignment
* **Affected Files**:
  - `.github/workflows/weekly-performance-cron.yml`
  - `TLCS_Website_Deploy/netlify/functions/cron-weekly-logs.js`
  - `.agents/AGENTS.md`
* **Problem**:
  The user observed: *"Last week row is not added automatically. See why it failed."*
* **Root Cause**:
  The scheduled weekly performance cron was previously configured with cron schedule `0 21 * * 5` (Friday 21:00 UTC). This created two critical failures:
  1. **Premature Week Cut-Off**: Friday 21:00 UTC equals Saturday 02:30 IST. Any trades closing late Friday evening or over the weekend (especially Crypto 24/7 markets) were completely omitted from that week's performance log.
  2. **Timezone Boundary Disconnect**: The weekly aggregation script expects a full calendar week closure. Running on Friday caused calendar math to miscalculate the week boundaries, resulting in skipped or incomplete summary entries.
* **Solution**:
  - Standardized cron schedule to **`30 18 * * 0`**:
    - **Sunday 18:30 UTC** $\equiv$ **Sunday 24:00 / Monday 00:00 IST**.
    - Exactly marks the complete end of the 7-day trading week (Monday 00:00:00 to Sunday 23:59:59 IST).
  - Updated both GitHub Actions (`.github/workflows/weekly-performance-cron.yml`) and Netlify function (`cron-weekly-logs.js`) with the canonical schedule.
  - Documented the exact timing mandate in `.agents/AGENTS.md`.

---

### 3. Repository Git Synchronization & Tagging

| Repository | Path | Version | Commit | Tag |
| :--- | :--- | :--- | :--- | :--- |
| **Mobile PWA** | `Tv-Alert-Mobile` | `2.0.0` | `713c7ee` | `v2.0` |
| **Web Dashboard** | `TLCS_Website_Deploy` | `2.0.0` | `89b57de` | `v2.0` |
| **Master Engine Root** | `RemoteURL` (`.`) | `2.0.0` | `f46b777` | `v2.0` |

---

### 4. Verification & Audit Trail
- **Mobile Terminal Build**: Verified with Next.js type checker and Tailwind CSS compilation; zero regressions in `page.tsx`.
- **Live HTTP Header Inspection**:
  ```bash
  curl -I https://thelioncapitalsolutions.com/strategy_tearsheet.html
  # HTTP/2 200 OK
  # content-security-policy: frame-ancestors *;
  ```
- **Weekly Cron Trigger Test**: Verified Netlify function logic and GitHub workflow YAML syntax validation.
