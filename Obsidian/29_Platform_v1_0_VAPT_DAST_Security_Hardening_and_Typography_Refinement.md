# Platform v1.0: VAPT, DAST Security Hardening & Typography Refinement

**Date**: October 4, 2026  
**Version**: v1.0.0 / v1.0  
**Status**: Institutional Security Hardened & Verified  

---

## 1. Executive Summary
A comprehensive security and presentation audit (VAPT, DAST, OWASP Top 10, privilege escalation analysis, and legibility review) was conducted across both primary applications (`Tv-Alert-Mobile` and `TLCS_Website_Deploy`). All vulnerabilities, privilege escalation vectors, duration tampering risks, credential exposures, clickjacking surfaces, open redirect loopholes, and contrast/typography defects were identified, remediated, and verified.

---

## 2. VAPT & DAST Security Hardening Matrix

### A. Subscription Duration Tampering & IDOR Protection (`/api/subscribe`)
- **Vulnerability**: Client-supplied `metadata.days` or altered pricing payloads could theoretically tamper with subscription durations if not strictly gated.
- **Remediation**:
  1. Enforced Bearer token authentication via `supabase.auth.getUser()`.
  2. Verified IDOR protection (`user.id === userId`).
  3. Locked subscription duration strictly on the server using canonical pricing lookup (`2999` -> 30d, `6999` -> 90d, `11999` -> 180d, `19999` -> 365d).
  4. Discarded any client-passed duration overrides.

### B. Database Privilege Escalation Shield (`HARDEN_PROFILES_RLS.sql`)
- **Vulnerability**: Authenticated users attempting to self-elevate `role` to `'admin'` or modify `subscription_status` / `subscription_end_date` directly in `profiles`.
- **Remediation**:
  1. Created PostgreSQL trigger function `public.protect_profile_security_fields()`.
  2. Bound BEFORE UPDATE trigger `trg_protect_profile_security_fields` on `public.profiles`.
  3. Strict denial of modifications to `role`, `subscription_status`, `subscription_plan`, and `subscription_end_date` unless executed by `service_role` or authorized admin.

### C. Zero Credential Exposure in Repositories
- **Remediation**:
  1. Scrubbed hardcoded fallback client IDs, PINs, and TOTP secrets from `api/fno-buildups/route.ts`, `api/option-chain/route.ts`, `netlify/functions/dhan-auth.js`, and `netlify/functions/dhan-option-chain.js`.
  2. Removed VAPID key samples from comment headers in `send-push-background.js`.
  3. Enforced strictly runtime environment variables (`process.env`).

### D. Anti-Clickjacking & XSS Protection
- **Remediation**:
  1. Removed `frame-ancestors *` wildcard from `TLCS_Website_Deploy/_headers`, locking iframe embedding strictly to `self`, `https://thelioncapitalsolutions.com`, and `https://tlcsterminal.netlify.app`.
  2. Implemented `sanitizeRedirectUrl()` in `login.html` blocking external protocols (`http:`, `https:`, `javascript:`, `data:`, `//`).

### E. Internal Cron & Background Worker Protection
- **Remediation**:
  1. Guarded `dhan-scanner-background.js`, `cron-dhan-scanner.js`, and `dhan-auth.js` with internal secret (`x-internal-secret` / `WEBHOOK_SECRET`) and Supabase admin authentication.

---

## 3. Typography & Contrast Architecture

### A. Shiny Card Isolation & Crispness Fix
- **Root Cause**: `.shiny-card::before` had `z-index: 1` and a 60% solid white gradient overlay covering card contents in light themes, causing a milky/opaque haze over text.
- **Remediation**:
  1. Applied `isolation: isolate` to `.shiny-card`.
  2. Assigned `z-index: 2` to all card children (`.shiny-card > *`).
  3. Positioned `.shiny-card::before` at `z-index: 0` with reduced opacity (`0.15`).
  4. Added global `-webkit-font-smoothing: antialiased` and `text-rendering: optimizeLegibility`.
  5. Enhanced light theme dark slate tokens: `--text-primary: #020617`, `--text-secondary: #0F172A`, `--text-dim: #334155`.

### B. F&O Stock Buildups Block Font Scaling
- Increased font sizes and contrast across:
  - Header & Subtitle (`text-[11px] sm:text-[12px] font-bold text-secondary`).
  - Market Breadth counter & sentiment pill (`text-xs sm:text-[13px] font-bold`).
  - 4 Filter Tabs (`text-xs sm:text-[13px] font-mono font-black`).
  - Active Stock Cards (Rank, Symbol, Sector, LTP, OI, Volume, Intensity meter).
  - Stock Analysis Modal (`text-xl font-black` title, `text-lg` prices, `text-xs` descriptions).

---

## 4. Verification & Build Integrity
- `Tv-Alert-Mobile`: Next.js 14.2.35 production build succeeded with **0 errors**.
- `TLCS_Website_Deploy`: Node.js syntax check across all Netlify functions passed with **0 errors**.
- Local backup archives and remote GitHub repositories synchronized under Version `v1.0` / `v1.0.0`.
