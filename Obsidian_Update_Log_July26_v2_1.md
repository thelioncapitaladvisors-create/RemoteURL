# TLCS Architecture Update Log
**Date:** July 26, 2026
**Version:** 2.1 (Performance Analytics & Security Update)

## 1. VectorBT 15-Min Comparative Market Analysis
The backend VectorBT engine (`algo_engine/backtest_edge.py`) has been overhauled to natively plot 6 simultaneous market timelines on a single interface. 
- It restricts the data query to the exact local `startOfToday` boundary.
- It pivots the market returns into a 6-column dataframe.
- It resamples strictly to a `15min` frequency for granular, synchronous intraday comparison across NIFTY, MCX, NYMEX, Cryptocurrency, Global Forex, and World Indices.

## 2. Cross-Origin Iframe Embedding Security for Mobile App
The live Netlify deployment's security headers (`TLCS_Website_Deploy/_headers`) were modified to completely strip the `X-Frame-Options: SAMEORIGIN` block.
- This globally opens the iframe gateway.
- It explicitly permits external Capacitor/Expo environments (like the live Mobile App) to seamlessly embed and auto-refresh the VectorBT tearsheet on the newly built ANALYTICS tab without triggering browser origin policy violations.

## 3. Interactive Analytics Tearsheet Interface
Replaced the static, single-plot VectorBT output with a custom, dark-mode HTML template.
- The tearsheet now features interactive vanilla JS tab filters to seamlessly toggle between 3 distinct dynamic Plotly visualizations (Full Equity Curve, Drawdowns, and Raw Returns) without reloading the iframe.
- Admin panel branding was streamlined by removing specific framework references.
