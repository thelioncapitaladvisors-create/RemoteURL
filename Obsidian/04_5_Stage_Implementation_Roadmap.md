---
title: "5-Stage Engineering Roadmap: Standalone Black Box & Shadow Protocol"
project: "TLCS Quantitative Trading Ecosystem"
module: "Project Management & Implementation"
author: "The Lion Capital Advisors"
date_created: 2026-09-18
last_updated: 2026-09-19
tags:
  - roadmap
  - milestones
  - stages
  - planning
  - implementation
total_estimated_days: "Completed in 1 Day"
verification_window: "2 - 3 weeks (Active Shadow Mode)"
start_date: 2026-09-19
status: "Phases 1-4 Complete / Phase 5 Active"
---

# 5-Stage Engineering Roadmap: Standalone Black Box & Shadow Protocol

---

## 1. Timeline & Execution Overview

```
Stage 1: Math & State Machine Core     [COMPLETED]   ████████████████████
Stage 2: Live WebSocket Ingestion      [COMPLETED]   ████████████████████
Stage 3: Headless Daemon & Supabase    [COMPLETED]   ████████████████████
Stage 4: Side-by-Side Shadow Lab UI    [COMPLETED]   ████████████████████
Stage 5: Live Market Shadow Auditing   [IN PROGRESS] ▓▓▓▓▓▓▓▓░░░░░░░░░░░░
```

---

## 2. Stage Details & Verification Deliverables

### Stage 1: Mathematical Engine & Strategy Porting (Completed)
- [x] **Pivots & CPR Core**: Implemented `algo_engine/pivots.py` calculating Camarilla $H_1\text{–}H_5, L_1\text{–}L_5$, Central Pivot Range (TC, P, BC, NCPR), and triple Typical Price EMAs (8, 21, 34).
- [x] **Day Type Classifier**: Implemented `algo_engine/day_types.py` porting the 5 Day Type Blueprints (*Rejection Day, Absorption Day, Failed New Low, Outside Day, Stop Run Day*) and 4 Trade Sequences.
- [x] **12 Strategy Triggers**: Implemented `algo_engine/strategies.py` with strict touch-point gating (`low < H4` for buy / `high > L4` for sell).
- [x] **State Machine**: Implemented `algo_engine/trade_manager.py` with immutable limit order levels, TP1 break-even adjustment, TP3 trailing stops, dynamic EMA exits, and EOD closures.
- [x] **Unit Tests**: 56 unit tests passed with 100% mathematical parity against historical Pine Script outputs (`algo_engine/tests/`).

### Stage 2: Real-Time Multi-Market Feed Ingestion (Completed)
- [x] **DhanHQ Feed**: Connected binary WebSocket for live ticks on NIFTY 50 and active MCX Commodity contracts (`algo_engine/broker_stream.py`).
- [x] **Binance Feed**: Connected public WebSocket streams for Crypto top 25 pairs (`BTCUSDT`, `ETHUSDT`, `SOLUSDT`, etc.).
- [x] **Global Ingestion**: Real-time tick aggregation for NYMEX, Forex majors, and World Indices via TwelveData / yfinance fallback.
- [x] **Candle Aggregator**: Multi-timeframe bar synthesizer (1m, 5m, 15m, Daily) with auto-reconnect and heartbeat ping/pong (`algo_engine/data_collector.py`).

### Stage 3: Headless Daemon & Shadow Database Pipeline (Completed)
- [x] **Service Daemon**: Implemented asynchronous main execution loop in `algo_engine/engine_daemon.py`.
- [x] **Supabase Shadow Schema**: Configured `shadow_signals` table in Supabase mirroring `signals` with complete indexes and RLS policies (`algo_engine/sql/create_shadow_signals.sql`).
- [x] **Exact Percentage Math**: Enforced automated injection of `metadata.exact_pct` upon signal resolution.
- [x] **Process Management & Containerization**: Packaged with `algo_engine/Dockerfile`, `algo_engine/docker-compose.yml`, and `algo_engine/tlcs-engine.service` for seamless VPS deployment.

### Stage 4: Side-by-Side Shadow Audit Screen in Mobile & Web (Completed)
- [x] **Source Segmented Switcher**: Added `[ ⚡ TV PROD ]` / `[ 🔲 BLACK BOX LIVE ]` / `[ ⚖️ PARITY AUDIT ]` pills in mobile terminal and web dashboard.
- [x] **Audit Parity Table**: Real-time comparison grid evaluating:
  - Trigger latency (TV timestamp vs. Black Box detection timestamp)
  - Level accuracy (Entry, SL, TP1–TP4 with $\pm 0.1\%$ tolerance bound)
  - Opening Bias & Day Type classification match
  - Win/Loss outcome and exact percentage match
- [x] **Telemetry KPI Grid**: Overall Parity Score ($\ge 99.0\%$), Level Fidelity ($\ge 99.0\%$), Timestamp Alignment, and Outcome Match %.
- [x] **Unit Tests**: 3 Phase 4 unit tests validating parity math and error boundaries (`algo_engine/tests/test_phase4.py`).
- [x] **Admin-Only Security Access Gating**:
  - Entire Engine Source Selector, Shadow Mode alert banner, and Parity Audit Screen are **strictly hidden from subscribers and public visitors**.
  - Accessible strictly by authenticated administrators and owners (`role === 'admin' | 'developer'`, `subscription_type === 'owner'`, or admin emails).
  - Client-side fallback automatically resets unauthorized users back to `'TV'`.

### Stage 5: Live Market Verification & Production Cutover (Active)
- [x] **Shadow Mode Migration Ready**: Supabase DDL, docker container, systemd unit, and local testing daemon operational.
- [ ] **Live Market Shadow Auditing**: Run engine daemon alongside live TradingView signals across Asian, European, and US market sessions.
- [ ] **Quality Gate Verification**: Sustain $\ge 99\%$ parity across live order generation and executions.
- [ ] **Master Cutover**: Route production notifications and auto-execution to Black Box engine once full parity is verified.
