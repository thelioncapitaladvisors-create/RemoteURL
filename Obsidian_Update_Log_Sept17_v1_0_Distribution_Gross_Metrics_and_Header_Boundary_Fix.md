# Obsidian Update Log: Version 1.0 (17 Sept 2026)
## Distribution Inspection Bar Gross Win/Loss Metrics & Screener Header Boundary Fix

---

### 1. Overview & Core Enhancements
Version 1.0 introduces enhanced mathematical transparency to the normalized trade performance distribution inspection bar and eliminates header button boundary overflow on mobile viewports:

1. **Inspection Bar Gross Win & Gross Loss Metrics**:
   - **Balanced Visual Arithmetic**: Replaced single-trade extremes (`↓ loss` worst loss, `↑ win` best win) in the inspection bar above the normalized trade distribution chart with aggregate session figures:
     - **`↓ gross loss`**: Sum of all realized losses formatted semantically in rose (`formatDistVal(-grossLoss, distUnit)`).
     - **`↑ gross win`**: Sum of all realized gains formatted semantically in emerald (`formatDistVal(grossWin, distUnit)`).
   - **Intuitive Visual Balance**:
     $$\mathbf{\text{NET}} = \mathbf{\text{Gross Win}} - \mathbf{\text{Gross Loss}}$$
     Directly aligning the displayed numbers with user intuition without losing the mathematical derivation of net performance.
   - **Single-Trade Bounds Retained**: Individual trade extremes (**`Min Loss`**, **`Max Loss`**, **`Max Win`**, **`Min Win`**) remain clearly displayed along the X-axis bounds beneath the symmetric per-trade bell curve.

2. **Screener & Paper Portfolio Header Overflow Fix & Line Split**:
   - **Dedicated Row Placement**: In `Tv-Alert-Mobile/src/app/page.tsx`, updated the header control clusters for both the **TLCS Screener Matrix** and the **Virtual Paper Portfolio**:
     - Converted the header containers to `flex flex-col gap-2 pb-2`, bringing the action button controls (`START AFRESH`, `RESTORE`, `COLLAPSE`/`EXPAND`) down by one line onto their own dedicated row beneath the title and subtitle.
     - With the controls occupying their own line, the title text is free to expand without awkward wrapping, and the action buttons have 100% card width with zero risk of collision, boundary overflow, or text truncation.

3. **TradingView Indicator Header Table (`tbl_bias`) Vertical Offset**:
   - **1-Line Spacer Shift**: In `TV Indicator/TLCS_Live_Pivot_Alerts.pine` and `TV_Indicator_Full_Code.txt`:
     - Updated `tbl_bias` from 2 rows to 3 rows (`table.new(position.top_center, 3, 3)`).
     - Row 0 is now a dedicated blank spacer (`" "` in `size.small`), shifting the entire 2-row display (`dX` & `mX` on Row 1, `c1` on Row 2) down by one line.
     - Prevents any overlap or visual collision with the TradingView indicator header bar and ticker OHLC statistics.

---

### 2. Files Modified
- `Tv-Alert-Mobile/src/app/page.tsx`:
  - Lines 4805–4820: Updated interactive inspection bar to display `↓ gross loss` and `↑ gross win`.
  - Lines 7098–7159: Brought Screener Matrix header action buttons down by one line (`flex-col gap-2`).
  - Lines 7702–7748: Brought Paper Portfolio header action buttons down by one line (`flex-col gap-2`).
- `TV Indicator/TLCS_Live_Pivot_Alerts.pine` & `TV_Indicator_Full_Code.txt`:
  - Lines 868–890: Shifted `tbl_bias` down by one line with a 3-row layout and Row 0 blank spacer.
- `.agents/AGENTS.md`:
  - Lines 1165–1170: Updated canonical Pine Script indicator header bar specification to 3 rows.
- `Obsidian_Update_Log_Sept17_v1_0_Distribution_Gross_Metrics_and_Header_Boundary_Fix.md`:
  - Official release log documenting math formulas, dedicated header line split, TradingView table offset, and commit history.
