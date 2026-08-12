# Obsidian Release Log v3.16: 7-Day Historical Lookback Engine & Strategy Performance Edge

**Release Version:** v3.16  
**Date:** 12 Aug 2026  
**Infrastructure Platform:** Netlify Only (thelioncapitalsolutions.com)

---

## 1. Pine Script Indicators (Vertical & Qwen Dashboards)
- **7-Day Historical Lookback Engine**: Integrated a Lookback Period (Days) setting (1 to 7 days). Signals on past daily bars are aggregated dynamically and formatted with historical timeframe tags (e.g. NSE:NIFTY1! (2d ago)).
- **Bitmask Packing Efficiency**: Compressed historical signal evaluations into tuple responses s[0]...s[6], using only 18 security calls for 9 domestic and global symbols (NSE:NIFTY1!, MCX:NATURALGAS1!, MCX:CRUDEOIL1!, MCX:GOLD1!, MCX:SILVER1!, NYMEX:CL1!, NYMEX:NG1!, COMEX:GC1!, COMEX:SI1!), keeping execution well under TradingView 40-call limit.
- **Dynamic Conditional Headers**: Table section headers (TLCS SIGNALS, DAY TYPE BLUEPRINTS, TRADE SEQUENCES) only render when there are active signals in that category. Empty headers are completely hidden from chart view.

---

## 2. Mobile App (Tv-Alert-Mobile)
- **7-Day Strategy Performance Edge Table**: Added a strategy-wise and day-wise performance breakdown table on the ANALYTICS tab (page.tsx).
- Displays 7-day cumulative signals, Win Rate %, Total Edge %, and Average Return % across all 6 hardcoded strategy types (LONG/SHORT MISSILE, LONG/SHORT SCALP, LONG/SHORT LIGHTNING).
- Fully interactive with all market filter tabs (SYSTEM-WIDE, NIFTY 50, MCX, NYMEX, CRYPTO, FOREX, WORLD INDICES).

---

## 3. System Consistency & Rules Verification
- Verified strict adherence to net exact percentage metrics (metadata.exact_pct).
- Verified rule enforcement on non-overlapping single market categories and canonical status resolution.
