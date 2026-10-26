# Platform v1.0: Institutional Bias (`c1`) Calibration — Bearish Rejection vs. Bullish Continuation Architecture

**Status**: PRODUCTION VERIFIED & SYNCHRONIZED  
**Date**: October 26, 2026  
**Indicator Version**: v1.0 (Pine Script v6) & Python BlackBox Engine  
**Target Files**:
- `TV Indicator/TLCS_Live_Pivot_Alerts.pine`
- `TV_Indicator_Full_Code.txt`
- `user_code.pine`
- `algo_engine/pivots.py`
- `algo_engine/tests/test_phase1.py`

---

## 1. Executive Summary & Root Cause Analysis

On the chart session HUD banner (`tbl_bias` displaying `dX_message`, `c1_message`, `mX_message`), a market setup with a **Bearish / Moderately Bearish CPR** where price opened above CPR (`OO_ > DTc`) and traded above CPR (`close > DTc`) displayed:
```
BULLISH CONTINUATION
```
The user identified this classification defect from live chart verification:
> *"This is not Bullish Continuation it is infact a Bearish rejection. Please make necessary changes in the code for this. Bullish continuation will happen only if the CPR is bullish or Moderately Bullish and Price opens below CPR but continues to move above CPR."*

### Root Cause
In legacy logic, `c1` blindly classified any closing price above `DTc` on `CONFIRMEDBEARISH` or `REJECTEDBEARISH` days as `"BULLISH \n CONTINUATION"`. Under authentic PivotBoss principles:
- If the macro CPR relationship is Bearish, opening above CPR or rallying above `DTc` represents a **rejection of the bearish CPR** (`BEARISH REJECTION`). It cannot represent "Bullish Continuation" because there was no bullish CPR trend to continue.
- **Bullish Continuation** can strictly and only occur when the CPR is Bullish or Moderately Bullish, price opens below CPR in a discount/gap-down (`OO_ < DBc`), and bulls take control to drive price above the entire CPR (`close > DTc`).

---

## 2. Deterministic Institutional Bias (`c1`) Rules Matrix

| Day Condition | Open Relative to CPR | Close Relative to CPR | Legacy Label | Calibrated Label (v1.0 Standard) | Rationale |
|---|---|---|---|---|---|
| `CONFIRMEDBULLISH` | `open > DBc` | `close > DTc` | `CONFIRMED BULLISH` | `CONFIRMED BULLISH` | Bullish CPR confirmed above Top CPR |
| `CONFIRMEDBULLISH` | `open > DBc` | `close < DBc` | `BEARISH CONTINUATION` | `BULLISH REJECTION` | Bullish CPR rejected below Bottom CPR |
| `CONFIRMEDBEARISH` | `open < DTc` | `close < DBc` | `CONFIRMED BEARISH` | `CONFIRMED BEARISH` | Bearish CPR confirmed below Bottom CPR |
| `CONFIRMEDBEARISH` | `open < DTc` | `close > DTc` | `BULLISH CONTINUATION` | `BEARISH REJECTION` | Bearish CPR rejected above Top CPR |
| `REJECTEDBULLISH` | `open < DBc` | `close > DTc` | `BULLISH CONTINUATION` | **`BULLISH CONTINUATION`** | **User Mandate**: Bullish/Mod-Bullish CPR, open below CPR, continues above CPR |
| `REJECTEDBULLISH` | `open < DBc` | `close < DBc` | `BEARISH CONTINUATION` | `BULLISH REJECTION` | Bullish CPR fails and closes below CPR |
| `REJECTEDBEARISH` | `open > DTc` | `close > DTc` | `BULLISH CONTINUATION` | **`BEARISH REJECTION`** | **User Mandate**: Bearish/Mod-Bearish CPR, open above CPR & closes > DTc is Bearish Rejection |
| `REJECTEDBEARISH` | `open > DTc` | `close < DBc` | `BEARISH CONTINUATION` | `BEARISH CONTINUATION` | Bearish/Mod-Bearish CPR, open above CPR, continues down below CPR |

---

## 3. Code Implementation Details

### 3.1 Pine Script v6 (`TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, `user_code.pine`)
Line 798 updated:
```pine
c1 = CONFIRMEDBULLISH and (close > DTc) ? "CONFIRMED \n BULLISH" :
     CONFIRMEDBULLISH and (close < DBc) ? "BULLISH \n REJECTION" :
     CONFIRMEDBEARISH and (close < DBc) ? "CONFIRMED \n BEARISH" :
     CONFIRMEDBEARISH and (close > DTc) ? "BEARISH \n REJECTION" :
     REJECTEDBULLISH and (close < DBc) ? "BULLISH \n REJECTION" :
     REJECTEDBULLISH and (BULLISH or MODERATELYBULLISH) and (close > DTc) ? "BULLISH \n CONTINUATION" :
     REJECTEDBEARISH and (close > DTc) ? "BEARISH \n REJECTION" :
     REJECTEDBEARISH and (BEARISH or MODERATELYBEARISH) and (close < DBc) ? "BEARISH \n CONTINUATION" :
     OUTSIDE ? "SIDEWAYS" :
     UNCHANGED ? "SIDEWAYS/ BREAKOUT" :
     ((ANYDAY and ((OO_ > h4) or (OO_ < l4))) or INSIDE) ? "BREAKOUT" : "DEBUG"
```
Line 857 updated:
```pine
else if c1 == 'REJECTION'
    c1_message := (close > DTc ? "BEARISH \n REJECTION" : "BULLISH \n REJECTION")
    c1_col := (close > DTc ? color.teal : color.fuchsia)
```

### 3.2 Python BlackBox (`algo_engine/pivots.py`)
`compute_institutional_bias_c1` updated in lockstep:
```python
    if anyday and (close_price < dtc and close_price > dbc):
        return "WATCH"
    elif confirmed_bullish and (close_price > dtc):
        return "CONFIRMED BULLISH"
    elif confirmed_bullish and (close_price < dbc):
        return "BULLISH REJECTION"
    elif confirmed_bearish and (close_price < dbc):
        return "CONFIRMED BEARISH"
    elif confirmed_bearish and (close_price > dtc):
        return "BEARISH REJECTION"
    elif rejected_bullish and (close_price < dbc):
        return "BULLISH REJECTION"
    elif rejected_bullish and (bullish or mod_bullish) and (close_price > dtc):
        return "BULLISH CONTINUATION"
    elif rejected_bearish and (close_price > dtc):
        return "BEARISH REJECTION"
    elif rejected_bearish and (bearish or mod_bearish) and (close_price < dbc):
        return "BEARISH CONTINUATION"
    elif outside:
        return "SIDEWAYS"
    elif unchanged:
        return "SIDEWAYS/ BREAKOUT"
    elif (anyday and ((open_price > h4) or (open_price < l4))) or inside:
        return "BREAKOUT"
    else:
        return "DEBUG"
```

---

## 4. Verification Results
- 113 Python test cases passed cleanly with 0 regressions (`python3 -m unittest discover -s algo_engine/tests -p "test_*.py"`).
- Verified bit-for-bit SHA-256 backup consistency across all 3 local tiers.
