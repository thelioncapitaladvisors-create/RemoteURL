# Obsidian Update Log (July 26) - V2.0 Analytics Edition (Hotfixes)

## Overview
This update implements critical responsiveness hotfixes to the Version 2.0 Analytics Edition architecture, resolving severe layout overflows in the mobile application and repairing a complex bug inside the Plotly Python engine that corrupted empty charts.

## Mobile CSP (Content Security Policy) Override
* **Bug**: The mobile application (deployed as a Next.js app via Vercel) featured an internal `next.config.js` with a rigorous `Content-Security-Policy`. The `frame-src` directive rigidly explicitly banned any external domains aside from Razorpay and Supabase.
* **Fix**: Added `https://thelioncapitalsolutions.com` to the mobile App's `frame-src` CSP directive to officially whitelist the Netlify-hosted tearsheet. 

## Plotly `bdata` Compression Glitch (Empty Markets)
* **Bug**: A user reported an issue asking "How can all equity curves align." When there are zero closed trades for the day, the VectorBT backtester mathematically generated returns of exactly `0.0`. Plotly Python aggressively compresses numpy arrays containing identical numbers into binary base64 `bdata` strings. However, standard iOS/Android WebViews fail to decode these empty binary strings natively. When Plotly loses its `Y` values, it defaults to plotting raw sequence indices (`y = [0, 1, 2, 3...]`). This resulted in artificial, perfectly overlapping diagonal lines dominating the chart across all empty markets.
* **Fix**: Intercepted the dataframe resampling engine in `backtest_edge.py`. The architecture now strictly detects all-zero `0.0` data columns and completely replaces them with `np.nan`. This instructs Plotly to skip rendering the trace completely, safely hiding inactive markets from the UI instead of falling back to broken `bdata` generation.

## Fluid Mobile Analytics UI
* **Bug**: The Analytics HTML UI overflowed the mobile screen boundaries, forcing horizontal touch-scrolling. The tab buttons were cut off, and the desktop-oriented Plotly modebar (camera, zoom icons) blocked the chart title.
* **Fix**: 
  - Eradicated `width: 100vw` inside the iframe styling (as it severely conflicts with mobile webview border boxes) and replaced it with strict `width: 100%` and `box-sizing: border-box`.
  - All generated Plotly traces explicitly inject `config={'responsive': True, 'displayModeBar': False}` to compress horizontally and permanently hide the desktop toolbar.
  - Re-styled the UI navigation tabs using a `.tab-container { display: flex }` and `.tab-btn { flex: 1 }` flexbox architecture, uniformly distributing the buttons evenly on one single line without requiring any swipe gestures.
