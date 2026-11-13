# 91. Platform v3.0: TradingView Indicator Decoupling, Regime Styling & Autonomous DhanHQ Infrastructure

**Date:** November 13, 2026  
**Release:** Version 3.0 Production Maintenance & Integrity Lock  
**Components:**
- TV Indicator/TLCS_Live_Pivot_Alerts.pine, TV_Indicator_Full_Code.txt, user_code.pine (Pine Script v6)
- algo_engine/strategies.py, algo_engine/tests/test_phase1.py (Python BlackBox Engine)
- TLCS_Website_Deploy/netlify/functions/dhan-auth.js, dhan-scanner-background.js (Netlify Cloud Execution)
- Tv-Alert-Mobile/src/lib/dhanAuth.ts (Dynamic TOTP Auth)
- AGENTS.md, .agents/AGENTS.md (Agent Rulebooks & Zero-Unilateral Alteration Mandates)

---

## 1. Executive Summary & Root-Cause Diagnosis

This release addresses two operational anomalies identified in the live trading environment:
1. **TradingView Webhook Muting Standalone Signals**:
   - Webhook alerts generated only VIRGIN CPR, EXTREME REVERSAL, and HIDDEN DIVERGENCE while MISSILE, SCALP, and REGULAR DIVERGENCE produced zero alerts.
   - **RCA**:
     - enable_confluence_filter had defaulted to true, strictly gating JustMissileBuy and JustScalpBuy behind hasBullDivWindow, muting standalone trend setups.
     - Regular Divergence (D) confirmation candle close (Bars 1 to 5) had been bound to GrS (GREEN1 and bouncedOffSR_Up) / ReS (RED1 and bouncedOffSR_Dn), which rarely coincided with the confirmation candle close, blocking Regular Divergence triggers.
2. **DhanHQ BlackBox Operational Inactivity on Local Machine**:
   - The local daemon on macOS had halted on Oct 8, 2026 due to macOS TCC sandbox restrictions (Operation not permitted) and directory path mismatch (/Users/vishant/Project vs ~/Documents/Project).
   - Autonomous execution is permanently transitioned to scheduled cloud infrastructure via Netlify Background Functions and Supabase, running 24/7 without dependency on local macOS wake state.

---

## 2. TradingView Indicator Enhancements & Checksum Parity

### 2.1 Default Confluence Filter Decoupling
The confluence filter input default is set to false:
```pine
enable_confluence_filter = input.bool(false, 'Enable Divergence Confluence Filter (Institutional Mode)')
```
Standalone MISSILE and SCALP alerts are unblocked and execute freely alongside all other canonical signals.

### 2.2 Symmetrical Divergence Confirmation Close Gating
Regular Divergence (D) is decoupled from the GrS / ReS Power Candle bounce requirement on the confirmation candle:
```pine
// Regular Divergence strictly requires subsequent directional confirmation candle close (zero unconfirmed entries)
bool confirmedRegBull = inWindowRegBull and isBullishConfirmCandle and (na(lastFiredRegBullBar) or lastFiredRegBullBar < lastRegBullDivBar)
bool confirmedRegBear = inWindowRegBear and isBearishConfirmCandle and (na(lastFiredRegBearBar) or lastFiredRegBearBar < lastRegBearDivBar)
```
Confirmation strictly evaluates directional candle close ((close > open) and (close > close[1]) for Long, (close < open) and (close < close[1]) for Short), providing exact mathematical symmetry between Regular and Hidden Divergences.

### 2.3 Strict Regime Classification, Color Palette & Message Blocks
Lines 801 to 911 are harmonized to the user's authentic specifications:
- paint:
```pine
paint = BULLISH ? color.gray : BEARISH ? color.gray : MODERATELYBULLISH ? color.silver : MODERATELYBEARISH ? color.silver : INSIDE ? color.black : UNCHANGED ? color.black : OUTSIDE ? color.black : color.gray
```
- c1 & paintc:
```pine
c1 = CONFIRMEDBULLISH and (close > DTc) ? "CONFIRMED 
 BULLISH" : CONFIRMEDBULLISH and (close < DBc) ? "BULLISH 
 REJECTION" : CONFIRMEDBEARISH and (close < DBc) ? "CONFIRMED 
 BEARISH" : CONFIRMEDBEARISH and (close > DTc)  ? "BEARISH 
 REJECTION" : REJECTEDBULLISH and (close < DBc) ? "BULLISH 
 REJECTION" : REJECTEDBULLISH and (BULLISH or MODERATELYBULLISH) and (close > DTc) ? "BULLISH 
 CONTINUATION" : REJECTEDBEARISH and (close > DTc)? "BEARISH 
 REJECTION" : REJECTEDBEARISH and (BEARISH or MODERATELYBEARISH) and (close < DBc) ? "BEARISH 
 CONTINUATION" : OUTSIDE ? "SIDEWAYS" : UNCHANGED ? "SIDEWAYS/ BREAKOUT" : ((ANYDAY and ((OO_ > h4) or (OO_ < l4))) or INSIDE) ? "BREAKOUT" : "DEBUG"
paintc = CONFIRMEDBULLISH and (close > DTc) ? color.green : CONFIRMEDBULLISH and (close < DBc) ? color.red : CONFIRMEDBEARISH and (close < DBc) ? color.red : CONFIRMEDBEARISH and (close > DTc) ? color.teal :  REJECTEDBULLISH and (close < DBc)? color.red : REJECTEDBULLISH and (close > DTc) ? color.teal : REJECTEDBEARISH and (close > DTc)? color.teal : REJECTEDBEARISH and (close < DBc) ? color.red : OUTSIDE ? color.orange : UNCHANGED ? color.blue : ((ANYDAY and ((OO_ > h4) or (OO_ < l4))) or INSIDE) ? color.fuchsia : color.red
```
- m1 & paintm: Momentum and Camarilla/CPR breakout ranges with high-contrast palette.
- dX & paintX: 4-branch opening relationship evaluation (IN RANGE IN VALUE, IN RANGE OUT OF VALUE, OUT OF RANGE OUT OF VALUE, DEBUG).
- mX & paintmX: Deterministic Frank Ochoa Swing Trade Pro 2.0 day type and regime classification.
- Message blocks: Direct assignment c1_message := str.tostring(c1).

### 2.4 Canonical Master Indicator SHA256 Checksum Parity
All three Pine Script source files match 100% byte-for-byte:
```
ca63dda575f902c6456019c703e2f2089f554b71783f583814d2ba224a5f6f0b  TV Indicator/TLCS_Live_Pivot_Alerts.pine
ca63dda575f902c6456019c703e2f2089f554b71783f583814d2ba224a5f6f0b  TV_Indicator_Full_Code.txt
ca63dda575f902c6456019c703e2f2089f554b71783f583814d2ba224a5f6f0b  user_code.pine
```

---

## 3. Python BlackBox Parity & Test Suite Validation

- algo_engine/strategies.py synchronized with decoupled Regular Divergence confirmation math.
- Unit test suite passed completely:
```
Ran 129 tests in 1.820s
OK (skipped=1)
```

---

## 4. Netlify Autonomous DhanHQ Cloud Infrastructure

- **Self-Healing Token Engine**:
  - TLCS_Website_Deploy/netlify/functions/dhan-auth.js and Tv-Alert-Mobile/src/lib/dhanAuth.ts implement dynamic TOTP generation (DHAN_PIN = '871346', DHAN_TOTP_SECRET = 'N5ZUIALJCBGJ63YS2DUB3BLW7EEPBJU2').
  - Automatically mints 24-hour tokens and caches them in Supabase (dhan_token table).
- **Scheduled Background Scanner**:
  - TLCS_Website_Deploy/netlify/functions/dhan-scanner-background.js executes every 15 minutes via Netlify Scheduled Cron (cron-dhan-scanner.js) during Indian exchange market hours (03:00 to 18:00 UTC / 08:30 to 23:30 IST).
  - Evaluates NSE Top 100 Equities and MCX Commodity front-month contracts, persisting trades directly to public.shadow_signals.

---

## 5. Strict Code Integrity & Zero-Alteration Mandate

To ensure no future agent or process alters any trading logic, regime classification, or styling without explicit user knowledge:
1. All changes must be backed by live database verification or unit tests before deployment.
2. The exact SHA256 checksum standard is enforced across all indicator files.
3. Zero unilateral logic alteration rule is permanently enshrined in AGENTS.md and .agents/AGENTS.md.
