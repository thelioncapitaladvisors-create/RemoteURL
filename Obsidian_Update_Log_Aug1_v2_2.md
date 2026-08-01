# TLCS Update Log: August 1, 2026

## 1. Webhook Payload JSON Compliance (Pine Script)
- **The Issue**: The `TLCS_Native_Oscillator.pine` script was generating plain text alert messages (`Alert : Bearish Hidden Divergence...`) rather than a structured JSON payload for its `alert()` call. 
- **The Consequence**: The Netlify backend (`process-webhook-background.js`) strictly requires a JSON format to extract the trigger, secret, and symbol. The backend fallback parser failed to extract critical fields and threw a `400 Bad Request`. However, because Netlify background functions (`*-background.js`) instantly return an `HTTP 202 Accepted` status before execution, TradingView erroneously logged the webhook as "Successfully delivered" (green tick), masking the silent failure. This caused live signals to never reach the Supabase database.
- **The Fix**: Rewrote the `alert()` logic in `TLCS_Native_Oscillator.pine` to explicitly construct the properly formatted `_divPay` JSON object, perfectly mirroring the robust implementation in `TLCS_Native_Divergence.pine`. Additionally added the missing `webhook_secret` input field to the script.

## 2. Dashboard Realtime Connection Hang (Supabase JS)
- **The Issue**: The web dashboard (`dashboard.html` and other pages) was perpetually stuck on the "CONNECTING..." state for its live performance feed. 
- **The Consequence**: The locally hosted `supabase-js-v2.min.js` file was fundamentally corrupted. It was an 86-byte file containing a CDN firewall policy rejection error (`Request to GET ... not allowed by policy`) instead of the actual JavaScript library code. As a result, `window.supabase` remained undefined, causing the frontend initialization (`window.sb()`) to return `null` and trap the `loadPerformanceSnapshot` function in an infinite retry loop.
- **The Fix**: Replaced the broken local `<script src="supabase-js-v2.min.js">` tag with the official unpkg CDN link (`https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2`) across all 11 HTML pages in the `TLCS_Website_Deploy` folder, fully restoring frontend realtime connectivity.
