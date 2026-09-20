---
title: "Platform Security Hardening, Strict Admin Gating & Version 2.0 Baseline"
project: "TLCS Quantitative Trading Ecosystem"
module: "Security Architecture & Blueprint Standardization"
author: "The Lion Capital Advisors"
date_created: 2026-09-20
last_updated: 2026-09-20
version: "2.0.0"
tags:
  - security
  - vapt
  - sast-dast
  - admin-gating
  - blueprints
  - failed-new-high-low
  - version-2-0
---

# Platform Security Hardening, Strict Admin Gating & Version 2.0 Baseline

> [!IMPORTANT]
> **Single Source of Truth & Zero Privilege Escalation**:
> All administrative capabilities, menu navigation chrome, database sentinels, autonomous repair tooling, and mutating endpoints are restricted exclusively to the 3 registered, whitelisted administrators.

---

## 1. Immutable 3-Admin Whitelist Authorization Model

All administrative authorization checks on Web (`auth.js`, `admin.html`, `dashboard.html`), Mobile (`page.tsx`, `AuthGuard.tsx`), and Netlify serverless functions (`system-audit.js`, `test-telegram.js`, `admin-clear-signals.js`, `admin-delete-item.js`) evaluate strictly against:

```typescript
const APPROVED_ADMIN_EMAILS = [
  'owner@tlcs.com',
  'vishantmeshram@gmail.com',
  'thelioncapitaladvisors@gmail.com'
];
```

### Protection Against Privilege Escalation
1. **Zero Wildcard Permitted**: Domain checks (e.g. `@thelioncapitaladvisors.com` or `admin@thelioncapitaladvisors.com`) are permanently deprecated.
2. **Registration Lockdown**: In `AuthGuard.tsx`, any newly registered or authenticated account not explicitly in `APPROVED_ADMIN_EMAILS` has its profile role forced to `role: 'user'` in state.
3. **Database RLS Enforced**: PostgreSQL Row-Level Security policies on `profiles` prevent client-side updates to `role` and `subscription_type`.

---

## 2. Menu Navigation & Interface Chrome Gating

### Mobile Terminal (`Tv-Alert-Mobile/src/app/page.tsx`)
- **Top Header `<Target /> Menu` Button**: Wrapped inside `{isAdmin && ( ... )}`. Standard subscribers and public users see only the Logout button.
- **Settings Drawer Maintenance Sentinels**: The `24/7 Database Sentinel`, `Autonomous Audit & Resolution Agent`, and `Clear All Alerts` buttons are wrapped inside `{isAdmin && ( ... )}`.
- **Engine Source Selector**: The `[ ⚡ TV PROD ]`, `[ 🔲 BLACK BOX LIVE ]`, and `[ ⚖️ PARITY AUDIT ]` switcher is strictly restricted to `isAdmin`.

### Web Dashboard (`TLCS_Website_Deploy/auth.js` & `dashboard.html`)
- **Header Admin Panel Button**: `⚙️ Admin Panel` is appended only when `isAdmin === true`.
- **Mobile Navigation Drawer**: Links to `Admin Panel` and `🗑 Clear Alerts` are rendered only when `isAdmin === true`.
- **Admin Panel Page Guard (`admin.html`)**: Direct access without an active session matching `APPROVED_ADMIN_EMAILS` immediately alerts the user and redirects to `index.html`.

---

## 3. Serverless API Route & Cron Endpoint Security

1. **Mutating Netlify Functions**:
   - `system-audit.js`, `test-telegram.js`, `test-instagram.js`, `admin-clear-signals.js`, `admin-delete-item.js`:
     Require an authenticated session token whose user email matches `APPROVED_ADMIN_EMAILS`.
2. **Automated Scheduled Netlify Crons**:
   - `cron-heal-outcomes.js`, `cron-eod-close.js`, `cron-weekly-logs.js`, `cron-keep-alive.js`:
     Require an `Authorization: Bearer <CRON_SECRET>` header. Unauthorized or direct browser GET requests return `401 Unauthorized`.
3. **XSS Sanitization**:
   - Dynamic error messages in `dashboard.html` (`[PERF_ERROR]`) pass through HTML entity sanitization (`<>&"'`) before DOM insertion.
4. **HTTP Security Headers (`_headers`)**:
   - Strict Content-Security-Policy (CSP)
   - `X-Frame-Options: DENY`
   - `X-Content-Type-Options: nosniff`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Permissions-Policy: camera=(), microphone=(), geolocation=()`

---

## 4. Canonical Day Type Blueprint Standardization

### Canonical 5 Day Type Blueprints
1. `Rejection Day Blueprint`
2. `Absorption Day Blueprint`
3. `Failed New High/Low Blueprint`
4. `Outside Day Blueprint`
5. `Stop Run Day Blueprint`

### Unification of FNL & FNH into `Failed New High/Low Blueprint`
Previously, Pine Script and UI components split Bullish Failed New Low and Bearish Failed New High into separate rows or used inconsistent labels ("Failed New High Blueprint", "Failed New Low Blueprint", "Failed New Low/High").

Under Version 2.0:
- **Pine Script (`TLCS_Main_Dashboard_7Day_Matrix.pine`)**:
  ```pine
  if f_render_matrix_row(dash1, currentRow, "Failed New High/Low Blueprint", bullFnl, bearFnh, txtSize)
      currentRow += 1
  ```
  Renders green ▲ for Bullish FNL and red ▼ for Bearish FNH under one canonical blueprint row.
- **Web Dashboard (`screener.js`, `dashboard.html`, `blog.html`)**:
  `blueprintCategories` `FNH_FNL` label is `'Failed New High/Low Blueprint'`.
- **Mobile Terminal (`page.tsx`)**:
  Matrix and Alerts Dashboard label is `'Failed New High/Low Blueprint'` (short badge: `FNH/L`).
- **Python Black Box Engine (`algo_engine/day_types.py`)**:
  `get_active_blueprints()` returns `"Failed New High/Low Blueprint (Bullish)"` and `"Failed New High/Low Blueprint (Bearish)"`.

---

## 5. Version 2.0 Baseline & Verification

- **Version 2.0 Standardization**:
  - `TLCS_Website_Deploy/package.json`: `2.0.0`
  - `Tv-Alert-Mobile/package.json`: `2.0.0`
  - Mobile header: `TLCS TERMINAL v2.0`
  - Web footers and cachebusters: `v2.0` / `?v=2.0`
- **Verification Status**:
  - Netlify Functions: `node -c` (0 syntax errors)
  - Mobile App: `npm run build` (0 errors, 8/8 static pages generated)
  - Python Engine: `python3 -m py_compile` (0 errors)
  - Database RLS: Verified live via anonymous PostgREST PATCH
