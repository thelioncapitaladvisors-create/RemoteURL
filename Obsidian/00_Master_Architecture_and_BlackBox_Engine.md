---
title: "TLCS Master System Architecture: Standalone Black Box Engine & Shadow Mode Verification"
project: "TLCS Quantitative Trading Ecosystem"
engine_version: "v1.0-BlackBox"
status: "Planned / In Development"
author: "The Lion Capital Advisors"
date_created: 2026-09-18
last_updated: 2026-09-18
tags:
  - architecture
  - blackbox
  - algorithmic-trading
  - quantitative-finance
  - shadow-mode
  - supabase
  - dhanhq
  - binance
markets_covered:
  - NIFTY
  - MCX
  - NYMEX
  - CRYPTO
  - FOREX
  - WORLD
execution_mode: "Tick-by-Tick Stateful Daemon"
database_target: "Supabase (shadow_signals / signals)"
---

# TLCS Master System Architecture: Standalone Black Box Engine

## 1. System Overview & Objective

The **TLCS Standalone Black Box Engine** is an institutional quantitative trading core designed to decouple signal generation from third-party charting platforms (TradingView webhooks).

Operating as a continuous, multi-threaded 24/7 background daemon, the engine:
1. Ingests raw real-time price ticks via low-latency broker WebSockets.
2. Synthesizes multi-timeframe candles (1m, 5m, 15m, Daily).
3. Computes deterministic mathematical models: **Camarilla Pivots**, **Central Pivot Range (CPR)**, **Triple EMAs**, **Day Type Blueprints**, and **Trade Sequences**.
4. Evaluates all **12 Canonical Strategy Triggers** with strict $H_4/L_4$ touch-point gating.
5. Manages order lifecycles (limit creation, fills, break-even SL shifts, dynamic trailing stops, target completions, EOD sweeps).
6. Writes directly to the Supabase database for instantaneous delivery across the Mobile Terminal PWA and Web Dashboard.

---

## 2. High-Level Component Topology

```mermaid
graph TD
    subgraph Data Layer ["Real-Time Market Ingestion"]
        DhanWS["DhanHQ WebSocket\n(NIFTY 50 Equities & MCX)"]
        BinanceWS["Binance WebSocket\n(Crypto Top 25 Pairs)"]
        GlobalWS["Global Market WebSocket\n(NYMEX, Forex Majors, World Indices)"]
    end

    subgraph Core Engine ["Python Black Box Engine (algo_engine)"]
        Aggregator["Candle & Tick Aggregator\n(1m, 5m, 15m, Daily OHLCV)"]
        PivotsEngine["Camarilla & CPR Math Core\n(H1-H5, L1-L5, TC, Pivot, BC)"]
        SequenceEngine["Day Type & Blueprint Classifier\n(5 Blueprints + 4 Sequences)"]
        TriggerEngine["12 Strategy Trigger Matrix\n(Touch-point Gated: low < H4, high > L4)"]
        OrderManager["Stateful Trade Lifecycle Manager\n(Active Limits, Fills, BE Shift, Trailing SL, EOD)"]
    end

    subgraph Database Layer ["Supabase Cloud"]
        LiveDB[("signals Table\n(Production TV Webhooks)")]
        ShadowDB[("shadow_signals Table\n(Black Box Parallel Stream)")]
    end

    subgraph Client Surfaces ["Trading Terminals"]
        MobilePWA["Mobile Terminal PWA\n(page.tsx)"]
        WebDash["Web Dashboard & Scanners\n(dashboard.html / metrics.html)"]
        TelegramBot["Market-Wise Telegram Dispatcher\n(Active Executions Only)"]
    end

    Data Layer --> Aggregator
    Aggregator --> PivotsEngine
    Aggregator --> SequenceEngine
    PivotsEngine --> TriggerEngine
    SequenceEngine --> TriggerEngine
    TriggerEngine --> OrderManager

    OrderManager -->|Parallel Stream| ShadowDB
    OrderManager -->|Active Trades Only| TelegramBot
    
    LiveDB --> MobilePWA
    LiveDB --> WebDash
    ShadowDB -.->|Parity Audit / Lab Mode| MobilePWA
    ShadowDB -.->|Parity Audit / Lab Mode| WebDash
```

---

## 3. Metadata Specification

| Metadata Property | Specification | Implementation Reference |
| :--- | :--- | :--- |
| `engine_type` | `Standalone Headless Daemon` | `algo_engine/engine_daemon.py` |
| `runtime_environment` | `Python 3.11+ / asyncio / uvloop` | `algo_engine/` |
| `feed_protocols` | `WebSocket (Binary / JSON-RPC)` | `algo_engine/feeds/` |
| `database_engine` | `PostgreSQL / PostgREST (Supabase v2)` | `@supabase/supabase-js` / `supabase-py` |
| `metric_truth` | `exact_pct: ((Exit - Entry) / Entry) * 100` | AGENTS.md Rule 1.0 |
| `gating_rule` | `low < H4` (Long) / `high > L4` (Short) | Strict Verification Mandate |
| `target_tiers` | `TP1, TP2, TP3, TP4` | Pre-defined, locked at limit creation |
| `market_categories` | `NIFTY, STOCKS, MCX, NYMEX, CRYPTO, FOREX, WORLD` | Canonical Memory Set |

---

## 4. Verification & Shadow Mode Architecture

To maintain zero downtime and avoid production trade disruption, the Black Box will operate under the **Institutional Shadow Mode Protocol**:
- **Dual-Stream Execution**: TradingView webhooks remain the active live trading feed on `signals`.
- **Parallel Logging**: The Black Box streams identical signals to `shadow_signals`.
- **Side-by-Side Audit**: The terminal surfaces a real-time comparison view auditing trigger latency, price precision, level fidelity, and win/loss parity.
- **Production Cutover**: Once $>99\%$ parity is sustained over live market trading sessions, the primary data source will switch to the Black Box engine.
