# Version 1.7.0 Update Log - July 25, 2026

## 🛠️ System-Wide Edge & AI Scanner Defaults Upgrade

### 1. Default System-Wide Metrics Mode on AI Scanner Page
- **System-Wide Default State**: Configured [`scanner.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.html) and [`scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js) to default to system-wide mode (`activeTab = 'all'`) on initial page load, where no specific market tab is highlighted.
- **Interactive Market Tab Deselection**: Clicking an active market tab now toggles it off, seamlessly returning the user to the system-wide view (`'all'`).
- **Aggregated Historical Edge Statistics**: The top summary bar (`#scanner-expectancy-bar`) calculates and displays the system-wide aggregated metrics (**Win Rate, Half-Kelly %, Profit Factor, Avg Profit / System Edge, Total Trades, Wins / Losses / BE, Best Trade**) across all 6 markets (`Nifty 50`, `MCX`, `NYMEX`, `Crypto Top 25`, `Forex Pairs`, `World Indices`).

---

### 2. Weekly Consolidated System Edge Alignment (`TLCS EDGE %`)
- **Current Week Consolidated System Edge**: Updated [`scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js) (`cachedData.signals`) and [`dashboard.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/dashboard.html) (`systemAvgEdge`) to compute consolidated system edge over **all 6 markets combined for the current week** (starting Monday 00:00 local time).
- **Dashboard & Scanner Parity**: The `TLCS EDGE %` card on `dashboard.html` and the `Avg Profit` summary metric on `scanner.html` match with 100% mathematical precision, showing the consolidated weekly edge of the entire TLCS system.

---

### 3. System-Wide Weekly Performance Edge Historical Aggregation
- **Dynamic System-Wide Weekly Edge Aggregation**: Updated `fetchWeeklyLogs('all')` in [`scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js) to query all historical weekly performance logs from `weekly_performance_logs`, group by `week_start_date`, and aggregate win rates, net edge, profit factors, and Half-Kelly percentages across all 6 market types week by week.
- **Cumulative All-Time System Edge Row**: The Weekly Performance Edge table renders an `ALL` Cumulative Edge row summarizing overall all-time historical performance across all recorded weeks.

---

### 4. Single Source of Truth & Rule Base Update (`AGENTS.md`)
- **Updated System Guidelines**: Appended new architecture rules to [.agents/AGENTS.md](file:///Users/vishant/Documents/Project/.agents/AGENTS.md) enforcing default system-wide metrics mode on the AI Scanner page, tab deselect toggles, and historical Week 1 to date signal aggregation for `TLCS EDGE %`.

---

### 5. Next.js Mobile Scope & Build Error Resolution (`isNYMEXSymbol`)
- **Resolved Next.js Type Compiler Error**: Defined `isNYMEXSymbol(symbol?: string)` helper function at module scope in [`page.tsx`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx) to resolve Netlify Next.js build worker exit error (`Type error: Cannot find name 'isNYMEXSymbol'`). Local build test verified 9/9 pages generated cleanly (`npm run build` exit code 0).

---

### 6. Netlify Secrets Scanning Security Enforcement
- **Eliminated Hardcoded Secret Credentials**: Sanitized 7 test/utility script files ([`check_crude.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/check_crude.js), [`debug_metrics.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/debug_metrics.js), [`find_outliers.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/find_outliers.js), [`fix_corrupted_mcx.py`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/fix_corrupted_mcx.py), [`inspect_losses.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/inspect_losses.js), [`test_dash_exact.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/test_dash_exact.js), [`test_metrics.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/test_metrics.js)) by replacing hardcoded service role JWTs with dynamic environment variable lookups (`process.env.SUPABASE_SERVICE_KEY` / `os.environ.get(...)`). Netlify automated secrets scanner verified 0 violations.

---

### 7. Netlify Automated EOD Market Closure Background Worker
- **Scheduled Netlify Background Cron (`cron-eod-close.js`)**: Created and deployed [`cron-eod-close.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/cron-eod-close.js) scheduled to run every 15 minutes (`schedule("*/15 * * * *")`) on Netlify infrastructure.
- **Automated Market Closure Sweeping**: Automatically closes all open positions across NYMEX, Nifty, MCX, World, and Forex markets at daily session close and weekend close. Executed 92 stale/weekend trade closures (including `CL1!`, `GC1!`, `NG1!`) as `EOD Exit` or `CANCELLED` (for unexecuted limits), leaving 0 unclosed trades hanging across closed sessions.

---

### 8. Default Mode Symbol Exclusion & Weekly Edge Header Market Badge
- **Default Mode Symbol Table Cleanliness**: In default mode (`activeTab = 'all'`), the scanner table [`scanner.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.html) no longer dumps individual market symbol rows. Instead, it renders an elegant prompt (`SELECT A MARKET CATEGORY ABOVE TO VIEW SYMBOL SIGNALS`). Symbol rows render ONLY when a specific market category tab is active.
- **Weekly Performance Edge Market Badge**: Added a dynamic theme badge (`#weekly-edge-market-pill`) to the right side of the Weekly Performance Edge header line in [`scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js), displaying the current active view (e.g. `🌐 SYSTEM-WIDE (ALL MARKETS)` in gold for default mode, `₿ CRYPTO TOP 25` in cyan, `🛢️ NYMEX` in orange, etc.).

---

### 9. Default Mode Weekly Performance Edge — Average of All Six Markets Alignment
- **Pure Average Consolidation**: Updated `fetchWeeklyLogs('all')` in [`scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js) so that all Weekly Performance Edge table metrics in default mode (`WIN RATE`, `NET EDGE`, `PROFIT FACTOR`, `HALF-KELLY %`) are computed as the **exact mathematical average of all six active markets** for each week (eliminating additive net edge sum inflation).
- **Cumulative Edge Row (`ALL`)**: The top `ALL - CUMULATIVE EDGE` row computes the average across the weekly consolidated averages, displaying true 6-market portfolio averages.

---

### 10. Local Projects Repository Cleanliness & Push Verification
- **Full Workspace Synchronization**: Verified that all local repositories ([`TLCS_Website_Deploy`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy), [`Tv-Alert-Mobile`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile), [`TV Indicator`](file:///Users/vishant/Documents/Project/TV%20Indicator), and the root workspace repository) are 100% clean, fully committed, and synchronized with remote `origin/main`.

---

### 11. Mandatory Stop, Target & R:R Level Deductions for Closed & EOD Trades
- **Universal Level Completeness Engine**: Implemented `getTradeLevels` across [`scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js), [`commodity-scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/commodity-scanner.js), and [`page.tsx`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx) so that closed trades (including EOD force closures and divergence signals lacking explicit payload stops/targets) dynamically compute `STOP`, `TARGET`, and `R:R` (e.g., `1.0R`) using entry prices and asset-class stop percentage defaults (`0.5%` Crude/Silver, `0.3%` Gold, `0.35%` Nifty, `0.75%` Crypto, `0.25%` Forex). `STOP`, `TARGET`, and `R:R` are no longer rendered as `--` on any closed trade card or table row.

---

### 12. Individual Market View Cumulative Edge Alignment (Un-inflated Weekly Averages)
- **Universal Weekly Average Metrics**: Updated `fetchWeeklyLogs` in [`scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js) so that the `ALL - CUMULATIVE EDGE` row for individual market tabs (e.g., `Crypto Top 25`, `Nifty 50`, `MCX`, `NYMEX`, `Forex Pairs`, `World Indices`) computes the **average weekly performance metrics** across recorded weeks (e.g. Crypto Average Weekly Net Edge = `+11.83%`), completely eliminating additive net edge sum inflation across all market views.

---

### 13. Centered Weekly Performance Edge Market Badge Alignment
- **Centered Header Layout**: Reconfigured [`scanner.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.html) (`.weekly-edge-header-grid`) using a 3-column CSS grid (`1fr auto 1fr`) to shift the active market badge (`#weekly-edge-market-pill`) from the far right edge to the **exact center/middle** of the Weekly Performance Edge header line across all screen sizes.

---

### 14. Zero `--` Fallback Elimination on Real Calculated Metrics
- **Strict Numeric Formatting Defaults**: Updated `renderSummaryBar`, `fmtWR`, and `fmtExp` across [`scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js) and [`commodity-scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/commodity-scanner.js) to display clean numeric fallbacks (`0.0%`, `+0.00%`, `0.00`, `0%`) instead of `--` when no trades exist or when Half-Kelly evaluates to 0/null.

---

### 15. Beginner Plan FREE Badge Tag Addition
- **Vibrant FREE Pill Badge**: Added a gradient `🎉 FREE` pill badge to the **TLCS Standard Pivots Indicator** Beginner plan cards on both [`index.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/index.html) and [`products.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/products.html).

---

### 16. Beginner Plan Price Overlay FREE Stamp Badge
- **Price Overlay FREE Badge**: Placed a secondary `🎉 FREE` pill badge directly over the `₹99/month` (or `$1/month`) price display on the Beginner plan cards ([`index.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/index.html) and [`products.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/products.html)). The badge is rotated `-5deg` and partially overlays the price text to partially hide it with a promotional stamp effect.

---

### 17. Official Blog Publications Upload & Interactive Reader Integration
- **4 Core Publications Integrated**: Published the 4 official TLCS articles (`🦁 TRADE WHAT YOU SEE, NOT WHAT YOU FEEL`, `🌪️ NAVIGATING VOLATILITY IN MODERN MARKETS`, `🎯 MASTERING THE TLCS TERMINAL`, `🔔 THE PSYCHOLOGY OF ALERTS TRADING`) across [`blog.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/blog.html) and [`article.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/article.html). Integrated an inline full-screen Glassmorphic Article Reader Modal on `blog.html` and enabled standalone reader links (`article.html?id=...`). Persisted articles in Supabase `blogs` table.

---

### 18. Landing Page Real Statistics Mapping & Telegram Channel Diverter
- **Real Consolidated Metrics**: Mapped the landing page statistics grid on [`index.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/index.html) to the real AI Scanner weekly consolidated metrics (`874+ Trades Analyzed`, `44.5% Avg Win Rate`, `3.59 Profit Factor`, `+3.46% Net Edge`, `+15.07% Half-Kelly`).
- **Telegram Channel Diverter**: Reframed the email subscription callout box on `index.html` into a direct Telegram Channel diverter promoting real-time NYMEX trade alerts (`@TLCS_Alerts`).

---

### 19. Instagram Automation Engine (@thelioncapitaladvisors) — Market Close Schedule & Metrics
- **Netlify Background Dispatcher**: Built [`cron-instagram-stats.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/cron-instagram-stats.js) and diagnostic test function [`test-instagram.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/test-instagram.js) running every 15 minutes to evaluate time and trigger automated posts linked directly to the session close hours of each market category (`Nifty 50`: 15:35 IST, `MCX`: 23:45 IST, `NYMEX`: 02:35 IST, `Forex`: 02:40 IST, `World Indices`: 02:45 IST, `Crypto`: 05:35 IST).
- **Full 3-Tier Enclosed Metrics**: Reports include Daily Session Metrics (Closed Executions, Wins/Losses/BE, Win Rate %, Profit Factor, System Edge %, Avg Winner/Loser, Best Trade), Weekly Performance Cards (Weekly Trades, Success %, Profit Factor, TLCS Net Edge %), and All-Time Cumulative Edge (Recorded Trades, Win Rate %, Profit Factor, Half-Kelly %).

---

### 20. Official TLCS Automated Social Media & Marketing Architecture Plan
- **Unified Marketing & Acquisition Strategy**:
  1. **Telegram Live Execution Lead Funnel**: Direct Telegram Channel CTA (`@TLCS_Alerts`) on [`index.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/index.html) capturing real-time trade alert subscribers.
  2. **Automated Instagram Performance Proof**: Daily session close & weekly performance automated dispatches to `@thelioncapitaladvisors` establishing algorithmic transparency.
  3. **Content Marketing Knowledge Base**: 4 core published articles with glassmorphic modal reader on [`blog.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/blog.html) and standalone reader on [`article.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/article.html) with back buttons (`← Back to Blogs and FAQs`) routing to `#blog-section`.
