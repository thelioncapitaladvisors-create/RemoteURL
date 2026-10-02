# Platform V7.0: Admin Whitelisting, Black Box Parity, Window Title & Golden Gate Light Architecture

**Document Version:** 7.0  
**Effective Date:** October 2, 2026  
**Status:** PRODUCTION HARDENED  
**Infrastructure & Environment:** Netlify Exclusive (`thelioncapitalsolutions.com` / `market-store.online`)  

---

## 1. Application Name & Top Window Title Standardization

### Objective & Implementation
* **PWA Standalone Window Border**: The macOS desktop wrapper / Chrome PWA standalone window title bar previously rendered `TLCS Intelligence - TLCS Terminal`.
* **Standardized Identity**: Updated both HTML metadata title and web app manifest to **`The Lion Capital Solutions TERMINAL`**:
  * **Next.js Root Layout (`Tv-Alert-Mobile/src/app/layout.tsx`)**:
    * `metadata.title` set to `"The Lion Capital Solutions TERMINAL"`.
    * `metadata.description` set to `"The Lion Capital Solutions TERMINAL for Paid Subscribers"`.
    * `<meta name="apple-mobile-web-app-title">` updated to `"The Lion Capital Solutions TERMINAL"`.
  * **Web App Manifest (`Tv-Alert-Mobile/public/manifest.json`)**:
    * `"name"` set to `"The Lion Capital Solutions TERMINAL"`.
    * `"short_name"` set to `"The Lion Capital Solutions TERMINAL"`.
* **Visual Result**: Eliminates compound strings and cleanly renders `The Lion Capital Solutions TERMINAL` across the top window border on macOS and PWA devices.

---

## 2. Universal "BLACK BOX" Autonomous Engine Label Parity

### Objective & Implementation
* **Deprecation of Legacy "DhanHQ 100" Labeling**: All instances of `DhanHQ 100 (Black Box)` and `DHANHQ 100 (BLACK BOX ⚡)` across all mobile tabs have been standardized to strictly **`BLACK BOX`**.
* **Cross-Tab Parity**:
  * **HUB Tab (`DASHBOARD`)**:
    * Parameter Matrix Subtitle: `Standalone 15m Black Box`.
    * Data Source Toggle Button: `BLACK BOX` with subtext `⚡ Standalone Black Box`.
  * **Normalized Trade Performance**: Top ribbon badge `⚡ BLACK BOX` with subtitle `AUTONOMOUS 15M QUANT BLACK BOX DISTRIBUTION`.
  * **LOGS Tab (`ALERTS`)**: Section header badge `⚡ BLACK BOX`, data source toggle button `BLACK BOX`, and subtext `⚡ Standalone Black Box`.
  * **MARKETS Tab (`ANALYSIS`)**: Real-time trajectory badge `⚡ BLACK BOX`.
  * **INSIGHTS Tab (`INSIGHTS`)**: Header badge `⚡ BLACK BOX`, toggle button `BLACK BOX`, and subtext `⚡ Standalone Black Box`.
  * **ANALYTICS Tab (`ANALYTICS`)**: Header badge `⚡ BLACK BOX`, toggle button `BLACK BOX`, and subtext `⚡ Standalone Black Box`.

---

## 3. Authorized Admin User Whitelist Expansion (`connect@thelioncapitalsolutions.com`)

### Objective & Implementation
* **Owner-Authorized Whitelist Expansion**: `connect@thelioncapitalsolutions.com` added to the immutable authorized admin user whitelist across both mobile and web ecosystems.
* **Mobile Terminal & PWA (`Tv-Alert-Mobile`)**:
  * `page.tsx`: Whitelisted in `APPROVED_ADMIN_EMAILS` with direct `isAdmin` verification, unlocking the `<Target />` Terminal Menu, the Autonomous Engine Selector (`TV PROD`, `BLACK BOX LIVE`, `PARITY AUDIT`), Visual Skins, and Audio Signature controls.
  * `AuthGuard.tsx`: Whitelisted in `APPROVED_ADMIN_EMAILS` and granted immediate unrestricted `owner`/`admin` role and active subscription privileges.
  * Admin API Endpoints (`admin-purge/route.ts`, `system-audit/route.ts`, `test-telegram/route.ts`): Fully authorized for administrative purge, audit, and testing routines.
* **Web Dashboard & Serverless Workers (`TLCS_Website_Deploy`)**:
  * `auth.js`: Whitelisted in `APPROVED_ADMIN_EMAILS` and granted bypass in `enforceSubscriptionSession`, `verifyPageAccess`, `checkTerminalAccess`, and `updateAuthUI` (revealing the desktop `⚙️ Admin Panel` button and mobile drawer links).
  * `admin.html`: Auth gate bypassed for management of trade signals, golden nuggets, blog posts, and pivot levels.
  * `dashboard.html`: Engine source selector displayed upon login.
  * Netlify Serverless Functions (`admin-clear-signals.js`, `admin-delete-item.js`, `system-audit.js`, `test-telegram.js`, `test-instagram.js`): Authorized for all administrative mutations.

---

## 4. macOS Golden Gate 27.0.1 Light Theme & "RISK ISHQ" Audio Signature

### macOS Golden Gate Light (Non-Dark) Theme
* **Visual Philosophy**: Liquid glass specular refraction with frosted 24px blur (`saturate(180%)`) combined with a California daylight pearlescent canvas (`#F8F9FC`) and frosted white glass surfaces (`#FFFFFF`).
* **Typography**: High-contrast California slate typography (`#0F172A`) for Retina-grade daylight readability.
* **Accents**: International Orange (`#FF5E3A`) accents, macOS Emerald (`#16A34A`), and Crimson (`#DC2626`) indicators.
* **Theme Picker**: Upgraded to 7 responsive skins (`DARK`, `SLATE`, `LIGHT`, `THE LION`, `GG DARK`, `GG LIGHT`, `AUTO`).

### "RISK ISHQ" Sound Theme
* **Cultural Reference**: Harshad Mehta's iconic dialogue *"Risk Hai Toh Ishq Hai"* from the *Scam 1992* soundtrack (composed by Achint Thakkar).
* **Audio Synthesis Hook**: 7-note D-minor blues hook:
  16424	ext{D4 (293.66 Hz)} \longrightarrow 	ext{F4} \longrightarrow 	ext{G4} \longrightarrow \mathbf{G\sharp 4\ (415.30\ Hz)} \longrightarrow 	ext{G4} \longrightarrow 	ext{F4} \longrightarrow 	ext{D4}16424
* **Tone**: Low-pass filtered resonant sawtooth synth wave with sub-bass sine oscillator (.83	ext{ Hz}$).
