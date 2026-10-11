# Platform v1.0: Zero-Fictitious Data Purge, Default GG Light Theme & Login Viewport Parity

**Release Date:** October 11, 2026  
**Version:** v1.0.0 (Production Hardened Baseline)  
**System Scope:** Next.js Mobile Application (`Tv-Alert-Mobile`), Netlify Background Functions (`TLCS_Website_Deploy`), Supabase Database (`fno_eod_snapshots`, `auth.users`, `profiles`), Obsidian Knowledge Base.

---

## 1. Executive Summary

On October 11, 2026, Platform **Version 1.0** enforced an absolute zero-tolerance policy against any fictitious, artificial, simulated, or fallback fabricated numbers across the entire codebase and database infrastructure, alongside setting Golden Gate Light (**GG LIGHT**) as the canonical default visual skin for all users and compacting the login viewport to prevent any option clipping.

### Key Milestones Achieved:
1. **Total Eradication of Fictitious & Fabricated Fallback Data**:
   - Cleanly purged all stale database snapshot rows in Supabase table `fno_eod_snapshots` that were previously seeded with synthetic mock numbers (e.g. RELIANCE LTP ₹2,948.5, INFY LTP ₹1,932.1).
   - Eradicated all `basePrice`, `baseOI`, and synthetic volume/OI formulas from all F&O universe definitions and EOD sweeper cron workers (`Tv-Alert-Mobile/src/app/api/cron/eod-close/route.ts`, `TLCS_Website_Deploy/netlify/functions/cron-eod-close.js`, `/api/fno-buildups`, and `dhan-fno-buildups.js`).
   - The platform strictly requires authentic ticks from DhanHQ for at least 10 active stocks before saving any closing snapshot. When markets are closed and no genuine snapshot exists, the application displays strictly the institutional empty card (`🌙 MARKET CLOSED • EOD SNAPSHOT PENDING`) with zero stocks (`stocksList.length === 0`).

2. **GG Light as Canonical Default Theme (`goldengate-light`)**:
   - Configured **Golden Gate Light (`goldengate-light` / GG LIGHT)** as the default visual skin for all users on first-time login and application launch.
   - Synchronous head script in `layout.tsx` guarantees zero flash of dark mode (FOUC) on cold starts.
   - Login screen theme selector pills updated to feature `[GG LIGHT]` as the primary default active option.

3. **Login Viewport Realignment & Zero-Clipping Layout**:
   - Realigned the login screen in `AuthGuard.tsx` so that **Sign in with Google** and **Access via OTP** render side-by-side in a responsive 2-column grid (`grid grid-cols-2 gap-2`).
   - Realigned `Register` and `Forgot Password?` horizontally on a single line (`justify-between`), saving excessive vertical space.
   - Converted the footer from `absolute bottom-6` to in-flow (`mt-4 sm:mt-6`), completely eliminating button cut-off or floating collisions.

4. **Admin Email Confirmation & Zero-Lockout Enforcement**:
   - Direct verification executed in Supabase Auth Admin API for `connect@thelioncapitalsolutions.com` (`email_confirmed_at: 2026-10-11T03:38:22Z`), resolving the `EMAIL NOT CONFIRMED` error.
   - Database profile record upgraded to `role: 'admin'`, `subscription_type: 'owner'`, `subscription_status: 'active'`, and `has_indicator_access: true` under the Version 1.0 Admin Mandate.

---

## 2. Technical Modifications & Files Modified

### A. Mobile Application (`Tv-Alert-Mobile`)
- `src/components/AuthGuard.tsx`:
  - Default theme state and `ThemeContext` set to `'goldengate-light'`.
  - Added `Sunrise` icon for `[GG LIGHT]` pill on the login screen.
  - Realigned Google Login and OTP Access into a 2-column grid (`grid grid-cols-2 gap-2`).
  - Realigned Register / Forgot Password into a single horizontal row (`flex items-center justify-between`).
  - Converted footer from `absolute` to in-flow flex item (`mt-4 sm:mt-6`).
- `src/app/layout.tsx`:
  - Added default `theme-goldengate-light` class to `<html>`.
  - Injected instant synchronous inline script in `<head>` to resolve theme from `localStorage.getItem('tlcs_theme') || 'goldengate-light'`.
  - Set viewport `themeColor` to `#F8F9FC`.
- `src/app/api/fno-buildups/route.ts`:
  - Removed `basePrice` and `baseOI` properties from `FNO_UNIVERSE`.
- `src/app/api/cron/eod-close/route.ts`:
  - Removed `basePrice` and `baseOI` from `FNO_UNIVERSE`.
  - Refactored `sweepFnoEodSnapshot` to only push stocks with authentic DhanHQ ticks (`live.last_price > 0`).
  - Added threshold check (`allProcessed.length >= 10`) before persisting any snapshot.

### B. Deployment & Background Functions (`TLCS_Website_Deploy`)
- `netlify/functions/dhan-fno-buildups.js`:
  - Purged `basePrice` and `baseOI` from `FNO_UNIVERSE`.
- `netlify/functions/cron-eod-close.js`:
  - Purged `basePrice` and `baseOI` from `FNO_UNIVERSE`.
  - Purged synthetic `.map()` fallback calculations.
  - Required authentic DhanHQ ticks for at least 10 stocks before persisting snapshots.

### C. Supabase Database
- `fno_eod_snapshots`: Cleanly purged all stale rows containing fabricated October 7th mock data.
- `auth.users`: Confirmed email for `connect@thelioncapitalsolutions.com`.
- `profiles`: Upgraded permissions for `connect@thelioncapitalsolutions.com` to `role: admin`, `subscription_type: owner`.

### D. Governance & Documentation
- `AGENTS.md` and `.agents/AGENTS.md`: Added **Version 1.0 Zero-Fictitious Data & Total Fallback Purge Mandate** and **Version 1.0 Canonical Default Theme Mandate**.
- `Obsidian/39_Platform_v1_0_Zero_Fictitious_Data_Purge_Default_GG_Light_and_Login_Viewport_Parity.md`: This comprehensive architecture specification.
- Root Update Log: `Obsidian_Update_Log_Oct11_v1_0_Zero_Fictitious_Data_Purge_Default_GG_Light_and_Login_Viewport_Parity.md`.
