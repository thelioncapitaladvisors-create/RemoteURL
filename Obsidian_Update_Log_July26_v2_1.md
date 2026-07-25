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
