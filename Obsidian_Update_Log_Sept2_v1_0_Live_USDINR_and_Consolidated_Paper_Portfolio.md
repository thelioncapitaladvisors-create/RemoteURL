# Version 1.0 Production Update: Live USD/INR Pair Price Benchmark, Multi-Asset Rupee Consolidation, Automated Active Trade Breach Fallback Scanner, Metric Pill Containment & Automated Strategy Tearsheet Sync

**Release Date:** September 2, 2026  
**Milestone Version:** `v1.0.0` (Production)  
**System Components Affected:** `Tv-Alert-Mobile (page.tsx)`, `TLCS_Website_Deploy (dashboard.html, generate_tearsheet.py, strategy_tearsheet.html, .github/workflows/generate_tearsheet_cron.yml)`, `Netlify Functions (cron-weekly-logs.js, cron-heal-outcomes.js)`

---

## 1. Live USD/INR Pair Price of the Day Benchmark
- **Problem**: Foreign asset trades (NYMEX, Crypto, Forex, and World Indices) were either displayed in raw US dollars (`$`) or multiplied using static hardcoded conversion rates, creating minuscule values (e.g. `+₹32`) and misrepresenting multi-asset returns.
- **Architectural Fix**:
  - **Dynamic Market Exchange Rate**: Frontend and backend dynamically query the live USD/INR pair price of the day (`usdInrRate`), verifying active `USDINR` signals/pivots first, with fallback to real-time daily FX feeds and Yahoo Finance's `USDINR=X` chart feed.
  - **Client-Side Caching**: Cached in local storage (`tlcs_usd_inr_rate`) with a 5-minute background refresh loop ensuring instant rendering without layout flicker.
  - **Dynamic UI Display**: Sizing subtitles across all foreign markets render the active market conversion rate dynamically (e.g., `USD to ₹ @ 94.96`).

---

## 2. Universal Paper Portfolio Rupee (`₹`) Consolidation
- **Problem**: When selecting different markets or `ALL MARKETS (Multi-Asset)`, metrics switched between `$` and `₹`, preventing consolidated multi-asset portfolio evaluation.
- **Architectural Fix**:
  - **Universal Currency**: All 6 market categories (`NIFTY 50`, `MCX COMMODITIES`, `NYMEX & COMEX`, `CRYPTO TOP 25`, `FOREX PAIRS`, `WORLD INDICES`, and `ALL MARKETS`) are consolidated strictly in **Rupees (`₹`)**.
  - **Standard 1-Lot Position Sizing**:
    - **NIFTY 50**: `65 Qty` (NIFTY1!) / `15 Qty` (BANKNIFTY) / `100 Shares` (Indian Equities).
    - **MCX**: `100 Qty` (Crude/Gold), `30 Qty` (Silver), `1250 Qty` (Natural Gas).
    - **NYMEX / COMEX**: `100 bbl` (CL), `2500 mmBtu` (NG), `10 oz` (GC), `1000 oz` (SI) converted at live `usdInrRate`.
    - **Crypto Top 25**: `0.1 BTC`, `1 ETH`, `10 SOL`, `10,000 Units` for low-priced tokens (DOGE, ADA, XRP) converted at live `usdInrRate`.
    - **Forex Pairs**: `10,000 Units` (0.1 Mini Lot) converted at live `usdInrRate`.
    - **World Indices**: `1 Contract` ($1/pt) converted at live `usdInrRate`.
  - **Rupee Tranches**: Capital presets unified across all views into **`1L` (₹1 Lakh)**, **`5L` (₹5 Lakhs)**, **`10L` (₹10 Lakhs)**, and **`25L` (₹25 Lakhs)**.

---

## 3. Metric Pill Border Containment & Dynamic Text-Scaling
- **Problem**: In the 10-pill KPI metrics grid (`ACTIVE LIMITS`, `LIVE TRADES`, `CLOSED TRADES`, `TODAY'S SUCCESS`, `TODAY'S PROFIT FACTOR`, `WEEKLY TRADES`, `WEEKLY SUCCESS`, `WEEKLY PROFIT FACTOR`, `WEEKLY EXPECTANCY`, `WEEKLY CALMAR`), bold italic characters and percentages (such as `+0.14%`, `100.0%`, `22%`) were overflowing their pill card containers and bleeding into adjacent pills.
- **Architectural Fix**:
  - **Strict Container Isolation**: Every pill card applies `overflow-hidden w-full max-w-full` and structured padding `py-2.5 px-0.5 sm:px-1.5`.
  - **Dynamic Length-Based Value Scaling (`getPillValueSize`)**: Automatically scales typography depending on the rendered character length:
    - $\le 2$ chars (`0`, `2`, `10`, `50`): `text-base sm:text-lg md:text-xl`
    - 3–4 chars (`20%`, `1.09`, `1.02`, `0.06`): `text-sm sm:text-base md:text-lg`
    - 5–6 chars (`+0.14%`, `-1.25%`, `100%`): `text-xs sm:text-sm md:text-base`
    - $> 6$ chars: `text-[10px] sm:text-xs md:text-sm`
  - **Single-Line Truncation Guard**: `truncate max-w-full px-0.5` ensures numbers and `%` signs never break onto a second line or poke past pill edges.

---

## 4. Analytics Tab Table Proportional Layout & Zero Horizontal Blowout
- **Problem**: Tables in the **ANALYTICS** Tab (`Weekly Performance Edge`, `Daily Signal Dashboard`, `Weekly Signal Performance & Achievement`) were wrapped in `min-w-[550px]` containers, forcing horizontal scrollbars and cutting off right-hand columns (such as `PF`, `Kelly`, `Net`, and `Avg`).
- **Architectural Fix**:
  - **Proportional `table-fixed w-full` Layout**: Removed all arbitrary min-widths and established edge-to-edge column percentages matching the mobile viewport perfectly.
  - **Weekly Performance Edge**: `Wk` (10%), `Date` (26%), `Win Rate` (20%), `Net Edge` (22%), `PF` (11%), `Kelly` (11%).
  - **Daily Signal Dashboard**: `Filter` (30%), `Today` (70%).
  - **Weekly Signal Performance & Achievement**: `Day` (21%), `Sigs` (19%), `WR` (16%), `Targets` (20%), `Net` (12%), `Avg` (12%).

---

## 5. Automated Strategy Tearsheet Generation on Market Closure
- **Problem**: The VectorBT strategy tearsheet iframe in the Analytics tab remained on August 31st data instead of automatically progressing through September 1st and September 2nd data upon market closure.
- **Architectural Fix**:
  - **Automated Market Close Schedule**: GitHub Actions workflow (`.github/workflows/generate_tearsheet_cron.yml`) scheduled across all market close boundaries (NSE 16:00 IST, MCX 00:00 IST, NYMEX 22:30 UTC, Global 00:30 UTC).
  - **CI/CD Token & Permissions**: Added `token: ${{ secrets.GITHUB_TOKEN }}` and `permissions: contents: write` to ensure the automated bot commits and pushes the generated `strategy_tearsheet.html` back to `TLCS_Website`.
  - **Zero-Failure Credential Fallback**: Added robust default Supabase fallbacks inside `generate_tearsheet.py` so CI runs never fail due to missing environment variables.
  - **Immediate Regenerated Tearsheet**: Re-ran the engine over all 54 closed trades and pushed live to production through September 2, 2026.

---

## 6. Automated Live Active Trade Breach Fallback Scanner
- **Problem**: Intermittent webhook timeouts from TradingView (e.g., `"Webhook delivery failed — request took too long and timed out"`) left exited trades in `Active` status without exit prices or P&L outcomes.
- **Architectural Fix**:
  - **Active Breach Scanner (`cross_check_active_trades`)**: Built into `yahoo_helper.py` to query 1-minute and 5-minute intraday market history for all open/active signals since entry.
  - **Stop-Loss / Take-Profit Verification**:
    - Long trades breaching `stop` → auto-exited as `Hit Initial SL`, `outcome = 'LOSS'`, `exit_price = stop`.
    - Long trades breaching `target` → auto-exited as `Completed TP1`, `outcome = 'WIN'`, `exit_price = target`.
    - Short trades breaching `stop` → auto-exited as `Hit Initial SL`, `outcome = 'LOSS'`, `exit_price = stop`.
    - Short trades breaching `target` → auto-exited as `Completed TP1`, `outcome = 'WIN'`, `exit_price = target`.
  - **EOD Session Auto-Close**: Closed market trades (e.g. NSE at 15:30 IST) auto-resolved to `EOD Exit (TP1)` or `EOD Exit (SL)` based on exact session closing prices.
