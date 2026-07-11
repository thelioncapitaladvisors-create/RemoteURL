# TLCS Platform Updates - July 10, 2026

## 1. Mobile App Fix: Market Categorization & Insights Alignment
*   **Strict Symbol Normalization**: Refactored the `getCategory` function in the mobile app (`page.tsx`) to enforce strict prefix stripping (e.g., removing `NSE:`, `TVC:`, and `1!` suffixes) before symbol matching.
*   **Exact Market Lists**: Hardcoded the exact sets from the definitive Global Market Symbols memory (nifty, mcx, nymex, crypto, forex, world) instead of relying on loose `.includes` checks.
*   **Total Trades Integrity**: Resolved a bug where un-normalized or loosely mapped symbols (like `BANKEX`, `SENSEX`) were falling into an invisible `OTHER` category. The Market Performance section in the INSIGHTS tab now accurately tracks and aggregates every trade, perfectly syncing its displayed sums with the "Today's Trades" overall count (e.g., 150 trades).
