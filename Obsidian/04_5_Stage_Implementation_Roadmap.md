---
title: "5-Stage Engineering Roadmap: Standalone Black Box & Shadow Protocol"
project: "TLCS Quantitative Trading Ecosystem"
module: "Project Management & Implementation"
author: "The Lion Capital Advisors"
date_created: 2026-09-18
last_updated: 2026-09-18
tags:
  - roadmap
  - milestones
  - stages
  - planning
  - implementation
total_estimated_days: "7 - 10 working days"
verification_window: "2 - 3 weeks"
start_date: 2026-09-19
---

# 5-Stage Engineering Roadmap: Standalone Black Box & Shadow Protocol

---

## 1. Timeline & Milestone Overview

```
Stage 1: Math & State Machine Core     [Days 1 - 3]  ████████░░░░░░░░░░░░
Stage 2: Live WebSocket Ingestion      [Days 4 - 6]  ░░░░░░░░████████░░░░
Stage 3: Headless Daemon & Supabase    [Days 7 - 8]  ░░░░░░░░░░░░░░░░████
Stage 4: Side-by-Side Shadow Lab UI    [Days 9 - 10] ░░░░░░░░░░░░░░░░░░██
Stage 5: Live Market Verification      [Weeks 3 - 5] ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

---

## 2. Stage Details & Verification Deliverables

### Stage 1: Mathematical Engine & Strategy Porting (Days 1–3)
- [ ] **Pivots & CPR**: Implement `algo_engine/pivots.py` calculating Camarilla $H_1\text{–}H_5, L_1\text{–}L_5$, Central Pivot Range (TC, P, BC), and EMAs (8, 21, 34).
- [ ] **Day Type Classifier**: Implement `algo_engine/day_types.py` porting the 5 Day Type Blueprints and 4 Trade Sequences.
- [ ] **12 Strategy Triggers**: Implement `algo_engine/strategies.py` with strict touch-point gating (`low < H4` for buy / `high > L4` for sell).
- [ ] **State Machine**: Implement `algo_engine/trade_manager.py` with immutable limit order levels, TP1 break-even adjustment, TP3 trailing stops, dynamic EMA exits, and EOD closures.
- [ ] **Unit Tests**: 100% mathematical parity against historical Pine Script outputs.

### Stage 2: Real-Time Multi-Market Feed Ingestion (Days 4–6)
- [ ] **DhanHQ Feed**: Connect binary WebSocket for live ticks on NIFTY 50 and active MCX Commodity contracts.
- [ ] **Binance Feed**: Connect public WebSocket streams for Crypto top 25 pairs (`BTCUSDT`, `ETHUSDT`, `SOLUSDT`, etc.).
- [ ] **Global Ingestion**: Real-time tick aggregation for NYMEX, Forex majors, and World Indices.
- [ ] **Candle Aggregator**: Multi-timeframe bar synthesizer (1m, 5m, 15m, Daily) with auto-reconnect and heartbeat ping/pong.

### Stage 3: Headless Daemon & Shadow Database Pipeline (Days 7–8)
- [ ] **Service Daemon**: Implement asynchronous main execution loop in `algo_engine/engine_daemon.py`.
- [ ] **Supabase Shadow Schema**: Configure `shadow_signals` table in Supabase mirroring `signals`.
- [ ] **Exact Percentage Math**: Enforce automated injection of `metadata.exact_pct` upon signal resolution.
- [ ] **Process Management**: Set up cloud VPS with `pm2` / `systemd` daemon supervision for 24/7 uptime.

### Stage 4: Side-by-Side Shadow Audit Screen in Mobile & Web (Days 9–10)
- [ ] **Source Segmented Switcher**: Add `LIVE (TradingView)` / `SHADOW (Black Box)` / `PARITY AUDIT` pills in mobile terminal and web dashboard.
- [ ] **Audit Parity Table**: Real-time comparison grid evaluating:
  - Trigger latency (TV timestamp vs. Black Box detection timestamp)
  - Level accuracy (Entry, SL, TP1–TP4)
  - Opening Bias & Day Type classification match
  - Win/Loss outcome and exact percentage match
- [ ] **Discrepancy Logging**: Automated flag for any trade detected by one engine but missed by the other.

### Stage 5: Live Market Verification & Production Cutover (Weeks 3–5)
- [ ] **Parallel Live Window**: Run alongside TradingView during live market hours across Indian and global sessions.
- [ ] **Quality Gates**: Confirm $>99\%$ level alignment, zero dropped ticks, and exact outcome resolution.
- [ ] **Master Cutover**: Flip primary client subscriptions to the Black Box engine and deprecate TradingView webhook dependencies.
