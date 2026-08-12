# TLCS System Update Release Notes — Version 3.18

## Release Overview
**Version**: `v3.18`  
**Date**: August 12, 2026  
**Scope**: Mobile App (`Tv-Alert-Mobile`), Website Platform (`TLCS_Website_Deploy`).

---

## 1. Daily Signal Dashboard Layout Repositioning
- **Mobile App (`Tv-Alert-Mobile/src/app/page.tsx`)**:
  - Moved the **TLCS Daily Signal Dashboard** table directly below the Day Type Blueprints & Trade Sequences scanner tables.
- **Website Platform (`TLCS_Website_Deploy/blog.html`)**:
  - Placed the **Daily Signal Dashboard** matrix table directly on the **Blogs & FAQs** (`blog.html`) page under the main Knowledge Base header.

---

## 2. Weekly Signal Performance & Target Achievement Table
- Built a brand new **Weekly Signal Performance & Achievement Table** directly below the **Daily Signal Dashboard** on both applications:
  - **Metrics Tracked**:
    - **Day Offset**: Day 7 down to Day 1 (Today)
    - **Signals (W/L)**: Total signals with Wins/Losses breakdown
    - **Win Rate %**: Realized win rate percentage per day
    - **Targets Achieved**: Granular target achievement levels (`TP1`, `TP2`, `TP3`, `TP4`)
    - **Net Edge %**: Net cumulative percentage return per day
    - **Avg Return %**: Average return per trade

---

## 3. Git Pushes & Deployment Verification
- **Mobile App Repo (`thelioncapital-alerts`)**: Pushed to `main` branch (`commit c00c081`). Netlify auto-deploys live build.
- **Website Platform Repo (`TLCS_Website`)**: Pushed to `main` branch (`commit 4e45c10`). Netlify auto-deploys live build.
