---
name: pivotboss
description: >-
  Canonical PivotBoss "Swing Trade Pro 2.0" (Frank Ochoa) methodology: the 5-Step
  Swing Trading Blueprint covering Risk Management, the 5 Day Type Blueprints
  (Rejection, Absorption, Failed New Low/High, Outside, Stop Run), the 4 Trade
  Sequences (Rejection Day, Stop Run, Failed Absorption, Accumulation), the
  Options Strategy Toolkit, Execution scale-in/scale-out techniques, and Trade
  Documentation. Use this skill whenever the user asks about day types,
  blueprints, trade sequences, absorption zones, FNL/FNH, stop run days, ADR
  thresholds, or wants to audit, build, or debug any Pine Script / Python /
  JS logic (TLCS_Main_Dashboard_7Day_Matrix.pine, algo_engine/day_types.py,
  screener.js, page.tsx) against the Swing Trade Pro 2.0 rulebook.
---

# PivotBoss: Swing Trade Pro 2.0 Skill

This skill is the **single source of truth** for the Swing Trade Pro 2.0 rulebook.
Before you write, audit, or explain any day-type or sequence logic, check it here.

- **Original PDF (135 pages):** `/Users/vishant/iCloud Drive (Archive)/Desktop/Swing-Trade-Pro-2.0.pdf`
- **Full extracted text (searchable, with page markers):** [resources/stp2_fulltext.txt](resources/stp2_fulltext.txt)

## The 5-Step Blueprint

| Step | Topic | Reference |
|---|---|---|
| 1 | Risk Management: Core Equity, Fixed Risk %, Portfolio Heat | [01_risk_management.md](references/01_risk_management.md) |
| 2a | Day Type Blueprints (5) | [02_day_type_blueprints.md](references/02_day_type_blueprints.md) |
| 2b | Trade Sequences (4) | [03_trade_sequences.md](references/03_trade_sequences.md) |
| 3 | Options Strategy Toolkit (credit/debit spreads, straddle, iron fly, ITM/OTM, covered call, put, collar) | [04_strategy_toolkit.md](references/04_strategy_toolkit.md) |
| 4 | Execution: 1x3 / 1x2 scale-in, 11 / 111 / 211 scale-out | [05_execution_scaling.md](references/05_execution_scaling.md) |
| 5 | Documentation: entry/exit docs, trade log, review cadence | [06_documentation.md](references/06_documentation.md) |
| — | **TLCS codebase mapping and known deviations** | [07_codebase_mapping.md](references/07_codebase_mapping.md) |

## Quick Reference: Day Type Measurements (bullish; flip for bearish)

`ADR` = average daily range (the PDF uses the 10-day average). `MID = (H+L)/2`. `y` = previous session.

| Blueprint | Range vs ADR | Key Conditions | Ideal Entry | Invalidation | Defend Window |
|---|---|---|---|---|---|
| **Rejection Day** | > 125% | Tail > 2.5 × Body; Close in upper 35%; at previous lows / LVN | MID on Day 1 or last hour; Day 2+ only if **OPEN > MID[1]** | Daily close < Rejection MID | 1–4 days (Entry 2: retest of high/close, 1–2 days) |
| **Absorption Day** | < 75% | Close > Rej/Expansion MID (usually > Open); Low near that MID; often an Inside Day | yMID, only if **OPEN > yMID** | Daily close < yMID | Same as parent Rejection (1–4 days) |
| **Failed New Low** | 75–100% | Low < yLow (or multi-day low); Close > yMID | yLO (day trade); close (swing); Day 2 FNL MID if **OPEN > MID[1]** | Daily close < FNL MID | 1–2 days |
| **Outside Day** | > 105% | Low < yLow (rejected); Close > yHigh | yLO, or between OD MID and rejected low; Day 2+ if **OPEN > MID[1]** | Daily close < OD MID | 1–4 days (Entry 2: retest of yHI/close, 1–2 days) |
| **Stop Run Day** | > 200% (often 200–300%) | Close > yHigh; Close in upper 10–15%; MID ≥ recent multi-day highs | yLO on Day 1 (failed range expansion); retest of yHI from above | Daily close < yHI / SRD MID | 1–2 days |

**Stop Run Day target:** `yHI + (yHI − L)`. Take today's range below yHI and project it above yHI.
**Day after a Stop Run:** expect a countertrend fade back toward the SRD midpoint.

## Mandatory Workflow When Using This Skill

1. **Cite the rule.** Quote the exact PDF rule (page number from `resources/stp2_fulltext.txt`, e.g. `grep -n "=== PAGE 22" resources/stp2_fulltext.txt`).
2. **Cite the code.** Inspect the exact source lines in the target file (see [07_codebase_mapping.md](references/07_codebase_mapping.md)).
3. **Prove with data.** For any claim about a specific symbol or day, run [scripts/pivotboss_rules.py](scripts/pivotboss_rules.py) on real OHLC data, or query Supabase. Never guess. This is required by the workspace `AGENTS.md` Fact-Backed Verification Mandate.
4. **Do not change logic on your own.** Never modify Pine triggers (`CanBuy`, `CanSell`, session arrays, execution wrappers) or detection thresholds without explicit user permission. Report deviations, then ask.
5. **Keep parity.** If a change is approved, apply it to **all** engines: `TLCS_Main_Dashboard_7Day_Matrix.pine`, `TLCS_Sequence_Dashboard.pine`, `algo_engine/day_types.py` (+ `RemoteURL/` mirrors). Re-run `algo_engine/tests/test_phase1.py`.

## Reference Rule Engine (verification tool)

[scripts/pivotboss_rules.py](scripts/pivotboss_rules.py) is a pure-Python, dependency-free classifier that uses the **canonical PDF thresholds**. It is not the production engine. Use it to check what the book says a bar should be:

```bash
# Self-test with synthetic bars
python3 .agents/skills/pivotboss/scripts/pivotboss_rules.py --selftest

# Classify real daily bars (CSV columns: date,open,high,low,close)
python3 .agents/skills/pivotboss/scripts/pivotboss_rules.py --csv path/to/daily.csv [--adr-mode tr|hl] [--last 10]
```

It prints, per bar: range % of ADR, tail/body ratio, close position, detected blueprints, MID, absorption zone, Day-2 OPEN gate status, and the Stop Run target.

## Key Principles (from the PDF)

- Day types are **daily-bar** concepts. They work on any timeframe, but the rules are written for daily sessions.
- **Absorption Zone** = between the rejection-type day's MID and the rejected price level. Bulls defend it. A daily **close** below it ends the trade and usually triggers a stop run the other way (long liquidation).
- **Pay yourself on the first major pop** into the forecast target zone (partial or full).
- **Match the strategy to the odds:** Good → 1% / spreads / 1x3; High → 1.5% / ITM; Best → 2–3% / 100% entry.
