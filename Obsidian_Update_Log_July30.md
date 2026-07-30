# TLCS Update Log: July 30, 2026

## 1. Supabase CDN Independence & SSO Interception Fix
- **The Issue**: Users were reporting that "None of the login options working on the landing and other pages." This was primarily caused by the `supabase-js-v2` library being loaded via `cdn.jsdelivr.net`. On certain browsers (like Brave with strict shields) or restrictive network firewalls, this CDN request was blocked. 
- **The Consequence**: When the script failed to load, `window.supabase` was left undefined, causing silent JavaScript failures that prevented the `bootAuth()` initialization from finishing. This broke the SSO interceptor for the "Launch App" button and prevented the UI from updating the static "Login" links.
- **The Fix**: Downloaded and permanently vendored the `supabase-js-v2.min.js` file locally within the `TLCS_Website_Deploy` folder. All 11 HTML pages across the website have been updated to point to this local script, fully immunizing the platform against CDN adblocker and firewall restrictions.

## 2. Bulletproof DOMContentLoaded Timing Constraints
- **The Issue**: In both `auth.js` and `main.js`, initialization functions (`bootAuth` and `initMain`) were bound strictly using `document.addEventListener('DOMContentLoaded', ...)`. 
- **The Consequence**: Because these scripts were included at the bottom of the `<body>` tag synchronously, standard browser HTML parsing behavior occasionally meant that the `DOMContentLoaded` event fired *before* the script even executed its event listener. This resulted in the auth loops and mobile navigation logic never initializing.
- **The Fix**: Wrapped all initialization bindings with a robust `document.readyState` fallback. 
  ```javascript
  if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initFn);
  } else {
      initFn();
  }
  ```
  This ensures the initialization functions always run, regardless of asynchronous delays, network conditions, or early HTML parsing completions.
