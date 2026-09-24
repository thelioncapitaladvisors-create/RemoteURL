# Obsidian Update Log: September 24, 2026 (v4.0)
## Master Architecture: Trade Distribution Histogram Bounds Alignment & Continuous GIFT NIFTY Session Protection

---

### 1. Executive Summary & Version 4.0 Platform Baseline
Under **Platform Version 4.0 (`v4.0` / `4.0.0`)**, two major enhancements were implemented, verified, and deployed across the production ecosystem:
1. **Trade Distribution Histogram Bounds Alignment**: Re-architected the X-axis bounds layout on both the Next.js mobile terminal (`page.tsx`) and the web tearsheet (`blog.html`). Grouped similar pill types on the same row (`Max Loss` & `Max Win` on the top row; `Min Loss`, `₹0`, and `Min Win` on the bottom row) and enlarged font size and padding for immediate operational legibility.
2. **GIFT NIFTY Continuous Futures Protection in Automated EOD Sweeps**: Resolved the premature 15:30 IST domestic equity EOD close bug affecting continuous futures (`NIFTY1!`, `BANKNIFTY1!`), ensuring live position persistence across the full GIFT trading schedule (06:30 AM to 02:45 AM IST next day).

---

### 2. Trade Distribution Bounds Hierarchy Standard

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TRADE DISTRIBUTION HISTOGRAM                     │
│               [  Losses Ascending  ]   │   [  Wins Descending  ]       │
└────────────────────────────────────────┼───────────────────────────────┘
                                         │ (Center Dotted Line)
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

#### Typography & Visual Styling
* **Top Row (Extreme Bounds)**:
  * `Max Loss`: `text-xs sm:text-[13px] md:text-sm font-black`, `bg-rose-500/15 text-rose-600 dark:text-rose-300 border border-rose-500/30 px-2.5 py-0.5 sm:py-1`
  * `Max Win`: `text-xs sm:text-[13px] md:text-sm font-black`, `bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border border-emerald-500/30 px-2.5 py-0.5 sm:py-1`
* **Bottom Row (Baseline Bounds & Zero Line)**:
  * `Min Loss`: `text-xs sm:text-[13px] md:text-sm font-black`, `bg-rose-500/15 text-rose-600 dark:text-rose-300 border border-rose-500/30 px-2.5 py-0.5 sm:py-1`
  * `₹0` / `0.00%`: `text-xs sm:text-[13px] font-black`, `bg-secondary/50 border border-primary/20 px-2.5 py-0.5 sm:py-1`
  * `Min Win`: `text-xs sm:text-[13px] md:text-sm font-black`, `bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border border-emerald-500/30 px-2.5 py-0.5 sm:py-1`
* **Summary Row**:
  * Scaled font size to `text-[11px] sm:text-xs md:text-[13px] font-mono font-black`
  * Status indicator dot scaled to `w-2.5 h-2.5`
  * Padding increased to `px-3 sm:px-3.5 py-1 sm:py-1.5`

---

### 3. Continuous GIFT NIFTY Session Protection Logic

1. **Continuous Contract Recognition**:
   ```javascript
   const isGiftContinuous = (symbol || '').toUpperCase().includes('1!') && 
                            (sym === 'NIFTY' || sym === 'BANKNIFTY');
   ```
2. **Session Guard**:
   If `isGiftContinuous` and `isCreatedToday`, returns `false` during regular hours. Only swept if:
   * Trade age exceeds 22 hours (`hoursAgo > 22`), OR
   * During the official daily maintenance window (`istHours >= 2.75 && istHours < 6.5`).
3. **Session Close ISO Generation**:
   Continuous GIFT contracts are stamped to close at `21:15:00Z` (02:45 AM IST next morning) rather than `10:00:00Z` (15:30 IST).

---

### 4. Git Repositories and Platform Artifacts

* **Root Repository**: Updated `.agents/AGENTS.md`, `Obsidian/10_Trade_Distribution_Histogram_Alignment_and_GIFT_Continuous_Protection.md`, and `Obsidian_Update_Log_Sept24_v4_0_Trade_Distribution_and_GIFT_Session_Protection.md`.
* **Tv-Alert-Mobile**: Pushed commit `14e9225` (`style(distribution): align similar pills in top/bottom rows and enlarge font size`).
* **TLCS_Website_Deploy**: Pushed commit `0ed3e1e` (`style(distribution): align similar pills in top/bottom rows and enlarge font size`).
