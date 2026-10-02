# TLCS Architecture Audit Log: Standalone DhanHQ Engine Migration & TradingView Sunset Roadmap

**Release**: `v7.0.0` (Platform Baseline v7.0)  
**Timestamp**: 2026-10-02T12:19:00+05:30  
**Scope**: Platform Strategy, `.agents/AGENTS.md`, Obsidian Documentation, System Architecture  

---

## 1. Summary of Strategic Roadmap Codification

- **Phase 1: Dual-Engine Comparative Parity (Current Baseline v7.0)**:
  - Both TradingView Webhook Engine and DhanHQ Black Box Shadow Engine operate concurrently across all 6 mobile application tabs (`HUB`, `LOGS`, `SCREENER`, `MARKETS`, `INSIGHTS`, `ANALYTICS`).
  - Zero additional database load: leverages the in-memory React state cache (`shadowSignals` / `dhanBlackboxSignals`) to deliver real-time mathematical parity audits and comparative performance without extra queries or API overhead.
  - Multi-week observation window: rigorously verify execution parity, trigger timing, trailing stop behavior, and zero-ghost invalidation across both live market environments (NSE and MCX) with zero bugs.
- **Phase 2: Autonomous Engine Consolidation & TradingView Sunset (Scheduled: Next Month)**:
  - Following the bug-free parity verification period, the TradingView Webhook ingestion layer will be permanently sunsetted and retired.
  - The architecture will consolidate exclusively around the high-performance **DhanHQ Autonomous Shadow Engine** (`dhan-scanner-background.js` and direct DhanHQ Market Feed API) writing directly to Supabase.
  - **Single Cloud Footprint & Cost Elimination**: TradingView enterprise/premium subscription dependencies and recurrent webhook costs will be eliminated 100%. The entire production platform will run lean on **Netlify** (hosting, serverless background workers, edge CDN) and **Supabase** (PostgreSQL real-time database, auth, storage) exclusively.

---

## 2. Updated Artifacts & References

1. `.agents/AGENTS.md`: Added top-level mandate section `Strategic Roadmap: Standalone DhanHQ Engine Migration & TradingView Sunset Plan`.
2. `Obsidian/25_Platform_V7_0_Strategic_Roadmap_DhanHQ_Migration_and_TradingView_Sunset.md`: Comprehensive architectural document detailing Phase 1 parity vs Phase 2 consolidation.
3. Repositories synchronized on `v7.0` baseline.
