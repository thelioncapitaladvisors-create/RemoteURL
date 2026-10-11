# TLCS Codebase Mapping for Swing Trade Pro 2.0 (STP2)

This document provides a precise mapping of where Swing Trade Pro 2.0 concepts and rules are implemented across the The Lion Capital Solutions (TLCS) repositories and modules.

---

## 1. Black Box Engine (Python)

### Primary Files
- [`algo_engine/day_types.py`](file:///Users/vishant/Documents/Project/algo_engine/day_types.py)
- [`RemoteURL/algo_engine/day_types.py`](file:///Users/vishant/Documents/Project/RemoteURL/algo_engine/day_types.py)
- [`algo_engine/engine.py`](file:///Users/vishant/Documents/Project/algo_engine/engine.py)
- [`algo_engine/scanner.py`](file:///Users/vishant/Documents/Project/algo_engine/scanner.py)
- [`algo_engine/run_nse100_scanner.py`](file:///Users/vishant/Documents/Project/algo_engine/run_nse100_scanner.py)

### Implemented Mechanics
1. **Day Type Detection (`detect_day_type`)**:
   - **Rejection Day (`REJ_BULL` / `REJ_BEAR`)**: Wicks $\ge 25\%$ ADR, opposite wick $< 10\%$ ADR, range $\ge 75\%$ ADR.
   - **Failed New Low / High (`FNL` / `FNH`)**: Breach of prior session extreme, reverse close inside prior range, bounded between $75\%$ and $100\%$ ADR (`fnl_max_pct = 1.00`).
   - **Stop Run Day (`SRD_BULL` / `SRD_BEAR`)**: Range $\ge 125\%$ ADR, close beyond prior 3-day high/low, closes in extreme quarter. Target calculation: `srd_target = yHI + (yHI - L)` (bull) or `yLO - (H - yLO)` (bear).
   - **Absorption Day (`ABS_BULL` / `ABS_BEAR`)**: Consecutive narrow-range tests of key pivot/level without expansion.
   - **Outside Day (`OD_BULL` / `OD_BEAR`)**: Range expands beyond prior high and low, closes near extreme. Midpoint defended for up to 4 sessions.
2. **Trade Sequence Tracking (`SequenceState` & `update_sequences`)**:
   - **Rejection Sequence (`seq_rej_bull` / `seq_rej_bear`)**: Active up to 20 bars (`max_active_days = 20`), MID defended, invalidates if close breaches MID.
   - **Stop Run Sequence (`seq_srd_bull` / `seq_srd_bear`)**: Active up to 20 bars (`max_active_days = 20`).
   - **Failed Absorption Sequence (`seq_fa_bull` / `seq_fa_bear`)**: Active up to 20 bars (`max_active_days = 20`).
   - **Accumulation Sequence (`seq_acc_bull` / `seq_acc_bear`)**: Multi-day absorption sequence active up to 60 bars (`acc_max_active_days = 60`).
3. **Execution Gating (`entry_open_valid`)**:
   - Day 2+ entries enforce open gate validation relative to sequence MID.

---

## 2. Test Verification Suite

### Primary Files
- [`algo_engine/tests/test_phase1.py`](file:///Users/vishant/Documents/Project/algo_engine/tests/test_phase1.py)
- [`algo_engine/tests/test_stp2_parity.py`](file:///Users/vishant/Documents/Project/algo_engine/tests/test_stp2_parity.py)

### Coverage
- `test_stp2_fnl_range_bound`: Verifies FNL upper bound ($100\%$ ADR ceiling).
- `test_stp2_sequence_expiration`: Verifies 20-day lifecycle expiration for sequences.
- `test_stp2_srd_target_calculation`: Verifies deterministic measured-move target formula.
- `test_stp2_day2_open_gate`: Verifies open gate filter for Day 2+ entries.

To run:
```bash
python3 -m pytest algo_engine/tests/ -v
```

---

## 3. Webhook Pine Script Strategy (TradingView)

> [!NOTE]
> Per the strict zero-unilateral modification rule, the TradingView Pine Script files and webhook endpoints remain frozen and untouched.

### Primary Files
- `TV Indicator/TLCS_Main_Dashboard_7Day_Matrix.pine`
- `TV Indicator/Strategy_Execution_Wrapper.pine`

### Mechanics
- Renders the 7-day parameter matrix showing Day Type and Sequence states for intraday and swing charts.
- Limit entry gating linked to `low < H4` (long) and `high > L4` (short).

---

## 4. Web Dashboard & Mobile Terminal

### Primary Files
- `TLCS_Website_Deploy/scanner.js` / `commodity-scanner.js`
- `Tv-Alert-Mobile/src/app/page.tsx` (`HubParameterMatrix`, `HubTradeSequences`)

### Mechanics
- Visualizes Day Types, ADR ratios, Sequence triggers, and pivot levels.
- Dual-engine switcher toggles between Webhook Signals and Black Box (`SHADOW`) engine telemetry.
