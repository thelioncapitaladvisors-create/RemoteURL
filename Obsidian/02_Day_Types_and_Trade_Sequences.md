---
title: "Day Type Blueprints & Trade Sequence Classification"
project: "TLCS Quantitative Trading Ecosystem"
module: "Market Profile & Price Action Classifier"
author: "The Lion Capital Advisors"
date_created: 2026-09-18
last_updated: 2026-09-18
tags:
  - market-profile
  - blueprints
  - sequences
  - pivotboss
  - day-types
blueprints:
  - Rejection Day Blueprint
  - Stop Run Day Blueprint
  - Absorption Day Blueprint
  - Failed New Low/High Blueprint
  - Outside Day Blueprint
sequences:
  - Rejection Day Sequence
  - Stop Run Sequence
  - Failed Absorption Sequence
  - Accumulation / Distribution Sequence
---

# Day Type Blueprints & Trade Sequence Classification

> [!IMPORTANT]
> **Strict Prohibition on Terminology Alteration**:
> Never introduce variant terminology (e.g. "Failed Breakout", "Retest", "Fade"). The system strictly permits only the canonical blueprint and sequence names defined below.

---

## 1. The 5 Day Type Blueprints

### A. Rejection Day Blueprint
Occurs when price extends aggressively away from value, meets strong responsive participants, and snaps back, leaving an elongated wick.
- **Range vs. ADR**: $\text{Daily Range} \ge 1.25 \times \text{ADR}_{10}$.
- **Tail-to-Body Ratio**:
  $$\text{Bullish (Rejection of Lows)}: \frac{\text{Lower Wick}}{\text{Body}} \ge 2.5$$
  $$\text{Bearish (Rejection of Highs)}: \frac{\text{Upper Wick}}{\text{Body}} \ge 2.5$$
- **Close Location**: Close must print within the top/bottom $35\%$ of the candle's extreme range.
- **Structural Extreme**: Candle must test within $\pm 1.0\%$ of a prior 20-bar swing high or low.

### B. Stop Run Day Blueprint
Identifies rapid liquidity sweeps beyond a key pivot or consolidation cluster followed by exhaustion.
- **ADR Threshold**: $\text{Daily Range} \ge 1.10 \times \text{ADR}_{10}$.
- **Extreme Sweep**: High sweeps prior session High ($H > H_{y}$) or Low sweeps prior session Low ($L < L_{y}$).
- **Failed Acceptance**: Price closes back inside the prior day's range.

### C. Absorption Day Blueprint
Signals passive institutional limit order absorption where high volume fails to push price directionally.
- **Compression**: $\text{Daily Range} \le 0.85 \times \text{ADR}_{10}$.
- **Balanced Profile**: Close prints near the midpoint ($\text{Close} \in [45\%, 55\%]$ of daily range).
- **Narrow CPR Convergence**: CPR width falls in bottom quartile.

### D. Failed New Low (FNL) / Failed New High (FNH) Blueprint
- **FNL**: Low breaches yesterday's low ($L < L_y$), but candle rallies to close above the prior day's midpoint ($\text{Close} > \text{yMid}$).
- **FNH**: High breaches yesterday's high ($H > H_y$), but candle sells off to close below the prior day's midpoint ($\text{Close} < \text{yMid}$).
- **ADR Minimum**: Daily range must meet at least $75\%$ of $\text{ADR}_{10}$.

### E. Outside Day Blueprint
A classic expansion regime where current candle encompasses the entirety of the prior session.
- **Envelope Condition**: $H > H_{y}$ AND $L < L_{y}$.
- **Expansion**: $\text{Daily Range} \ge 1.05 \times \text{ADR}_{10}$.

---

## 2. The 4 Trade Sequences

### A. Rejection Day Sequence
A multi-day structural flow triggered by a Rejection Day Blueprint:
- **Day 1**: Rejection Day Blueprint confirms (exhaustion wick at key swing boundary).
- **Day 2**: Responsive Confirmation candle opens and moves in the direction of the rejection.
- **Day 3**: Target Acceleration towards opposite Camarilla band ($H_4$ to $L_4$ or $L_4$ to $H_4$).

### B. Stop Run Sequence
- **Step 1 (Sweep)**: Liquidity pool above prior day high or below prior day low is triggered.
- **Step 2 (Fade Setup)**: Price rejected at liquidity band; counter-trend entry qualified on touch of Camarilla $H_3 / L_3$.
- **Step 3 (Reversal Sweep)**: Price travels back across Central Pivot Range to opposite boundary.

### C. Failed Absorption Sequence
- **Phase 1**: Symmetrical range compression inside Camarilla $H_3 - L_3$.
- **Phase 2 (Failed Breakout)**: Attempted breakout outside the range is immediately rejected.
- **Phase 3 (Retest)**: Retest of the value area boundary confirms institutional reversal.

### D. Accumulation / Distribution Sequence
- **Lookback Window**: 20 consecutive sessions.
- **Macro Compression**: Cumulative 20-day range $\le 3.0 \times \text{ADR}_{10}$.
- **Coiled Spring Setup**: Anticipates massive multi-session expansion day (Trend Day / Double Distribution Trend Day).
