---
title: "Mathematical Formulas & Pivot Engine Specifications"
project: "TLCS Quantitative Trading Ecosystem"
module: "Camarilla & CPR Math Core"
author: "The Lion Capital Advisors"
date_created: 2026-09-18
last_updated: 2026-09-18
tags:
  - math
  - camarilla
  - cpr
  - pivots
  - formulas
  - exact_pct
equations:
  - Camarilla H1-H5, L1-L5
  - Central Pivot Range (CPR)
  - Triple EMA (8, 21, 34)
  - Canonical Exact Percentage Method
---

# Mathematical Formulas & Pivot Engine Specifications

## 1. Camarilla Equation System

Camarilla pivot points utilize the prior session's High ($H$), Low ($L$), and Close ($C$) to compute deterministic intraday support and resistance boundaries.

### Daily Range Definition
$$\text{Range} = H - L$$

### Camarilla Pivot Tiers
$$\begin{aligned}
H_5 &= \left(\frac{H}{L}\right) \times C \\
H_4 &= C + \text{Range} \times \frac{1.1}{2} = C + \text{Range} \times 0.55 \\
H_3 &= C + \text{Range} \times \frac{1.1}{4} = C + \text{Range} \times 0.275 \\
H_2 &= C + \text{Range} \times \frac{1.1}{6} \approx C + \text{Range} \times 0.1833 \\
H_1 &= C + \text{Range} \times \frac{1.1}{12} \approx C + \text{Range} \times 0.0917 \\
L_1 &= C - \text{Range} \times \frac{1.1}{12} \approx C - \text{Range} \times 0.0917 \\
L_2 &= C - \text{Range} \times \frac{1.1}{6} \approx C - \text{Range} \times 0.1833 \\
L_3 &= C - \text{Range} \times \frac{1.1}{4} = C - \text{Range} \times 0.275 \\
L_4 &= C - \text{Range} \times \frac{1.1}{2} = C - \text{Range} \times 0.55 \\
L_5 &= C - (H_5 - C)
\end{aligned}$$

---

## 2. Central Pivot Range (CPR) Formulation

The Central Pivot Range defines the institutional value anchor of the session:

$$\begin{aligned}
\text{Pivot (P)} &= \frac{H + L + C}{3} \\
\text{Bottom Central (BC)} &= \frac{H + L}{2} \\
\text{Top Central (TC)} &= (\text{Pivot} - \text{BC}) + \text{Pivot} = 2 \times \text{Pivot} - \text{BC}
\end{aligned}$$

### CPR Width Classification (Volatility Regime)
$$\text{CPR Width} = |\text{TC} - \text{BC}|$$
- **Narrow CPR** ($\text{Width} < 0.25 \times \text{ADR}$): Trending / Breakout Day anticipated.
- **Average CPR**: Normal distribution.
- **Wide CPR** ($\text{Width} > 0.65 \times \text{ADR}$): Sideways / Mean-reversion / Trading Range Day.

---

## 3. Triple Exponential Moving Averages (EMA)

Calculated on close prices using exponential smoothing factor $\alpha = \frac{2}{N + 1}$:

$$\text{EMA}_t = \alpha \times C_t + (1 - \alpha) \times \text{EMA}_{t-1}$$

- **Fast Ribbon**: $\text{EMA}_8$ ($\alpha = \frac{2}{9} \approx 0.2222$)
- **Medium Anchor**: $\text{EMA}_{21}$ ($\alpha = \frac{2}{22} \approx 0.0909$)
- **Macro Trend Filter**: $\text{EMA}_{34}$ ($\alpha = \frac{2}{35} \approx 0.0571$)

---

## 4. Canonical Exact Percentage Method (Single Source of Truth)

In strict adherence to **Version 1.0 Platform Rules**, all outcomes, P/L percentages, win rates, and profit factors rely solely on the exact percentage formula:

### Long Trades
$$\text{exact\_pct} = \left(\frac{\text{Exit Price} - \text{Entry Price}}{\text{Entry Price}}\right) \times 100$$

### Short Trades
$$\text{exact\_pct} = \left(\frac{\text{Entry Price} - \text{Exit Price}}{\text{Entry Price}}\right) \times 100$$

### Canonical Outcome Resolution Rules
$$\text{Outcome} = \begin{cases}
\text{WIN} & \text{if } \text{exact\_pct} > 0 \\
\text{LOSS} & \text{if } \text{exact\_pct} < 0 \\
\text{BREAKEVEN} & \text{if } \text{exact\_pct} = 0.00
\end{cases}$$

### Canonical Win Rate / Success Rate Formula
$$\text{Win Rate} = \left(\frac{\text{Total Wins}}{\text{Total Realized Closed Trades}}\right) \times 100$$
*(Note: Breakeven trades MUST be included in the denominator; $(W + L)$ alone is strictly prohibited).*
