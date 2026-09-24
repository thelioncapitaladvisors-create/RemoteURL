# Obsidian Architectural Documentation: September 24, 2026 (v4.0)
## Master Architecture: Trade Distribution Histogram Bounds Alignment & Continuous GIFT NIFTY Session Protection

---

### 1. Executive Summary & Version 4.0 Baseline
This document formally ratifies two critical UI and operational milestones under **Platform Version 4.0**:
1. **Trade Distribution Histogram Bounds Alignment & Legibility Overhaul**: Standardized the X-axis bounds pills beneath the Trade Distribution histogram across both mobile and web tearsheets, grouping similar metric bounds on the same row (`Max Loss` & `Max Win` on the top row; `Min Loss`, `₹0`, and `Min Win` on the bottom row) and increasing text font size and padding for immediate operational legibility.
2. **GIFT NIFTY Continuous Futures Protection in Automated EOD Sweeps**: Eliminated the premature 15:30 IST domestic equity EOD closure bug on continuous futures (`NIFTY1!`, `BANKNIFTY1!`), guaranteeing live position persistence through the full GIFT trading day (06:30 AM to 02:45 AM IST).

---

### 2. Trade Distribution Histogram Bounds Hierarchy

#### Root Cause of Previous Pill Inversion
In previous implementations, bounds pills were rendered using two separate `flex flex-wrap` containers:
* **Left Container**: `[Min Loss, Max Loss]`
* **Right Container**: `[Max Win, Min Win]`

When rendered on narrow mobile screens (or responsive cards), each container wrapped into two distinct lines:
* **Row 1**: Left displayed `Min Loss`, Right displayed `Max Win` (mismatched metric types).
* **Row 2**: Left displayed `Max Loss`, Right displayed `Min Win` (mismatched metric types).

Furthermore, the pill text font size (`text-[10.5px]`) and summary pills (`text-[10px]`) were compact, making them hard to read at a glance on mobile devices.

#### The Version 4.0 Standardized Layout
The layout has been re-architected into explicit, dedicated columns with matching vertical rows:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TRADE DISTRIBUTION HISTOGRAM                     │
│               [  Losses Ascending  ]   │   [  Wins Descending  ]       │
└────────────────────────────────────────┼───────────────────────────────┘
                                         │ (Center Dotted Baseline)
                                         ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TOP ROW (Extreme Strategy Bounds):                                     │
│ [ Max Loss: -₹380 ]                                [ Max Win: +₹240 ]  │
│                                                                        │
│ BOTTOM ROW (Zero-Adjacent Baseline Bounds):                            │
│ [ Min Loss: -₹60 ]                 [  ₹0  ]        [ Min Win: +₹60  ]  │
└────────────────────────────────────────────────────────────────────────┘
                                         ▼
┌────────────────────────────────────────────────────────────────────────┐
│ SUMMARY ROW:                                                           │
│    (● 2 WINS)       (● 6 LOSSES)       (● 1 B/E)       (9 TOTAL)       │
└────────────────────────────────────────────────────────────────────────┘
```

#### Typography & Visual Specifications
* **Top Row (Extreme Bounds)**:
  * `Max Loss`: `bg-rose-500/15 text-rose-600 dark:text-rose-300 border-rose-500/30 text-xs sm:text-[13px] md:text-sm font-black px-2.5 py-0.5 sm:py-1`
  * `Max Win`: `bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30 text-xs sm:text-[13px] md:text-sm font-black px-2.5 py-0.5 sm:py-1`
* **Bottom Row (Baseline Bounds & Zero Line)**:
  * `Min Loss`: `bg-rose-500/15 text-rose-600 dark:text-rose-300 border-rose-500/30 text-xs sm:text-[13px] md:text-sm font-black px-2.5 py-0.5 sm:py-1`
  * `₹0` / `0.00%`: `bg-secondary/50 border-primary/20 text-xs sm:text-[13px] font-black px-2.5 py-0.5 sm:py-1`
  * `Min Win`: `bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30 text-xs sm:text-[13px] md:text-sm font-black px-2.5 py-0.5 sm:py-1`
* **Distribution Summary Row**:
  * Font size increased to `text-[11px] sm:text-xs md:text-[13px] font-mono font-black`
  * Status indicator dot scaled to `w-2.5 h-2.5`
  * Padding increased to `px-3 sm:px-3.5 py-1 sm:py-1.5`

---

### 3. Continuous GIFT NIFTY Session Protection Architecture

#### Root Cause Analysis
At 15:30 IST (10:00 UTC), Netlify's scheduled EOD worker (`cron-eod-close.js`) ran its automated sweep.
Because `cleanSymbol('NIFTY1!')` stripped the trailing `1!` suffix to `NIFTY`, the worker evaluated:
```javascript
if (niftySymbols.includes(sym) && istHours >= 15.5) // Evaluated to TRUE
```
The automated script treated `NIFTY1!` as a domestic NSE cash equity, assumed the session was closed at 15:30 IST, and forced an `EOD_FORCE_CLOSE`, setting `exit_price = s.trail_sl` (`23,330.00`), converting an active +360 pt winning short trade into a closed `BREAKEVEN 0.00%` trade.

#### Continuous Session Operating Reality
`NIFTY1!` and `BANKNIFTY1!` are continuous contracts traded on the NSE IX (GIFT City):
* **Morning Session**: 06:30 AM – 03:40 PM IST
* **Evening Session**: 04:35 PM – 02:45 AM IST (next day)
* **Daily Maintenance Window**: 02:45 AM – 06:30 AM IST

#### Permanent Protection Logic
1. **Explicit Continuous Contract Detection**:
   ```javascript
   const isGiftContinuous = (symbol || '').toUpperCase().includes('1!') && 
                            (sym === 'NIFTY' || sym === 'BANKNIFTY');
   ```
2. **Session Gate Safeguard**:
   If `isGiftContinuous` and the trade was created today (`isCreatedToday`), it returns `false` during regular operating hours.
   It is strictly protected from early 15:30 IST sweeps and only swept if:
   * Trade age exceeds 22 hours (`hoursAgo > 22`), OR
   * During the official daily maintenance window (`istHours >= 2.75 && istHours < 6.5`).
3. **Session Close ISO Generation**:
   Continuous GIFT contracts are closed at `21:15:00Z` (02:45 AM IST next day) rather than `10:00:00Z` (15:30 IST).

---

### 4. Verification & Deployment Baseline

| System / Component | File | Version | Status |
| :--- | :--- | :--- | :--- |
| **Mobile PWA Terminal** | `Tv-Alert-Mobile/src/app/page.tsx` | `4.0.0` | Production build verified (`0 errors`) |
| **Mobile Cron Route** | `Tv-Alert-Mobile/src/app/api/cron/eod-close/route.ts` | `4.0.0` | GIFT continuous protection deployed |
| **Netlify Background Worker** | `TLCS_Website_Deploy/netlify/functions/cron-eod-close.js` | `4.0.0` | Continuous session awareness deployed |
| **Web Strategy Tearsheet** | `TLCS_Website_Deploy/blog.html` | `4.0.0` | Bounds alignment and typography updated |
| **Supabase Database** | `signals` table | `v4.0` | Live trade `878ef2bf` restored to `⚡ TRADE ACTIVE` |
| **Agent Mandates** | `.agents/AGENTS.md` | `v4.0` | Ratified Version 4.0 Platform Baseline |
