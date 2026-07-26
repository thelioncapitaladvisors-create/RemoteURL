# TLCS Architecture Update Log
**Date:** July 26, 2026
**Version:** 2.1 (Performance Analytics & Security Update)

## 1. VectorBT 15-Min Comparative Market Analysis
The backend VectorBT engine (`algo_engine/backtest_edge.py`) has been overhauled to natively plot 6 simultaneous market timelines on a single interface. 
- It restricts the data query to the exact local `startOfToday` boundary.
- It pivots the market returns into a 6-column dataframe.
- It resamples strictly to a `15min` frequency for granular, synchronous intraday comparison across NIFTY, MCX, NYMEX, Cryptocurrency, Global Forex, and World Indices.

## 2. Cross-Origin Iframe Embedding Security for Mobile App
The live Netlify deployment's security headers (`TLCS_Website_Deploy/_headers`) were overhauled to definitively fix Capacitor/Expo mobile embedding blocks.
- Completely removed indented `X-Frame-Options` comments that were misparsed by Netlify as live headers.
- Explicitly added `frame-ancestors *;` to the `Content-Security-Policy` to globally whitelist external webview framing without triggering browser origin policy violations.
- Whitelisted `https://cdn.plot.ly` in the CSP `script-src` to guarantee the embedded VectorBT dynamic charts successfully download and render on the new ANALYTICS tab.

## 3. Interactive Analytics Tearsheet Interface
Replaced the static, single-plot VectorBT output with a custom, dark-mode HTML template.
- The tearsheet now features interactive vanilla JS tab filters to seamlessly toggle between 3 distinct dynamic Plotly visualizations (Full Equity Curve, Drawdowns, and Raw Returns) without reloading the iframe.
- Admin panel branding was streamlined by removing specific framework references.

## 4. UI/UX Improvements & Feature Access (Version 2.1 Finalization)
- **Mobile Analytics Table Layout**: Restructured the Analytics tab in the Next.js mobile application to expand the statistics table container height (`min-h-[1100px]`), removing internal scrolling and allowing users to view all backtest metric rows sequentially via native app scrolling.
- **Frozen Statistics Headers**: Updated the VectorBT HTML generator (`algo_engine/backtest_edge.py`) to freeze the top row (`thead th`) of the statistics table using `position: sticky`. It dynamically overlaps with the already frozen first column via `z-index` layering to ensure market category names remain visible during vertical scrolling.
- **Website Products Page Optimization**: Relocated the "Terminal & Contact" section from the AI Dashboard to the Products page, positioning it below the subscription pricing to streamline user inquiries.
- **Public Performance Analytics**: Moved the comprehensive "Alerts Intelligence Edge: Performance Analytics" iframe from the authenticated Admin panel directly into the public AI Dashboard. This guarantees that all website visitors, regardless of subscription status, can view the live multi-market statistical tearsheet.
- **Version Bumping**: Standardized the overarching application version tags to **v2.1** across both the mobile application (`page.tsx`) and the website endpoints (`auth.js`, `sw.js`).

## 5. Data Integrity and Security Enhancements
- **Webhook and Frontend Security**: Completed a security audit verifying that no `SERVICE_ROLE` keys are exposed, and all database updates (`.update`, `.insert`, etc.) securely pass through authenticated serverless webhook endpoints instead of client-side queries. Verified Supabase v2 PostgREST syntax compliance.
- **Canonical `resolveOutcome` Fix**: Permanently patched a critical data regression across all 5 UIs (`trade-metrics.js`, `scanner.js`, `commodity-scanner.js`, `dashboard.html`, and `page.tsx`). The engine now calculates the mathematical `exact_pct` prior to executing any legacy string keyword evaluations, completely eliminating the "Hit B/E" miscategorization error.
- **Date Parsing Safety**: Audited `Intl.DateTimeFormat` across the codebase, confirming that backend derivations properly wrap instances in an `!isNaN()` check before execution to mitigate fatal `RangeError: Invalid time value` crashes.
