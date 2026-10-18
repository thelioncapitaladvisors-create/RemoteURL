# Platform Update Note: Version 1.0 DhanHQ Oscillator Momentum, DMI, 4 Reversal Systems & Bias Synchronization
**Date**: October 18, 2026  
**Module**: Algo Engine (`algo_engine/pivots.py`, `algo_engine/strategies.py`, `algo_engine/nse100_scanner.py`, `algo_engine/engine_daemon.py`, `algo_engine/tests/test_phase1.py`)  
**Scope**: Full mathematical synchronization of Oscillator Momentum ($m0, m10$), Directional Movement Index ($plus, minus$), 4 Candle Reversal Systems (Wick, Extreme, Outside, Doji), $GreenCandle / RedCandle$, Institutional Bias ($c1$), Day Type ($mX$), and Narrow CPR ($NCPR$) gating.

---

## 1. Executive Summary & Rationale

To achieve 100% mathematical parity with the canonical Pine Script indicator (`TLCS iTrend Indicator` / `TLCS_Dashboards_4_Commodities_Merged.pine`), the DhanHQ algorithmic trading engine has been extended with the exact indicator equations, momentum oscillators, and candle pattern recognition rules:

1. **Oscillator Momentum ($m0, m10$)**:
   $$\text{upper} = \text{ta.highest}(92), \quad \text{lower} = \text{ta.lowest}(92)$$
   $$\text{out} = 100 \times \frac{\text{close} - \text{upper}}{\text{upper} - \text{lower}}$$
   $$m0 = \text{ta.ema}(\text{out}, 21), \quad m10 = \text{ta.sma}(\text{out}, 96)$$

2. **Directional Movement Index ($plus, minus$) with Wilder's Smoothing (RMA)**:
   $$\text{up} = \Delta(\text{high}), \quad \text{down} = -\Delta(\text{low})$$
   $$\text{plusDM} = (\text{up} > \text{down} \land \text{up} > 0) \ ? \ \text{up} : 0$$
   $$\text{minusDM} = (\text{down} > \text{up} \land \text{down} > 0) \ ? \ \text{down} : 0$$
   $$\text{trur} = \text{ta.rma}(\text{ta.tr}, 14), \quad \text{plus} = 100 \times \frac{\text{ta.rma}(\text{plusDM}, 14)}{\text{trur}}, \quad \text{minus} = 100 \times \frac{\text{ta.rma}(\text{minusDM}, 14)}{\text{trur}}$$

3. **GREEN1 / RED1 & GREENZONE / REDZONE Separation**:
   $$\text{GREEN1} = (\text{plus} > \text{minus}) \land (m0 > m10)$$
   $$\text{RED1} = (\text{minus} > \text{plus}) \land (m0 < m10)$$
   - $\text{GREEN1} / \text{RED1}$ gates Power Candle formation ($GrS = \text{GREEN1} \land \text{bouncedOffSR\_Up}$) and Scalp conditions.
   - $\text{GREENZONE} / \text{REDZONE}$ gates the 4 Candle Reversal Systems.

4. **4 Reversal Systems**:
   - **Wick Reversal ($Wlongsig, Wshortsig$)**:
     $$\text{Wlongsig} = \text{GREENZONE} \land (\text{range} > \text{avgCandle} \times 0.9) \land (\text{open} - \text{low} \ge 0.40 \times \text{range}) \land (\text{close} - \text{low} \ge 0.40 \times \text{range}) \land (\text{close} > \text{open})$$
     $$\text{Wshortsig} = \text{REDZONE} \land (\text{range} > \text{avgCandle} \times 0.9) \land (\text{high} - \text{open} \ge 0.40 \times \text{range}) \land (\text{high} - \text{close} \ge 0.40 \times \text{range}) \land (\text{close} < \text{open})$$
   - **Extreme Reversal ($Elongsig, Eshortsig$)**: Exhaustion bar of $\ge 75\%$ body and $> 2.0 \times \text{avgCandle}$ followed by reversal bar in direction of zone.
   - **Outside Reversal ($Olongsig, Oshortsig$)**: Outside engulfing candle in direction of zone.
   - **Doji Reversal ($Dlongsig, Dshortsig$)**: Prior bar doji ($\text{body} \le 5\% \text{ of range}$ and $\text{range} > \text{avgCandle} \times 0.9$) followed by directional breakout bar.
   - **$GreenCandle / RedCandle$**:
     $$\text{GreenCandle} = Wlongsig[1] \lor Olongsig[1] \lor Elongsig[1] \lor Dlongsig[1]$$
     $$\text{RedCandle} = Wshortsig[1] \lor Oshortsig[1] \lor Eshortsig[1] \lor Dshortsig[1]$$

5. **Normalized Narrow CPR ($NCPR$) & Institutional Bias ($c1$) Gating**:
   - $\text{NCPR} = (\text{cprWidth} / \text{prevDayRange}) \times 100 < 5.0\%$.
   - $c1$ evaluates CPR relationship to prior day (`WATCH`, `CONFIRMED BULLISH`, `CONFIRMED BEARISH`, `REJECTED BULLISH`, `REJECTED BEARISH`, `SIDEWAYS`, `BREAKOUT`).
   - Integrated directly into $bull\_conds$ and $bear\_conds$ alongside day type $mX$ and opening bias $dX$.

---

## 2. Mathematical Implementations in `algo_engine/pivots.py`

- `rma(values, length)`: Running Moving Average with $\alpha = 1 / \text{length}$.
- `compute_dmi(bars, length=14)`: Computes exact $+DI$ and $-DI$.
- `compute_m0_m10(bars, len0=21, len1=96, lookback=92)`: Highest/lowest oscillator with 21 EMA and 96 SMA.
- `compute_institutional_bias_c1(...)`: Full conditional tree for institutional bias.
- `compute_day_type_mx(...)`: Frank Ochoa PivotBoss day type classifier.

---

## 3. Strategy Engine Updates in `algo_engine/strategies.py`

- Extended `MarketContext` with `institutional_bias: str = ""`.
- Enriched `bull_conds` and `bear_conds` with $c1$ checks and `ctx.is_ncpr`.
- Enriched Power Candle detection ($GrS$ and $ReS$) to gate on $green1$ and $red1$ with backward-compatible fallback.
- Added `detect_wick_reversal`, `detect_outside_reversal`, `detect_doji_reversal`, and `compute_reversal_candles`.

---

## 4. Verification & Testing

- Added `TestOscillatorAndReversalSystems` to `algo_engine/tests/test_phase1.py` covering:
  - RMA calculation and smoothing factor.
  - DMI trending behavior.
  - Oscillator $m0/m10$ momentum curves.
  - Institutional bias $c1$ and day type $mX$.
  - 4 Reversal Systems and $GreenCandle / RedCandle$ 1-bar shift.
  - $NCPR$ and $c1$ gating in `bull_conds` / `bear_conds`.
- 103 unit tests passed (100% success rate).
