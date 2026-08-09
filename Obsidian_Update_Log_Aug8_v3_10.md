# Update Log: Version 3.10
**Date:** Aug 8, 2026
**Components:** TLCS Indicator Pine Script

## 1. Divergence X-Cross Visibility Fix
- **Issue:** The red 'D' (Bearish Divergence) was fully overlapping and hiding the red X-cross because both elements were plotted using similar vertical anchoring on TradingView (`yloc.abovebar` and `label.style_label_down` at the exact same bar), causing the opaque Divergence box to swallow the X-cross.
- **Solution:** 
  - Restructured the plotting logic to leverage a transparent label box for the X-cross.
  - Implemented a programmatic newline offset technique (`"\n\n✖"` for Bearish, `"✖\n\n"` for Bullish) combined with `label.style_label_down` and `label.style_label_up`.
  - This perfectly forces the X-cross icon outside of the Divergence box's bounding area, ensuring it plots distinctly above (for bearish) or below (for bullish) the divergence signal without relying on imprecise `yloc.abovebar` rendering overlaps.
  - Sized the X-cross to `size.normal` to make it prominent and easily discernible against the chart.

## 2. Code Compilation
- Version incremented from 3.9 to 3.10.
