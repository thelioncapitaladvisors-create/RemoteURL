# 92. Platform v3.0: DhanHQ Autonomous Zero-Touch Architecture & MCX Contract Rollover

**Date:** November 13, 2026  
**Release:** Version 3.0 Production Maintenance & Autonomous Hardening  
**Components:**
- TLCS_Website_Deploy/netlify/functions/dhan-scanner-symbols.json (Active MCX Front-Month Scrips)
- algo_engine/dhan_executor.py (Active MCX Lot Sizes & Scrips)
- algo_engine/feeds/dhan_feed.py (Active Front-Month Contracts)
- AGENTS.md, .agents/AGENTS.md (Autonomous Infrastructure & Zero-Touch Gating Rules)
- Project Backup Mirrors & Backups Vault

---

## 1. Executive Summary

This release anchors the complete architectural specifications required to operate the **TLCS DhanHQ Black Box Signal Engine** autonomously 24/7/365 with **zero manual intervention**. It establishes:
1. **Active MCX Front-Month Contract Parity**: Aligned active front-month commodity contracts (CRUDEOIL: 573422, CRUDEOILM: 573423, NATURALGAS: 574319, GOLD: 495213, SILVER: 495214, COPPER: 574829, ZINC: 574834) across Netlify batch scanners, the BlackBox execution engine, and symbol mappings.
2. **Self-Healing Token Engine Integration**: Automated dynamic TOTP token minting (DHAN_PIN = 871346, DHAN_TOTP_SECRET = N5ZUIALJCBGJ63YS2DUB3BLW7EEPBJU2) and /v2/RenewToken cycling, synchronized across Supabase (public.dhan_token and public.system_config).
3. **24/7 Cloud Host Requirement**: Documentation and operational readiness for hosting the real-time WebSocket tick streamer on persistent Linux cloud infrastructure (Docker Compose / Systemd) to decouple from macOS sleep restrictions.

---

## 2. Active MCX Commodity Contracts Synchronization

Security IDs for active front-month contracts are synchronized across all modules:
- CRUDEOIL: 573422 (Lot: 100)
- CRUDEOILM: 573423 (Lot: 10)
- NATURALGAS: 574319 (Lot: 1250)
- GOLD: 495213 (Lot: 1)
- GOLDM: 571445 (Lot: 1)
- SILVER: 495214 (Lot: 30)
- SILVERM: 483080 (Lot: 5)
- COPPER: 574829 (Lot: 2500)
- ZINC: 574834 (Lot: 5000)
- ALUMINIUM: 574828 (Lot: 5000)
- ALUMINI: 574827 (Lot: 1000)

Updated files:
- TLCS_Website_Deploy/netlify/functions/dhan-scanner-symbols.json
- algo_engine/dhan_executor.py
- algo_engine/feeds/dhan_feed.py

---

## 3. Autonomous Zero-Touch Infrastructure Architecture

### 3.1 Token Lifecycle
- Fresh 24-hour JWT access tokens are minted on-the-fly using dynamic RFC 6238 HMAC-SHA1 TOTP.
- Automatic renewal via /v2/RenewToken triggers when token lifetime is under 4 hours, avoiding unnecessary TOTP requests.
- Shared cache in Supabase allows Netlify serverless functions, the Next.js mobile terminal, and the standalone Python daemon to operate on a single synchronized token.

### 3.2 24/7 Cloud Execution (algo_engine/DEPLOYMENT.md)
- Real-time tick ingestion (DhanFeed), in-memory candle aggregation (aggregator.py), midpoint limit order placement, and Telegram dispatches run continuously in Docker or Systemd.
- Automated restart on system reboot (restart: always) ensures zero downtime during server maintenance.

---

## 4. Local Backup Mirror Synchronization

Local project mirrors and backup vaults updated:
1. Primary Workspace Mirror: Project Backup/
2. Secondary External Mirror: /Users/vishant/Documents/Project Backup/
3. Timestamped Snapshot: Backups/TLCS_v3.0_Complete_Backup_20261113_224500/
4. Documents Backup Vault: /Users/vishant/Documents/Backups/
