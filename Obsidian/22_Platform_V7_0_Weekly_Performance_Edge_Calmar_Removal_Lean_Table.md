# TLCS Platform Architecture Note: Weekly Performance Edge Lean Table Architecture (v7.0)

**Document ID**: `TLCS-DOC-20261002-V7-WEEKLY-EDGE-LEAN-TABLE`  
**Date**: October 2, 2026  
**Platform Version**: `v7.0` (`7.0.0`)  
**Target Applications**: `Tv-Alert-Mobile` (Next.js PWA), `.agents/AGENTS.md`  

---

## 1. Executive Summary

To keep the financial audit data presentation lean, readable, and visually unconstrained on mobile and tablet displays, the **`Calmar`** column has been permanently removed from the **Weekly Performance Edge** table in the **ANALYTICS** tab of the mobile terminal (`page.tsx`).

The table has been re-architected into a balanced 6-column grid where remaining financial metrics receive generous horizontal space, eliminating cramped text wrapping and horizontal overflow.

---

## 2. Re-Balanced Column Proportion Structure

| Column | Previous Width | Updated Lean Width | Content Alignment |
| :--- | :--- | :--- | :--- |
| **`Wk`** | 7% | **8%** | Center |
| **`Date`** | 18% | **21%** | Left (`CUMULATIVE` / `DD Mon`) |
| **`Win Rate`** | 15% | **18%** | Center (`XX.XX%`, `Wins/Losses`) |
| **`Net Edge`** | 16% | **19%** | Center (`+X.XX%`, `Avg:±X.XX%`) |
| **`PF`** | 14% | **16%** | Center (`X.XX`, `Ratio`) |
| **`Kelly`** | 15% | **18%** | Center (`+X.XX%`, `Risk`) |
| **Total** | **100% (7 cols)** | **100% (6 cols)** | **Evenly balanced across 100% width** |

---

## 3. Compliance & Verification

- **Target Table**: `Weekly Performance Edge` in `page.tsx` (`ANALYTICS` tab).
- **TypeScript Build**: `tsc --noEmit` $\rightarrow$ **PASS (0 errors)**.
- **Visual Presentation**: Zero column collision; ample breathing room for cumulative and weekly date strings.
