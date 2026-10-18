# Platform Update Log: Version 1.0 Power Candle Midpoint Retest-Only Scalp Synchronization
**Date**: October 18, 2026  
**Module**: Strategy Engine (`algo_engine/strategies.py`) & Pine Script Indicators (`TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, `user_code.pine`)  
**Scope**: 
1. Decoupled initial macro S&R breakout bounces from Scalp triggers across Pine Script and Python DhanHQ engine.
2. Enforced 50% Power Candle Midpoint Retest-only qualification for `LONG SCALP` and `SHORT SCALP`.
3. Sequential midpoint consumption preventing double-triggering.

### Changes Summary:
1. **Retest-Only Midpoint Gating**:
   - `bouncedOffGrsMid = bouncedOffActualGrsMid`
   - `bouncedOffResMid = bouncedOffActualResMid`
   - Eliminated `bouncedOffSR_Up` and `bouncedOffSR_Down` from qualifying directly as scalp bounces on the impulse bar.
2. **DhanHQ Python Strategy Parity (`algo_engine/strategies.py`)**:
   - 4-step sequence: Check retests against existing midpoints $\rightarrow$ consume/clear midpoints upon bounce $\rightarrow$ register fresh midpoints if new power candles form $\rightarrow$ evaluate scalp setups.
3. **Verification**:
   - Added unit test `TestMidpointRetestScalp` in `algo_engine/tests/test_phase1.py`.
   - All 93 unit tests passing.
4. **Documentation & Governance**:
   - Added `Version 1.0 Power Candle Midpoint Retest-Only Scalp Synchronization Mandate` to `AGENTS.md` and `.agents/AGENTS.md`.
   - Created Obsidian reference note `Obsidian/46_Platform_v1_0_Power_Candle_Midpoint_Retest_Only_Scalp_Synchronization.md`.
