# Platform Update Log: Version 1.0 DhanHQ Oscillator Momentum, DMI, 4 Reversal Systems & Bias Synchronization
**Date**: October 18, 2026  
**Module**: Algo Engine (`algo_engine/pivots.py`, `algo_engine/strategies.py`, `algo_engine/nse100_scanner.py`, `algo_engine/engine_daemon.py`, `algo_engine/tests/test_phase1.py`)  
**Scope**: 
1. Integrated Oscillator Momentum ($m0, m10$) and Directional Movement Index ($plus, minus$ with RMA smoothing) matching Pine Script mathematical definitions.
2. Implemented 4 Candle Reversal Systems (Wick, Extreme, Outside, Doji) and 1-bar shifted $GreenCandle / RedCandle$ tracking.
3. Integrated Institutional Bias ($c1$), Day Type ($mX$), and Narrow CPR ($NCPR$) into $bull\_conds$ and $bear\_conds$ gating.
4. Synchronized `NSE100Scanner` and `EngineDaemon` to calculate and feed authentic indicator values into `MarketContext`.

### Changes Summary:
1. **Mathematical Indicators in `algo_engine/pivots.py`**:
   - `rma(values, length)`: Running Moving Average (Wilder's smoothing with $\alpha = 1/\text{length}$).
   - `compute_dmi(bars, length=14)`: $+DI$ ($plus$) and $-DI$ ($minus$).
   - `compute_m0_m10(bars, len0=21, len1=96, lookback=92)`: $m0$ (21 EMA) and $m10$ (96 SMA) of 92-bar normalized range oscillator.
   - `compute_institutional_bias_c1(...)`: Full conditional tree for institutional bias.
   - `compute_day_type_mx(...)`: PivotBoss day type classifier.
2. **Strategy Engine Synchronization in `algo_engine/strategies.py`**:
   - Added `institutional_bias: str = ""` to `MarketContext`.
   - Updated `bull_conds` & `bear_conds` to evaluate `institutional_bias` ($c1$) and include `ctx.is_ncpr`.
   - Updated Power Candle $GrS$ and $ReS$ to link to $green1 = (plus > minus \land m0 > m10)$ and $red1 = (minus > plus \land m0 < m10)$ with backward-compatible fallback.
   - Added `detect_wick_reversal`, `detect_outside_reversal`, `detect_doji_reversal`, and `compute_reversal_candles`.
3. **Execution Daemon & Scanner Synchronization**:
   - `algo_engine/nse100_scanner.py`: Calculates authentic DMI, $m0/m10$, $c1$, and $mX$ on 15m bars.
   - `algo_engine/engine_daemon.py`: Assembles full `MarketContext` with authentic oscillator and bias values.
4. **Verification & Testing**:
   - Added `TestOscillatorAndReversalSystems` in `algo_engine/tests/test_phase1.py`.
   - All 103 unit tests passed (100% success rate).
5. **Documentation & Governance**:
   - Added `Version 1.0 DhanHQ Oscillator Momentum, DMI, 4 Reversal Systems & Bias Synchronization Mandate` to `AGENTS.md` and `.agents/AGENTS.md`.
   - Created Obsidian note `Obsidian/47_Platform_v1_0_DhanHQ_Oscillator_Momentum_DMI_Reversal_Systems_and_Bias_Synchronization.md`.
