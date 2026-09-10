# Version 1.4 Production Release: Trade Card Timestamp Parity, Exit Lifecycle Alignment & Micro-Card Calibration

**Release Date:** September 10, 2026  
**Milestone Version:** `v1.4` (Production Master)  
**System Components Affected:** 
- Mobile App: `Tv-Alert-Mobile/src/app/page.tsx`, `Tv-Alert-Mobile/package.json`
- Production Web: `TLCS_Website_Deploy/package.json`
- Root Project: `RemoteURL` (Git Submodules & Version Tagging)

---

## 1. Executive Summary

Version 1.4 resolves a critical visual and temporal discrepancy on the Mobile Application's trade cards across both the **HUB** and **LOGS** tabs. Previously, regardless of whether a position was held for minutes, hours, or overnight, the trade card header displayed the trade's entry time under `CLOSED TRADE`, creating the illusion that entry and exit timestamps were identical. 

This release fixes the timestamp binding hierarchy, redistributes micro-card layout parameters logically, and guarantees 100% intuitive and mathematical harmony across all trade lifecycle states.

---

## 2. Root Cause Analysis

1. **Header Misbinding (`liveEntryTime` vs `exitTimeStr`)**:
   - In `Tv-Alert-Mobile/src/app/page.tsx`, the card header component evaluated:
     ```typescript
     const signalTime = liveEntryTime || signal.signal_ts || signal.created_at;
     ```
   - For closed trades (`resolveOutcome !== 'OPEN'`), this always evaluated to `liveEntryTime` (the trade entry timestamp).
   - As a result, a trade entered at `09 SEPT 20:45 IST` and closed at `10 SEPT 08:44 IST` displayed `CLOSED TRADE: 20:45 IST 09 SEPT` in its header, identically mirroring the `ENTRY` micro-card below it.

2. **Misplaced Exit Timestamp in Micro-Cards**:
   - Although `signal.exit_at` was stored correctly in the Supabase PostgreSQL database, the UI template mistakenly placed `signal.exit_at` inside the **`STOP LOSS`** card (`{!isActive && signal.exit_at && ...}`).
   - This caused winning trades exiting at Take Profit (`TP1`–`TP4`) to bizarrely display an exit timestamp inside the red Stop Loss card.
   - Concurrently, the **`EXITED AT`** card was merely displaying the static string `'EXECUTED'` without any timestamp.

---

## 3. Permanent Architecture & UI Upgrades

| Card Component | State | Previous Behavior | Version 1.4 Canonical Implementation |
| :--- | :--- | :--- | :--- |
| **Card Header (Top Right)** | `CLOSED TRADE` | Displayed Entry Time (`20:45 IST 09 SEPT`) | Dynamically evaluates `(!isActive && exitTimeStr) ? exitTimeStr : liveEntryTime`. Unambiguously displays the **exact closure time & date** (`08:44 IST 10 SEPT`). |
| **Card Header (Top Right)** | `LIVE TRADE` | Displayed Entry Time | Preserved — displays the live execution/entry time. |
| **Card Header (Top Right)** | `LIMIT SIGNAL` | Displayed Creation Time | Preserved — displays the limit order trigger time. |
| **`ENTRY` Micro-Card** | All States | Displayed Entry Time | Unchanged — cleanly anchors the **entry date and time** (`09 SEPT 20:45`). |
| **`STOP LOSS` Micro-Card** | Closed Trades | Erroneously displayed Exit Time | Cleaned — displays canonical label **`INITIAL SL`** (or protected risk). |
| **`EXITED AT` Micro-Card** | Closed Trades | Displayed static string `'EXECUTED'` | Displays formatted **exit date and time** (`10 SEPT 08:44`). |
| **`OUTCOME` Micro-Card** | Closed Trades | Displayed `HELD: 11h 59m` | Preserved — perfectly validates elapsed duration between entry and exit. |

---

## 4. Multi-Repository Version 1.4 Deployment Matrix

| Repository | Branch | Version Tag | Key Deliverables |
| :--- | :--- | :--- | :--- |
| **`thelioncapitaladvisors-create/thelioncapital-alerts`** (`Tv-Alert-Mobile`) | `main` | **`v1.4`** | Fixed trade card header & micro-card exit timestamp binding in HUB & LOGS, bumped `package.json` to `1.4.0`, updated `Terminal V1.4`. |
| **`thelioncapitaladvisors-create/TLCS_Website`** (`TLCS_Website_Deploy`) | `main` | **`v1.4`** | Version parity alignment, bumped `package.json` to `1.4.0`. |
| **`RemoteURL`** (Root Project) | `main` | **`v1.4`** | Updated git submodules, tagged version 1.4, added Obsidian documentation. |

---

## 5. Verification Checklist

- [x] Next.js 14 production compilation cleanly verified (0 errors, 10/10 static/dynamic routes generated).
- [x] All 3 Git repositories committed, tagged (`v1.4`), and pushed to GitHub remotes.
- [x] Verified entry (`09 SEPT 20:45`), exit (`10 SEPT 08:44`), and duration (`11h 59m`) visual harmony on sample closed trades (NDQ, BTCUSDT).
- [x] Zero regressions on active trade states (`LIMIT SIGNAL` and `LIVE TRADE`).
