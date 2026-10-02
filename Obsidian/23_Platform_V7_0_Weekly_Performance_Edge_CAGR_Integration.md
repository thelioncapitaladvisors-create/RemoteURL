# TLCS Platform Architecture Note: Weekly Performance Edge CAGR Integration (v7.0)

**Document ID**: `TLCS-DOC-20261002-V7-WEEKLY-EDGE-CAGR-INTEGRATION`  
**Date**: October 2, 2026  
**Platform Version**: `v7.0` (`7.0.0`)  
**Target Applications**: `Tv-Alert-Mobile` (Next.js PWA), `.agents/AGENTS.md`  

---

## 1. Executive Summary

At the position of the removed `Calmar` column in the **Weekly Performance Edge** table on the mobile terminal (`page.tsx`, **ANALYTICS** tab), a deterministic **Compounded Annual Growth Rate (`CAGR`)** column has been introduced.

This provides institutional annual compounding visibility based on weekly net growth rates ($R_w$), both at the granular weekly level and across the multi-week cumulative trajectory.

---

## 2. Mathematical Formulation & Institutional Annualization

Annualization in systematic weekly trading assumes $M = 52$ active trading weeks per calendar year.

### 2.1 Single-Week Annualized Compounding (Weekly Rows)
For an individual week with net growth rate $R_w$ (in percent, e.g. $+1.04\%$ or $-0.09\%$):
$$\text{Factor}_w = 1 + \frac{R_w}{100}$$
$$\text{CAGR}_w = \left[\left(\text{Factor}_w\right)^{52} - 1\right] \times 100$$

- **Positive Return Example** ($R_w = +1.04\%$):
  $$\text{CAGR} = \left[(1.0104)^{52} - 1\right] \times 100 = +71.32\%$$
- **Negative Return Example** ($R_w = -0.09\%$):
  $$\text{CAGR} = \left[(0.9991)^{52} - 1\right] \times 100 = -4.57\%$$

### 2.2 Multi-Week Cumulative Compounded Growth (Cumulative Row)
For a sequence of $N$ completed trading weeks with weekly returns $R_{w,1}, R_{w,2}, \dots, R_{w,N}$, the cumulative compounding factor $G$ is:
$$G = \prod_{i=1}^{N} \left(1 + \frac{R_{w,i}}{100}\right)$$
The annualized compounded rate across $N$ weeks is:
$$\text{CAGR}_{\text{cum}} = \left[G^{\frac{52}{N}} - 1\right] \times 100$$

- **Example ($N = 5$ weeks, $G = 1.003855$, net $+0.39\%$)**:
  $$\text{CAGR} = \left[(1.003855)^{\frac{52}{5}} - 1\right] \times 100 = +4.08\%$$

---

## 3. Re-Balanced Column Proportion Structure

The 7 columns occupy exactly 100% of table width with generous space allocated to date descriptors and financial ratios:

| Column | Width | Alignment | Typography & Semantic Color |
| :--- | :--- | :--- | :--- |
| **`Wk`** | **7%** | Center | Primary font-bold |
| **`Date`** | **20%** | Left | Amber-accent for `CUMULATIVE`, Primary for `DD Mon` |
| **`Win Rate`** | **15%** | Center | Emerald ($\ge 50\%$) / Rose ($<50\%$) |
| **`Net Edge`** | **15%** | Center | Emerald ($\ge 0\%$) / Rose ($<0\%$) |
| **`PF`** | **13%** | Center | Emerald ($\ge 1.5$) / Amber ($\ge 1.0$) / Rose ($<1.0$) |
| **`CAGR`** | **15%** | Center | Emerald ($\ge 0\%$) / Rose ($<0\%$) with `+`/`-` formatting |
| **`Kelly`** | **15%** | Center | Amber ($>0\%$) / Rose ($<0\%$) |
| **Total** | **100%** | — | **Zero text overlap, zero truncation** |

---

## 4. Verification & Build Confirmation

- **TypeScript Typecheck**: Verified via `./node_modules/.bin/tsc --noEmit` $\rightarrow$ **0 errors**.
- **Edge-Case Bounds Handling**:
  - Handles non-positive growth factors ($G \le 0$) with clean floor at `-100.0%`.
  - Formats large numbers ($|\text{CAGR}| \ge 100\%$) cleanly with 1 decimal place (`+71.3%`) and sub-hundred values with 2 decimal places (`+4.08%`).
  - Caps extreme values at `>9999%`.
