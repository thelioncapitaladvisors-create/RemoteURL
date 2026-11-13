# 94. Platform v3.0: Zero Workstation Dependency & Cloud-Native Execution Architecture

**Date:** November 13, 2026  
**Release:** Version 3.0 Production Maintenance & Operational Mandate  
**Components:**
- AGENTS.md, .agents/AGENTS.md (Zero Local Workstation Dependency Mandate)
- TLCS_Website_Deploy/netlify/functions/ (Autonomous Cloud Execution Engine)
- Supabase PostgreSQL (Shared Cloud Persistence & Realtime State)
- Local macOS (Dedicated Exclusively to Offline Research, Development & VectorBT Optimization)

---

## 1. Core Architectural Principle

The TLCS algorithmic trading platform operates on a strict **Zero Workstation Dependency** architectural principle:
- **Nothing runs on the user's local Mac for production trading.**
- The local macOS machine is strictly and exclusively dedicated to:
  1. Codebase development, feature additions, and refactoring.
  2. Offline quantitative research and historical backtesting.
  3. High-performance parameter sweeps and optimization (VectorBT).

---

## 2. Cloud-Native Production Infrastructure

All production trading operations are 100% self-sufficient and hosted in the cloud:
1. **Autonomous Market Scanning**:
   - Hosted on Netlify Scheduled Background Functions (cron-dhan-scanner.js / dhan-scanner-background.js).
   - Automatically runs every 15 minutes during Indian market hours (08:30 to 23:30 IST) covering NSE Top 100 Equities and MCX Commodity Futures.
2. **Self-Healing Authentication**:
   - Minting and auto-renewal of 24-hour DhanHQ access tokens via dynamic TOTP runs serverlessly in Netlify (dhan-auth.js) and persists to Supabase (dhan_token / system_config).
3. **Dynamic Commodity Rollover**:
   - Monthly MCX commodity contract rollovers are resolved dynamically from Dhan's live scrip master and synchronized through Supabase (system_config key mcx_front_month_symbols).
4. **Live Alert Dispatching**:
   - Webhook-driven and scan-driven trade notifications dispatch directly to Telegram channels via cloud execution without workstation dependency.
5. **Real-time Mobile PWA**:
   - Next.js mobile terminal connects directly to Supabase realtime channels and Netlify serverless API routes.

---

## 3. Operational Integrity Guarantee

Under no circumstances should any future process or AI assistant assume, prescribe, or require that production daemons, background workers, or listeners run on the user's local machine. The platform remains permanently autonomous in the cloud.
