# TLCS Platform Updates - June 27, 2026

## 1. Mobile Application (Tv-Alert-Mobile)
- **The Lion Theme Aesthetics**: Implemented proprietary Lion Theme gradient styles and neon glowing header pills across the platform's Dashboard and Alerts feeds.
- **Trade Card Styling Logic**: Fixed a core bug in the `getAssetTheme` styling engine where Breakeven and Active trades (especially those closing via Trailing Stops) failed to display their background hues. Integrated the robust `resolveOutcome` calculation engine directly into the UI layer.
- **Outcome Pill Enhancements**: Added distinct left-border shading and matching text colors to the outcome badges inside the trade cards.
  - **Breakeven (B/E)**: Now displays a vibrant blue left border and blue text.
  - **Active / Open**: Now displays a clean gray left border and gray text.
- **Filter Reorganization**: Structurally relocated the `Opening Print / Bias` and `Day Type` interactive filters to be positioned strictly between the "MARKETS TODAY" and "MARKET WIDE PERFORMANCE" headers on the Analysis tab.

## 2. Main Website (TLCS_Website_Deploy)
- **Monthly Indicator Pricing Revision**: Updated `products.html` and `localization.js` to support new automated IP-based currency toggle prices for standard plans ($1, $9, $29, $49 / ₹99, ₹1,999, ₹4,999, ₹9,999).
- **Signals Rebranding**: Renamed the signals subscription plans header to **TLCS ALERTS INTELLIGENCE (AI) SUBSCRIPTION PLANS**.
- **Updated USPs for AI Subscriptions**:
  - **Professional Plan**: Updated features to include AI Pro Indicator access, website & app access, active/past trade analysis, and live pivot strategy research.
  - **Premium Plan**: Updated identical features aligning with the requested intelligence tier.
  - **Elite Plan**: Upgraded features to include both the TLCS AI Elite Indicator and Bonus Oscillator Indicator alongside standard intelligence features.
