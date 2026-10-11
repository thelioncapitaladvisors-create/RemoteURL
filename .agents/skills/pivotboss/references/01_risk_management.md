# Step 1: Risk Management (PDF pp. 4–14)

## Risk Profiles
- **Conservative:** protects and grows capital, takes income trades, limits risk.
- **Moderate:** raises or lowers exposure according to the odds.
- **Aggressive:** grows the account quickly with directional bets, adding exposure as the odds improve.

## 1.1 Core Equity Model (p.6)
Core equity = cash − risk allocated to each open position. Equity is added back only when a position closes.

| Step | Calc | Value |
|---|---|---|
| Total equity | — | $50,000 |
| Trade 1 risk @1% | 50,000 × 1% | $500 → remaining $49,500 |
| Trade 2 risk @1% | 49,500 × 1% | $495 → remaining $49,005 |
| Trade 3 risk @1% | 49,005 × 1% | $490 → remaining $48,515 |

## 1.2 Trade Allocation: Fixed Risk (Fixed Fractional) Model (pp.7–8)
Position risk = % of **core equity**. Van Tharp simulation stats (100k account, 100 trades, ruin = −25%):

| Fixed Risk | Chance of ruin | Chance of +300% |
|---|---|---|
| 0.8% | 0.1% | 0.4% |
| 1.2% | <1% | 8.5% |
| **2.6%** (optimal retire/ruin) | 12.3% | 53.9% |
| 3.6% | 22.6% | 60.3% (highest) |
| 4.6% | 31.7% | 58.2% (highest median gain +545.5%) |

| Core Equity | Conservative | Moderate | Aggressive |
|---|---|---|---|
| > $25,000 | 1.0% | 1.5% | 2–3% |
| < $25,000 | 2.5% | 5.0% | 10.0% |

Example: $150,000 × 1.5% = $2,250 allocation. Example: $10,000 × 10% = $1,000.

## 1.3 Odds-Based Allocation (p.9)
- **Good odds:** Conservative tier (1% / 2.5%)
- **High odds:** Moderate tier (1.5% / 5%)
- **Best odds:** Aggressive tier (2–3% / 10%)

## 1.4 Percent of Trade Allocation: Entry Allocation (p.10)
Scale into the chosen allocation:
- Good odds (1%): scale 33% / 50% / 100% of 1%
- High odds (1.5%): scale 33% / 50% / 100% of 1.5%
- Best odds (2–3%): scale 33% / 50% / 100% of 2.6%

## 1.5 Portfolio Heat (pp.11–12)
- **Portfolio Heat** = total capital at risk across all open positions.
- **Max Heat:** > $25k account → **10–15%**; < $25k account → **20–30%**.
- Purpose: limit damage from price shocks and flash crashes when leverage is high.

| Example | Max Heat | Allocation | Max Positions |
|---|---|---|---|
| $100,000 @10% | $10,000 | 1.5% = $1,500 | 6 (10,000/1,500 = 6.6) |
| $5,000 @20% | $1,000 | 5% = $250 | 4 |

## 1.6 Risk Management Matrix (p.13)
A spreadsheet. You fill in the yellow cells (equity, %s), and it computes conservative, moderate and aggressive allocations and max heat in real time.

**Formulas:**
```
trade_allocation = core_equity * fixed_risk_pct
max_heat_amount  = total_equity * max_heat_pct
max_positions    = floor(max_heat_amount / trade_allocation)
scale_in_amount  = trade_allocation * scale_pct   # 0.33 / 0.50 / 1.00
```
